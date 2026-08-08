"""Turning whatever arrives into geometry the engine can use.

Written because the alternative was refusing files. Ingestion used to reject
anything drawn with `<rect>`, `<circle>` or `<polygon>` and tell whoever sent it
to convert the shapes first -- which is asking someone else to do work that
belongs here, and turning away material in the meantime.

Every SVG primitive becomes a path. Colour is read rather than discarded: the
engine assigns its own inks, but the source's palette is information about the
artwork and destroying it at the door means it can never be looked at again.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from app.archive.svg import num

# Attribute readers. Deliberately tolerant -- exporters vary, and a missing
# attribute should mean a default rather than a rejected file.
ATTRIBUTE = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"')
TAG = re.compile(r"<(path|rect|circle|ellipse|polygon|polyline|line)\b([^>]*)>", re.I | re.S)
NUMBER = re.compile(r"-?\d*\.?\d+(?:e-?\d+)?", re.I)
STYLE_FILL = re.compile(r"fill\s*:\s*([^;]+)", re.I)


@dataclass(frozen=True)
class Shape:
    """One drawn thing: its geometry, and the colour it arrived in."""

    path: str
    fill: str = ""


def _attributes(raw: str) -> dict[str, str]:
    found = {key.lower(): value.strip() for key, value in ATTRIBUTE.findall(raw)}
    # A fill in a style attribute is the same fact written differently.
    style = found.get("style", "")
    if "fill" not in found and style:
        match = STYLE_FILL.search(style)
        if match:
            found["fill"] = match.group(1).strip()
    return found


def _number(attributes: dict[str, str], key: str, default: float = 0.0) -> float:
    raw = attributes.get(key, "")
    match = NUMBER.search(raw)
    return float(match.group()) if match else default


def _points(raw: str) -> list[tuple[float, float]]:
    values = [float(value) for value in NUMBER.findall(raw)]
    return [(values[index], values[index + 1]) for index in range(0, len(values) - 1, 2)]


def _rect(a: dict[str, str]) -> str:
    x, y = _number(a, "x"), _number(a, "y")
    width, height = _number(a, "width"), _number(a, "height")
    rx = _number(a, "rx", _number(a, "ry"))
    ry = _number(a, "ry", rx)
    if rx <= 0 or ry <= 0:
        return (
            f"M {num(x)} {num(y)} L {num(x + width)} {num(y)} "
            f"L {num(x + width)} {num(y + height)} L {num(x)} {num(y + height)} Z"
        )
    rx, ry = min(rx, width / 2), min(ry, height / 2)
    return (
        f"M {num(x + rx)} {num(y)} L {num(x + width - rx)} {num(y)} "
        f"A {num(rx)} {num(ry)} 0 0 1 {num(x + width)} {num(y + ry)} "
        f"L {num(x + width)} {num(y + height - ry)} "
        f"A {num(rx)} {num(ry)} 0 0 1 {num(x + width - rx)} {num(y + height)} "
        f"L {num(x + rx)} {num(y + height)} "
        f"A {num(rx)} {num(ry)} 0 0 1 {num(x)} {num(y + height - ry)} "
        f"L {num(x)} {num(y + ry)} "
        f"A {num(rx)} {num(ry)} 0 0 1 {num(x + rx)} {num(y)} Z"
    )


def _ellipse(cx: float, cy: float, rx: float, ry: float) -> str:
    return (
        f"M {num(cx - rx)} {num(cy)} "
        f"A {num(rx)} {num(ry)} 0 1 1 {num(cx + rx)} {num(cy)} "
        f"A {num(rx)} {num(ry)} 0 1 1 {num(cx - rx)} {num(cy)} Z"
    )


def _polygon(raw: str, close: bool) -> str:
    points = _points(raw)
    if len(points) < 2:
        return ""
    body = " ".join(f"L {num(x)} {num(y)}" for x, y in points[1:])
    head = f"M {num(points[0][0])} {num(points[0][1])}"
    return f"{head} {body}" + (" Z" if close else "")


def shapes_in(svg: str) -> list[Shape]:
    """Every drawn thing in the file, as paths, with the colours they arrived in.

    Order is preserved, because in SVG that is stacking order and stacking order
    is part of the drawing.
    """
    found: list[Shape] = []
    for match in TAG.finditer(svg):
        tag = match.group(1).lower()
        attributes = _attributes(match.group(2))
        fill = attributes.get("fill", "").strip()

        if tag == "path":
            data = attributes.get("d", "").strip()
        elif tag == "rect":
            data = _rect(attributes)
        elif tag == "circle":
            radius = _number(attributes, "r")
            data = _ellipse(_number(attributes, "cx"), _number(attributes, "cy"), radius, radius)
        elif tag == "ellipse":
            data = _ellipse(
                _number(attributes, "cx"),
                _number(attributes, "cy"),
                _number(attributes, "rx"),
                _number(attributes, "ry"),
            )
        elif tag == "polygon":
            data = _polygon(attributes.get("points", ""), close=True)
        elif tag == "polyline":
            data = _polygon(attributes.get("points", ""), close=False)
        elif tag == "line":
            data = (
                f"M {num(_number(attributes, 'x1'))} {num(_number(attributes, 'y1'))} "
                f"L {num(_number(attributes, 'x2'))} {num(_number(attributes, 'y2'))}"
            )
        else:
            data = ""

        if data:
            found.append(Shape(path=data, fill=fill))
    return found


def colours_in(shapes: list[Shape]) -> tuple[str, ...]:
    """The palette the artwork arrived in, in the order it was drawn.

    Kept because it is information about the piece. The engine assigns its own
    inks, but how many colours the original used, and which, is the sort of
    thing that is impossible to recover once thrown away.
    """
    seen: list[str] = []
    for shape in shapes:
        colour = shape.fill.lower()
        if colour and colour not in ("none", "transparent") and colour not in seen:
            seen.append(colour)
    return tuple(seen)


def combined_path(shapes: list[Shape]) -> str:
    """All the geometry as one path, for single-ink use."""
    return " ".join(shape.path for shape in shapes if shape.path)


def has_raster(svg: str) -> bool:
    """Whether the file leans on an embedded bitmap.

    Recorded rather than refused. A file can carry both, and the vector part is
    still worth having.
    """
    return bool(re.search(r"<image\b", svg, re.I))


def scale_to_box(path_data: str, source: tuple[float, float], target: float) -> str:
    """Rescale a path so its longest side is `target`.

    Source artwork arrives in whatever units its author used. Normalising here
    means the archive does not have to care.
    """
    width, height = source
    longest = max(width, height, 1e-6)
    factor = target / longest
    if math.isclose(factor, 1.0):
        return path_data

    out: list[str] = []
    tokens = path_data.split()
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in ("M", "L"):
            out.append(token)
            out.extend(num(float(tokens[index + step]) * factor) for step in (1, 2))
            index += 3
        elif token in ("C",):
            out.append(token)
            out.extend(num(float(tokens[index + step]) * factor) for step in range(1, 7))
            index += 7
        elif token == "Q":
            out.append(token)
            out.extend(num(float(tokens[index + step]) * factor) for step in range(1, 5))
            index += 5
        elif token == "A":
            out.append(token)
            out.append(num(float(tokens[index + 1]) * factor))
            out.append(num(float(tokens[index + 2]) * factor))
            out.extend(tokens[index + 3 : index + 6])
            out.append(num(float(tokens[index + 6]) * factor))
            out.append(num(float(tokens[index + 7]) * factor))
            index += 8
        else:
            out.append(token)
            index += 1
    return " ".join(out)
