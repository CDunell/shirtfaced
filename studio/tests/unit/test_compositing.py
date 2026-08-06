"""Printing a design onto a photograph.

The judgement of whether a print looks real is the owner's and is made by looking.
What is pinned here is the behaviour that has to hold for it to be worth looking at:
the print lands where it was put, it takes the garment's light, and it stops at the
edge of the garment.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from app.services.compositing import Placement, PrintSettings, print_design

FLAT = PrintSettings(displacement=0.0, shading=0.0, opacity=1.0, garment_tolerance=0.0)


@pytest.fixture
def photo() -> Image.Image:
    """A mid-grey garment filling the frame."""
    return Image.new("RGB", (120, 120), (90, 90, 90))


@pytest.fixture
def design() -> Image.Image:
    """Solid red, so any pixel it touches is unmistakable."""
    return Image.new("RGBA", (40, 40), (255, 0, 0, 255))


@pytest.fixture
def middle() -> Placement:
    return Placement((40, 40), (80, 40), (80, 80), (40, 80))


def pixel(image: Image.Image, x: int, y: int) -> tuple[int, int, int]:
    return image.convert("RGB").getpixel((x, y))  # type: ignore[return-value]


def test_the_design_lands_inside_the_placement(photo, design, middle) -> None:  # type: ignore[no-untyped-def]
    printed = print_design(photo, design, middle, FLAT)

    assert pixel(printed, 60, 60) == (255, 0, 0)


def test_nothing_outside_the_placement_is_touched(photo, design, middle) -> None:  # type: ignore[no-untyped-def]
    """A print that bleeds is worse than no print: it cannot be undone by eye."""
    printed = print_design(photo, design, middle, FLAT)

    for point in [(5, 5), (115, 5), (5, 115), (115, 115), (60, 20)]:
        assert pixel(printed, *point) == (90, 90, 90), f"{point} was painted over"


def test_the_photograph_is_not_modified(photo, design, middle) -> None:  # type: ignore[no-untyped-def]
    """It returns a new image; the original is somebody's approved frame."""
    before = np.asarray(photo.copy())

    print_design(photo, design, middle, FLAT)

    assert np.array_equal(np.asarray(photo), before)


def test_the_print_takes_the_garment_s_light(design, middle) -> None:  # type: ignore[no-untyped-def]
    """A fold that darkens the shirt has to darken the ink on it.

    Without this the design sits on the photograph rather than in it, which is the
    single thing that gives away a composite.
    """
    shaded = Image.new("RGB", (120, 120), (90, 90, 90))
    for x in range(60, 80):
        for y in range(40, 80):
            shaded.putpixel((x, y), (20, 20, 20))

    printed = print_design(shaded, design, middle, PrintSettings(displacement=0.0, opacity=1.0))

    lit = pixel(printed, 50, 60)
    in_shadow = pixel(printed, 70, 60)
    assert in_shadow[0] < lit[0], "the ink ignored the shadow it is lying in"


def test_the_print_stops_at_the_edge_of_the_garment(design, middle) -> None:  # type: ignore[no-untyped-def]
    """An arm or a bag in front of the chest must not be printed on.

    The fabric colour is learned from the photograph under the design, so this holds
    for a black tee at night and a white one at sunrise without being told which.
    """
    with_arm = Image.new("RGB", (120, 120), (90, 90, 90))
    for x in range(62, 80):
        for y in range(40, 80):
            with_arm.putpixel((x, y), (215, 180, 150))

    printed = print_design(
        with_arm, design, middle, PrintSettings(displacement=0.0, shading=0.0, opacity=1.0)
    )

    assert pixel(printed, 50, 60) == (255, 0, 0), "the garment lost its print"
    assert pixel(printed, 70, 60) == (215, 180, 150), "the arm was printed on"


def test_displacement_moves_the_print_without_losing_it(design, middle) -> None:  # type: ignore[no-untyped-def]
    """Folds push the print around; they do not delete or duplicate it."""
    folded = Image.new("RGB", (120, 120), (90, 90, 90))
    for x in range(120):
        for y in range(120):
            folded.putpixel((x, y), (int(60 + 60 * np.sin(x / 7)),) * 3)

    printed = print_design(folded, design, middle, PrintSettings(shading=0.0, opacity=1.0))
    flat = print_design(folded, design, middle, FLAT)

    red = np.asarray(printed.convert("RGB"), dtype=np.int16)[..., 0]
    flat_red = np.asarray(flat.convert("RGB"), dtype=np.int16)[..., 0]

    assert (red > 150).any(), "the print vanished"
    # Roughly the same amount of ink, in different places. Not exactly the same:
    # displacement resamples, so the edge of a hard-edged shape softens.
    moved = int((red > 150).sum())
    still = int((flat_red > 150).sum())
    assert abs(moved - still) < still * 0.25, f"{moved} vs {still} — ink was gained or lost"
    assert not np.array_equal(red, flat_red), "displacement changed nothing"
