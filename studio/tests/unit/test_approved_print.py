"""Printing an approved design into a defined zone.

The parts that need no database: turning artwork of either kind into an SVG at
a real millimetre size, and reading the zones a garment declares.
"""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from app.services.approved_print import PrintRefused, _as_svg, _svg_height, available_garments

ASSETS = Path(__file__).resolve().parents[3] / "assets"


def png(width: int, height: int) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), (200, 40, 40)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_a_raster_keeps_its_aspect_ratio_rather_than_filling_the_zone() -> None:
    """The width is the decision and the height is arithmetic. A print
    stretched to fill a zone is not the design that was approved."""
    document, width, height = _as_svg(png(2000, 1000), "image/png", 240)

    assert width == 240
    assert height == pytest.approx(120)
    assert document.startswith("<svg")
    assert 'href="data:image/png;base64,' in document


def test_a_raster_is_embedded_not_referenced() -> None:
    """The rendered document has to survive being saved and opened somewhere
    with no access to this server."""
    data = png(100, 100)
    document, _width, _height = _as_svg(data, "image/png", 100)

    assert base64.b64encode(data).decode("ascii") in document


def test_a_tall_raster_stays_tall() -> None:
    _document, width, height = _as_svg(png(500, 1500), "image/png", 100)

    assert width == 100
    assert height == pytest.approx(300)


def test_vector_artwork_is_used_as_it_stands_and_only_measured() -> None:
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 150"><rect/></svg>'
    document, width, height = _as_svg(svg, "image/svg+xml", 240)

    assert document == svg.decode()
    assert width == 240
    assert height == pytest.approx(120)


def test_an_svg_without_a_declared_mime_type_is_still_recognised() -> None:
    """An upload can arrive as application/octet-stream. The bytes decide."""
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 200"></svg>'
    _document, width, height = _as_svg(svg, "application/octet-stream", 50)

    assert (width, height) == (50, pytest.approx(100))


def test_an_unreadable_viewbox_falls_back_to_square_rather_than_guessing() -> None:
    assert _svg_height("<svg></svg>", 240) == 240
    assert _svg_height('<svg viewBox="0 0 0 100"></svg>', 240) == 240


def test_a_type_that_cannot_be_placed_is_refused_by_name() -> None:
    with pytest.raises(PrintRefused, match="application/pdf"):
        _as_svg(b"%PDF-1.4", "application/pdf", 240)


def test_bytes_that_are_not_an_image_are_refused_rather_than_placed_blank() -> None:
    with pytest.raises(PrintRefused, match="not a readable image"):
        _as_svg(b"not an image at all", "image/png", 240)


@pytest.mark.skipif(not (ASSETS / "garments").is_dir(), reason="no garment files present")
def test_garments_declare_their_zones_and_are_read_off_the_files() -> None:
    """Adding a garment is dropping a file in, not editing a list."""
    found = available_garments(ASSETS)

    assert found, "expected at least one garment SVG with zones"
    assert "garment_tee_crew_front" in found
    zones = {zone.key for zone in found["garment_tee_crew_front"]}
    assert zones
    assert all(zone.width_mm > 0 and zone.height_mm > 0 for zone in found["garment_tee_crew_front"])


def test_a_missing_garments_directory_is_empty_rather_than_an_error(tmp_path: Path) -> None:
    assert available_garments(tmp_path) == {}
