"""Rotation state.

What was used most recently, and what should come next.

The database is authoritative for what has actually been approved. ``CONTINUITY.md``
supplies the author's stated intent — the next product and camera priorities they have
written down — and the rejected drift a planner should be warned about.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.db.models import Shot
from app.domain.enums import ShotStatus
from app.services.markdown_sections import bullets_of, find_section, subsections_of

HERO_PRODUCT_ROTATION = "Hero Product Rotation"
CAMERA_POSITION_ROTATION = "Camera Position Rotation"
NEXT_ROTATION_PRIORITY = "Next Rotation Priority"
NEXT_CAMERA_PRIORITY = "Next Camera Priority"
REJECTED_DRIFT = "Rejected Drift"
CURRENT_CANON_NOTES = "Current Canon Notes"

RECENT_LIMIT = 5


@dataclass(frozen=True)
class RejectedDrift:
    """One rejected direction and the lesson taken from it."""

    title: str
    body: str


@dataclass
class RotationState:
    """What has been used, and what the author wants used next."""

    last_hero_product: str | None = None
    last_camera_position: str | None = None
    recent_hero_products: list[str] = field(default_factory=list)
    recent_camera_positions: list[str] = field(default_factory=list)
    next_product_priority: list[str] = field(default_factory=list)
    next_camera_priority: list[str] = field(default_factory=list)
    canon_notes: list[str] = field(default_factory=list)
    rejected_drift: list[RejectedDrift] = field(default_factory=list)

    def describe(self) -> str:
        """A short line for a selection explanation."""
        product = self.last_hero_product or "none recorded"
        camera = self.last_camera_position or "none recorded"
        return f"last approved hero product {product!r}, last approved camera {camera!r}"


def rotation_from_shots(shots: list[Shot], limit: int = RECENT_LIMIT) -> RotationState:
    """Derive what has been used from approved shots, most recent first.

    Sequence is the running order of the world, so the approved shot with the highest
    sequence is the one immediately preceding whatever comes next.
    """
    approved = sorted(
        (shot for shot in shots if shot.status is ShotStatus.APPROVED),
        key=lambda shot: shot.sequence,
        reverse=True,
    )[:limit]

    products = [shot.hero_product for shot in approved if shot.hero_product]
    cameras = [shot.camera_position for shot in approved if shot.camera_position]

    return RotationState(
        last_hero_product=products[0] if products else None,
        last_camera_position=cameras[0] if cameras else None,
        recent_hero_products=products,
        recent_camera_positions=cameras,
    )


def apply_continuity(state: RotationState, continuity_text: str) -> RotationState:
    """Add the author's stated intent from ``CONTINUITY.md``."""
    state.next_product_priority = _priority_list(continuity_text, NEXT_ROTATION_PRIORITY)
    state.next_camera_priority = _priority_list(continuity_text, NEXT_CAMERA_PRIORITY)

    notes = find_section(continuity_text, CURRENT_CANON_NOTES)
    state.canon_notes = bullets_of(notes.body) if notes else []

    state.rejected_drift = [
        RejectedDrift(title=section.heading, body=section.body)
        for section in subsections_of(continuity_text, REJECTED_DRIFT)
    ]

    return state


def _priority_list(text: str, heading: str) -> list[str]:
    section = find_section(text, heading)
    return bullets_of(section.body) if section else []
