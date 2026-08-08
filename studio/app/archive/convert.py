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


TRANSFORM = re.compile(r"(translate|scale|matrix)\s*\(([^)]*)\)", re.I)
GROUP_OPEN = re.compile(r"<g\b([^>]*)>", re.I | re.S)
GROUP_CLOSE = re.compile(r"</g\s*>", re.I)


def _matrix_of(raw: str) -> tuple[float, float, float, float, float, float]:
    """One transform attribute as a 2x3 matrix, applied left to right."""
    result = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    for kind, body in TRANSFORM.findall(raw):
        values = [float(v) for v in NUMBER.findall(body)]
        if kind.lower() == "translate":
            step = (1.0, 0.0, 0.0, 1.0, values[0], values[1] if len(values) > 1 else 0.0)
        elif kind.lower() == "scale":
            sx = values[0] if values else 1.0
            sy = values[1] if len(values) > 1 else sx
            step = (sx, 0.0, 0.0, sy, 0.0, 0.0)
        elif len(values) >= 6:
            step = (values[0], values[1], values[2], values[3], values[4], values[5])
        else:
            continue
        result = _compose(result, step)
    return result


def _compose(
    outer: tuple[float, float, float, float, float, float],
    inner: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float]:
    a1, b1, c1, d1, e1, f1 = outer
    a2, b2, c2, d2, e2, f2 = inner
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def _apply(path_data: str, matrix: tuple[float, float, float, float, float, float]) -> str:
    """Bake a matrix into path coordinates.

    Done rather than emitting a nested transform, because a transform is a
    promise that whatever opens the file will apply it the same way, and
    flattening it here means the geometry is the geometry.
    """
    a, b, c, d, e, f = matrix
    if (a, b, c, d, e, f) == (1.0, 0.0, 0.0, 1.0, 0.0, 0.0):
        return path_data

    def point(x: float, y: float) -> tuple[str, str]:
        return num(a * x + c * y + e), num(b * x + d * y + f)

    scale = max(abs(a), abs(d)) or 1.0
    out: list[str] = []
    tokens = path_data.replace(",", " ").split()
    index = 0
    while index < len(tokens):
        token = tokens[index]
        upper = token.upper()
        if upper in ("M", "L", "T"):
            out.append(token)
            out.extend(point(float(tokens[index + 1]), float(tokens[index + 2])))
            index += 3
        elif upper == "C":
            out.append(token)
            for step in range(3):
                out.extend(
                    point(float(tokens[index + 1 + step * 2]), float(tokens[index + 2 + step * 2]))
                )
            index += 7
        elif upper in ("S", "Q"):
            out.append(token)
            for step in range(2):
                out.extend(
                    point(float(tokens[index + 1 + step * 2]), float(tokens[index + 2 + step * 2]))
                )
            index += 5
        elif upper == "A":
            out.append(token)
            out.append(num(float(tokens[index + 1]) * scale))
            out.append(num(float(tokens[index + 2]) * scale))
            out.extend(tokens[index + 3 : index + 6])
            out.extend(point(float(tokens[index + 6]), float(tokens[index + 7])))
            index += 8
        elif upper in ("H", "V"):
            # Rewritten as a line, since a horizontal move stops being horizontal
            # under a matrix that rotates or shears.
            out.append(token)
            out.append(num(float(tokens[index + 1]) * scale))
            index += 2
        else:
            out.append(token)
            index += 1
    return " ".join(out)


def shapes_in(svg: str) -> list[Shape]:
    """Every drawn thing in the file, as paths, with the colours they arrived in.

    Group transforms are resolved and baked into the coordinates. Ignoring them
    puts every transformed shape at the wrong place, which is silent and looks
    like a placement bug rather than a parsing one.

    Order is preserved, because in SVG that is stacking order and stacking order
    is part of the drawing.
    """
    # Where each group opens and closes, so a shape knows its inherited matrix.
    stack: list[tuple[int, tuple[float, float, float, float, float, float]]] = []
    boundaries: list[tuple[int, int, tuple[float, float, float, float, float, float]]] = []
    events = sorted(
        [(m.start(), "open", m.group(1)) for m in GROUP_OPEN.finditer(svg)]
        + [(m.start(), "close", "") for m in GROUP_CLOSE.finditer(svg)]
    )
    for position, kind, attributes in events:
        if kind == "open":
            inherited = stack[-1][1] if stack else (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
            transform = re.search(r'transform="([^"]*)"', attributes)
            matrix = _compose(inherited, _matrix_of(transform.group(1))) if transform else inherited
            stack.append((position, matrix))
        elif stack:
            start, matrix = stack.pop()
            boundaries.append((start, position, matrix))

    def matrix_at(position: int) -> tuple[float, float, float, float, float, float]:
        best = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        span = None
        for start, end, matrix in boundaries:
            if start < position < end and (span is None or end - start < span):
                span, best = end - start, matrix
        return best

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
            found.append(Shape(path=_apply(data, matrix_at(match.start())), fill=fill))
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
