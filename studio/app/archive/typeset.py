"""Setting supplied words as vector outlines.

Text in the output is never a `<text>` element naming a font. It is glyph
outlines, for two reasons that both matter:

*Print.* A separator, a trapper and an RIP all want paths. A font reference
means the file only renders correctly where that font is installed, which is
exactly the failure that produces a reprint set in Arial.

*Determinism.* A `<text>` element defers layout to whatever renders it, so the
same file is a different design on a different machine. Outlines settle it here,
once, from a vendored font file whose metrics are pinned.

The word itself is always supplied by the owner. Nothing in this module invents,
shortens or judges text; it decides how the given words are set, which is the
only question the engine is allowed to answer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from app.archive.svg import num

REPO_ROOT = Path(__file__).resolve().parents[3]

# Vendored, and versioned with the repository. A font update changes metrics and
# therefore every composition ever produced, so the file is part of the archive
# rather than part of the machine.
FONT_FILES = {
    "shirtfaced": REPO_ROOT / "assets" / "type" / "Shirtfaced-Regular.ttf",
}


class MissingGlyph(Exception):
    """A supplied character the chosen face cannot set.

    Raised rather than silently dropped. A missing glyph in a display face is
    how "BRIEF:" became "BRIEF[]" on screen; on a garment it would be a printed
    run of the wrong word.
    """


@dataclass(frozen=True)
class SetText:
    """Words, set: one SVG path plus the box it occupies."""

    path: str
    width: float
    height: float
    # Distance from the text's own top to its baseline, for stacking.
    ascent: float


@lru_cache(maxsize=8)
def _font(face: str) -> TTFont:
    path = FONT_FILES.get(face)
    if path is None or not path.is_file():
        raise FileNotFoundError(f"no vendored font file for face {face!r}")
    return TTFont(str(path))


@lru_cache(maxsize=8)
def _metrics(face: str) -> tuple[float, dict[str, float], object]:
    font = _font(face)
    units = float(font["head"].unitsPerEm)
    glyph_set = font.getGlyphSet()
    widths = {name: float(font["hmtx"][name][0]) for name in font.getGlyphOrder()}
    return units, widths, glyph_set


@lru_cache(maxsize=4)
def _cmap(face: str) -> dict[int, str]:
    return dict(_font(face).getBestCmap())


def _glyph_names(face: str, text: str) -> list[str]:
    cmap = _cmap(face)
    names = []
    for character in text:
        if character == " ":
            names.append(" ")
            continue
        name = cmap.get(ord(character))
        if name is None:
            raise MissingGlyph(f"face {face!r} has no glyph for {character!r} in {text!r}")
        names.append(name)
    return names


def set_line(
    text: str,
    face: str = "shirtfaced",
    cap_height: float = 10.0,
    tracking: float = 0.0,
) -> SetText:
    """One straight line of text as outlines.

    `cap_height` is the height the capitals should occupy in millimetres, which
    is how a printer talks about type on a garment. `tracking` is a share of
    that height, so it scales with the type rather than being a fixed gap.
    """
    units, widths, glyph_set = _metrics(face)
    scale = cap_height / units
    track = tracking * cap_height

    segments: list[str] = []
    cursor = 0.0
    for name in _glyph_names(face, text):
        if name == " ":
            cursor += units * scale * 0.28 + track
            continue
        pen = SVGPathPen(glyph_set, ntos=num)
        # Y is negated because font space rises and SVG space falls.
        transform = TransformPen(pen, (scale, 0, 0, -scale, cursor, 0))
        glyph_set[name].draw(transform)
        commands = pen.getCommands()
        if commands:
            segments.append(commands)
        cursor += widths[name] * scale + track

    height = cap_height
    return SetText(
        path=" ".join(segments),
        width=max(cursor - track, 0.0),
        height=height,
        ascent=height,
    )


def set_arc(
    text: str,
    radius: float,
    face: str = "shirtfaced",
    cap_height: float = 10.0,
    tracking: float = 0.0,
    upper: bool = True,
) -> SetText:
    """Text on a circular arc -- the collegiate arch.

    Each glyph is rotated about the arc centre by its own accumulated width, so
    letters sit on the curve rather than being sheared onto it. The arc is
    centred on vertical, so the composition is symmetrical without the caller
    computing angles.
    """
    units, widths, glyph_set = _metrics(face)
    scale = cap_height / units
    track = tracking * cap_height

    names = _glyph_names(face, text)
    advances = [
        (units * scale * 0.28 if name == " " else widths[name] * scale) + track
        for name in names
    ]
    total = max(sum(advances) - track, 1e-6)

    # Arc length to angle. The whole word is centred on twelve o'clock.
    sweep = total / radius
    angle = -sweep / 2.0

    segments: list[str] = []
    for name, advance in zip(names, advances):
        centre_angle = angle + (advance - track) / (2.0 * radius)
        if name != " ":
            if upper:
                x = radius * math.sin(centre_angle)
                y = -radius * math.cos(centre_angle)
                rotation = centre_angle
            else:
                x = radius * math.sin(-centre_angle)
                y = radius * math.cos(centre_angle)
                rotation = -centre_angle
            cosine = math.cos(rotation)
            sine = math.sin(rotation)
            # Rotate, then place, then flip the font's rising Y.
            transform = (
                scale * cosine,
                scale * sine,
                scale * sine,
                -scale * cosine,
                x - (advance - track) / 2.0 * cosine,
                y - (advance - track) / 2.0 * sine,
            )
            pen = SVGPathPen(glyph_set, ntos=num)
            glyph_set[name].draw(TransformPen(pen, transform))
            commands = pen.getCommands()
            if commands:
                segments.append(commands)
        angle += advance / radius

    half = math.sin(sweep / 2.0) * radius
    return SetText(
        path=" ".join(segments),
        width=max(half * 2.0, 0.0),
        height=cap_height + radius * (1.0 - math.cos(sweep / 2.0)),
        ascent=cap_height,
    )
