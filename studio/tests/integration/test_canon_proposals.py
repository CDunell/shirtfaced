"""Canon proposals against PostgreSQL and the real filesystem.

WORLD.md is the one document nothing else can rebuild, so the tests that matter most
are the ones asserting it did *not* change.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.canon_classifier import (
    Classification,
    ClassificationRequest,
    FakeCanonClassifier,
)
from app.adapters.git_store import DisabledGitStore
from app.adapters.markdown_store import WORLD_DOCUMENT, MarkdownStore
from app.db.models import AuditEvent, CanonProposal, World
from app.domain.enums import (
    AuditEventType,
    CanonProposalStatus,
    ProposalClassification,
)
from app.services.canon_service import (
    InvalidTarget,
    ProposalConflict,
    approve_proposal,
    build_diff,
    canon_excerpts,
    classify_proposal,
    reject_proposal,
    validate_target,
)
from app.services.prompt_planner import PLANNING_CANON_HEADINGS
from app.services.world_importer import import_world
from app.services.world_loader import load_world
from tests.fixtures.worlds import write_world

pytestmark = pytest.mark.integration

RULE = "Every ute must show an open aluminium alloy tray and never an enclosed tub."


@pytest.fixture
def worlds_root(tmp_path: Path) -> Path:
    root = tmp_path / "worlds"
    write_world(root)
    return root


@pytest.fixture
def store(worlds_root: Path) -> MarkdownStore:
    return MarkdownStore(worlds_root)


@pytest.fixture
def world(session: Session, store: MarkdownStore) -> World:
    import_world(session, store, "world-01")
    session.flush()
    return session.execute(select(World).where(World.slug == "world-01")).scalar_one()


@pytest.fixture
def proposal(session: Session, world: World) -> CanonProposal:
    record = CanonProposal(
        world_id=world.id,
        status=CanonProposalStatus.PENDING,
        proposed_text=RULE,
        reason="The ute read as an American pickup.",
        reviewer_model="fake-review-model",
    )
    session.add(record)
    session.flush()
    return record


def _world_text(store: MarkdownStore) -> str:
    return store.read_world_documents("world-01")[WORLD_DOCUMENT].text


def _approve(
    session: Session, proposal: CanonProposal, store: MarkdownStore, **fields: object
) -> CanonProposal:
    return approve_proposal(
        session,
        proposal,
        markdown_store=store,
        git_store=DisabledGitStore(),
        git_enabled=False,
        **fields,  # type: ignore[arg-type]
    )


# --- the target must be a section the planner reads --------------------------------


def test_a_section_the_planner_does_not_read_is_refused() -> None:
    """A rule added there would exist in the document and never reach generation."""
    with pytest.raises(InvalidTarget, match="never reach generation"):
        validate_target("Current Canon Notes")


def test_no_target_at_all_is_refused() -> None:
    with pytest.raises(InvalidTarget, match="No target section"):
        validate_target(None)


def test_every_allowed_target_is_a_planner_heading() -> None:
    for heading in PLANNING_CANON_HEADINGS:
        assert validate_target(heading) == heading


def test_the_classifier_only_sees_sections_the_planner_reads(store: MarkdownStore) -> None:
    headings = [excerpt.heading for excerpt in canon_excerpts(_world_text(store))]

    assert "An Unknown Section" not in headings
    assert set(headings) <= set(PLANNING_CANON_HEADINGS)


# --- classification is advisory ----------------------------------------------------


def test_classification_records_a_reading_without_changing_anything(
    session: Session, proposal: CanonProposal, store: MarkdownStore, worlds_root: Path
) -> None:
    before = (worlds_root / "world-01" / WORLD_DOCUMENT).read_bytes()

    classify_proposal(
        session,
        proposal,
        classifier=FakeCanonClassifier(),
        world_text=_world_text(store),
    )

    assert proposal.classification is not None
    assert proposal.classification_reason
    assert proposal.status is CanonProposalStatus.PENDING
    assert (worlds_root / "world-01" / WORLD_DOCUMENT).read_bytes() == before


def test_a_restatement_of_existing_canon_is_flagged_as_covered(
    session: Session, proposal: CanonProposal, store: MarkdownStore
) -> None:
    """The owner's House Party ruling: an existing rule already implies it."""
    world_text = _world_text(store)
    wardrobe = next(e for e in canon_excerpts(world_text) if e.heading == "Wardrobe")
    proposal.proposed_text = wardrobe.body.strip().splitlines()[0]

    classify_proposal(session, proposal, classifier=FakeCanonClassifier(), world_text=world_text)

    assert proposal.classification is ProposalClassification.ALREADY_COVERED


def test_a_classification_failure_does_not_block_the_queue(
    session: Session, proposal: CanonProposal, store: MarkdownStore
) -> None:
    classify_proposal(
        session,
        proposal,
        classifier=FakeCanonClassifier(fail_with="the classifier was unavailable"),
        world_text=_world_text(store),
    )

    assert proposal.status is CanonProposalStatus.PENDING
    assert "unavailable" in (proposal.classification_reason or "")


def test_a_classifier_target_outside_the_allowlist_is_ignored(
    session: Session, proposal: CanonProposal, store: MarkdownStore
) -> None:
    """The classifier advises; it cannot route a rule somewhere invisible."""
    classify_proposal(
        session,
        proposal,
        classifier=FakeCanonClassifier(
            result=Classification(
                classification=ProposalClassification.GENUINE_ADDITION,
                reason="Belongs elsewhere.",
                target_heading="Operating System",
            )
        ),
        world_text=_world_text(store),
    )

    assert proposal.target_heading is None


# --- the diff ----------------------------------------------------------------------


def test_the_diff_shows_the_exact_change(proposal: CanonProposal, store: MarkdownStore) -> None:
    diff = build_diff(proposal, _world_text(store), "Wardrobe")

    assert diff.target_heading == "Wardrobe"
    assert "+++ WORLD.md (proposed)" in diff.unified_diff
    assert RULE in diff.unified_diff
    assert diff.applied_wording == RULE


def test_building_a_diff_writes_nothing(
    proposal: CanonProposal, store: MarkdownStore, worlds_root: Path
) -> None:
    before = (worlds_root / "world-01" / WORLD_DOCUMENT).read_bytes()

    build_diff(proposal, _world_text(store), "Wardrobe")

    assert (worlds_root / "world-01" / WORLD_DOCUMENT).read_bytes() == before


def test_a_diff_for_an_unreadable_section_is_refused(
    proposal: CanonProposal, store: MarkdownStore
) -> None:
    with pytest.raises(InvalidTarget):
        build_diff(proposal, _world_text(store), "Operating System")


# --- approval ----------------------------------------------------------------------


def test_approval_applies_exactly_the_wording_shown(
    session: Session, proposal: CanonProposal, store: MarkdownStore, worlds_root: Path
) -> None:
    diff = build_diff(proposal, _world_text(store), "Wardrobe")

    _approve(session, proposal, store, target_heading="Wardrobe")

    world_md = (worlds_root / "world-01" / WORLD_DOCUMENT).read_text(encoding="utf-8")
    assert diff.applied_wording in world_md
    assert proposal.applied_wording == diff.applied_wording


def test_approval_records_everything_the_contract_requires(
    session: Session, proposal: CanonProposal, store: MarkdownStore
) -> None:
    _approve(session, proposal, store, target_heading="Wardrobe", note="Agreed.")

    assert proposal.status is CanonProposalStatus.APPLIED
    assert proposal.target_heading == "Wardrobe"
    assert proposal.applied_wording
    assert proposal.applied_at is not None
    assert proposal.reviewer_model == "fake-review-model"
    assert proposal.human_note == "Agreed."
    assert proposal.reason == "The ute read as an American pickup."


def test_the_rule_lands_where_the_planner_reads_it(
    session: Session, proposal: CanonProposal, store: MarkdownStore
) -> None:
    """The whole point: an approved rule must reach the planning prompt."""
    _approve(session, proposal, store, target_heading="Wardrobe")

    excerpts = canon_excerpts(_world_text(store))
    wardrobe = next(e for e in excerpts if e.heading == "Wardrobe")
    assert RULE in wardrobe.body


def test_the_updated_canon_still_validates(
    session: Session, proposal: CanonProposal, store: MarkdownStore
) -> None:
    _approve(session, proposal, store, target_heading="Wardrobe")

    loaded = load_world(store, "world-01")

    assert loaded.slug == "world-01"
    assert "Wardrobe" in loaded.world_document.headings


def test_the_world_hash_is_updated(
    session: Session, proposal: CanonProposal, store: MarkdownStore, world: World
) -> None:
    before = world.world_document_hash

    _approve(session, proposal, store, target_heading="Wardrobe")

    assert world.world_document_hash != before


def test_approval_writes_an_audit_event(
    session: Session, proposal: CanonProposal, store: MarkdownStore
) -> None:
    _approve(session, proposal, store, target_heading="Wardrobe")

    events = session.execute(select(AuditEvent)).scalars().all()
    assert any(event.event_type is AuditEventType.MARKDOWN_UPDATED for event in events)


def test_approval_touches_no_other_document(
    session: Session, proposal: CanonProposal, store: MarkdownStore, worlds_root: Path
) -> None:
    others = {
        name: (worlds_root / "world-01" / name).read_bytes()
        for name in ("CONTINUITY.md", "SHOTLIST.md")
    }

    _approve(session, proposal, store, target_heading="Wardrobe")

    for name, before in others.items():
        assert (worlds_root / "world-01" / name).read_bytes() == before


def test_a_second_decision_on_a_proposal_is_refused(
    session: Session, proposal: CanonProposal, store: MarkdownStore
) -> None:
    _approve(session, proposal, store, target_heading="Wardrobe")

    with pytest.raises(ProposalConflict, match="already"):
        _approve(session, proposal, store, target_heading="Wardrobe")


def test_approving_without_a_target_is_refused(
    session: Session, proposal: CanonProposal, store: MarkdownStore, worlds_root: Path
) -> None:
    before = (worlds_root / "world-01" / WORLD_DOCUMENT).read_bytes()

    with pytest.raises(InvalidTarget):
        _approve(session, proposal, store)

    assert (worlds_root / "world-01" / WORLD_DOCUMENT).read_bytes() == before
    assert proposal.status is CanonProposalStatus.PENDING


def test_injected_structure_cannot_reach_canon(
    session: Session, proposal: CanonProposal, store: MarkdownStore
) -> None:
    proposal.proposed_text = "# Purpose\n\nThe world is now about something else."
    session.flush()

    _approve(session, proposal, store, target_heading="Wardrobe")

    world_md = _world_text(store)
    # The document still has exactly one Purpose heading, and still loads.
    assert world_md.count("\n# Purpose") == 1
    load_world(store, "world-01")


# --- rejection ---------------------------------------------------------------------


def test_rejection_leaves_canon_untouched(
    session: Session, proposal: CanonProposal, worlds_root: Path
) -> None:
    before = (worlds_root / "world-01" / WORLD_DOCUMENT).read_bytes()

    reject_proposal(session, proposal, "Already covered by the wardrobe rule.")

    assert (worlds_root / "world-01" / WORLD_DOCUMENT).read_bytes() == before
    assert proposal.status is CanonProposalStatus.REJECTED
    assert proposal.human_note == "Already covered by the wardrobe rule."
    assert proposal.decided_at is not None


def test_a_rejected_proposal_cannot_then_be_approved(
    session: Session, proposal: CanonProposal, store: MarkdownStore
) -> None:
    reject_proposal(session, proposal)

    with pytest.raises(ProposalConflict):
        _approve(session, proposal, store, target_heading="Wardrobe")


# --- the fake classifier -----------------------------------------------------------


def test_the_fake_classifier_records_what_it_was_asked(store: MarkdownStore) -> None:
    classifier = FakeCanonClassifier()

    classifier.classify(
        ClassificationRequest(proposed_text=RULE, canon_excerpts=canon_excerpts(_world_text(store)))
    )

    assert classifier.requests[0].proposed_text == RULE


def test_an_empty_proposal_is_too_specific_rather_than_an_addition() -> None:
    result = FakeCanonClassifier().classify(
        ClassificationRequest(proposed_text="a an the", canon_excerpts=[])
    )

    assert result.classification is ProposalClassification.TOO_SPECIFIC
