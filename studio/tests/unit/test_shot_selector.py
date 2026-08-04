"""Deterministic next-shot selection.

These build ORM objects without a database: the selector is a pure function of the
shots it is handed.
"""

from __future__ import annotations

import datetime as dt

import pytest

from app.db.models import Shot, World
from app.domain.enums import ShotStatus
from app.services.shot_selector import NoSelection, Selection, select_next_shot

BASE_TIME = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)


def make_shot(
    external_id: str,
    *,
    sequence: int,
    priority: int = 100,
    status: ShotStatus = ShotStatus.PLANNED,
    hero_product: str | None = "Tote bag",
    camera_position: str | None = "Rear seat",
    disabled: bool = False,
    blocked_reason: str | None = None,
    created_offset: int = 0,
) -> Shot:
    shot = Shot(
        external_id=external_id,
        sequence=sequence,
        priority=priority,
        title=f"Scene {external_id}",
        hero_product=hero_product,
        camera_position=camera_position,
        status=status,
        disabled=disabled,
        blocked_reason=blocked_reason,
    )
    shot.created_at = BASE_TIME + dt.timedelta(seconds=created_offset)
    return shot


def make_world() -> World:
    return World(slug="world-01", name="World 01", directory_path="world-01")


def select(shots: list[Shot]) -> Selection:
    outcome = select_next_shot(make_world(), shots)
    assert isinstance(outcome, Selection), outcome
    return outcome


def test_selects_the_lowest_priority_eligible_shot() -> None:
    shots = [
        make_shot("W01-011", sequence=11, priority=100),
        make_shot("W01-012", sequence=12, priority=5),
        make_shot("W01-013", sequence=13, priority=50),
    ]

    assert select(shots).shot.external_id == "W01-012"


def test_sequence_breaks_a_priority_tie() -> None:
    shots = [
        make_shot("W01-013", sequence=13),
        make_shot("W01-011", sequence=11),
        make_shot("W01-012", sequence=12),
    ]

    assert select(shots).shot.external_id == "W01-011"


def test_creation_time_breaks_a_sequence_tie() -> None:
    shots = [
        make_shot("W01-B", sequence=11, created_offset=60),
        make_shot("W01-A", sequence=11, created_offset=0),
    ]

    assert select(shots).shot.external_id == "W01-A"


def test_skips_disabled_shots() -> None:
    shots = [
        make_shot("W01-011", sequence=11, priority=1, disabled=True),
        make_shot("W01-012", sequence=12),
    ]

    outcome = select(shots)
    assert outcome.shot.external_id == "W01-012"
    assert any(c.external_id == "W01-011" and c.reason == "disabled" for c in outcome.set_aside)


def test_skips_shots_already_generating() -> None:
    shots = [
        make_shot("W01-011", sequence=11, priority=1, status=ShotStatus.IN_PROGRESS),
        make_shot("W01-012", sequence=12),
    ]

    outcome = select(shots)
    assert outcome.shot.external_id == "W01-012"
    assert any(c.reason == "already generating" for c in outcome.set_aside)


def test_skips_approved_shots() -> None:
    shots = [
        make_shot("W01-001", sequence=1, priority=1, status=ShotStatus.APPROVED),
        make_shot("W01-012", sequence=12),
    ]

    assert select(shots).shot.external_id == "W01-012"


def test_skips_blocked_shots() -> None:
    shots = [
        make_shot("W01-011", sequence=11, priority=1, blocked_reason="waiting on location"),
        make_shot("W01-012", sequence=12),
    ]

    outcome = select(shots)
    assert outcome.shot.external_id == "W01-012"
    assert any("waiting on location" in c.reason for c in outcome.set_aside)


def test_rotates_the_hero_product_when_an_alternative_exists() -> None:
    shots = [
        make_shot("W01-001", sequence=1, status=ShotStatus.APPROVED, hero_product="Cap"),
        make_shot("W01-011", sequence=11, hero_product="Cap"),
        make_shot("W01-012", sequence=12, hero_product="Tote bag"),
    ]

    outcome = select(shots)
    assert outcome.shot.external_id == "W01-012"
    assert any("repeats the previous hero product" in c.reason for c in outcome.set_aside)


def test_repeats_the_hero_product_when_nothing_else_is_eligible() -> None:
    """The rule applies only when another eligible option exists."""
    shots = [
        make_shot("W01-001", sequence=1, status=ShotStatus.APPROVED, hero_product="Cap"),
        make_shot("W01-011", sequence=11, hero_product="Cap"),
    ]

    outcome = select(shots)
    assert outcome.shot.external_id == "W01-011"
    assert "every remaining candidate repeats" in outcome.reason


def test_rotates_the_camera_when_an_alternative_exists() -> None:
    shots = [
        make_shot(
            "W01-001",
            sequence=1,
            status=ShotStatus.APPROVED,
            hero_product="Cap",
            camera_position="Front gate",
        ),
        make_shot("W01-011", sequence=11, hero_product="Tote bag", camera_position="Front gate"),
        make_shot("W01-012", sequence=12, hero_product="Tote bag", camera_position="Rear seat"),
    ]

    outcome = select(shots)
    assert outcome.shot.external_id == "W01-012"
    assert any("repeats the previous camera" in c.reason for c in outcome.set_aside)


def test_product_rotation_is_applied_before_camera_rotation() -> None:
    """The specification lists product rotation first, and it is the stronger rule."""
    shots = [
        make_shot(
            "W01-001",
            sequence=1,
            status=ShotStatus.APPROVED,
            hero_product="Cap",
            camera_position="Front gate",
        ),
        # Differs on camera but repeats the product.
        make_shot("W01-011", sequence=11, hero_product="Cap", camera_position="Rear seat"),
        # Differs on product but repeats the camera.
        make_shot("W01-012", sequence=12, hero_product="Tote bag", camera_position="Front gate"),
    ]

    assert select(shots).shot.external_id == "W01-012"


def test_rotation_uses_the_most_recently_approved_shot() -> None:
    shots = [
        make_shot("W01-001", sequence=1, status=ShotStatus.APPROVED, hero_product="T-shirt"),
        make_shot("W01-009", sequence=9, status=ShotStatus.APPROVED, hero_product="Cap"),
        make_shot("W01-011", sequence=11, hero_product="Cap"),
        make_shot("W01-012", sequence=12, hero_product="T-shirt"),
    ]

    outcome = select(shots)
    assert outcome.rotation.last_hero_product == "Cap"
    assert outcome.shot.external_id == "W01-012"


def test_records_why_the_shot_was_selected() -> None:
    shots = [
        make_shot("W01-001", sequence=1, status=ShotStatus.APPROVED, hero_product="Cap"),
        make_shot("W01-011", sequence=11, hero_product="Tote bag", camera_position="Rear seat"),
    ]

    reason = select(shots).reason

    assert "W01-011" in reason
    assert "priority" in reason
    assert "sequence" in reason
    assert "Tote bag" in reason
    assert "Rear seat" in reason


def test_is_deterministic_regardless_of_input_order() -> None:
    def shots() -> list[Shot]:
        return [
            make_shot("W01-011", sequence=11, hero_product="Tote bag"),
            make_shot("W01-012", sequence=12, hero_product="Hoodie"),
            make_shot("W01-013", sequence=13, hero_product="Cap"),
        ]

    forwards = select(shots())
    backwards = select(list(reversed(shots())))

    assert forwards.shot.external_id == backwards.shot.external_id
    assert forwards.reason == backwards.reason


def test_repeated_selection_returns_the_same_shot() -> None:
    shots = [make_shot("W01-011", sequence=11), make_shot("W01-012", sequence=12)]

    assert {select(shots).shot.external_id for _ in range(5)} == {"W01-011"}


def test_reports_when_nothing_is_eligible() -> None:
    shots = [
        make_shot("W01-001", sequence=1, status=ShotStatus.APPROVED),
        make_shot("W01-002", sequence=2, disabled=True),
    ]

    outcome = select_next_shot(make_world(), shots)

    assert isinstance(outcome, NoSelection)
    assert "No planned shot is eligible" in outcome.reason
    assert len(outcome.set_aside) == 2


def test_reports_when_a_world_has_no_shots() -> None:
    outcome = select_next_shot(make_world(), [])

    assert isinstance(outcome, NoSelection)


@pytest.mark.parametrize("status", [ShotStatus.REJECTED, ShotStatus.ABANDONED, ShotStatus.APPROVED])
def test_only_planned_shots_are_eligible(status: ShotStatus) -> None:
    outcome = select_next_shot(make_world(), [make_shot("W01-011", sequence=11, status=status)])

    assert isinstance(outcome, NoSelection)
