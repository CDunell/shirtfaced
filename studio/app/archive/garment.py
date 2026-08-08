"""Reading a garment file, and putting a design into one of its zones.

A garment SVG carries an outline and a set of named print zones in real
millimetres. The composer produces designs in real millimetres. This is what
joins them: it reads the zones, works out where a design of a given size sits
inside one, and returns the whole thing as a single document.

The zone is the authority on position. A design is centred horizontally in its
zone and sits at the top of it, because that is where prints go -- a chest print
hangs from its top edge, it does not float in the middle of a rectangle.

Nothing here rescales the garment. Both sides are already in millimetres, which
is the point of having insisted on that.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.archive.svg import num

PATH_TAG = re.compile(r"<path\b([^>]*?)/?>", re.I | re.S)
ATTRIBUTE = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"', re.S)
VIEWBOX = re.compile(r'viewBox="\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([-\d.]+)[\s,]+([-\d.]+)"')
NUMBER = re.compile(r"-?\d*\.?\d+")

# Zones split per side carry a suffix; the engine's placement is the base name.
SIDE_SUFFIXES = ("_left", "_right")


class GarmentError(Exception):
    """The garment file cannot be used, with a durable reason code."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Zone:
    """A named print area, in millimetres, in the garment's own coordinates."""

    key: str
    left: float
    top: float
    width: float
    height: float

    @property
    def base_key(self) -> str:
        for suffix in SIDE_SUFFIXES:
            if self.key.endswith(suffix):
                return self.key[: -len(suffix)]
        return self.key

    @property
    def centre_x(self) -> float:
        return self.left + self.width / 2


@dataclass(frozen=True)
class Garment:
    """One garment: its drawing, its size, and where things may be printed."""

    name: str
    width_mm: float
    height_mm: float
    # The structural paths, in document order, with their fills.
    structure: tuple[tuple[str, str], ...]
    zones: dict[str, Zone]

    def zone(self, key: str) -> Zone:
        if key in self.zones:
            return self.zones[key]
        # A brief asking for "short_sleeve" on a garment that splits per side
        # gets the wearer's left, which is the side a single sleeve print goes.
        for suffix in SIDE_SUFFIXES:
            if key + suffix in self.zones:
                return self.zones[key + suffix]
        raise GarmentError("NO_SUCH_ZONE", f"{self.name} has no zone {key!r}")


def _bounds(path_data: str) -> tuple[float, float, float, float]:
    values = [float(v) for v in NUMBER.findall(path_data)]
    xs, ys = values[0::2], values[1::2]
    if not xs or not ys:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(xs), min(ys), max(xs), max(ys))


def load(file: Path) -> Garment:
    """Read a garment file. Never guesses at a missing viewBox or outline."""
    try:
        svg = file.read_text(encoding="utf-8")
    except OSError as error:
        raise GarmentError("UNREADABLE_FILE", str(error)) from error

    box = VIEWBOX.search(svg)
    if not box:
        raise GarmentError(
            "NO_VIEWBOX", "millimetres cannot be read without one, and everything here is mm"
        )
    width_mm, height_mm = float(box.group(3)), float(box.group(4))

    structure: list[tuple[str, str]] = []
    zones: dict[str, Zone] = {}

    for match in PATH_TAG.finditer(svg):
        attributes = dict(ATTRIBUTE.findall(match.group(1)))
        identifier = attributes.get("id", "")
        data = attributes.get("d", "").strip()
        if not data:
            continue

        if identifier.startswith("zone-"):
            key = identifier[5:]
            left, top, right, bottom = _bounds(data)
            zones[key] = Zone(key, left, top, right - left, bottom - top)
        else:
            # Structural. Stroke is kept as a fill hint so the preview reads.
            fill = attributes.get("fill", "").strip()
            structure.append((data, fill or "none"))

    if not structure:
        raise GarmentError("NO_OUTLINE", "nothing to place a design against")

    return Garment(
        name=file.stem,
        width_mm=width_mm,
        height_mm=height_mm,
        structure=tuple(structure),
        zones=zones,
    )


def place(
    garment: Garment,
    zone_key: str,
    design_svg: str,
    design_width_mm: float,
    design_height_mm: float,
    garment_colour: str = "#1A1A1A",
    show_zones: bool = False,
) -> str:
    """Put a design into a zone and return the whole garment as one document.

    The design is centred across the zone and hung from its top edge. A chest
    print hangs from the top; it does not float in the middle of a rectangle.

    Raises rather than shrinking to fit. A design too big for a zone is a
    composition problem, and silently scaling it would hide the fact that the
    print will not be the size it was designed at.
    """
    zone = garment.zone(zone_key)

    if design_width_mm > zone.width + 0.5 or design_height_mm > zone.height + 0.5:
        raise GarmentError(
            "DESIGN_EXCEEDS_ZONE",
            f"{design_width_mm:.0f}x{design_height_mm:.0f}mm will not fit "
            f"{zone.key} at {zone.width:.0f}x{zone.height:.0f}mm",
        )

    x = zone.centre_x - design_width_mm / 2
    y = zone.top

    body: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{num(garment.width_mm)}mm" height="{num(garment.height_mm)}mm" '
        f'viewBox="0 0 {num(garment.width_mm)} {num(garment.height_mm)}">'
    ]
    for data, fill in garment.structure:
        colour = garment_colour if fill not in ("none", "") else "none"
        stroke = "#3A3A3A" if colour == "none" else garment_colour
        body.append(f'<path d="{data}" fill="{colour}" stroke="{stroke}" stroke-width="1"/>')

    if show_zones:
        for zoned in garment.zones.values():
            body.append(
                f'<rect x="{num(zoned.left)}" y="{num(zoned.top)}" '
                f'width="{num(zoned.width)}" height="{num(zoned.height)}" '
                f'fill="none" stroke="#3D5A2A" stroke-width="0.8" stroke-dasharray="4 3"/>'
            )

    # The design arrives as its own document; its contents are lifted out and
    # translated into place rather than nested, so the result is one drawing.
    inner = design_svg.split(">", 1)[1].rsplit("</svg>", 1)[0]
    body.append(f'<g transform="translate({num(x)} {num(y)})">{inner}</g>')
    body.append("</svg>")
    return "".join(body)
