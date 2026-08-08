"""Check a garment SVG against the engine before it joins the library.

Garment files carry the print zones the composer places designs into, so a zone
that is the wrong size or on the wrong side of the body is not a cosmetic
problem -- every design placed there inherits it.

What it checks:

* Zone ids resolve to placements the engine knows. A typo makes a zone
  invisible rather than wrong, which is harder to notice.
* Zone dimensions against the defaults in placements.py, reported as notes
  rather than failures. Those defaults describe a standard adult tee; an
  oversized cut genuinely has more printable area, and the engine sizes a
  design to the garment's own zone. A larger zone means larger prints, not
  broken ones.
* Which side of the body a chest zone sits on. In a front view the wearer's
  left is the viewer's right, and getting that backwards mirrors every
  left-chest print the garment ever carries.
* Body proportions against the flat measurements the file itself declares.

    python scripts/check_garment.py garment_tee_crew_front.svg
    python scripts/check_garment.py garment_tee_crew_front.svg --render out.png

Rendering matters as much as the numbers. Zones can measure correctly and sit
in the wrong place, and a silhouette can be structurally valid and not look
like the garment.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.archive.convert import shapes_in
from app.archive.placements import BY_FIT, placement

ID_TAG = re.compile(r'<path[^>]*\bid="([^"]+)"[^>]*>', re.I | re.S)
NUMBER = re.compile(r"-?\d*\.?\d+")
VIEWBOX = re.compile(r'viewBox="\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([-\d.]+)[\s,]+([-\d.]+)"')

KNOWN_ZONES = {p.key for p in BY_FIT["adult"]}

# A garment has two sleeves and the engine has one sleeve placement, so a file
# may split a zone per side. The suffix says which side; the bounds are the
# placement's.
SIDE_SUFFIXES = ("_left", "_right")


def _base_zone(key: str) -> str:
    for suffix in SIDE_SUFFIXES:
        if key.endswith(suffix) and key[: -len(suffix)] in KNOWN_ZONES:
            return key[: -len(suffix)]
    return key


STRUCTURE_IDS = {
    "garment-outline",
    "garment-collar",
    "garment-seams",
    # Headwear parts. A brim, a peak and a knitted cuff are structure, not
    # print zones, and reporting them as unknown ids is noise.
    "garment-brim",
    "garment-peak",
    "garment-cuff",
    "garment-crown",
}

# How far a zone may exceed the engine's maximum before it is reported. Two
# millimetres is drawing slop; twenty is a different zone.
TOLERANCE_MM = 2.0


def _bounds(path_data: str) -> tuple[float, float, float, float]:
    """Rough bounding box from the path's coordinates.

    Control points are included, so a curve's box can read slightly large. For
    checking a zone against a production maximum that errs the safe way.
    """
    values = [float(v) for v in NUMBER.findall(path_data)]
    xs = values[0::2]
    ys = values[1::2]
    if not xs or not ys:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(xs), min(ys), max(xs), max(ys))


def check(file: Path, render_to: Path | None = None) -> int:
    svg = file.read_text(encoding="utf-8")
    problems: list[str] = []
    notes: list[str] = []

    box = VIEWBOX.search(svg)
    if not box:
        print("no viewBox; cannot read millimetres")
        return 1
    width_mm, height_mm = float(box.group(3)), float(box.group(4))
    print(f"{file.name}\n  canvas {width_mm:.0f} x {height_mm:.0f} mm")

    # Ids present, split into structure and zones.
    ids = ID_TAG.findall(svg)
    zones = {i[5:]: i for i in ids if i.startswith("zone-")}
    structure = {i for i in ids if i in STRUCTURE_IDS}
    unknown = [i for i in ids if not i.startswith("zone-") and i not in STRUCTURE_IDS]

    print(f"  structure: {', '.join(sorted(structure)) or 'none'}")
    if unknown:
        notes.append(f"ids the engine does not read: {', '.join(unknown)}")
    if "garment-outline" not in structure:
        problems.append("no garment-outline; nothing to place a design against")

    # Geometry per id, for measuring.
    geometry: dict[str, str] = {}
    for match in re.finditer(r"<path\b([^>]*)>", svg, re.I | re.S):
        attributes = match.group(1)
        found_id = re.search(r'\bid="([^"]+)"', attributes)
        found_d = re.search(r'\bd="([^"]+)"', attributes, re.S)
        if found_id and found_d:
            geometry[found_id.group(1)] = found_d.group(1)

    outline = geometry.get("garment-outline", "")
    body_left = body_right = None
    if outline:
        x0, y0, x1, y1 = _bounds(outline)
        print(f"  outline  {x1 - x0:.0f} x {y1 - y0:.0f} mm (widest point, sleeves included)")
        # Body width between the side seams, taken from the seam path when present.
        seams = geometry.get("garment-seams", "")
        verticals = re.findall(r"M\s*([\d.]+),(\d+)\s*L\s*\1,", seams)
        if verticals:
            xs = sorted({float(v[0]) for v in verticals})
            if len(xs) >= 2:
                body_left, body_right = xs[0], xs[-1]
                print(f"  body     {body_right - body_left:.0f} mm between side seams")

    print()
    if not zones:
        problems.append("no zone- paths; the engine has nowhere to place a design")

    for key in sorted(zones):
        data = geometry.get(zones[key], "")
        x0, y0, x1, y1 = _bounds(data)
        w, h = x1 - x0, y1 - y0
        line = f"  zone-{key:<18} {w:>5.0f} x {h:<5.0f} mm"

        base = _base_zone(key)
        if base not in KNOWN_ZONES:
            print(line + "   UNKNOWN ID")
            problems.append(f"zone-{key} is not a placement the engine knows")
            continue

        try:
            spec = placement(base)
        except KeyError:
            print(line + "   (no bounds to check)")
            continue

        # Over the standard maximum is a note, not a failure. The table in
        # placements.py describes a standard adult tee; an oversized cut has
        # more printable area, and a garment may reasonably declare a bigger
        # zone than the default. The engine sizes designs to the garment's own
        # zone, so a larger one means larger prints rather than broken ones.
        flags = []
        if w > spec.max_width_mm + TOLERANCE_MM:
            flags.append(
                f"{w - spec.max_width_mm:.0f}mm wider than the {spec.max_width_mm:.0f} default"
            )
        if h > spec.max_height_mm + TOLERANCE_MM:
            flags.append(
                f"{h - spec.max_height_mm:.0f}mm taller than the {spec.max_height_mm:.0f} default"
            )
        print(line + ("   over: " + "; ".join(flags) if flags else "   ok"))
        for flag in flags:
            notes.append(f"zone-{key} {flag}")

        # Chest side. In a front view the wearer's left is the viewer's right.
        if base == "left_chest" and body_left is not None and body_right is not None:
            centre = (body_left + body_right) / 2
            if (x0 + x1) / 2 < centre:
                problems.append(
                    "zone-left_chest sits on the viewer's left. In a front view the "
                    "wearer's left is the viewer's right, so this mirrors every "
                    "left-chest print"
                )

    shapes = shapes_in(svg)
    print(f"\n  ingests as {len(shapes)} shape(s)")

    if notes:
        print("\nNOTES")
        for note in notes:
            print(f"  - {note}")
    if problems:
        print("\nPROBLEMS")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("\nno problems found")
    return 0


def _render(svg: str, width_mm: float, height_mm: float, out: Path) -> None:
    """Outlines only, in each shape's own colour, so zones read against the body."""
    from PIL import Image, ImageDraw

    scale = 900 / max(width_mm, height_mm)
    image = Image.new("RGB", (int(width_mm * scale), int(height_mm * scale)), (20, 20, 22))
    draw = ImageDraw.Draw(image)
    for shape in shapes_in(svg):
        colour = shape.fill if shape.fill and shape.fill.lower() != "none" else "#DDDDDD"
        for polygon in _flatten(shape.path):
            if len(polygon) < 3:
                continue
            draw.polygon([(x * scale, y * scale) for x, y in polygon], outline=colour)
    image.save(out)


def _cubic(p0, c1, c2, p3, steps: int = 20) -> list[tuple[float, float]]:
    out = []
    for step in range(1, steps + 1):
        t = step / steps
        u = 1 - t
        out.append(
            (
                u**3 * p0[0] + 3 * u**2 * t * c1[0] + 3 * u * t**2 * c2[0] + t**3 * p3[0],
                u**3 * p0[1] + 3 * u**2 * t * c1[1] + 3 * u * t**2 * c2[1] + t**3 * p3[1],
            )
        )
    return out


def _quadratic(p0, c, p2, steps: int = 14) -> list[tuple[float, float]]:
    out = []
    for step in range(1, steps + 1):
        t = step / steps
        u = 1 - t
        out.append(
            (
                u * u * p0[0] + 2 * u * t * c[0] + t * t * p2[0],
                u * u * p0[1] + 2 * u * t * c[1] + t * t * p2[1],
            )
        )
    return out


def _elliptical(
    start,
    radius_x,
    radius_y,
    rotation,
    large_arc,
    sweep,
    end,
    steps: int = 24,
) -> list[tuple[float, float]]:
    """The SVG spec's endpoint-to-centre arc conversion.

    The previous version bulged off the chord in one fixed direction and
    ignored the sweep flag entirely, so the standard two-arc circle -- two
    semicircles that must bulge opposite ways -- came out as a lens. Every
    circle in the archive rendered as a rugby ball and the wheels on a
    supplied ute looked like they had merged into the body.

    This tool decides whether files get sent back, so it does the real
    conversion rather than something that looks close on the easy cases.
    """
    import math

    rx, ry = abs(radius_x), abs(radius_y)
    if rx == 0 or ry == 0 or start == end:
        return [end]

    phi = math.radians(rotation)
    cos_phi, sin_phi = math.cos(phi), math.sin(phi)

    dx2 = (start[0] - end[0]) / 2.0
    dy2 = (start[1] - end[1]) / 2.0
    x1 = cos_phi * dx2 + sin_phi * dy2
    y1 = -sin_phi * dx2 + cos_phi * dy2

    # Radii too small to span the chord get scaled up, per the spec, rather
    # than producing a negative under the root below.
    lam = (x1 * x1) / (rx * rx) + (y1 * y1) / (ry * ry)
    if lam > 1:
        scale = math.sqrt(lam)
        rx *= scale
        ry *= scale

    numerator = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
    denominator = rx * rx * y1 * y1 + ry * ry * x1 * x1
    factor = math.sqrt(max(numerator / denominator, 0.0))
    if large_arc == sweep:
        factor = -factor
    cx1 = factor * rx * y1 / ry
    cy1 = -factor * ry * x1 / rx

    cx = cos_phi * cx1 - sin_phi * cy1 + (start[0] + end[0]) / 2.0
    cy = sin_phi * cx1 + cos_phi * cy1 + (start[1] + end[1]) / 2.0

    theta = math.atan2((y1 - cy1) / ry, (x1 - cx1) / rx)
    theta_end = math.atan2((-y1 - cy1) / ry, (-x1 - cx1) / rx)
    delta = theta_end - theta
    if sweep and delta < 0:
        delta += 2 * math.pi
    elif not sweep and delta > 0:
        delta -= 2 * math.pi

    out = []
    for step in range(1, steps + 1):
        angle = theta + delta * step / steps
        px = rx * math.cos(angle)
        py = ry * math.sin(angle)
        out.append((cos_phi * px - sin_phi * py + cx, sin_phi * px + cos_phi * py + cy))
    return out


def _flatten(path_data: str) -> list[list[tuple[float, float]]]:
    """Path to polygons, with curves actually subdivided.

    An earlier version jumped a cubic straight to its endpoint, so every curve
    drew as a chord. Domes read as triangles and I sent five headwear files
    back to be redrawn for a fault in this function.
    """
    tokens = re.findall(r"[MLCAQHVZmlcaqhvz]|-?\d*\.?\d+", path_data)
    polygons: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    index = 0
    point = (0.0, 0.0)
    while index < len(tokens):
        token = tokens[index].upper()
        if token == "M":
            if current:
                polygons.append(current)
            point = (float(tokens[index + 1]), float(tokens[index + 2]))
            current = [point]
            index += 3
        elif token == "L":
            point = (float(tokens[index + 1]), float(tokens[index + 2]))
            current.append(point)
            index += 3
        elif token == "C":
            control_one = (float(tokens[index + 1]), float(tokens[index + 2]))
            control_two = (float(tokens[index + 3]), float(tokens[index + 4]))
            end = (float(tokens[index + 5]), float(tokens[index + 6]))
            current.extend(_cubic(point, control_one, control_two, end))
            point = end
            index += 7
        elif token == "A":
            end = (float(tokens[index + 6]), float(tokens[index + 7]))
            radius_x, radius_y = float(tokens[index + 1]), float(tokens[index + 2])
            rotation = float(tokens[index + 3])
            large_arc, sweep = int(float(tokens[index + 4])), int(float(tokens[index + 5]))
            current.extend(_elliptical(point, radius_x, radius_y, rotation, large_arc, sweep, end))
            point = end
            index += 8
        elif token == "Q":
            control = (float(tokens[index + 1]), float(tokens[index + 2]))
            end = (float(tokens[index + 3]), float(tokens[index + 4]))
            current.extend(_quadratic(point, control, end))
            point = end
            index += 5
        elif token == "H":
            point = (float(tokens[index + 1]), point[1])
            current.append(point)
            index += 2
        elif token == "V":
            point = (point[0], float(tokens[index + 1]))
            current.append(point)
            index += 2
        elif token == "Z":
            if current:
                polygons.append(current)
                current = []
            index += 1
        else:
            index += 1
    if current:
        polygons.append(current)
    return polygons


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    render_to = None
    if "--render" in argv:
        render_to = Path(argv[argv.index("--render") + 1])
    return check(Path(argv[1]), render_to)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
