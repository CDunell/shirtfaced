"""What the corpus measurement must get right.

``_analyse`` produces every number in ``design_patterns.json`` and
``joined.json``, and until now had no test at all. That is not incidental: it is
exactly why three separate failures survived in it for months, each one only
found by painting the print mask back over a photograph and looking.

Each of those three has a test here, named for what it actually got wrong. The
images are synthetic on purpose -- a real photograph would make the assertion
depend on a file nobody can see from the test, and these properties are simple
enough to state exactly.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from mine_design_patterns import _analyse

BACKDROP = (245, 245, 245)


def garment_image(
    path: Path,
    fabric: tuple[int, int, int],
    *,
    print_colour: tuple[int, int, int] | None = None,
    print_box: tuple[int, int, int, int] | None = None,
    shading: bool = False,
    size: int = 900,
) -> Path:
    """A garment on a studio backdrop, optionally printed and optionally draped.

    The garment is a plain rectangle. Nothing here needs it to look like a tee --
    what is being tested is that a region of fabric is found and that what it
    encloses is measured.
    """
    canvas = np.full((size, size, 3), BACKDROP, dtype=np.float32)
    top, bottom = int(size * 0.12), int(size * 0.88)
    left, right = int(size * 0.18), int(size * 0.82)
    canvas[top:bottom, left:right] = fabric

    if shading:
        # A fold is the fabric colour times a scalar: same hue, less light. This
        # is the drape that used to measure as 31% ink on a plain worn tee.
        ramp = np.linspace(0.55, 1.30, right - left, dtype=np.float32)
        canvas[top:bottom, left:right] *= ramp[None, :, None]

    if print_colour is not None and print_box is not None:
        x0, y0, x1, y1 = print_box
        canvas[
            top + int((bottom - top) * y0) : top + int((bottom - top) * y1),
            left + int((right - left) * x0) : left + int((right - left) * x1),
        ] = print_colour

    Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8)).save(path)
    return path


def test_a_plain_garment_has_no_print(tmp_path: Path) -> None:
    result = _analyse(garment_image(tmp_path / "plain.png", (30, 30, 30)))

    assert result is not None
    assert result["has_print"] is False


def test_drape_is_not_ink(tmp_path: Path) -> None:
    """The 31% bug.

    A plain worn tee scored 31% print coverage because the shaded side of it sat
    far enough from the garment's median colour to pass a flat distance test.
    Brightness is divided out before the comparison now, so a fold is still
    fabric.
    """
    result = _analyse(garment_image(tmp_path / "draped.png", (205, 179, 154), shading=True))

    assert result is not None
    assert result.get("refused") is None, result.get("refused")
    assert result["has_print"] is False, f"drape measured as {result['print_coverage']:.1%} ink"


def test_a_light_print_on_a_dark_garment_is_found(tmp_path: Path) -> None:
    """The Formula 1 bug.

    A white print sits far enough from a black garment to trip the cut-off that
    removes skin and background, so a full-front graphic measured as no print at
    all. It is a region the garment encloses like any other.
    """
    result = _analyse(
        garment_image(
            tmp_path / "white-on-black.png",
            (25, 25, 25),
            print_colour=(245, 245, 245),
            print_box=(0.3, 0.3, 0.7, 0.6),
        )
    )

    assert result is not None
    assert result["has_print"] is True
    assert result["light_on_dark"] is True
    assert result["print_coverage"] > 0.05


def test_a_chest_print_high_on_the_garment_is_found(tmp_path: Path) -> None:
    """The CCS bug.

    Measurement used to start 35% down the frame. A chest graphic sits above
    that, so a printed tee measured zero. Placement is read against the garment
    now, not against the frame.
    """
    result = _analyse(
        garment_image(
            tmp_path / "chest.png",
            (215, 215, 215),
            print_colour=(20, 40, 200),
            print_box=(0.3, 0.08, 0.7, 0.24),
        )
    )

    assert result is not None
    assert result["has_print"] is True
    assert result["centroid_y"] < 0.34, "a chest print should read as upper on the garment"


def test_coverage_is_measured_against_the_garment_not_the_frame(tmp_path: Path) -> None:
    """A print covering a known share of the fabric measures near that share."""
    result = _analyse(
        garment_image(
            tmp_path / "quarter.png",
            (60, 90, 160),
            print_colour=(250, 220, 40),
            print_box=(0.25, 0.25, 0.75, 0.75),
        )
    )

    assert result is not None
    # The box is half the garment's width and half its height: a quarter of it.
    assert 0.20 < result["print_coverage"] < 0.30, result["print_coverage"]


def test_ink_colours_counts_flat_spot_colours(tmp_path: Path) -> None:
    path = garment_image(
        tmp_path / "two-ink.png",
        (20, 20, 20),
        print_colour=(230, 40, 40),
        print_box=(0.3, 0.3, 0.7, 0.5),
    )
    # A second ink, painted over part of the first.
    with Image.open(path) as opened:
        canvas = np.asarray(opened.convert("RGB")).copy()
    canvas[380:460, 300:560] = (40, 80, 230)
    Image.fromarray(canvas).save(path)

    result = _analyse(path)

    assert result is not None
    assert result["has_print"] is True
    assert result["ink_colours"] >= 2


def test_a_region_against_the_edge_is_refused_rather_than_scored(tmp_path: Path) -> None:
    """Shading runs off the garment's edge; a graphic does not.

    Where the answer looks like the shaded side of a garment rather than ink, it
    is refused with a reason, and the miner counts refusals instead of averaging
    them in.
    """
    result = _analyse(
        garment_image(
            tmp_path / "edge.png",
            (200, 120, 60),
            print_colour=(40, 40, 40),
            print_box=(0.04, 0.1, 0.16, 0.9),
        )
    )

    assert result is not None
    assert result.get("refused") == "edge shading", result


def test_a_white_garment_on_a_white_backdrop_cannot_be_separated(tmp_path: Path) -> None:
    """A limit, written down rather than discovered again.

    Segmentation starts by asking what differs from the backdrop. A near-white
    garment on a near-white ground differs by almost nothing, so there is no
    subject to find. Real white tees in the corpus measure fine -- they carry
    edge shadow and their own shading -- but a flat white on flat white does not,
    and it should say so rather than return a confident zero.
    """
    result = _analyse(garment_image(tmp_path / "white.png", (243, 243, 243)))

    assert result is not None
    assert result.get("refused") is not None, "expected a refusal, not a measurement"


def test_a_file_that_is_not_an_image_is_none_rather_than_a_crash(tmp_path: Path) -> None:
    broken = tmp_path / "notes.txt"
    broken.write_text("not an image")

    assert _analyse(broken) is None


@pytest.mark.parametrize(
    ("fabric", "ink", "expected"),
    [
        ((20, 20, 20), (240, 240, 240), True),
        ((215, 215, 215), (20, 20, 20), False),
    ],
    ids=["light-on-dark", "dark-on-light"],
)
def test_value_polarity_reads_the_right_way_round(
    tmp_path: Path,
    fabric: tuple[int, int, int],
    ink: tuple[int, int, int],
    expected: bool,
) -> None:
    result = _analyse(
        garment_image(
            tmp_path / f"polarity-{expected}.png",
            fabric,
            print_colour=ink,
            print_box=(0.3, 0.35, 0.7, 0.6),
        )
    )

    assert result is not None
    assert result["has_print"] is True
    assert result["light_on_dark"] is expected
