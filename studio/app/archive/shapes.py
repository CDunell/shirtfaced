"""The second wave of shapes: the ones with attitude.

`geometry.py` holds the plain forms a design can always fall back on -- a
rectangle, a circle, a star. These are the shapes that say something before a
word is added. A ribbon says award. A gear says workshop. A southern cross says
where this is from and needs no explaining here.

Everything returns SVG path data in millimetres inside a box whose top-left is
the origin, same as the plain shapes, so the grammar can use them
interchangeably.

Composite shapes -- a sun, a palm, five stars in a constellation -- are returned
as one path with several subpaths rather than as a group. On press that is one
object in one ink, which is what it needs to be.
"""

from __future__ import annotations

import math

from app.archive.geometry import _arc, _curve, _line, _move, _path, star
from app.archive.svg import num


def translate(path_data: str, dx: float, dy: float) -> str:
    """Shift a path by rewriting its numbers.

    Done by rewriting rather than with an SVG transform so a composite shape
    stays a single path. A transform would work on screen and then arrive at the
    separator as a nested group, which is exactly the kind of thing that gets
    flattened wrongly by somebody else's software.
    """
    out: list[str] = []
    tokens = path_data.split()
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in ("M", "L"):
            out.append(token)
            out.append(num(float(tokens[index + 1]) + dx))
            out.append(num(float(tokens[index + 2]) + dy))
            index += 3
        elif token == "C":
            out.append(token)
            for step in range(3):
                out.append(num(float(tokens[index + 1 + step * 2]) + dx))
                out.append(num(float(tokens[index + 2 + step * 2]) + dy))
            index += 7
        elif token == "A":
            out.extend(tokens[index : index + 6])
            out.append(num(float(tokens[index + 6]) + dx))
            out.append(num(float(tokens[index + 7]) + dy))
            index += 8
        else:
            out.append(token)
            index += 1
    return " ".join(out)


# --- Frames with an opinion --------------------------------------------------


def ribbon(width: float, height: float, tail: float = 0.16) -> str:
    """A banner with a V cut into both ends. One notch is a bone, not a banner."""
    notch = width * tail
    return _path(
        [
            _move(0, 0),
            _line(width, 0),
            _line(width - notch, height / 2),
            _line(width, height),
            _line(0, height),
            _line(notch, height / 2),
            "Z",
        ]
    )


def diamond(width: float, height: float) -> str:
    return _path(
        [
            _move(width / 2, 0),
            _line(width, height / 2),
            _line(width / 2, height),
            _line(0, height / 2),
            "Z",
        ]
    )


def polygon(diameter: float, sides: int = 6, rotation: float = 0.0) -> str:
    """A regular polygon: hexagon, octagon, triangle, whatever the count says."""
    radius = diameter / 2
    commands: list[str] = []
    for index in range(sides):
        angle = -math.pi / 2 + rotation + index * 2 * math.pi / sides
        x = radius + radius * math.cos(angle)
        y = radius + radius * math.sin(angle)
        commands.append(_move(x, y) if index == 0 else _line(x, y))
    commands.append("Z")
    return _path(commands)


def gear(diameter: float, teeth: int = 12, depth: float = 0.14) -> str:
    """A cog. Workshop, garage, trade -- and a good frame for a small mark."""
    outer = diameter / 2
    inner = outer * (1 - depth)
    commands: list[str] = []
    for index in range(teeth * 2):
        radius = outer if index % 2 == 0 else inner
        angle = index * math.pi / teeth
        x = outer + radius * math.cos(angle)
        y = outer + radius * math.sin(angle)
        commands.append(_move(x, y) if index == 0 else _line(x, y))
    commands.append("Z")
    return _path(commands)


def rope_roundel(diameter: float, knots: int = 22) -> str:
    """A circle whose edge is scalloped, which reads as rope at any size."""
    radius = diameter / 2
    bump = radius * 0.06
    commands: list[str] = []
    for index in range(knots * 2):
        this_radius = radius if index % 2 == 0 else radius - bump
        angle = index * math.pi / knots
        x = radius + this_radius * math.cos(angle)
        y = radius + this_radius * math.sin(angle)
        commands.append(_move(x, y) if index == 0 else _line(x, y))
    commands.append("Z")
    return _path(commands)


# --- Marks -------------------------------------------------------------------


def southern_cross(width: float, height: float) -> str:
    """Five stars in the arrangement everyone here can draw from memory.

    Four seven-pointed and one five-pointed, which is the flag's convention.
    The positions are the constellation's rather than a decorative scatter --
    getting those wrong is noticed instantly and by everyone.
    """
    stars = (
        (0.50, 0.90, 0.20, 7),
        (0.13, 0.50, 0.19, 7),
        (0.50, 0.10, 0.19, 7),
        (0.85, 0.33, 0.18, 7),
        (0.63, 0.60, 0.11, 5),
    )
    parts: list[str] = []
    for centre_x, centre_y, size, points in stars:
        span = min(width, height) * size
        parts.append(
            translate(
                star(span, points=points, inner=0.42),
                width * centre_x - span / 2,
                height * centre_y - span / 2,
            )
        )
    return " ".join(parts)


def wings(width: float, height: float) -> str:
    """A swept pair with stepped trailing edges, so it reads as feathers.

    The first attempt was two smooth curves and looked like a moustache; what
    makes a wing legible from across a room is the steps, not the sweep. The
    halves meet at the centre so the pair is one continuous mark.
    """
    parts: list[str] = []
    centre = width / 2
    for sign in (1.0, -1.0):
        commands = [
            _move(centre, height * 0.26),
            _curve(
                centre + sign * width * 0.16,
                height * 0.14,
                centre + sign * width * 0.34,
                height * 0.14,
                centre + sign * width * 0.48,
                height * 0.22,
            ),
        ]
        for out, down in ((0.42, 0.36), (0.30, 0.46), (0.17, 0.54)):
            commands.append(_line(centre + sign * width * (out + 0.08), height * down))
            commands.append(_line(centre + sign * width * out, height * (down - 0.07)))
        commands.append(_line(centre, height * 0.44))
        commands.append("Z")
        parts.append(_path(commands))
    return " ".join(parts)


def anchor(width: float, height: float) -> str:
    """One outline: ring, crossbar, shank and flukes.

    Drawn as a single silhouette rather than overlapping pieces, so it does not
    depend on a fill rule to hold together.
    """
    arm = width * 0.06
    centre = width / 2
    return _path(
        [
            _move(centre - arm, height * 0.10),
            _line(centre + arm, height * 0.10),
            _line(centre + arm, height * 0.24),
            _line(width * 0.76, height * 0.24),
            _line(width * 0.76, height * 0.34),
            _line(centre + arm, height * 0.34),
            _line(centre + arm, height * 0.72),
            _line(width * 0.84, height * 0.52),
            _line(width * 0.94, height * 0.66),
            _line(centre, height * 0.98),
            _line(width * 0.06, height * 0.66),
            _line(width * 0.16, height * 0.52),
            _line(centre - arm, height * 0.72),
            _line(centre - arm, height * 0.34),
            _line(width * 0.24, height * 0.34),
            _line(width * 0.24, height * 0.24),
            _line(centre - arm, height * 0.24),
            "Z",
        ]
    )


def flame(width: float, height: float) -> str:
    """A flame: tip leaning one way, body swelling the other.

    Symmetry is what made the first two attempts read as a leaf. A fire is never
    symmetrical, and the lean is the whole tell.
    """
    return _path(
        [
            _move(width * 0.40, height * 0.02),
            # Up the leading edge, kinking back -- the flicker.
            _curve(
                width * 0.52,
                height * 0.20,
                width * 0.46,
                height * 0.30,
                width * 0.58,
                height * 0.38,
            ),
            _curve(
                width * 0.80,
                height * 0.50,
                width * 0.90,
                height * 0.68,
                width * 0.82,
                height * 0.84,
            ),
            _curve(width * 0.74, height * 0.97, width * 0.58, height, width * 0.46, height),
            _curve(width * 0.28, height, width * 0.12, height * 0.88, width * 0.12, height * 0.70),
            _curve(
                width * 0.12,
                height * 0.54,
                width * 0.26,
                height * 0.44,
                width * 0.30,
                height * 0.32,
            ),
            _curve(
                width * 0.33,
                height * 0.22,
                width * 0.32,
                height * 0.10,
                width * 0.40,
                height * 0.02,
            ),
            "Z",
        ]
    )


def wave(width: float, height: float) -> str:
    """A wave with a curl. Without the lip it is only a crescent."""
    return _path(
        [
            _move(0, height * 0.86),
            _curve(
                width * 0.18,
                height * 0.44,
                width * 0.40,
                height * 0.10,
                width * 0.76,
                height * 0.08,
            ),
            _curve(width * 0.94, height * 0.08, width, height * 0.26, width * 0.86, height * 0.40),
            _curve(
                width * 0.90,
                height * 0.22,
                width * 0.78,
                height * 0.20,
                width * 0.68,
                height * 0.28,
            ),
            _curve(
                width * 0.48,
                height * 0.42,
                width * 0.30,
                height * 0.64,
                width * 0.20,
                height * 0.88,
            ),
            "Z",
        ]
    )


def mountains(width: float, height: float, peaks: int = 3) -> str:
    """A range. Outdoor, hiking, and the back of every camp mug."""
    commands = [_move(0, height)]
    span = width / peaks
    for index in range(peaks):
        left = index * span
        commands.append(_line(left + span * 0.5, height * (0.22 if index % 2 else 0.04)))
        commands.append(_line(left + span, height))
    commands.append("Z")
    return _path(commands)


def sun(diameter: float, rays: int = 12) -> str:
    """A disc with rays. Unlike a burst, the middle stays solid."""
    radius = diameter / 2
    core = radius * 0.50
    parts = [
        _path(
            [
                _move(radius - core, radius),
                _arc(core, core, 1, 1, radius + core, radius),
                _arc(core, core, 1, 1, radius - core, radius),
                "Z",
            ]
        )
    ]
    for index in range(rays):
        angle = index * 2 * math.pi / rays
        spread = math.pi / rays * 0.36
        inner = core * 1.20
        parts.append(
            _path(
                [
                    _move(
                        radius + inner * math.cos(angle - spread),
                        radius + inner * math.sin(angle - spread),
                    ),
                    _line(radius + radius * math.cos(angle), radius + radius * math.sin(angle)),
                    _line(
                        radius + inner * math.cos(angle + spread),
                        radius + inner * math.sin(angle + spread),
                    ),
                    "Z",
                ]
            )
        )
    return " ".join(parts)


def droplet(width: float, height: float) -> str:
    """A teardrop: sharp at the top, round at the bottom."""
    return _path(
        [
            _move(width * 0.5, 0),
            _curve(
                width * 0.56,
                height * 0.22,
                width * 0.98,
                height * 0.44,
                width * 0.98,
                height * 0.68,
            ),
            _curve(width * 0.98, height * 0.88, width * 0.78, height, width * 0.5, height),
            _curve(width * 0.22, height, width * 0.02, height * 0.88, width * 0.02, height * 0.68),
            _curve(width * 0.02, height * 0.44, width * 0.44, height * 0.22, width * 0.5, 0),
            "Z",
        ]
    )


def crown(width: float, height: float, points: int = 3) -> str:
    """A crown with a flat band. Reads as a claim or as a joke about one."""
    commands = [_move(0, height), _line(0, height * 0.30)]
    span = width / points
    for index in range(points):
        left = index * span
        commands.append(_line(left + span * 0.5, height * 0.02))
        commands.append(_line(left + span, height * 0.30))
    commands.append(_line(width, height))
    commands.append("Z")
    return _path(commands)


def heart(width: float, height: float) -> str:
    return _path(
        [
            _move(width * 0.5, height),
            _curve(width * 0.06, height * 0.62, 0, height * 0.34, width * 0.16, height * 0.16),
            _curve(width * 0.32, 0, width * 0.5, height * 0.12, width * 0.5, height * 0.26),
            _curve(width * 0.5, height * 0.12, width * 0.68, 0, width * 0.84, height * 0.16),
            _curve(width, height * 0.34, width * 0.94, height * 0.62, width * 0.5, height),
            "Z",
        ]
    )


def stubby(width: float, height: float) -> str:
    """A short-necked bottle, as one outline: cap, neck, shoulder, body."""
    return _path(
        [
            _move(width * 0.38, 0),
            _line(width * 0.62, 0),
            _line(width * 0.62, height * 0.08),
            _line(width * 0.60, height * 0.08),
            _line(width * 0.60, height * 0.24),
            # Shoulder out to the body on both sides.
            _curve(
                width * 0.60,
                height * 0.30,
                width * 0.86,
                height * 0.32,
                width * 0.88,
                height * 0.42,
            ),
            _line(width * 0.88, height * 0.95),
            _curve(width * 0.88, height, width * 0.84, height, width * 0.80, height),
            _line(width * 0.20, height),
            _curve(width * 0.16, height, width * 0.12, height, width * 0.12, height * 0.95),
            _line(width * 0.12, height * 0.42),
            _curve(
                width * 0.14,
                height * 0.32,
                width * 0.40,
                height * 0.30,
                width * 0.40,
                height * 0.24,
            ),
            _line(width * 0.40, height * 0.08),
            _line(width * 0.38, height * 0.08),
            "Z",
        ]
    )


def tinnie(width: float, height: float) -> str:
    """A can: straight sides, chamfered top and bottom."""
    chamfer = height * 0.08
    inset = width * 0.10
    return _path(
        [
            _move(inset, chamfer),
            _line(width * 0.30, 0),
            _line(width * 0.70, 0),
            _line(width - inset, chamfer),
            _line(width - inset, height - chamfer),
            _line(width * 0.70, height),
            _line(width * 0.30, height),
            _line(inset, height - chamfer),
            "Z",
        ]
    )


def boomerang(width: float, height: float) -> str:
    """Two arms at an angle, thicker at the elbow."""
    return _path(
        [
            _move(width * 0.08, height * 0.08),
            _curve(
                width * 0.46,
                height * 0.24,
                width * 0.72,
                height * 0.52,
                width * 0.94,
                height * 0.94,
            ),
            _line(width * 0.70, height * 0.90),
            _curve(
                width * 0.52,
                height * 0.60,
                width * 0.32,
                height * 0.40,
                width * 0.04,
                height * 0.30,
            ),
            "Z",
        ]
    )


def thong(width: float, height: float) -> str:
    """A thong sole, with the toe-post notched into the silhouette.

    Earlier versions drew the strap as a separate shape and relied on a fill
    rule to make it a hole. Cutting the notch into the outline instead means it
    reads the same at any size and in any single ink.
    """
    return _path(
        [
            _move(width * 0.5, height * 0.16),
            # Toe notch: in, down, and back out.
            _line(width * 0.44, height * 0.02),
            _curve(
                width * 0.24,
                height * 0.06,
                width * 0.14,
                height * 0.24,
                width * 0.16,
                height * 0.46,
            ),
            _curve(width * 0.18, height * 0.72, width * 0.28, height, width * 0.5, height),
            _curve(width * 0.72, height, width * 0.82, height * 0.72, width * 0.84, height * 0.46),
            _curve(
                width * 0.86,
                height * 0.24,
                width * 0.76,
                height * 0.06,
                width * 0.56,
                height * 0.02,
            ),
            "Z",
        ]
    )


def spanner(width: float, height: float) -> str:
    """One outline: an open-jawed head running into a straight shaft."""
    shaft = width * 0.16
    centre = width * 0.5
    return _path(
        [
            # Left horn of the jaw.
            _move(width * 0.20, height * 0.02),
            _line(width * 0.34, height * 0.02),
            _line(width * 0.34, height * 0.14),
            _line(width * 0.66, height * 0.14),
            _line(width * 0.66, height * 0.02),
            _line(width * 0.80, height * 0.02),
            # Down the outside of the head, into the shaft.
            _line(width * 0.80, height * 0.26),
            _line(centre + shaft / 2, height * 0.32),
            _line(centre + shaft / 2, height),
            _line(centre - shaft / 2, height),
            _line(centre - shaft / 2, height * 0.32),
            _line(width * 0.20, height * 0.26),
            "Z",
        ]
    )


def palm(width: float, height: float, fronds: int = 6) -> str:
    """A leaning trunk and a crown of fronds."""
    parts = [
        _path(
            [
                _move(width * 0.44, height),
                _curve(
                    width * 0.50,
                    height * 0.66,
                    width * 0.52,
                    height * 0.50,
                    width * 0.50,
                    height * 0.34,
                ),
                _line(width * 0.58, height * 0.34),
                _curve(
                    width * 0.60, height * 0.52, width * 0.58, height * 0.70, width * 0.56, height
                ),
                "Z",
            ]
        )
    ]
    for index in range(fronds):
        angle = math.pi + index * math.pi / max(fronds - 1, 1)
        reach = width * 0.42
        tip_x = width * 0.53 + reach * math.cos(angle)
        tip_y = height * 0.28 + reach * 0.6 * math.sin(angle)
        parts.append(
            _path(
                [
                    _move(width * 0.53, height * 0.30),
                    _curve(
                        (width * 0.53 + tip_x) / 2,
                        height * 0.08,
                        tip_x,
                        tip_y - height * 0.08,
                        tip_x,
                        tip_y,
                    ),
                    _curve(
                        tip_x,
                        tip_y + height * 0.02,
                        (width * 0.53 + tip_x) / 2,
                        height * 0.20,
                        width * 0.53,
                        height * 0.36,
                    ),
                    "Z",
                ]
            )
        )
    return " ".join(parts)


def sparkle(size: float) -> str:
    """A four-point glint with concave sides. Not a star -- a shine."""
    half = size / 2
    waist = size * 0.09
    return _path(
        [
            _move(half, 0),
            _curve(half + waist, half - waist, half + waist, half - waist, size, half),
            _curve(half + waist, half + waist, half + waist, half + waist, half, size),
            _curve(half - waist, half + waist, half - waist, half + waist, 0, half),
            _curve(half - waist, half - waist, half - waist, half - waist, half, 0),
            "Z",
        ]
    )


def zigzag(width: float, height: float, teeth: int = 6) -> str:
    """A jagged rule. Danger, or the border on a jumper."""
    span = width / teeth
    commands = [_move(0, height * 0.62)]
    for index in range(teeth):
        commands.append(_line(index * span + span * 0.5, height * 0.10))
        commands.append(_line((index + 1) * span, height * 0.62))
    commands.append(_line(width, height))
    for index in range(teeth, 0, -1):
        commands.append(_line(index * span - span * 0.5, height * 0.48))
        commands.append(_line((index - 1) * span, height))
    commands.append("Z")
    return _path(commands)


def dots_row(width: float, height: float, count: int = 5) -> str:
    """A row of dots. The quietest divider there is."""
    radius = height / 2
    step = width / max(count, 1)
    parts: list[str] = []
    for index in range(count):
        cx = step * (index + 0.5)
        parts.append(
            _path(
                [
                    _move(cx - radius, radius),
                    _arc(radius, radius, 1, 1, cx + radius, radius),
                    _arc(radius, radius, 1, 1, cx - radius, radius),
                    "Z",
                ]
            )
        )
    return " ".join(parts)
