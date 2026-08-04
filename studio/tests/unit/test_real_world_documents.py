"""The world documents actually shipped in the repository.

The fixtures elsewhere are simplified. This is the real thing: if World 1 stops
loading, this fails.
"""

from __future__ import annotations

import pytest

from app.adapters.markdown_store import MarkdownStore
from app.config import PROJECT_ROOT
from app.domain.enums import ShotStatus
from app.services.world_loader import load_world

WORLDS_ROOT = PROJECT_ROOT / "worlds"

pytestmark = pytest.mark.skipif(
    not (WORLDS_ROOT / "world-01" / "SHOTLIST.md").is_file(),
    reason="World 1 documents are not present.",
)


@pytest.fixture
def world():  # type: ignore[no-untyped-def]
    return load_world(MarkdownStore(WORLDS_ROOT), "world-01")


def test_world_one_loads(world) -> None:  # type: ignore[no-untyped-def]
    assert world.slug == "world-01"
    assert "SHIRTFACED" in world.name


def test_all_twenty_shots_are_read(world) -> None:  # type: ignore[no-untyped-def]
    assert len(world.shots) == 20
    assert world.shots[0].external_id == "W01-001"
    assert world.shots[-1].external_id == "W01-020"


def test_the_shotlist_statuses_match_the_document(world) -> None:  # type: ignore[no-untyped-def]
    by_id = {shot.external_id: shot for shot in world.shots}

    assert by_id["W01-001"].status is ShotStatus.APPROVED
    assert by_id["W01-008"].status is ShotStatus.REJECTED
    assert by_id["W01-011"].status is ShotStatus.PLANNED
    assert len(world.planned_shots) == 10


def test_the_next_planned_shot_is_the_car_interior(world) -> None:  # type: ignore[no-untyped-def]
    """Matches the Next Prompt Brief at the foot of CONTINUITY.md."""
    upcoming = world.planned_shots[0]

    assert upcoming.external_id == "W01-011"
    assert upcoming.title == "Car interior transition"
    assert upcoming.hero_product == "Tote bag"
    assert upcoming.camera_position == "Rear seat"


def test_hero_products_and_cameras_are_read(world) -> None:  # type: ignore[no-untyped-def]
    by_id = {shot.external_id: shot for shot in world.shots}

    assert by_id["W01-006"].hero_product == "Hoodie"
    assert by_id["W01-006"].camera_position == "Dining room"
    assert by_id["W01-020"].hero_product == "Cap"
    assert by_id["W01-020"].camera_position == "Window seat"


def test_documents_hash_to_distinct_values(world) -> None:  # type: ignore[no-untyped-def]
    digests = {
        world.world_document.sha256,
        world.continuity_document.sha256,
        world.shotlist_document.sha256,
    }

    assert len(digests) == 3
