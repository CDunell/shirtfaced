"""Printing an approved design into a defined zone.

The parts that need no database: turning artwork of either kind into an SVG at
a real millimetre size, and reading the zones a garment declares.
"""

from __future__ import annotations

import base64
from io import BytesIO

import pytest
from PIL import Image

from app.config import GARMENTS_DIR as GARMENT_DIR
from app.db.concept_models import ApprovedDesign, DesignAsset
from app.domain.enums import DesignAssetKind
from app.services.approved_print import (
    PrintRefused,
    _as_svg,
    _svg_height,
    available_garments,
    print_approved,
)


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


@pytest.mark.skipif(not GARMENT_DIR.is_dir(), reason="no garment files present")
def test_garments_declare_their_zones_and_are_read_off_the_files() -> None:
    """Adding a garment is dropping a file in, not editing a list.

    Read from the repository's own assets/garments, the same directory
    design_composition uses. An earlier version took an assets_root argument and
    passed this test only because the test handed it a directory it had just
    copied a garment into -- which is precisely how a path bug survives a green
    suite and fails in production.
    """
    found = available_garments()

    assert found, "expected at least one garment SVG with zones"
    assert "garment_tee_crew_front" in found
    zones = {zone.key for zone in found["garment_tee_crew_front"]}
    assert zones
    assert all(zone.width_mm > 0 and zone.height_mm > 0 for zone in found["garment_tee_crew_front"])


def test_the_garment_directory_resolves_to_files_that_exist() -> None:
    """Two bugs pinned at once.

    ASSETS_ROOT is writable output and garments are checked-in source, so they
    are not there. And the location differs between a checkout and the box --
    the deploy syncs studio/'s contents, so walking up to a repository root
    lands outside the deployment. Asserting a *shape* let the second bug
    through; asserting that real files are found does not.
    """
    assert GARMENT_DIR.is_dir(), f"{GARMENT_DIR} does not exist"
    assert list(GARMENT_DIR.glob("garment_*.svg")), f"no garment SVGs in {GARMENT_DIR}"


class _Store:
    """The asset store, reduced to the one thing print_approved asks of it."""

    def __init__(self, data: bytes) -> None:
        self.data = data

    def load(self, key: str) -> bytes:
        return self.data


def _version(spec: dict[str, object], mime: str = "image/png") -> ApprovedDesign:
    """A transient approved version. No session: printing reads the row only."""
    master = DesignAsset(
        kind=DesignAssetKind.ARTWORK,
        relative_path="a.png",
        sha256="0" * 64,
        mime_type=mime,
        byte_size=1,
    )
    version = ApprovedDesign(version=1, approved_by="owner", production_spec=spec)
    version.master_asset = master
    return version


def test_an_approved_version_renders_onto_a_real_garment() -> None:
    """The whole production path, against a checked-in garment.

    This is the test that would have caught the path bug: it names a garment
    that exists in the repository and never creates a directory for it.
    """
    document = print_approved(
        _Store(png(1200, 1200)),
        _version(
            {
                "garment_key": "garment_tee_crew_front",
                "zone_key": "centre_chest",
                "print_width_mm": 180,
            }
        ),
    )

    assert document.startswith("<svg")
    assert "<path" in document, "the garment outline should be drawn"
    assert "data:image/png;base64," in document, "the artwork should be embedded"
    assert "translate(" in document, "the design should be placed into its zone"


def test_a_print_too_large_for_its_zone_is_refused_rather_than_shrunk() -> None:
    """centre_chest is 200x240mm. A 400mm print does not quietly become 200."""
    with pytest.raises(PrintRefused, match="Reduce the print width"):
        print_approved(
            _Store(png(1000, 1000)),
            _version(
                {
                    "garment_key": "garment_tee_crew_front",
                    "zone_key": "centre_chest",
                    "print_width_mm": 400,
                }
            ),
        )


def test_a_zone_the_garment_does_not_have_lists_the_ones_it_does() -> None:
    with pytest.raises(PrintRefused, match="cap_front"):
        print_approved(
            _Store(png(100, 100)),
            _version(
                {
                    "garment_key": "garment_tee_crew_front",
                    "zone_key": "cap_front",
                    "print_width_mm": 80,
                }
            ),
        )


def test_a_version_with_no_print_spec_names_all_three_missing_things() -> None:
    with pytest.raises(PrintRefused, match="garment and no print zone and no print width"):
        print_approved(_Store(png(100, 100)), _version({}))


@pytest.mark.parametrize(
    "garment_key",
    ["../secrets", "..\\secrets", "sub/dir", "/etc/passwd"],
    ids=["parent", "windows-parent", "subdirectory", "absolute"],
)
def test_a_garment_key_cannot_escape_the_garment_directory(garment_key: str) -> None:
    """The key reaches this function from a request body.

    It is a file stem and nothing else. This assertion used to live against
    ``load_design`` in test_print_service.py, guarding the same class of bug on
    the corner-drag print's design names; that path was deleted on 15 August
    2026 and the guard here is what is left holding the property, so the test
    moved rather than went.
    """
    with pytest.raises(PrintRefused, match="no garment called"):
        print_approved(
            _Store(png(100, 100)),
            _version(
                {
                    "garment_key": garment_key,
                    "zone_key": "front_chest",
                    "print_width_mm": 80,
                }
            ),
        )
