"""The owner's decision, and everything that follows from it.

The decision is recorded first, in its own committed transaction. Only then does the
application try to update the Markdown, re-import, promote a reference and commit to
Git. Those cannot share a transaction with the database, so each reports its own
outcome and the response distinguishes "decided" from "written" from "committed".

A downstream failure never undoes the decision. It sets ``reconciliation_required``
with the exact stage and error, and the caller is told plainly.

Nothing here writes ``WORLD.md``. Permanent canon changes only through the separately
approved proposal path.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore
from app.adapters.git_store import GitError, GitStore
from app.adapters.markdown_store import (
    CONTINUITY_DOCUMENT,
    SHOTLIST_DOCUMENT,
    MarkdownStore,
    MarkdownWriteFailed,
)
from app.db.models import AuditEvent, GenerationAttempt, HumanDecision, ImageAsset, World
from app.domain.enums import (
    DECISION_ATTEMPT_STATES,
    AssetKind,
    AttemptState,
    AuditEventType,
    HumanDecisionKind,
    ShotStatus,
    SyncState,
)
from app.domain.errors import StudioError
from app.services import markdown_writer as writer
from app.services.generation_orchestrator import acquire_world_lock
from app.services.world_importer import import_world

logger = logging.getLogger(__name__)

OWNER = "owner"
MAX_REASON_LENGTH = 2000
MAX_INSTRUCTION_LENGTH = 2000


class DecisionConflict(StudioError):
    """The attempt cannot be decided, or already has been."""


class InvalidDecision(StudioError):
    """The request itself is not acceptable."""


@dataclass
class DecisionOutcome:
    """The decision and the state of every system that had to follow it."""

    decision: HumanDecision
    attempt: GenerationAttempt
    shot_status: ShotStatus
    markdown_sync: SyncState = SyncState.NOT_ATTEMPTED
    git_sync: SyncState = SyncState.NOT_ATTEMPTED
    reference_sync: SyncState = SyncState.NOT_ATTEMPTED
    git_commit: str | None = None
    document_hashes: dict[str, str] = field(default_factory=dict)
    reconciliation: list[str] = field(default_factory=list)

    @property
    def reconciliation_required(self) -> bool:
        return bool(self.reconciliation)


def _audit(
    session: Session,
    event_type: AuditEventType,
    *,
    world_id: Any = None,
    attempt_id: Any = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Append-only. Never a secret, never a signed URL."""
    session.add(
        AuditEvent(
            world_id=world_id,
            attempt_id=attempt_id,
            event_type=event_type,
            actor=OWNER,
            payload_json=payload or {},
        )
    )


def _require_decidable(session: Session, attempt: GenerationAttempt) -> None:
    if attempt.state is not AttemptState.AWAITING_DECISION:
        raise DecisionConflict(
            f"Attempt {attempt.attempt_number} is {attempt.state.value}, not awaiting a "
            "decision. Only an attempt that has been generated and reviewed can be decided."
        )
    if not any(asset.kind is AssetKind.ORIGINAL for asset in attempt.assets):
        raise DecisionConflict("The attempt has no stored image, so it cannot be decided.")


def _existing_decision(session: Session, attempt: GenerationAttempt) -> HumanDecision | None:
    return session.execute(
        select(HumanDecision).where(HumanDecision.attempt_id == attempt.id)
    ).scalar_one_or_none()


def _clean(text: str | None, limit: int, label: str, *, required: bool) -> str | None:
    value = (text or "").strip()
    if not value:
        if required:
            raise InvalidDecision(f"A {label} is required.")
        return None
    if len(value) > limit:
        raise InvalidDecision(f"The {label} is longer than {limit} characters.")
    return value


def record_decision(
    session: Session,
    attempt: GenerationAttempt,
    kind: HumanDecisionKind,
    *,
    reason: str | None = None,
    note: str | None = None,
    instruction: str | None = None,
    promote_to_reference: bool = False,
    idempotency_key: str | None = None,
) -> tuple[HumanDecision, bool]:
    """Persist the decision. Returns it, and whether it was newly created.

    Acquires the world lock first so two requests cannot both pass the duplicate check.
    The unique constraint is the real guarantee; this produces a clear message.
    """
    world = attempt.world
    acquire_world_lock(session, world)

    # The duplicate check comes first. Once decided, the attempt is no longer
    # awaiting a decision, so checking decidability first would answer a retry with
    # the wrong error and hide the fact that a decision already exists.
    existing = _existing_decision(session, attempt)
    if existing is not None:
        # A retried request that means the same thing gets the same answer.
        if existing.decision is kind and (
            idempotency_key is None or existing.idempotency_key == idempotency_key
        ):
            return existing, False
        raise DecisionConflict(
            f"Attempt {attempt.attempt_number} was already {existing.decision.value}. "
            "A decision is final."
        )

    _require_decidable(session, attempt)

    decision = HumanDecision(
        attempt_id=attempt.id,
        decision=kind,
        reason=_clean(
            reason, MAX_REASON_LENGTH, "reason", required=kind is HumanDecisionKind.REJECTED
        ),
        note=_clean(note, MAX_REASON_LENGTH, "note", required=False),
        instruction=_clean(
            instruction,
            MAX_INSTRUCTION_LENGTH,
            "instruction",
            required=kind is HumanDecisionKind.VARIATION_REQUESTED,
        ),
        promote_to_reference=promote_to_reference and kind is HumanDecisionKind.APPROVED,
        actor=OWNER,
        idempotency_key=idempotency_key,
    )
    session.add(decision)

    attempt.state = DECISION_ATTEMPT_STATES[kind]
    if kind is HumanDecisionKind.APPROVED:
        attempt.shot.status = ShotStatus.APPROVED
    # Rejection and variation leave the shot planned: it is still to be made.

    try:
        session.flush()
    except IntegrityError as error:
        session.rollback()
        raise DecisionConflict(
            "That attempt was decided by another request a moment ago."
        ) from error

    _audit(
        session,
        AuditEventType.DECISION_RECORDED,
        world_id=world.id,
        attempt_id=attempt.id,
        payload={
            "decision": kind.value,
            "shot": attempt.shot.external_id,
            "attempt_number": attempt.attempt_number,
            "promote_to_reference": decision.promote_to_reference,
        },
    )
    session.commit()

    logger.info("Attempt %s decided: %s", attempt.id, kind.value)
    return decision, True


def _promote_reference(
    session: Session, attempt: GenerationAttempt, asset_store: AssetStore
) -> ImageAsset:
    """Record the approved original as a reference.

    The original bytes and hash are reused rather than copied, so a reference can
    never drift from the image that was approved.
    """
    original = next(asset for asset in attempt.assets if asset.kind is AssetKind.ORIGINAL)

    existing = next((a for a in attempt.assets if a.kind is AssetKind.REFERENCE), None)
    if existing is not None:
        return existing  # idempotent

    reference = ImageAsset(
        attempt_id=attempt.id,
        kind=AssetKind.REFERENCE,
        relative_path=original.relative_path,
        sha256=original.sha256,
        mime_type=original.mime_type,
        width=original.width,
        height=original.height,
        byte_size=original.byte_size,
    )
    session.add(reference)
    session.flush()
    return reference


def _build_documents(
    attempt: GenerationAttempt,
    kind: HumanDecisionKind,
    decision: HumanDecision,
    current: dict[str, str],
) -> dict[str, str]:
    """Construct the candidate documents in memory from validated fields."""
    shot = attempt.shot
    review = attempt.latest_review
    continuity = current[CONTINUITY_DOCUMENT]
    shotlist = current[SHOTLIST_DOCUMENT]

    if kind is HumanDecisionKind.APPROVED:
        continuity = writer.append_approved_entry(
            continuity,
            writer.ApprovedEntry(
                shot_external_id=shot.external_id,
                scene=shot.title,
                hero_product=attempt.hero_product,
                camera_position=attempt.camera_position,
                strongest_success=review.strongest_success if review else None,
                note=decision.note,
                is_reference=decision.promote_to_reference,
            ),
        )
        continuity = writer.append_rotation_row(
            continuity,
            writer.HERO_PRODUCT_ROTATION_HEADING,
            [
                shot.external_id,
                shot.title,
                attempt.hero_product or "unset",
                "Recorded",
                "APPROVED",
            ],
        )
        continuity = writer.append_rotation_row(
            continuity,
            writer.CAMERA_POSITION_ROTATION_HEADING,
            [shot.external_id, shot.title, attempt.camera_position or "unset", "APPROVED"],
        )
        shotlist = writer.set_shot_status_marker(shotlist, shot.external_id, writer.APPROVED_MARKER)
        return {CONTINUITY_DOCUMENT: continuity, SHOTLIST_DOCUMENT: shotlist}

    # Rejection. The shot stays planned, so the shotlist marker is untouched; only the
    # drift record is added, newest first.
    continuity = writer.insert_drift_entry(
        continuity,
        writer.DriftEntry(
            shot_external_id=shot.external_id,
            label=shot.title,
            reason=decision.reason or "No reason recorded.",
            lesson=review.material_drift if review else None,
        ),
    )
    return {CONTINUITY_DOCUMENT: continuity}


def apply_decision_documents(
    session: Session,
    outcome: DecisionOutcome,
    *,
    markdown_store: MarkdownStore,
    git_store: GitStore,
    asset_store: AssetStore,
    git_enabled: bool,
) -> DecisionOutcome:
    """Update the world documents, re-import and commit.

    Each stage records its own audit event. A failure at any stage leaves the decision
    intact and flags reconciliation.
    """
    attempt = outcome.attempt
    world: World = attempt.world
    kind = outcome.decision.decision

    if outcome.decision.promote_to_reference:
        try:
            _promote_reference(session, attempt, asset_store)
            outcome.reference_sync = SyncState.SUCCEEDED
            _audit(
                session,
                AuditEventType.REFERENCE_PROMOTED,
                world_id=world.id,
                attempt_id=attempt.id,
            )
        except (StudioError, OSError) as error:
            outcome.reference_sync = SyncState.FAILED
            outcome.reconciliation.append(f"Reference promotion failed: {error}")
            _audit(
                session,
                AuditEventType.REFERENCE_FAILED,
                world_id=world.id,
                attempt_id=attempt.id,
                payload={"error": str(error)},
            )

    if kind is HumanDecisionKind.VARIATION_REQUESTED:
        # A variation changes no document: it records intent and frees the world.
        session.commit()
        return outcome

    snapshot = markdown_store.snapshot(world.slug)

    try:
        candidates = _build_documents(attempt, kind, outcome.decision, snapshot)
    except writer.MarkdownWriteError as error:
        return _flag(
            session, outcome, AuditEventType.MARKDOWN_FAILED, f"Could not build the update: {error}"
        )

    try:
        written = markdown_store.write_documents(world.slug, candidates)
    except (MarkdownWriteFailed, StudioError) as error:
        return _flag(session, outcome, AuditEventType.MARKDOWN_FAILED, f"Could not write: {error}")

    outcome.markdown_sync = SyncState.SUCCEEDED
    outcome.document_hashes = {name: document.sha256 for name, document in written.items()}
    _audit(
        session,
        AuditEventType.MARKDOWN_UPDATED,
        world_id=world.id,
        attempt_id=attempt.id,
        payload={"documents": outcome.document_hashes},
    )

    # Re-import, so the database matches what is now on disk.
    try:
        import_world(session, markdown_store, world.slug)
        _audit(session, AuditEventType.WORLD_REIMPORTED, world_id=world.id, attempt_id=attempt.id)
    except StudioError as error:
        # Restore the documents that were valid a moment ago rather than leaving the
        # database and the files disagreeing.
        restored = "restored"
        try:
            markdown_store.write_documents(world.slug, snapshot)
        except StudioError:
            restored = "could not be restored"
        return _flag(
            session,
            outcome,
            AuditEventType.IMPORT_FAILED,
            f"The updated documents did not import ({error}). Previous documents {restored}.",
        )

    if not git_enabled:
        session.commit()
        return outcome

    directory = markdown_store.world_directory(world.slug)
    paths = [directory / name for name in candidates]
    message = (
        f"chore(world-01): {kind.value} {attempt.shot.external_id} "
        f"(attempt {attempt.attempt_number})"
    )

    try:
        result = git_store.commit_paths(paths, message)
    except GitError as error:
        # Files are valid and imported. They are simply not versioned yet.
        outcome.git_sync = SyncState.FAILED
        outcome.reconciliation.append(f"Uncommitted changes: {error}")
        outcome.decision.git_sync = SyncState.FAILED
        outcome.decision.reconciliation_required = True
        outcome.decision.reconciliation_detail = "; ".join(outcome.reconciliation)
        _audit(
            session,
            AuditEventType.GIT_FAILED,
            world_id=world.id,
            attempt_id=attempt.id,
            payload={"error": str(error)},
        )
        session.commit()
        return outcome

    outcome.git_sync = SyncState.SUCCEEDED
    outcome.git_commit = result.commit
    outcome.decision.git_sync = SyncState.SUCCEEDED
    outcome.decision.git_commit = result.commit
    outcome.decision.markdown_sync = SyncState.SUCCEEDED
    _audit(
        session,
        AuditEventType.GIT_COMMITTED,
        world_id=world.id,
        attempt_id=attempt.id,
        payload={"commit": result.commit, "paths": result.committed_paths},
    )
    session.commit()
    return outcome


def _flag(
    session: Session,
    outcome: DecisionOutcome,
    event_type: AuditEventType,
    message: str,
) -> DecisionOutcome:
    """Record that the decision stands but something downstream needs a human."""
    outcome.markdown_sync = SyncState.FAILED
    outcome.reconciliation.append(message)
    outcome.decision.markdown_sync = SyncState.FAILED
    outcome.decision.reconciliation_required = True
    outcome.decision.reconciliation_detail = "; ".join(outcome.reconciliation)

    _audit(
        session,
        event_type,
        world_id=outcome.attempt.world_id,
        attempt_id=outcome.attempt.id,
        payload={"error": message},
    )
    _audit(
        session,
        AuditEventType.RECONCILIATION_REQUIRED,
        world_id=outcome.attempt.world_id,
        attempt_id=outcome.attempt.id,
        payload={"detail": message},
    )
    session.commit()

    logger.warning("Decision on attempt %s needs reconciliation: %s", outcome.attempt.id, message)
    return outcome


def decide(
    session: Session,
    attempt: GenerationAttempt,
    kind: HumanDecisionKind,
    *,
    markdown_store: MarkdownStore,
    git_store: GitStore,
    asset_store: AssetStore,
    git_enabled: bool,
    reason: str | None = None,
    note: str | None = None,
    instruction: str | None = None,
    promote_to_reference: bool = False,
    idempotency_key: str | None = None,
) -> DecisionOutcome:
    """Record the decision, then bring the documents and Git into line with it."""
    decision, created = record_decision(
        session,
        attempt,
        kind,
        reason=reason,
        note=note,
        instruction=instruction,
        promote_to_reference=promote_to_reference,
        idempotency_key=idempotency_key,
    )

    outcome = DecisionOutcome(
        decision=decision,
        attempt=attempt,
        shot_status=attempt.shot.status,
        markdown_sync=decision.markdown_sync,
        git_sync=decision.git_sync,
        reference_sync=decision.reference_sync,
        git_commit=decision.git_commit,
    )

    if not created:
        # A retry. The work was done the first time; report what that produced.
        if decision.reconciliation_detail:
            outcome.reconciliation.append(decision.reconciliation_detail)
        return outcome

    return apply_decision_documents(
        session,
        outcome,
        markdown_store=markdown_store,
        git_store=git_store,
        asset_store=asset_store,
        git_enabled=git_enabled,
    )


def repository_root_for(worlds_root: Path) -> Path:
    """The Git repository the world documents live in."""
    for candidate in [worlds_root, *worlds_root.parents]:
        if (candidate / ".git").exists():
            return candidate
    return worlds_root
