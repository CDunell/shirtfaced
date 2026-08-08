"""The garment checker's own preview must not lie.

It has misled me four times. It read only the viewBox width and clipped every
tall shape. It ignored quadratic segments, so glyphs rendered as debris. It
ignored group transforms, so every placed design sat in the corner. And it drew
cubic curves as straight lines between their endpoints, which made every dome
read as a triangle -- on the strength of which five headwear files were sent
back to be redrawn for a fault that was mine.

A tool used to judge whether a shape looks right has to be checked itself.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "check_garment", ROOT / "scripts" / "check_garment.py"
)
assert _spec and _spec.loader
check_garment = importlib.util.module_from_spec(_spec)
sys.modules["check_garment"] = check_garment
_spec.loader.exec_module(check_garment)


def test_a_cubic_curve_is_subdivided_not_chorded() -> None:
    """A dome drawn as a chord is a triangle, which is what happened."""
    dome = "M 0 100 C 0 20 40 0 100 0 C 160 0 200 20 200 100 Z"
    points = check_garment._flatten(dome)[0]
    assert len(points) > 20, "curve collapsed to its endpoints"

    # The apex must sit near the middle horizontally. A chorded version puts the
    # highest point at the curve's end instead.
    top = min(points, key=lambda p: p[1])
    assert 60 < top[0] < 140, f"apex at x={top[0]:.0f}; the curve is not curving"


def test_a_quadratic_curve_is_subdivided() -> None:
    points = check_garment._flatten("M 0 0 Q 50 100 100 0 Z")[0]
    assert len(points) > 8
    assert max(p[1] for p in points) > 20, "quadratic drawn flat"


def test_an_arc_bulges_off_its_chord() -> None:
    points = check_garment._flatten("M 0 50 A 50 50 0 1 1 100 50 Z")[0]
    assert len(points) > 8
    assert max(abs(p[1] - 50) for p in points) > 10, "arc drawn as a straight line"


def test_two_arcs_make_a_circle_not_a_lens() -> None:
    """The sweep flag has to flip the bulge, or every circle is a rugby ball.

    A circle is normally drawn as two semicircles that must curve opposite
    ways. Ignoring the flag bulged both the same way, which is how a supplied
    ute's wheels came to look as though they had merged into the body.
    """
    import math

    points = check_garment._flatten("M 0 10 A 10 10 0 1 1 20 10 A 10 10 0 1 1 0 10 Z")[0]
    centre_x = sum(p[0] for p in points) / len(points)
    centre_y = sum(p[1] for p in points) / len(points)
    radii = [math.hypot(x - centre_x, y - centre_y) for x, y in points]

    assert min(radii) > 9.0, "circle collapsed towards its chord"
    assert max(radii) < 11.0, "circle bulged past its radius"


def test_an_arc_honours_its_sweep_direction() -> None:
    """The same endpoints with opposite sweeps must curve opposite ways."""
    one = check_garment._flatten("M 0 50 A 50 50 0 0 1 100 50 Z")[0]
    other = check_garment._flatten("M 0 50 A 50 50 0 0 0 100 50 Z")[0]

    assert min(p[1] for p in one) < 50, "sweep 1 did not curve upwards"
    assert max(p[1] for p in other) > 50, "sweep 0 did not curve downwards"


def test_a_straight_path_stays_straight() -> None:
    """The subdivision must not invent curvature where there is none."""
    points = check_garment._flatten("M 0 0 L 100 0 L 100 100 L 0 100 Z")[0]
    assert len(points) == 4
