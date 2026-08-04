"""Rotation state, including against the real CONTINUITY.md."""

from __future__ import annotations

import pytest

from app.adapters.markdown_store import MarkdownStore
from app.config import PROJECT_ROOT
from app.domain.enums import ShotStatus
from app.services.markdown_sections import bullets_of, find_section, split_sections
from app.services.rotation import RotationState, apply_continuity, rotation_from_shots
from tests.unit.test_shot_selector import make_shot

WORLDS_ROOT = PROJECT_ROOT / "worlds"


def test_last_used_comes_from_the_highest_sequence_approved_shot() -> None:
    shots = [
        make_shot("W01-001", sequence=1, status=ShotStatus.APPROVED, hero_product="T-shirt"),
        make_shot(
            "W01-010",
            sequence=10,
            status=ShotStatus.APPROVED,
            hero_product="Cap",
            camera_position="Beside parked car",
        ),
        make_shot("W01-011", sequence=11, hero_product="Tote bag"),
    ]

    state = rotation_from_shots(shots)

    assert state.last_hero_product == "Cap"
    assert state.last_camera_position == "Beside parked car"


def test_planned_and_rejected_shots_do_not_count_as_used() -> None:
    shots = [
        make_shot("W01-008", sequence=8, status=ShotStatus.REJECTED, hero_product="Mixed"),
        make_shot("W01-011", sequence=11, hero_product="Tote bag"),
    ]

    assert rotation_from_shots(shots).last_hero_product is None


def test_recent_history_is_ordered_most_recent_first_and_capped() -> None:
    shots = [
        make_shot(
            f"W01-{index:03d}",
            sequence=index,
            status=ShotStatus.APPROVED,
            hero_product=f"Product {index}",
        )
        for index in range(1, 9)
    ]

    state = rotation_from_shots(shots)

    assert state.recent_hero_products[0] == "Product 8"
    assert len(state.recent_hero_products) == 5


def test_describe_is_readable_when_nothing_is_recorded() -> None:
    assert "none recorded" in RotationState().describe()


# --- section reading ---------------------------------------------------------------


def test_sections_are_split_by_heading() -> None:
    text = "# One\n\nfirst\n\n## Nested\n\nsecond\n\n# Two\n\nthird\n"

    sections = split_sections(text)

    assert [section.heading for section in sections] == ["One", "Nested", "Two"]
    assert sections[0].body == "first"
    assert sections[2].body == "third"


def test_bullets_drop_markers_and_emphasis() -> None:
    assert bullets_of("- **APPROVED** — belongs\n- plain\n1. numbered\n") == [
        "APPROVED — belongs",
        "plain",
        "numbered",
    ]


def test_a_missing_section_is_none() -> None:
    assert find_section("# One\n\ntext\n", "Nope") is None


# --- the real document -------------------------------------------------------------

pytestmark_real = pytest.mark.skipif(
    not (WORLDS_ROOT / "world-01" / "CONTINUITY.md").is_file(),
    reason="World 1 documents are not present.",
)


@pytest.fixture
def continuity_text() -> str:
    return MarkdownStore(WORLDS_ROOT).read_document("world-01", "CONTINUITY.md").text


@pytestmark_real
def test_reads_the_authors_next_product_priority(continuity_text: str) -> None:
    state = apply_continuity(RotationState(), continuity_text)

    assert state.next_product_priority[0] == "Black tote bag"
    assert "Hoodie tied around waist" in state.next_product_priority


@pytestmark_real
def test_reads_the_authors_next_camera_priority(continuity_text: str) -> None:
    state = apply_continuity(RotationState(), continuity_text)

    assert any("rear seat" in entry.lower() for entry in state.next_camera_priority)


@pytestmark_real
def test_reads_the_rejected_drift_entries(continuity_text: str) -> None:
    state = apply_continuity(RotationState(), continuity_text)

    titles = [entry.title for entry in state.rejected_drift]
    assert "Closed Bottle Shop" in titles
    assert any("Pickup Tub" in title for title in titles)


@pytestmark_real
def test_rejected_drift_carries_the_permanent_lesson(continuity_text: str) -> None:
    state = apply_continuity(RotationState(), continuity_text)
    bottle_shop = next(e for e in state.rejected_drift if e.title == "Closed Bottle Shop")

    assert "Permanent lesson" in bottle_shop.body
    assert "movement" in bottle_shop.body


@pytestmark_real
def test_reads_the_current_canon_notes(continuity_text: str) -> None:
    state = apply_continuity(RotationState(), continuity_text)

    assert "Optimism does not require loud behaviour." in state.canon_notes
    assert any("tray-back ute" in note for note in state.canon_notes)
