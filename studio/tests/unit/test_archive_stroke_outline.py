"""Thickening a stroked path into a fillable outline.

The archive stores filled silhouettes. Supplied line art is frequently strokes
instead -- a bought pack, a traced sheet, a technical drawing -- and filling a
stroked path directly turns a drawing of a water tank into a black blob.

The alternative was a rule telling suppliers to outline before sending. Seven of
twelve files in one delivery would have failed it, and the supplier had already
said it expected to filter out bulk sources to meet rules like that. So the
engine does the work instead.
"""

from __future__ import annotations

from app.archive.convert import _polyline, outline_stroke


def _points(path_data: str) -> list[tuple[float, float]]:
    import re

    numbers = [float(n) for n in re.findall(r"-?\d*\.?\d+", path_data)]
    return list(zip(numbers[0::2], numbers[1::2], strict=False))


def test_a_stroked_line_becomes_a_rectangle_of_its_width() -> None:
    outlined = outline_stroke("M 0 5 L 20 5", 2.0)
    ys = {y for _, y in _points(outlined)}

    assert ys == {4.0, 6.0}, "the stroke was not offset half its width either side"


def test_the_outline_is_closed() -> None:
    """An open ring would fill as a wedge rather than a line."""
    assert outline_stroke("M 0 0 L 10 0", 1.0).rstrip().endswith("Z")


def test_a_zero_width_stroke_is_left_alone() -> None:
    """Nothing to thicken. Returning the input keeps callers simple."""
    assert outline_stroke("M 0 0 L 5 5", 0.0) == "M 0 0 L 5 5"


def test_curves_are_walked_rather_than_chorded() -> None:
    """A curve reduced to its endpoints would thicken into a straight bar."""
    curve = _polyline("M 0 0 C 10 -10 20 10 30 0")

    assert len(curve) > 8, "the curve was not subdivided"


def test_a_closed_subpath_returns_to_its_start() -> None:
    """Z has to close back to the last M, not to the origin."""
    square = _polyline("M 5 5 L 15 5 L 15 15 L 5 15 Z")

    assert square[0] == square[-1] == (5.0, 5.0)


def test_each_subpath_is_thickened_separately() -> None:
    """Two strokes must not be joined into one ring across the gap."""
    outlined = outline_stroke("M 0 0 L 10 0 M 0 10 L 10 10", 2.0)

    assert outlined.count("M") == 2, "the subpaths were merged"
