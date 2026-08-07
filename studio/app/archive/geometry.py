"""Authored parametric shapes: the frames, symbols and ornaments.

These are the families that cannot be ingested. A shield is not a picture of a
shield -- it is an aspect, a shoulder height, a point depth and a corner radius,
and writing it as geometry gives something a scan never can: it scales to any
print without resampling, it separates cleanly, and it is identical every time.

Everything here returns SVG path data in millimetres, drawn inside a box whose
top-left is the origin. Nothing reads a clock or a random source; where a shape
wants variation, the caller passes a seeded generator explicitly.

The shapes are deliberately plain. A frame's job is to hold supplied content at
a known proportion, not to be interesting on its own -- an ornate outline
competes with the words inside it, and the words are the part the owner chose.
"""

from __future__ import annotations

import math
import random

from app.archive.svg import jitter, num


def _path(commands: list[str]) -> str:
    return " ".join(commands)


def _move(x: float, y: float) -> str:
    return f"M {num(x)} {num(y)}"


def _line(x: float, y: float) -> str:
    return f"L {num(x)} {num(y)}"


def _curve(x1: float, y1: float, x2: float, y2: float, x: float, y: float) -> str:
    return f"C {num(x1)} {num(y1)} {num(x2)} {num(y2)} {num(x)} {num(y)}"


def _arc(rx: float, ry: float, large: int, sweep: int, x: float, y: float) -> str:
    return f"A {num(rx)} {num(ry)} 0 {large} {sweep} {num(x)} {num(y)}"


# --- Frames -----------------------------------------------------------------


def rectangle(width: float, height: float, radius: float = 0.0) -> str:
    """A rectangle, optionally with rounded corners."""
    r = max(0.0, min(radius, min(width, height) / 2))
    if r <= 0:
        return _path([_move(0, 0), _line(width, 0), _line(width, height), _line(0, height), "Z"])
    return _path(
        [
            _move(r, 0),
            _line(width - r, 0),
            _arc(r, r, 0, 1, width, r),
            _line(width, height - r),
            _arc(r, r, 0, 1, width - r, height),
            _line(r, height),
            _arc(r, r, 0, 1, 0, height - r),
            _line(0, r),
            _arc(r, r, 0, 1, r, 0),
            "Z",
        ]
    )


def capsule(width: float, height: float) -> str:
    """A stadium: straight sides, semicircular ends. Reads as a patch or tab."""
    return rectangle(width, height, radius=height / 2)


def shield(width: float, height: float, shoulder: float = 0.26, point: float = 0.34) -> str:
    """A workwear or institutional shield.

    ``shoulder`` is how far down the straight sides run before the shape starts
    turning in, and ``point`` how much of the height the bottom taper occupies.
    Both are shares of the height, so the shield holds its character at any size.
    """
    shoulder_y = height * shoulder
    taper_y = height * (1.0 - point)
    return _path(
        [
            _move(0, 0),
            _line(width, 0),
            _line(width, shoulder_y),
            _line(width, taper_y),
            _curve(width, height * 0.90, width * 0.72, height, width / 2, height),
            _curve(width * 0.28, height, 0, height * 0.90, 0, taper_y),
            _line(0, shoulder_y),
            "Z",
        ]
    )


def circle(diameter: float) -> str:
    r = diameter / 2
    return _path(
        [
            _move(0, r),
            _arc(r, r, 1, 1, diameter, r),
            _arc(r, r, 1, 1, 0, r),
            "Z",
        ]
    )


def arch(width: float, height: float, spring: float = 0.55) -> str:
    """A rounded top over straight sides -- a plaque, a headstone, a gateway.

    ``spring`` is where the curve begins, as a share of the height.
    """
    spring_y = height * spring
    return _path(
        [
            _move(0, height),
            _line(0, spring_y),
            _arc(width / 2, spring_y, 0, 1, width, spring_y),
            _line(width, height),
            "Z",
        ]
    )


def ticket(width: float, height: float, notch: float = 0.12) -> str:
    """A rectangle with a notch bitten out of each side, like a torn stub."""
    r = height * notch
    middle = height / 2
    return _path(
        [
            _move(0, 0),
            _line(width, 0),
            _line(width, middle - r),
            _arc(r, r, 0, 0, width, middle + r),
            _line(width, height),
            _line(0, height),
            _line(0, middle + r),
            _arc(r, r, 0, 0, 0, middle - r),
            "Z",
        ]
    )


def plaque(width: float, height: float, inset: float = 0.14) -> str:
    """A rectangle with concave sides -- a cartouche, a nameplate."""
    dx = width * inset
    return _path(
        [
            _move(0, 0),
            _line(width, 0),
            _curve(width - dx, height * 0.3, width - dx, height * 0.7, width, height),
            _line(0, height),
            _curve(dx, height * 0.7, dx, height * 0.3, 0, 0),
            "Z",
        ]
    )


# --- Symbols ----------------------------------------------------------------


def star(diameter: float, points: int = 5, inner: float = 0.40) -> str:
    """A star with the first point at twelve o'clock."""
    outer_r = diameter / 2
    inner_r = outer_r * inner
    commands: list[str] = []
    for index in range(points * 2):
        radius = outer_r if index % 2 == 0 else inner_r
        angle = -math.pi / 2 + index * math.pi / points
        x = outer_r + radius * math.cos(angle)
        y = outer_r + radius * math.sin(angle)
        commands.append(_move(x, y) if index == 0 else _line(x, y))
    commands.append("Z")
    return _path(commands)


def bolt(width: float, height: float) -> str:
    """A lightning bolt, the proportions kept sharp rather than cartoonish."""
    return _path(
        [
            _move(width * 0.58, 0),
            _line(width * 0.06, height * 0.56),
            _line(width * 0.40, height * 0.56),
            _line(width * 0.30, height),
            _line(width * 0.94, height * 0.40),
            _line(width * 0.58, height * 0.40),
            "Z",
        ]
    )


def arrow(width: float, height: float, head: float = 0.42, shaft: float = 0.34) -> str:
    """A block arrow pointing right."""
    head_x = width * (1.0 - head)
    top = height * (0.5 - shaft / 2)
    bottom = height * (0.5 + shaft / 2)
    return _path(
        [
            _move(0, top),
            _line(head_x, top),
            _line(head_x, 0),
            _line(width, height / 2),
            _line(head_x, height),
            _line(head_x, bottom),
            _line(0, bottom),
            "Z",
        ]
    )


def cross(size: float, arm: float = 0.32) -> str:
    """An equal-armed cross."""
    thickness = size * arm
    low = (size - thickness) / 2
    high = low + thickness
    return _path(
        [
            _move(low, 0),
            _line(high, 0),
            _line(high, low),
            _line(size, low),
            _line(size, high),
            _line(high, high),
            _line(high, size),
            _line(low, size),
            _line(low, high),
            _line(0, high),
            _line(0, low),
            _line(low, low),
            "Z",
        ]
    )


def burst(diameter: float, spikes: int = 12, inner: float = 0.62) -> str:
    """A sunburst or explosion -- many shallow points rather than a few deep."""
    return star(diameter, points=spikes, inner=inner)


def chevron(width: float, height: float, thickness: float = 0.34) -> str:
    """A single rank chevron, pointing up."""
    t = height * thickness
    return _path(
        [
            _move(0, height),
            _line(width / 2, 0),
            _line(width, height),
            _line(width - t * 0.9, height),
            _line(width / 2, t * 1.1),
            _line(t * 0.9, height),
            "Z",
        ]
    )


# --- Ornaments --------------------------------------------------------------


def divider(width: float, height: float, taper: float = 0.5) -> str:
    """A rule that thins towards both ends -- a printers' divider."""
    middle = height / 2
    thin = height * (1.0 - taper) / 2
    return _path(
        [
            _move(0, middle),
            _line(width * 0.12, middle - (middle - thin)),
            _line(width * 0.88, middle - (middle - thin)),
            _line(width, middle),
            _line(width * 0.88, middle + (middle - thin)),
            _line(width * 0.12, middle + (middle - thin)),
            "Z",
        ]
    )


def corner_mark(size: float, weight: float = 0.18) -> str:
    """An L for a corner. Four of these frame a composition without a box."""
    t = size * weight
    return _path(
        [
            _move(0, 0),
            _line(size, 0),
            _line(size, t),
            _line(t, t),
            _line(t, size),
            _line(0, size),
            "Z",
        ]
    )


def bracket(width: float, height: float, weight: float = 0.16) -> str:
    """A square bracket, opening right."""
    t = width * weight
    return _path(
        [
            _move(0, 0),
            _line(width, 0),
            _line(width, t),
            _line(t, t),
            _line(t, height - t),
            _line(width, height - t),
            _line(width, height),
            _line(0, height),
            "Z",
        ]
    )


# --- Treatments -------------------------------------------------------------


def distress(
    path_width: float,
    path_height: float,
    generator: random.Random,
    density: float = 0.35,
    grain: float = 1.4,
) -> list[str]:
    """Speckle geometry for a worn print, as knock-out dots.

    Returned as separate paths so the caller decides whether they are drilled
    out of the ink or overlaid. Positions come from the supplied generator and
    nowhere else, so the same seed distresses the same way every time -- a
    reprint has to match the original, and "roughly similar" is not a match.
    """
    count = int(path_width * path_height * density / 60.0)
    marks: list[str] = []
    for _ in range(max(count, 0)):
        x = generator.random() * path_width
        y = generator.random() * path_height
        r = grain * (0.4 + generator.random() * 0.8)
        marks.append(
            _path(
                [
                    _move(x - r, y),
                    _arc(r, r, 1, 1, x + r, y),
                    _arc(r, r, 1, 1, x - r, y),
                    "Z",
                ]
            )
        )
    return marks


def halftone(
    width: float, height: float, pitch: float = 2.2, radius_ratio: float = 0.34
) -> list[str]:
    """A regular dot screen. Deterministic by construction -- no generator."""
    dots: list[str] = []
    r = pitch * radius_ratio
    rows = int(height / pitch)
    columns = int(width / pitch)
    for row in range(rows + 1):
        for column in range(columns + 1):
            # Offset alternate rows, which is what makes it read as a screen
            # rather than as a grid.
            x = column * pitch + (pitch / 2 if row % 2 else 0)
            y = row * pitch
            if x > width or y > height:
                continue
            dots.append(
                _path(
                    [
                        _move(x - r, y),
                        _arc(r, r, 1, 1, x + r, y),
                        _arc(r, r, 1, 1, x - r, y),
                        "Z",
                    ]
                )
            )
    return dots


def wobble(value: float, generator: random.Random, amount: float) -> float:
    """Nudge one coordinate, from an explicitly supplied generator."""
    return value + jitter(generator, amount)
