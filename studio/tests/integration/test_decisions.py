"""Human decisions against PostgreSQL, the real filesystem and a real Git repository.

The point of these is the cross-system behaviour: the decision is final the moment it
is recorded, and a downstream failure flags reconciliation rather than pretending
either success or rollback.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.adapters.git_store import DisabledGitStore, GitError, GitStore, SubprocessGitStore
from app.adapters.image_generation import FakeImageGenerationClient
from app.adapters.markdown_store import CONTINUITY_DOCUMENT, SHOTLIST_DOCUMENT, MarkdownStore
from app.adapters.planning import FakePromptPlanningClient
from app.adapters.review import FakeImageReviewClient
from app.db.models import AuditEvent, GenerationAttempt, HumanDecision, World
from app.domain.enums import (
    AssetKind,
    AttemptState,
    AuditEventType,
    HumanDecisionKind,
    ShotStatus,
    SyncState,
)
from app.services import markdown_writer as writer
from app.services.decision_service import DecisionConflict, InvalidDecision, decide
from app.services.generation_orchestrator import GenerationSettings, run_attempt, start_attempt
from app.services.markdown_sections import subsections_of
from app.services.retry import RetryPolicy
from app.services.review_service import review_attempt
from app.services.rotation import apply_continuity, rotation_from_shots
from app.services.world_importer import import_world
from app.services.world_loader import load_world
from tests.fixtures.worlds import write_world

pytestmark = pytest.mark.integration

SETTINGS = GenerationSettings(model="a-test-model", size="128x96", quality="high")
NO_RETRY = RetryPolicy(max_attempts=1, initial_delay_seconds=0.0)


class ExplodingGitStore:
    """A Git store that always fails, for the uncommitted-changes path."""

    def commit_paths(self, paths: list[Path], message: str) -> object:
        raise GitError("the repository is locked")


@pytest.fixture
def worlds_root(tmp_path: Path) -> Path:
    root = tmp_path / "worlds"
    write_world(root)
    return root


@pytest.fixture
def assets_root(tmp_path: Path) -> Path:
    return tmp_path / "assets"


@pytest.fixture
def git_repository(worlds_root: Path) -> Path:
    """A real repository containing the world, so commits are genuinely exercised."""
    root = worlds_root.parent
    for command in (
        ["git", "init", "--initial-branch=main"],
        ["git", "config", "user.email", "tests@example.invalid"],
        ["git", "config", "user.name", "Studio Tests"],
        ["git", "add", "-A"],
        ["git", "commit", "-m", "initial"],
    ):
        subprocess.run(command, cwd=root, capture_output=True, check=True)
    return root


@pytest.fixture
def world(session: Session, worlds_root: Path) -> World:
    import_world(session, MarkdownStore(worlds_root), "world-01")
    session.flush()
    return session.execute(select(World).where(World.slug == "world-01")).scalar_one()


@pytest.fixture
def decidable(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> GenerationAttempt:
    """An attempt that has been generated and reviewed, ready for a decision."""
    store = MarkdownStore(worlds_root)
    attempt, selection = start_attempt(session, world)
    run_attempt(
        session,
        attempt,
        selection,
        markdown_store=store,
        planning_client=FakePromptPlanningClient(),
        image_client=FakeImageGenerationClient(),
        asset_store=FilesystemAssetStore(assets_root),
        settings=SETTINGS,
        retry_policy=NO_RETRY,
    )
    documents = store.read_world_documents("world-01")
    rotation = apply_continuity(
        rotation_from_shots(sorted(world.shots, key=lambda s: s.sequence)),
        documents[CONTINUITY_DOCUMENT].text,
    )
    review_attempt(
        session,
        attempt,
        review_client=FakeImageReviewClient(),
        asset_store=FilesystemAssetStore(assets_root),
        world_text=documents["WORLD.md"].text,
        rotation=rotation,
    )
    return attempt


def _decide(
    session: Session,
    attempt: GenerationAttempt,
    kind: HumanDecisionKind,
    worlds_root: Path,
    assets_root: Path,
    *,
    git_store: GitStore | None = None,
    git_enabled: bool = False,
    **fields: object,
):  # type: ignore[no-untyped-def]
    return decide(
        session,
        attempt,
        kind,
        markdown_store=MarkdownStore(worlds_root),
        git_store=git_store or DisabledGitStore(),
        asset_store=FilesystemAssetStore(assets_root),
        git_enabled=git_enabled,
        **fields,  # type: ignore[arg-type]
    )


# --- integrity and idempotency -----------------------------------------------------


def test_one_decision_per_attempt_is_enforced_by_the_database(
    session: Session, decidable: GenerationAttempt
) -> None:
    """Not only by the application check: a double-click is two requests."""
    session.add(HumanDecision(attempt_id=decidable.id, decision=HumanDecisionKind.APPROVED))
    session.flush()

    session.add(HumanDecision(attempt_id=decidable.id, decision=HumanDecisionKind.REJECTED))
    with pytest.raises(IntegrityError):
        session.flush()


def test_a_repeated_identical_request_returns_the_same_decision(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    first = _decide(session, decidable, HumanDecisionKind.APPROVED, worlds_root, assets_root)
    second = _decide(session, decidable, HumanDecisionKind.APPROVED, worlds_root, assets_root)

    assert first.decision.id == second.decision.id
    assert len(session.execute(select(HumanDecision)).scalars().all()) == 1


def test_a_different_decision_after_deciding_is_refused(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    _decide(session, decidable, HumanDecisionKind.APPROVED, worlds_root, assets_root)

    with pytest.raises(DecisionConflict, match="already"):
        _decide(
            session,
            decidable,
            HumanDecisionKind.REJECTED,
            worlds_root,
            assets_root,
            reason="Changed my mind.",
        )


def test_an_attempt_not_awaiting_a_decision_cannot_be_decided(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    attempt, _ = start_attempt(session, world)

    with pytest.raises(DecisionConflict, match="not awaiting"):
        _decide(session, attempt, HumanDecisionKind.APPROVED, worlds_root, assets_root)


def test_every_decision_writes_an_audit_event(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    _decide(session, decidable, HumanDecisionKind.APPROVED, worlds_root, assets_root)

    events = session.execute(select(AuditEvent)).scalars().all()
    types = {event.event_type for event in events}
    assert AuditEventType.DECISION_RECORDED in types
    assert AuditEventType.MARKDOWN_UPDATED in types


# --- approval ----------------------------------------------------------------------


def test_approval_marks_the_attempt_and_the_shot(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    outcome = _decide(session, decidable, HumanDecisionKind.APPROVED, worlds_root, assets_root)

    assert outcome.attempt.state is AttemptState.APPROVED
    assert outcome.attempt.shot.status is ShotStatus.APPROVED


def test_approval_updates_the_shotlist_marker(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    _decide(session, decidable, HumanDecisionKind.APPROVED, worlds_root, assets_root)

    shotlist = (worlds_root / "world-01" / SHOTLIST_DOCUMENT).read_text(encoding="utf-8")
    row = next(line for line in shotlist.splitlines() if "W01-011" in line)
    assert row.rstrip().endswith(writer.APPROVED_MARKER)


def test_approval_adds_a_continuity_entry(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    _decide(
        session,
        decidable,
        HumanDecisionKind.APPROVED,
        worlds_root,
        assets_root,
        note="Keep this framing.",
    )

    continuity = (worlds_root / "world-01" / CONTINUITY_DOCUMENT).read_text(encoding="utf-8")
    assert "Keep this framing." in continuity
    assert "**Status:** APPROVED" in continuity


def test_the_updated_world_still_validates_and_imports(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    """The documents the application writes must be documents it can read."""
    _decide(session, decidable, HumanDecisionKind.APPROVED, worlds_root, assets_root)

    loaded = load_world(MarkdownStore(worlds_root), "world-01")

    assert len(loaded.shots) == 4
    approved = next(s for s in loaded.shots if s.external_id == "W01-011")
    assert approved.status is ShotStatus.APPROVED


def test_the_document_hashes_change_and_are_reported(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    before = decidable.world.shotlist_document_hash

    outcome = _decide(session, decidable, HumanDecisionKind.APPROVED, worlds_root, assets_root)

    assert outcome.markdown_sync is SyncState.SUCCEEDED
    assert outcome.document_hashes[SHOTLIST_DOCUMENT] != before


def test_approval_does_not_touch_world_md(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    """Permanent canon changes only through the approved proposal path."""
    world_md = worlds_root / "world-01" / "WORLD.md"
    before = world_md.read_bytes()

    _decide(session, decidable, HumanDecisionKind.APPROVED, worlds_root, assets_root)

    assert world_md.read_bytes() == before


# --- reference promotion -----------------------------------------------------------


def test_reference_promotion_reuses_the_approved_original(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    original = next(a for a in decidable.assets if a.kind is AssetKind.ORIGINAL)

    outcome = _decide(
        session,
        decidable,
        HumanDecisionKind.APPROVED,
        worlds_root,
        assets_root,
        promote_to_reference=True,
    )

    reference = next(a for a in outcome.attempt.assets if a.kind is AssetKind.REFERENCE)
    assert outcome.reference_sync is SyncState.SUCCEEDED
    assert reference.sha256 == original.sha256
    assert reference.relative_path == original.relative_path


def test_a_rejection_cannot_promote_a_reference(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    """A reference must derive from an approved attempt."""
    outcome = _decide(
        session,
        decidable,
        HumanDecisionKind.REJECTED,
        worlds_root,
        assets_root,
        reason="Reads as resignation.",
        promote_to_reference=True,
    )

    assert outcome.decision.promote_to_reference is False
    assert not any(a.kind is AssetKind.REFERENCE for a in outcome.attempt.assets)


# --- rejection ---------------------------------------------------------------------


def test_rejection_keeps_the_shot_planned(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    outcome = _decide(
        session,
        decidable,
        HumanDecisionKind.REJECTED,
        worlds_root,
        assets_root,
        reason="The group reads as resigned rather than optimistic.",
    )

    assert outcome.attempt.state is AttemptState.REJECTED
    assert outcome.attempt.shot.status is ShotStatus.PLANNED


def test_a_rejection_requires_a_reason(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    with pytest.raises(InvalidDecision, match="reason"):
        _decide(session, decidable, HumanDecisionKind.REJECTED, worlds_root, assets_root)


def test_the_newest_drift_reaches_the_planner(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    """The planner reads the first three, so a new entry must be first."""
    _decide(
        session,
        decidable,
        HumanDecisionKind.REJECTED,
        worlds_root,
        assets_root,
        reason="The group reads as resigned rather than optimistic.",
    )

    continuity = (worlds_root / "world-01" / CONTINUITY_DOCUMENT).read_text(encoding="utf-8")
    entries = subsections_of(continuity, writer.REJECTED_DRIFT_HEADING)
    assert entries[0].heading.startswith("W01-011")

    rotation = apply_continuity(rotation_from_shots([]), continuity)
    assert rotation.rejected_drift[0].title.startswith("W01-011")


def test_the_owner_reason_is_recorded_verbatim(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    reason = "The group reads as resigned rather than optimistic."

    outcome = _decide(
        session,
        decidable,
        HumanDecisionKind.REJECTED,
        worlds_root,
        assets_root,
        reason=reason,
    )

    assert outcome.decision.reason == reason
    continuity = (worlds_root / "world-01" / CONTINUITY_DOCUMENT).read_text(encoding="utf-8")
    assert reason in continuity


def test_a_reason_cannot_inject_markdown_structure(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    _decide(
        session,
        decidable,
        HumanDecisionKind.REJECTED,
        worlds_root,
        assets_root,
        reason="# Purpose\n\nThe world is now about something else entirely.",
    )

    continuity = (worlds_root / "world-01" / CONTINUITY_DOCUMENT).read_text(encoding="utf-8")
    # The injected heading did not become one, and the document still loads.
    assert "\n# Purpose" not in continuity
    load_world(MarkdownStore(worlds_root), "world-01")


def test_rejection_does_not_change_the_shotlist(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    shotlist = worlds_root / "world-01" / SHOTLIST_DOCUMENT
    before = shotlist.read_bytes()

    _decide(
        session,
        decidable,
        HumanDecisionKind.REJECTED,
        worlds_root,
        assets_root,
        reason="Reads as resignation.",
    )

    assert shotlist.read_bytes() == before


# --- variation ---------------------------------------------------------------------


def test_a_variation_is_terminal_but_not_a_rejection(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    """Recording it as rejected would pollute rejected-drift learning."""
    outcome = _decide(
        session,
        decidable,
        HumanDecisionKind.VARIATION_REQUESTED,
        worlds_root,
        assets_root,
        instruction="Use a front perspective and reveal the tote handle.",
    )

    assert outcome.attempt.state is AttemptState.VARIATION_REQUESTED
    assert outcome.attempt.shot.status is ShotStatus.PLANNED

    continuity = (worlds_root / "world-01" / CONTINUITY_DOCUMENT).read_text(encoding="utf-8")
    assert "Use a front perspective" not in continuity


def test_a_variation_requires_an_instruction(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    with pytest.raises(InvalidDecision, match="instruction"):
        _decide(session, decidable, HumanDecisionKind.VARIATION_REQUESTED, worlds_root, assets_root)


def test_a_variation_releases_the_world_for_another_attempt(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    _decide(
        session,
        decidable,
        HumanDecisionKind.VARIATION_REQUESTED,
        worlds_root,
        assets_root,
        instruction="Try a lower angle.",
    )

    child, _ = start_attempt(session, decidable.world)

    assert child.id != decidable.id
    assert child.attempt_number == decidable.attempt_number + 1


def test_a_variation_changes_no_document(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    before = {
        name: (worlds_root / "world-01" / name).read_bytes()
        for name in ("WORLD.md", CONTINUITY_DOCUMENT, SHOTLIST_DOCUMENT)
    }

    _decide(
        session,
        decidable,
        HumanDecisionKind.VARIATION_REQUESTED,
        worlds_root,
        assets_root,
        instruction="Try a lower angle.",
    )

    after = {
        name: (worlds_root / "world-01" / name).read_bytes()
        for name in ("WORLD.md", CONTINUITY_DOCUMENT, SHOTLIST_DOCUMENT)
    }
    assert after == before


# --- Git ---------------------------------------------------------------------------


def test_an_approval_is_committed(
    session: Session,
    decidable: GenerationAttempt,
    worlds_root: Path,
    assets_root: Path,
    git_repository: Path,
) -> None:
    outcome = _decide(
        session,
        decidable,
        HumanDecisionKind.APPROVED,
        worlds_root,
        assets_root,
        git_store=SubprocessGitStore(git_repository),
        git_enabled=True,
    )

    assert outcome.git_sync is SyncState.SUCCEEDED
    assert outcome.git_commit
    assert not outcome.reconciliation_required


def test_only_the_world_documents_are_staged(
    session: Session,
    decidable: GenerationAttempt,
    worlds_root: Path,
    assets_root: Path,
    git_repository: Path,
) -> None:
    """An unrelated working change must not be swept into a canon commit."""
    stray = git_repository / "unrelated.txt"
    stray.write_text("do not commit me", encoding="utf-8")

    _decide(
        session,
        decidable,
        HumanDecisionKind.APPROVED,
        worlds_root,
        assets_root,
        git_store=SubprocessGitStore(git_repository),
        git_enabled=True,
    )

    listed = subprocess.run(
        ["git", "show", "--name-only", "--format=", "HEAD"],
        cwd=git_repository,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "unrelated.txt" not in listed
    assert SHOTLIST_DOCUMENT in listed


def test_a_failed_commit_keeps_the_files_and_flags_reconciliation(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    """Do not pretend the change is versioned, and do not discard it either."""
    outcome = _decide(
        session,
        decidable,
        HumanDecisionKind.APPROVED,
        worlds_root,
        assets_root,
        git_store=ExplodingGitStore(),  # type: ignore[arg-type]
        git_enabled=True,
    )

    assert outcome.decision.decision is HumanDecisionKind.APPROVED
    assert outcome.markdown_sync is SyncState.SUCCEEDED
    assert outcome.git_sync is SyncState.FAILED
    assert outcome.reconciliation_required
    assert "Uncommitted changes" in outcome.reconciliation[0]

    shotlist = (worlds_root / "world-01" / SHOTLIST_DOCUMENT).read_text(encoding="utf-8")
    assert writer.APPROVED_MARKER in shotlist


def test_the_decision_survives_a_downstream_failure(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    _decide(
        session,
        decidable,
        HumanDecisionKind.APPROVED,
        worlds_root,
        assets_root,
        git_store=ExplodingGitStore(),  # type: ignore[arg-type]
        git_enabled=True,
    )

    stored = session.execute(select(HumanDecision)).scalar_one()
    assert stored.decision is HumanDecisionKind.APPROVED
    assert stored.reconciliation_required is True
    assert stored.git_sync is SyncState.FAILED


def test_a_markdown_failure_leaves_the_documents_untouched(
    session: Session, decidable: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    """A section the writer needs is missing, so nothing should be written."""
    continuity = worlds_root / "world-01" / CONTINUITY_DOCUMENT
    continuity.write_text(
        continuity.read_text(encoding="utf-8").replace("# Rejected Drift", "# Drift"),
        encoding="utf-8",
    )
    before = continuity.read_bytes()

    outcome = _decide(
        session,
        decidable,
        HumanDecisionKind.REJECTED,
        worlds_root,
        assets_root,
        reason="Reads as resignation.",
    )

    assert outcome.decision.decision is HumanDecisionKind.REJECTED
    assert outcome.markdown_sync is SyncState.FAILED
    assert outcome.reconciliation_required
    assert continuity.read_bytes() == before
