"""Canon proposals: the only path by which ``WORLD.md`` changes without a hand edit.

Nothing changes until the owner approves an exact diff. Classification is advisory,
the diff is shown as text, and approval applies exactly the wording that was shown.

A rule can only be added under a heading the planner actually reads. Landing one
anywhere else would produce a rule that exists in the document and is invisible to
generation — the failure that hid the vehicle canon until 5 August 2026.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import difflib
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.adapters.canon_classifier import (
    CanonClassifier,
    ClassificationError,
    ClassificationRequest,
)
from app.adapters.git_store import GitError, GitStore
from app.adapters.markdown_store import WORLD_DOCUMENT, MarkdownStore, MarkdownWriteFailed
from app.db.models import AuditEvent, CanonProposal
from app.domain.enums import AuditEventType, CanonProposalStatus
from app.domain.errors import StudioError
from app.domain.schemas import CanonExcerpt
from app.services import markdown_writer as writer
from app.services.markdown_sections import section_with_subsections
from app.services.prompt_planner import PLANNING_CANON_HEADINGS, truncate_excerpt
from app.services.world_loader import load_world

logger = logging.getLogger(__name__)

OWNER = "owner"


class ProposalConflict(StudioError):
    """The proposal cannot be acted on in its current state."""


class InvalidTarget(StudioError):
    """The rule would land where the planner never looks."""


@dataclass
class ProposalDiff:
    """The exact change, as text."""

    target_heading: str
    unified_diff: str
    candidate_world_text: str
    applied_wording: str


def canon_excerpts(world_text: str) -> list[CanonExcerpt]:
    """The sections a rule could join: exactly what the planner reads."""
    return [
        CanonExcerpt(heading=heading, body=truncate_excerpt(body))
        for heading in PLANNING_CANON_HEADINGS
        if (body := section_with_subsections(world_text, heading)) is not None and body.strip()
    ]


def classify_proposal(
    session: Session,
    proposal: CanonProposal,
    *,
    classifier: CanonClassifier,
    world_text: str,
) -> CanonProposal:
    """Weigh the proposal against canon. Advisory; it decides nothing."""
    request = ClassificationRequest(
        proposed_text=proposal.proposed_text,
        canon_excerpts=canon_excerpts(world_text),
        source_shot=(proposal.attempt.shot.external_id if proposal.attempt else None),
        source_reason=proposal.reason,
    )

    try:
        result = classifier.classify(request)
    except ClassificationError as error:
        # A failed classification must not block the owner from reading the proposal.
        proposal.classification_reason = f"Classification unavailable: {error}"
        session.flush()
        session.commit()
        return proposal

    proposal.classification = result.classification
    proposal.classification_reason = result.reason
    proposal.classified_by = result.model
    if result.target_heading in PLANNING_CANON_HEADINGS:
        proposal.target_heading = result.target_heading

    session.flush()
    session.commit()
    return proposal


def validate_target(heading: str | None) -> str:
    """Reject a target the planner does not read.

    Silently accepting one would produce a rule that is in the document and invisible
    to generation, which is worse than refusing.
    """
    if not heading:
        raise InvalidTarget(
            "No target section. Choose one of the sections the planner reads: "
            + ", ".join(PLANNING_CANON_HEADINGS)
        )
    if heading not in PLANNING_CANON_HEADINGS:
        raise InvalidTarget(
            f"{heading!r} is not a section the planning model reads, so a rule added "
            "there would never reach generation. Choose one of: "
            + ", ".join(PLANNING_CANON_HEADINGS)
        )
    return heading


def build_diff(
    proposal: CanonProposal, world_text: str, target_heading: str | None = None
) -> ProposalDiff:
    """The exact change this proposal would make to ``WORLD.md``."""
    heading = validate_target(target_heading or proposal.target_heading)
    wording = writer.sanitise_inline(proposal.proposed_text)

    candidate = writer.append_canon_rule(world_text, heading, wording)

    diff = "\n".join(
        difflib.unified_diff(
            world_text.splitlines(),
            candidate.splitlines(),
            fromfile="WORLD.md (current)",
            tofile="WORLD.md (proposed)",
            lineterm="",
            n=3,
        )
    )

    return ProposalDiff(
        target_heading=heading,
        unified_diff=diff,
        candidate_world_text=candidate,
        applied_wording=wording,
    )


def reject_proposal(
    session: Session, proposal: CanonProposal, note: str | None = None
) -> CanonProposal:
    """Decline. ``WORLD.md`` is untouched."""
    _require_pending(proposal)

    proposal.status = CanonProposalStatus.REJECTED
    proposal.human_note = (note or "").strip() or None
    proposal.decided_at = dt.datetime.now(dt.UTC)
    session.flush()

    session.add(
        AuditEvent(
            world_id=proposal.world_id,
            attempt_id=proposal.attempt_id,
            event_type=AuditEventType.DECISION_RECORDED,
            actor=OWNER,
            payload_json={"canon_proposal": str(proposal.id), "status": "rejected"},
        )
    )
    session.commit()
    return proposal


def approve_proposal(
    session: Session,
    proposal: CanonProposal,
    *,
    markdown_store: MarkdownStore,
    git_store: GitStore,
    git_enabled: bool,
    target_heading: str | None = None,
    note: str | None = None,
) -> CanonProposal:
    """Apply the diff. This is the only write to ``WORLD.md`` the application makes."""
    _require_pending(proposal)

    world = proposal.world
    documents = markdown_store.read_world_documents(world.slug)
    world_text = documents[WORLD_DOCUMENT].text

    diff = build_diff(proposal, world_text, target_heading)

    # Validate the candidate before it touches the disk: an invalid WORLD.md would
    # stop the next generation, and canon is the one document nothing else can rebuild.
    snapshot = markdown_store.snapshot(world.slug)
    try:
        markdown_store.write_documents(world.slug, {WORLD_DOCUMENT: diff.candidate_world_text})
        load_world(markdown_store, world.slug)
    except (MarkdownWriteFailed, StudioError) as error:
        # Put the previous canon back. It is the one document nothing else can rebuild.
        with contextlib.suppress(StudioError):
            markdown_store.write_documents(world.slug, snapshot)
        return _fail(session, proposal, f"The proposed canon did not validate: {error}")

    proposal.status = CanonProposalStatus.APPLIED
    proposal.target_heading = diff.target_heading
    proposal.applied_wording = diff.applied_wording
    proposal.applied_at = dt.datetime.now(dt.UTC)
    proposal.decided_at = proposal.applied_at
    proposal.human_note = (note or "").strip() or None
    proposal.failure_detail = None

    world.world_document_hash = markdown_store.read_document(world.slug, WORLD_DOCUMENT).sha256
    session.flush()

    session.add(
        AuditEvent(
            world_id=world.id,
            attempt_id=proposal.attempt_id,
            event_type=AuditEventType.MARKDOWN_UPDATED,
            actor=OWNER,
            payload_json={
                "canon_proposal": str(proposal.id),
                "section": diff.target_heading,
                "wording": diff.applied_wording,
            },
        )
    )

    if git_enabled:
        path = markdown_store.world_directory(world.slug) / WORLD_DOCUMENT
        message = f"canon(world-01): {diff.target_heading} — approved rule"
        try:
            result = git_store.commit_paths([path], message)
            proposal.git_commit = result.commit
            session.add(
                AuditEvent(
                    world_id=world.id,
                    event_type=AuditEventType.GIT_COMMITTED,
                    actor=OWNER,
                    payload_json={"commit": result.commit, "canon_proposal": str(proposal.id)},
                )
            )
        except GitError as error:
            # The rule is applied and valid. It is simply not versioned yet.
            proposal.failure_detail = f"Uncommitted changes: {error}"
            session.add(
                AuditEvent(
                    world_id=world.id,
                    event_type=AuditEventType.GIT_FAILED,
                    actor=OWNER,
                    payload_json={"error": str(error), "canon_proposal": str(proposal.id)},
                )
            )

    session.commit()
    logger.info("Canon proposal %s applied under %s", proposal.id, diff.target_heading)
    return proposal


def _require_pending(proposal: CanonProposal) -> None:
    if proposal.status is not CanonProposalStatus.PENDING:
        raise ProposalConflict(
            f"This proposal is already {proposal.status.value}. Canon decisions are final."
        )


def _fail(session: Session, proposal: CanonProposal, message: str) -> CanonProposal:
    proposal.status = CanonProposalStatus.FAILED
    proposal.failure_detail = message
    session.flush()
    session.add(
        AuditEvent(
            world_id=proposal.world_id,
            event_type=AuditEventType.MARKDOWN_FAILED,
            actor=OWNER,
            payload_json={"canon_proposal": str(proposal.id), "error": message},
        )
    )
    session.commit()
    logger.warning("Canon proposal %s failed: %s", proposal.id, message)
    return proposal


__all__ = [
    "InvalidTarget",
    "ProposalConflict",
    "ProposalDiff",
    "approve_proposal",
    "build_diff",
    "canon_excerpts",
    "classify_proposal",
    "reject_proposal",
    "validate_target",
]
