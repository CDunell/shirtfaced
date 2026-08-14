"""The design pipeline's guarantees, held against a real database.

The rules under test are the ones that make an approval mean something: a
decision is immutable, signed and singular; versions are per-concept and
monotonic; the master asset is pinned by the database; and a linked composed
design never tells a different story from its attempt.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.db.concept_models import DesignBrief, DesignConcept
from app.domain.enums import (
    CollectionRole,
    ConceptStatus,
    DesignAssetKind,
    DesignAttemptMethod,
    DesignAttemptState,
    DesignDecisionKind,
    GraphicArchetype,
)
from app.services.concept_importer import import_concepts
from app.services.concept_loader import parse_concept_library
from app.services.design_pipeline import (
    DesignPipelineConflict,
    InvalidDesignAction,
    approve_design,
    create_attempt,
    decide_attempt,
    next_concept,
    record_asset,
    submit_attempt,
)
from tests.fixtures.concepts import VALID_LIBRARY

pytestmark = pytest.mark.integration

SVG = b'<svg xmlns="http://www.w3.org/2000/svg"><text>ABSOLUTE WEAPON</text></svg>'


@pytest.fixture
def store(tmp_path: Path) -> FilesystemAssetStore:
    return FilesystemAssetStore(tmp_path)


@pytest.fixture
def unbriefed(session: Session) -> DesignConcept:
    """A concept as the importer leaves it: an idea, with no product decided."""
    loaded = parse_concept_library(VALID_LIBRARY, source_path="docs/design/FIXTURE.md")
    import_concepts(session, loaded)
    session.flush()
    found = next_concept(session)
    assert found is not None
    return found


@pytest.fixture
def concept(session: Session, unbriefed: DesignConcept) -> DesignConcept:
    """The same concept with a brief, because since Phase 4 an attempt cannot
    open without one.

    The tests below are about the pipeline -- attempts, decisions, versions --
    and the brief is a precondition of reaching it rather than their subject.
    The gate itself is tested by ``test_an_attempt_needs_a_brief_first``.
    """
    unbriefed.brief = DesignBrief(
        concept_id=unbriefed.id,
        collection_role=CollectionRole.CORE,
        graphic_archetype=GraphicArchetype.TYPOGRAPHIC_HERO,
    )
    session.flush()
    return unbriefed


def _submitted(session: Session, store: FilesystemAssetStore, concept: DesignConcept):
    attempt = create_attempt(session, concept, DesignAttemptMethod.MANUAL_IMPORT)
    record_asset(
        session, store, attempt, DesignAssetKind.ARTWORK, "design.svg", SVG, "image/svg+xml"
    )
    return submit_attempt(session, attempt)


# --- The brief gates artwork -------------------------------------------------


def test_an_attempt_needs_a_brief_first(session: Session, unbriefed: DesignConcept) -> None:
    """Constitution steps 2 and 4, enforced where artwork begins.

    The audit's diagnosis of generic output was that the bench produced a
    graphic idea and jumped straight to artwork. This is the jump, refused.
    """
    with pytest.raises(InvalidDesignAction) as refused:
        create_attempt(session, unbriefed, DesignAttemptMethod.MANUAL_IMPORT)

    message = str(refused.value)
    assert "a collection role" in message
    assert "a graphic archetype" in message
    assert "before any artwork exists" in message


def test_a_half_written_brief_still_refuses_and_names_the_gap(
    session: Session, unbriefed: DesignConcept
) -> None:
    unbriefed.brief = DesignBrief(concept_id=unbriefed.id, collection_role=CollectionRole.HERO)
    session.flush()

    with pytest.raises(InvalidDesignAction) as refused:
        create_attempt(session, unbriefed, DesignAttemptMethod.MANUAL_IMPORT)

    message = str(refused.value)
    assert "a graphic archetype" in message
    assert "a collection role" not in message


def test_a_briefed_concept_opens_an_attempt(session: Session, concept: DesignConcept) -> None:
    attempt = create_attempt(session, concept, DesignAttemptMethod.MANUAL_IMPORT)

    assert attempt.attempt_number == 1
    # The brief travels with the attempt, so it stays explicable if the brief
    # changes afterwards.
    assert attempt.brief_snapshot["title"] == concept.title


# --- The queue ---------------------------------------------------------------


def test_next_concept_is_the_lowest_live_number(session: Session, concept: DesignConcept) -> None:
    assert concept.external_number == 1


def test_ready_outranks_backlog_and_priority_outranks_number(session: Session) -> None:
    loaded = parse_concept_library(VALID_LIBRARY, source_path="docs/design/FIXTURE.md")
    import_concepts(session, loaded)
    session.flush()

    concepts = {
        c.external_number: c
        for c in session.query(DesignConcept).all()  # type: ignore[attr-defined]
    }
    concepts[6].status = ConceptStatus.READY
    concepts[7].status = ConceptStatus.READY
    concepts[7].priority = -1
    session.flush()

    chosen = next_concept(session)
    assert chosen is not None
    assert chosen.external_number == 7


# --- The lifecycle -----------------------------------------------------------


def test_the_full_lifecycle_leaves_a_complete_lineage(
    session: Session, store: FilesystemAssetStore, concept: DesignConcept
) -> None:
    attempt = _submitted(session, store, concept)
    assert concept.status is ConceptStatus.EXPLORING
    assert attempt.state is DesignAttemptState.AWAITING_DECISION

    decision = decide_attempt(session, attempt, DesignDecisionKind.APPROVED, "owner")
    assert attempt.state is DesignAttemptState.APPROVED

    version = approve_design(session, attempt, "owner")
    session.flush()

    assert version.version == 1
    assert version.master_asset_id == attempt.assets[0].id
    assert concept.status is ConceptStatus.APPROVED
    assert decision.actor == "owner"
    # The bytes are on disk under the namespaced key, hash recorded.
    asset = attempt.assets[0]
    assert asset.relative_path.startswith("designs/tshirt/001/attempts/")
    assert store.load(asset.relative_path) == SVG
    assert len(asset.sha256) == 64


def test_the_first_attempt_moves_the_concept_to_exploring(
    session: Session, concept: DesignConcept
) -> None:
    create_attempt(session, concept, DesignAttemptMethod.IMAGE_GENERATION)
    assert concept.status is ConceptStatus.EXPLORING


def test_attempt_numbers_increment_per_concept(session: Session, concept: DesignConcept) -> None:
    first = create_attempt(session, concept, DesignAttemptMethod.MANUAL_IMPORT)
    second = create_attempt(
        session, concept, DesignAttemptMethod.MANUAL_IMPORT, parent_attempt=first
    )
    assert (first.attempt_number, second.attempt_number) == (1, 2)
    assert second.parent_attempt_id == first.id


def test_an_attempt_with_no_assets_cannot_be_submitted(
    session: Session, concept: DesignConcept
) -> None:
    attempt = create_attempt(session, concept, DesignAttemptMethod.MANUAL_IMPORT)
    with pytest.raises(InvalidDesignAction, match="only a generated attempt"):
        submit_attempt(session, attempt)


# --- Decisions ---------------------------------------------------------------


def test_a_second_decision_is_a_conflict(
    session: Session, store: FilesystemAssetStore, concept: DesignConcept
) -> None:
    attempt = _submitted(session, store, concept)
    decide_attempt(session, attempt, DesignDecisionKind.APPROVED, "owner")

    with pytest.raises(DesignPipelineConflict, match="already decided"):
        decide_attempt(session, attempt, DesignDecisionKind.REJECTED, "owner")


def test_the_same_idempotency_key_returns_the_same_decision(
    session: Session, store: FilesystemAssetStore, concept: DesignConcept
) -> None:
    attempt = _submitted(session, store, concept)
    first = decide_attempt(
        session, attempt, DesignDecisionKind.APPROVED, "owner", idempotency_key="retry-1"
    )
    replay = decide_attempt(
        session, attempt, DesignDecisionKind.APPROVED, "owner", idempotency_key="retry-1"
    )
    assert replay.id == first.id


def test_an_unsigned_decision_is_refused(
    session: Session, store: FilesystemAssetStore, concept: DesignConcept
) -> None:
    attempt = _submitted(session, store, concept)
    with pytest.raises(InvalidDesignAction, match="nobody signed"):
        decide_attempt(session, attempt, DesignDecisionKind.APPROVED, "   ")


def test_a_variation_is_terminal_and_not_a_rejection(
    session: Session, store: FilesystemAssetStore, concept: DesignConcept
) -> None:
    attempt = _submitted(session, store, concept)
    decide_attempt(
        session,
        attempt,
        DesignDecisionKind.VARIATION_REQUESTED,
        "owner",
        instruction="Bigger fan.",
    )
    assert attempt.state is DesignAttemptState.VARIATION_REQUESTED


# --- Versions ----------------------------------------------------------------


def test_approving_requires_a_decided_attempt(
    session: Session, store: FilesystemAssetStore, concept: DesignConcept
) -> None:
    attempt = _submitted(session, store, concept)
    with pytest.raises(InvalidDesignAction, match="only an approved attempt"):
        approve_design(session, attempt, "owner")


def test_a_second_version_supersedes_the_first(
    session: Session, store: FilesystemAssetStore, concept: DesignConcept
) -> None:
    first_attempt = _submitted(session, store, concept)
    decide_attempt(session, first_attempt, DesignDecisionKind.APPROVED, "owner")
    first_version = approve_design(session, first_attempt, "owner")

    second_attempt = _submitted(session, store, concept)
    decide_attempt(session, second_attempt, DesignDecisionKind.APPROVED, "owner")
    second_version = approve_design(session, second_attempt, "owner")
    session.flush()

    assert (first_version.version, second_version.version) == (1, 2)
    assert first_version.superseded_at is not None
    assert second_version.superseded_at is None


def test_an_attempt_cannot_become_two_versions(
    session: Session, store: FilesystemAssetStore, concept: DesignConcept
) -> None:
    attempt = _submitted(session, store, concept)
    decide_attempt(session, attempt, DesignDecisionKind.APPROVED, "owner")
    approve_design(session, attempt, "owner")

    with pytest.raises(DesignPipelineConflict, match="already version 1"):
        approve_design(session, attempt, "owner")
