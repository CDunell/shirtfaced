"""Loading and validating world documents."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.adapters.markdown_store import MarkdownStore
from app.domain.enums import ShotStatus
from app.domain.errors import WorldValidationError
from app.services.world_loader import load_world
from tests.fixtures.worlds import VALID_SHOTLIST, VALID_WORLD, write_world


def _load(root: Path, **overrides: str):  # type: ignore[no-untyped-def]
    write_world(root, **overrides)
    return load_world(MarkdownStore(root), "world-01")


def test_loads_valid_documents(tmp_path: Path) -> None:
    loaded = _load(tmp_path)

    assert loaded.slug == "world-01"
    assert loaded.name.startswith("SHIRTFACED")
    assert loaded.directory_path == "world-01"


def test_records_a_hash_for_each_document(tmp_path: Path) -> None:
    loaded = _load(tmp_path)

    digests = {
        loaded.world_document.sha256,
        loaded.continuity_document.sha256,
        loaded.shotlist_document.sha256,
    }
    assert len(digests) == 3
    assert all(len(digest) == 64 for digest in digests)


def test_parses_every_shot(tmp_path: Path) -> None:
    loaded = _load(tmp_path)

    assert [shot.external_id for shot in loaded.shots] == [
        "W01-001",
        "W01-008",
        "W01-011",
        "W01-012",
    ]


def test_maps_status_markers(tmp_path: Path) -> None:
    loaded = _load(tmp_path)
    by_id = {shot.external_id: shot for shot in loaded.shots}

    assert by_id["W01-001"].status is ShotStatus.APPROVED
    assert by_id["W01-008"].status is ShotStatus.REJECTED
    assert by_id["W01-011"].status is ShotStatus.PLANNED


def test_planned_shots_are_available_separately(tmp_path: Path) -> None:
    loaded = _load(tmp_path)

    assert [shot.external_id for shot in loaded.planned_shots] == ["W01-011", "W01-012"]


def test_captures_shot_metadata(tmp_path: Path) -> None:
    loaded = _load(tmp_path)
    shot = next(s for s in loaded.shots if s.external_id == "W01-011")

    assert shot.title == "Car interior transition"
    assert shot.hero_product == "Tote bag"
    assert shot.camera_position == "Rear seat"
    assert shot.sequence == 3
    assert shot.source_line > 0


def test_unknown_sections_are_preserved(tmp_path: Path) -> None:
    """The loader must not require the author to drop their own sections."""
    loaded = _load(tmp_path)

    assert "An Unknown Section" in loaded.world_document.headings


def test_accepts_canonical_text_statuses(tmp_path: Path) -> None:
    """The contract requires the file to stay usable in a plain terminal."""
    shotlist = VALID_SHOTLIST.replace("✅", "approved").replace("⬜", "planned")
    shotlist = shotlist.replace("❌", "rejected")

    loaded = _load(tmp_path, shotlist=shotlist)

    assert {shot.status for shot in loaded.shots} == {
        ShotStatus.APPROVED,
        ShotStatus.REJECTED,
        ShotStatus.PLANNED,
    }


def test_reports_a_missing_world_heading(tmp_path: Path) -> None:
    broken = VALID_WORLD.replace("# Colour Palette", "# Color Palette")

    with pytest.raises(WorldValidationError) as caught:
        _load(tmp_path, world=broken)

    assert "Colour Palette" in str(caught.value)
    assert "WORLD.md" in str(caught.value)


def test_reports_every_problem_at_once(tmp_path: Path) -> None:
    """An operator fixing a file wants the whole list, not one fault per run."""
    broken = VALID_WORLD.replace("# Lighting", "# Lights").replace("# People", "# Persons")

    with pytest.raises(WorldValidationError) as caught:
        _load(tmp_path, world=broken)

    assert len(caught.value.problems) == 2


def test_reports_a_missing_continuity_heading(tmp_path: Path) -> None:
    with pytest.raises(WorldValidationError, match="Rejected Drift"):
        _load(tmp_path, continuity="# Status Key\n")


def test_reports_a_missing_shot_table(tmp_path: Path) -> None:
    with pytest.raises(WorldValidationError, match="required columns"):
        _load(tmp_path, shotlist="# Shotlist\n\nNo table here.\n")


def test_reports_an_unrecognised_status_with_its_line(tmp_path: Path) -> None:
    shotlist = VALID_SHOTLIST.replace("Rear seat           ⬜", "Rear seat           ~")

    with pytest.raises(WorldValidationError) as caught:
        _load(tmp_path, shotlist=shotlist)

    problem = caught.value.problems[0]
    assert "W01-011" in problem.message
    assert problem.line is not None


def test_reports_a_duplicate_shot_id(tmp_path: Path) -> None:
    shotlist = VALID_SHOTLIST.replace("W01-012   Apartment lift", "W01-011   Apartment lift")

    with pytest.raises(WorldValidationError, match="Duplicate shot ID W01-011"):
        _load(tmp_path, shotlist=shotlist)


def test_reports_a_row_with_no_scene(tmp_path: Path) -> None:
    shotlist = VALID_SHOTLIST.replace(
        "W01-012   Apartment lift            Hoodie waist   Inside lift         ⬜",
        "W01-012                             Hoodie waist   Inside lift         ⬜",
    )

    with pytest.raises(WorldValidationError, match="no scene"):
        _load(tmp_path, shotlist=shotlist)


def test_priority_defaults_when_the_column_is_absent(tmp_path: Path) -> None:
    loaded = _load(tmp_path)

    assert {shot.priority for shot in loaded.shots} == {100}


def test_priority_is_read_when_present(tmp_path: Path) -> None:
    shotlist = """\
# Shotlist

| ID | Scene | Hero Product | Camera | Status | Priority |
|---|---|---|---|---|---|
| W01-011 | Car interior | Tote bag | Rear seat | ⬜ | 5 |
"""

    loaded = _load(tmp_path, shotlist=shotlist)

    assert loaded.shots[0].priority == 5


def test_reports_a_non_numeric_priority(tmp_path: Path) -> None:
    shotlist = """\
# Shotlist

| ID | Scene | Hero Product | Camera | Status | Priority |
|---|---|---|---|---|---|
| W01-011 | Car interior | Tote bag | Rear seat | ⬜ | urgent |
"""

    with pytest.raises(WorldValidationError, match="non-numeric priority"):
        _load(tmp_path, shotlist=shotlist)
