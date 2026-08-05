"""The reference library: active, archived, pinned.

Approvals accumulate. Left alone, ``# Approved Reference Frames`` would grow without
limit and every frame would carry equal weight, which is the same as none of them
carrying any.

So the library has three states:

* **active** — the strongest frames, capped, and the only ones the planner reads;
* **archived** — everything else, kept and searchable, because an approved frame
  records a decision as well as feeding one;
* **pinned** — exceptional frames, outside the cap, never aged out automatically.

Nothing is ever deleted. Ageing out is a change of state, not a loss.
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditEvent, GenerationAttempt, ImageAsset, ReferenceFrame
from app.domain.enums import AssetKind, AuditEventType, ReferenceState
from app.domain.errors import StudioError

logger = logging.getLogger(__name__)


class DraftNotPromotable(StudioError):
    """A draft ran on the cheap model, so it cannot join the reference library."""


OWNER = "owner"
DEFAULT_ACTIVE_LIMIT = 16
# How many reference notes the planner receives. Bounded like every other input.
PLANNER_REFERENCE_LIMIT = 8


@dataclass(frozen=True)
class LibraryCounts:
    """How the library breaks down."""

    active: int
    pinned: int
    archived: int

    @property
    def reaching_planner(self) -> int:
        return self.active + self.pinned


def _strength(attempt: GenerationAttempt) -> int:
    """How strong a frame is, from its review.

    The sum of the five scores. Without a review the frame scores zero and survives
    on recency alone, which is the right outcome: an unreviewed frame has not earned
    a place ahead of a reviewed one.
    """
    review = attempt.latest_review
    if review is None:
        return 0
    return (
        review.mood_score
        + review.australian_authenticity_score
        + review.product_visibility_score
        + review.documentary_credibility_score
        + review.story_score
    )


def promote(
    session: Session,
    attempt: GenerationAttempt,
    *,
    label: str | None = None,
    active_limit: int = DEFAULT_ACTIVE_LIMIT,
) -> ReferenceFrame:
    """Add an approved attempt to the library, then rebalance.

    Idempotent: promoting the same attempt twice returns the existing frame.
    """
    existing = session.execute(
        select(ReferenceFrame).where(ReferenceFrame.attempt_id == attempt.id)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    # Strength is the sum of the five review scores, and those scores are not
    # comparable across image models: a draft on the cheap model loses marks for
    # texture and product legibility that a full frame never risked. Letting one in
    # would either park a handicapped frame in the active set or, worse, let it age a
    # real frame out. Drafts are for framing and composition, and stop there.
    if attempt.is_draft:
        raise DraftNotPromotable(
            f"Attempt {attempt.id} ran on the draft model "
            f"({attempt.image_model or 'unknown'}) and cannot become a reference frame. "
            "Re-run the shot on the full model first."
        )

    asset = next(
        (a for a in attempt.assets if a.kind is AssetKind.REFERENCE),
        next((a for a in attempt.assets if a.kind is AssetKind.ORIGINAL), None),
    )
    if asset is None:
        raise ValueError("The attempt has no stored image to reference.")

    review = attempt.latest_review
    frame = ReferenceFrame(
        world_id=attempt.world_id,
        attempt_id=attempt.id,
        asset_id=asset.id,
        state=ReferenceState.ACTIVE,
        label=(label or f"{attempt.shot.external_id} — {attempt.shot.title}")[:200],
        why_it_works=review.strongest_success if review else None,
        hero_product=attempt.hero_product,
        camera_position=attempt.camera_position,
        strength=_strength(attempt),
    )
    session.add(frame)
    session.flush()

    session.add(
        AuditEvent(
            world_id=attempt.world_id,
            attempt_id=attempt.id,
            event_type=AuditEventType.REFERENCE_PROMOTED,
            actor=OWNER,
            payload_json={"reference": str(frame.id), "strength": frame.strength},
        )
    )

    rebalance(session, attempt.world_id, active_limit=active_limit)
    return frame


def rebalance(
    session: Session, world_id: object, *, active_limit: int = DEFAULT_ACTIVE_LIMIT
) -> list[ReferenceFrame]:
    """Keep the active set at the cap, archiving the weakest beyond it.

    Pinned frames are outside the cap entirely: they neither count towards it nor age
    out. Returns the frames that were archived by this call.
    """
    active = list(
        session.execute(
            select(ReferenceFrame)
            .where(ReferenceFrame.world_id == world_id)
            .where(ReferenceFrame.state == ReferenceState.ACTIVE)
        )
        .scalars()
        .all()
    )

    # Strongest first; recency breaks ties, so a newer frame of equal strength stays.
    active.sort(key=lambda frame: (frame.strength, frame.created_at), reverse=True)

    archived: list[ReferenceFrame] = []
    for frame in active[active_limit:]:
        frame.state = ReferenceState.ARCHIVED
        frame.archived_at = dt.datetime.now(dt.UTC)
        archived.append(frame)
        session.add(
            AuditEvent(
                world_id=frame.world_id,
                attempt_id=frame.attempt_id,
                event_type=AuditEventType.REFERENCE_ARCHIVED,
                actor=OWNER,
                payload_json={"reference": str(frame.id), "reason": "aged out of the active set"},
            )
        )

    if archived:
        session.flush()
        logger.info("Archived %d reference frame(s) beyond the active limit", len(archived))

    return archived


def set_pinned(
    session: Session,
    frame: ReferenceFrame,
    *,
    pinned: bool,
    active_limit: int = DEFAULT_ACTIVE_LIMIT,
) -> ReferenceFrame:
    """Pin a frame so it never ages out, or unpin it back into the active set.

    Unpinning returns the frame to ``active`` and rebalances, so it takes its chances
    with everything else rather than silently disappearing.
    """
    frame.state = ReferenceState.PINNED if pinned else ReferenceState.ACTIVE
    frame.archived_at = None
    session.flush()

    session.add(
        AuditEvent(
            world_id=frame.world_id,
            attempt_id=frame.attempt_id,
            event_type=AuditEventType.REFERENCE_PINNED,
            actor=OWNER,
            payload_json={"reference": str(frame.id), "pinned": pinned},
        )
    )

    rebalance(session, frame.world_id, active_limit=active_limit)
    return frame


def planner_frames(session: Session, world_id: object) -> list[ReferenceFrame]:
    """The frames the planner sees: pinned first, then the strongest active."""
    frames = list(
        session.execute(
            select(ReferenceFrame)
            .where(ReferenceFrame.world_id == world_id)
            .where(ReferenceFrame.state.in_([ReferenceState.ACTIVE, ReferenceState.PINNED]))
        )
        .scalars()
        .all()
    )

    frames.sort(
        key=lambda frame: (
            frame.state is ReferenceState.PINNED,
            frame.strength,
            frame.created_at,
        ),
        reverse=True,
    )
    return frames[:PLANNER_REFERENCE_LIMIT]


def reference_notes(session: Session, world_id: object) -> list[str]:
    """One line per frame, for the planning request."""
    notes: list[str] = []
    for frame in planner_frames(session, world_id):
        parts = [frame.label]
        if frame.hero_product:
            parts.append(f"hero {frame.hero_product}")
        if frame.camera_position:
            parts.append(frame.camera_position)
        if frame.why_it_works:
            parts.append(frame.why_it_works)
        notes.append(" — ".join(parts))
    return notes


def counts(session: Session, world_id: object) -> LibraryCounts:
    """How the library currently breaks down."""
    frames = (
        session.execute(select(ReferenceFrame).where(ReferenceFrame.world_id == world_id))
        .scalars()
        .all()
    )
    return LibraryCounts(
        active=sum(1 for f in frames if f.state is ReferenceState.ACTIVE),
        pinned=sum(1 for f in frames if f.state is ReferenceState.PINNED),
        archived=sum(1 for f in frames if f.state is ReferenceState.ARCHIVED),
    )


__all__ = [
    "DEFAULT_ACTIVE_LIMIT",
    "PLANNER_REFERENCE_LIMIT",
    "DraftNotPromotable",
    "ImageAsset",
    "LibraryCounts",
    "counts",
    "planner_frames",
    "promote",
    "rebalance",
    "reference_notes",
    "set_pinned",
]
