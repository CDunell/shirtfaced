"""Deterministic next-shot selection.

Version 1 selection is a rule, not a judgement. The same database state always yields
the same shot, and the selector records why — an unexplainable choice is a failure of
the product, not just of the code.

Ordering, per the product specification:

1. explicit priority ascending;
2. sequence ascending;
3. creation time ascending.

A shot is ineligible when it is disabled, not planned, blocked by a dependency, or —
where another eligible option exists — when it repeats the hero product or camera
perspective of the immediately preceding approved shot.

Attempt history arrives with the generation orchestrator. Until then "currently
generating" is read from a shot's ``in_progress`` status.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass, field

from app.db.models import Shot, World
from app.domain.enums import ShotStatus
from app.services.rotation import RotationState, rotation_from_shots


@dataclass(frozen=True)
class RejectedCandidate:
    """A shot that was considered and set aside, and why."""

    external_id: str
    reason: str


@dataclass
class Selection:
    """The chosen shot and the reasoning that produced it."""

    shot: Shot
    reason: str
    rotation: RotationState
    eligible_count: int
    set_aside: list[RejectedCandidate] = field(default_factory=list)


@dataclass
class NoSelection:
    """Nothing could be selected, and why not."""

    reason: str
    set_aside: list[RejectedCandidate] = field(default_factory=list)


SelectionOutcome = Selection | NoSelection

# Ties are broken by creation time; this stands in for a null one.
_EPOCH = dt.datetime(1970, 1, 1, tzinfo=dt.UTC)


def _ordering_key(shot: Shot) -> tuple[int, int, dt.datetime, str]:
    """Priority, then sequence, then creation time.

    ``external_id`` is a final tie-break so the result is total: two shots created in
    the same transaction can share a timestamp, and an arbitrary winner would make the
    selector non-deterministic.
    """
    return (shot.priority, shot.sequence, shot.created_at or _EPOCH, shot.external_id)


def _ineligibility(shot: Shot) -> str | None:
    """Why this shot cannot be selected at all, independent of rotation."""
    if shot.disabled:
        return "disabled"
    if shot.status is ShotStatus.IN_PROGRESS:
        return "already generating"
    if shot.status is ShotStatus.APPROVED:
        return "already approved"
    if shot.status is not ShotStatus.PLANNED:
        return f"status is {shot.status.value}"
    if shot.blocked_reason:
        return f"blocked: {shot.blocked_reason}"
    return None


def select_next_shot(world: World, shots: list[Shot] | None = None) -> SelectionOutcome:
    """Choose the next shot for a world, or explain why none can be chosen."""
    all_shots = list(shots if shots is not None else world.shots)
    rotation = rotation_from_shots(all_shots)

    set_aside: list[RejectedCandidate] = []
    eligible: list[Shot] = []

    for shot in all_shots:
        problem = _ineligibility(shot)
        if problem is None:
            eligible.append(shot)
        else:
            set_aside.append(RejectedCandidate(external_id=shot.external_id, reason=problem))

    if not eligible:
        return NoSelection(
            reason=(
                "No planned shot is eligible. Every shot is approved, disabled, blocked "
                "or already generating."
            ),
            set_aside=set_aside,
        )

    eligible.sort(key=_ordering_key)
    eligible_count = len(eligible)

    candidates, product_note = _rotate(
        eligible,
        rotation.last_hero_product,
        lambda shot: shot.hero_product,
        "hero product",
        set_aside,
    )
    candidates, camera_note = _rotate(
        candidates,
        rotation.last_camera_position,
        lambda shot: shot.camera_position,
        "camera",
        set_aside,
    )

    chosen = candidates[0]
    reason = _explain(chosen, eligible_count, product_note, camera_note, rotation)

    return Selection(
        shot=chosen,
        reason=reason,
        rotation=rotation,
        eligible_count=eligible_count,
        set_aside=set_aside,
    )


def _rotate(
    candidates: list[Shot],
    previous: str | None,
    attribute: Callable[[Shot], str | None],
    label: str,
    set_aside: list[RejectedCandidate],
) -> tuple[list[Shot], str]:
    """Drop candidates repeating ``previous``, but never empty the list.

    The specification makes a repeat ineligible only "when another eligible option
    exists", so when every candidate repeats, the rotation rule yields.
    """
    if previous is None:
        return candidates, f"no previous {label} recorded"

    differing = [shot for shot in candidates if attribute(shot) != previous]

    if not differing:
        return candidates, f"every remaining candidate repeats the {label} {previous!r}"

    if len(differing) < len(candidates):
        for shot in candidates:
            if attribute(shot) == previous:
                set_aside.append(
                    RejectedCandidate(
                        external_id=shot.external_id,
                        reason=f"repeats the previous {label} {previous!r}",
                    )
                )

    return differing, f"{label} differs from the previous {previous!r}"


def _explain(
    shot: Shot,
    eligible_count: int,
    product_note: str,
    camera_note: str,
    rotation: RotationState,
) -> str:
    plural = "shot" if eligible_count == 1 else "shots"
    return (
        f"{shot.external_id} chosen from {eligible_count} eligible planned {plural}. "
        f"Lowest priority ({shot.priority}), then sequence ({shot.sequence}). "
        f"Hero product {shot.hero_product or 'unset'!r}: {product_note}. "
        f"Camera {shot.camera_position or 'unset'!r}: {camera_note}. "
        f"Rotation: {rotation.describe()}."
    )
