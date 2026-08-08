"""Bringing outside artwork in.

Everything comes in and everything can be designed with. What is tested here is
that the file is readable as geometry and that where it came from travels with
it -- because the rights question is asked later, about a finished design, and
whoever asks it needs to know what to look up.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.archive.ingest import (
    BUSY_COMMANDS,
    NotIngestible,
    Source,
    complexity_of,
    ingest_svg,
    verify,
)
from app.archive.render import Palette, render
from app.domain.enums import LicenceStatus

SOURCE = Source(
    name="smithsonian",
    item_id="SI-1234",
    url="https://example.invalid/SI-1234",
)

SIMPLE_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<path d="M 10 10 L 90 10 L 90 90 L 10 90 Z" fill="#ff0000"/>'
    "</svg>"
)


def _write(tmp_path: Path, svg: str, name: str = "artwork.svg") -> Path:
    file = tmp_path / name
    file.write_text(svg, encoding="utf-8")
    return file


def _ingest(tmp_path: Path, svg: str = SIMPLE_SVG):
    return ingest_svg(
        _write(tmp_path, svg),
        element_key="ingested_test_0001",
        recipe_family="symbol",
        subtype="test_shape",
        source=SOURCE,
    )


# --- The rule the module exists to hold -------------------------------------


def test_ingesting_records_the_terms_as_unknown(tmp_path: Path) -> None:
    """Unknown is the honest state for something nobody has looked up. It is
    not a block -- see the next test."""
    element = _ingest(tmp_path)
    assert element.licence.status is LicenceStatus.UNVERIFIED


def test_an_ingested_element_can_be_designed_with_immediately(tmp_path: Path) -> None:
    """Other people's work is what everyone learns from. Turning away from it
    to avoid seeing it is not caution, it is not looking."""
    element = _ingest(tmp_path)
    result = render(element, {}, Palette(inks=("#C6FF00",)), seed=1)
    assert "<path" in result.svg


def test_the_source_is_recorded_against_the_item_not_the_collection(tmp_path: Path) -> None:
    """A collection's open metadata is not a licence for every image in it."""
    element = _ingest(tmp_path)
    assert element.licence.source == "smithsonian"
    assert element.licence.source_id == "SI-1234"
    assert element.licence.source_url.endswith("SI-1234")


def test_a_source_with_no_item_identifier_is_refused() -> None:
    with pytest.raises(NotIngestible) as raised:
        Source(name="internet-archive", item_id="", url="https://example.invalid")
    assert raised.value.reason == "SOURCE_HAS_NO_IDENTIFIER"


def test_a_source_with_no_name_is_refused() -> None:
    with pytest.raises(NotIngestible) as raised:
        Source(name="", item_id="x", url="https://example.invalid")
    assert raised.value.reason == "SOURCE_NOT_NAMED"


# --- Verification is a person's act, recorded --------------------------------


def test_verifying_records_what_the_terms_actually_say(tmp_path: Path) -> None:
    element = verify(
        _ingest(tmp_path), terms="CC0", checked_at=date(2026, 8, 8), commercial_use=True
    )
    assert element.licence.usable
    assert element.licence.terms == "CC0"
    assert element.licence.checked_at == date(2026, 8, 8)


def test_a_verified_element_then_renders(tmp_path: Path) -> None:
    element = verify(
        _ingest(tmp_path), terms="CC0", checked_at=date(2026, 8, 8), commercial_use=True
    )
    result = render(element, {}, Palette(inks=("#C6FF00",)), seed=1)
    assert "<path" in result.svg


def test_verifying_without_recording_the_terms_is_refused(tmp_path: Path) -> None:
    """Verified must mean what was read, not that someone looked."""
    with pytest.raises(NotIngestible) as raised:
        verify(_ingest(tmp_path), terms="   ", checked_at=date(2026, 8, 8), commercial_use=True)
    assert raised.value.reason == "TERMS_NOT_RECORDED"


def test_non_commercial_terms_mark_it_refused_rather_than_deleting_it(tmp_path: Path) -> None:
    """So the same artwork is not found and re-checked in six months."""
    element = verify(
        _ingest(tmp_path),
        terms="CC BY-NC",
        checked_at=date(2026, 8, 8),
        commercial_use=False,
        note="Non-commercial only; unusable on goods that are sold.",
    )
    assert element.licence.status is LicenceStatus.REFUSED
    assert not element.licence.usable
    assert "Non-commercial" in element.licence.note


# --- What the file itself can and cannot be ---------------------------------


def test_geometry_is_taken_and_colour_is_not(tmp_path: Path) -> None:
    """Baking the original's colours in would make one ink choice permanent."""
    element = _ingest(tmp_path)
    assert "M 10 10" in element.geometry
    assert "#ff0000" not in element.geometry


def test_several_paths_become_one_element(tmp_path: Path) -> None:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<path d="M 0 0 L 10 0 Z"/><path d="M 20 20 L 30 20 Z"/></svg>'
    )
    element = _ingest(tmp_path, svg)
    assert "M 0 0" in element.geometry
    assert "M 20 20" in element.geometry


def test_a_file_with_no_paths_is_refused_with_advice(tmp_path: Path) -> None:
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>'
    with pytest.raises(NotIngestible) as raised:
        _ingest(tmp_path, svg)
    assert raised.value.reason == "NO_PATH_GEOMETRY"
    assert "rect" in raised.value.detail


def test_artwork_too_detailed_to_separate_is_refused(tmp_path: Path) -> None:
    """Refused now beats ingested and quietly disappointing someone later."""
    busy = "".join(f"L {index} {index} " for index in range(5000))
    svg = f'<svg xmlns="http://www.w3.org/2000/svg"><path d="M 0 0 {busy}Z"/></svg>'
    with pytest.raises(NotIngestible) as raised:
        _ingest(tmp_path, svg)
    assert raised.value.reason == "TOO_DETAILED_TO_PRINT"


def test_a_missing_file_is_refused_rather_than_crashing(tmp_path: Path) -> None:
    with pytest.raises(NotIngestible) as raised:
        ingest_svg(
            tmp_path / "nothing.svg",
            element_key="k",
            recipe_family="symbol",
            subtype="s",
            source=SOURCE,
        )
    assert raised.value.reason == "UNREADABLE_FILE"


def test_complexity_is_measured_from_drawing_commands(tmp_path: Path) -> None:
    """File size mostly measures how the exporter felt about decimal places."""
    assert complexity_of("M 0 0 L 1 1 Z") == pytest.approx(3 / BUSY_COMMANDS)
    assert complexity_of("M 0 0 " + "L 1 1 " * 10_000) == 1.0


def test_an_ingested_element_carries_no_slots(tmp_path: Path) -> None:
    """Found artwork has no declared place for supplied words; someone must
    author that before it can hold any."""
    assert _ingest(tmp_path).slots == ()
