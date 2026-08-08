"""Check an artwork SVG before it joins the element archive.

Companion to `check_garment.py`, which checks print zones. This describes the
artwork itself.

**It is a report, not a gate.** Nothing here decides whether a file may be
ingested; everything is ingested. It exists so that what arrived is visible
without opening thirty files by hand, and so that anything the pipeline cannot
read yet is named as work for us rather than treated as a fault in the artwork.

The first version of this scored files out of a total and printed FAIL, which
made a description into a filter. That was the same instinct that put a
single-path rule and a size test into a supplier brief, wearing a different hat.

Bulk artwork -- a bought pack, a vectorised sheet -- is what this is for, so it
takes a folder as readily as a file.

    python scripts/check_element.py flash/skull.svg
    python scripts/check_element.py flash/ --render out.png

The render is the point. The checks catch what is measurable; looking at it
catches everything else.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from check_garment import _flatten

from app.archive.convert import combined_path, shapes_in

STROKE = re.compile(r'\bstroke="(?!none\b)([^"]+)"', re.I)
FILL = re.compile(r'\bfill="([^"]+)"', re.I)
FILL_RULE = re.compile(r'\bfill-rule="([^"]+)"', re.I)

# A subpath smaller than this share of the artwork is a speck. Specks are not
# wrong, but they are the first thing to disappear at print size, so they are
# worth naming rather than leaving for someone to notice on a sample garment.
SPECK_SHARE = 0.004


def _area(polygon: list[tuple[float, float]]) -> float:
    """Signed area. The sign is the winding direction, which is the point."""
    total = 0.0
    for index in range(len(polygon)):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % len(polygon)]
        total += x1 * y2 - x2 * y1
    return total / 2.0


def _box(polygon: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]
    return min(xs), min(ys), max(xs), max(ys)


def _inside(inner: tuple[float, ...], outer: tuple[float, ...]) -> bool:
    return (
        inner[0] >= outer[0] - 1e-6
        and inner[1] >= outer[1] - 1e-6
        and inner[2] <= outer[2] + 1e-6
        and inner[3] <= outer[3] + 1e-6
    )


def check(file: Path) -> tuple[list[str], list[str]]:
    """What is in one file: problems, then notes.

    A problem here means there is no artwork to place -- an empty file, an
    outline with no area. Everything else is a note describing what arrived.
    """
    problems: list[str] = []
    notes: list[str] = []

    try:
        svg = file.read_text(encoding="utf-8")
    except OSError as error:
        return ([f"unreadable: {error}"], [])

    if "<text" in svg:
        notes.append(
            "contains <text>; the converter does not read it yet, so those words "
            "will not arrive -- a converter is ours to write"
        )
    strokes = STROKE.findall(svg)
    if strokes:
        notes.append(
            f"stroked geometry ({', '.join(sorted(set(strokes)))}); strokes are lost "
            "on flattening, so the artwork needs outlining -- also ours to do"
        )

    shapes = shapes_in(svg)
    if not shapes:
        return ([*problems, "nothing the converter can read"], notes)

    fills = {f for f in FILL.findall(svg) if f.lower() != "none"}
    if len(fills) > 1:
        notes.append(f"{len(fills)} fill colours; the engine assigns its own inks")

    evenodd = "evenodd" in {r.lower() for r in FILL_RULE.findall(svg)}
    subpaths = [p for p in _flatten(combined_path(shapes)) if len(p) >= 3]
    if not subpaths:
        return ([*problems, "no closed subpaths"], notes)

    areas = [_area(p) for p in subpaths]
    boxes = [_box(p) for p in subpaths]
    outer = max(range(len(subpaths)), key=lambda i: abs(areas[i]))
    total = abs(areas[outer])

    detached: list[int] = []
    same_wound: list[int] = []
    specks: list[int] = []
    for index in range(len(subpaths)):
        if index == outer:
            continue
        if abs(areas[index]) < total * SPECK_SHARE:
            specks.append(index)
        if _inside(boxes[index], boxes[outer]):
            if not evenodd and (areas[index] > 0) == (areas[outer] > 0):
                same_wound.append(index)
        else:
            detached.append(index)

    if same_wound:
        notes.append(
            f"{len(same_wound)} counter(s) wound with the outline rather than against "
            "it; ingested artwork is filled even-odd, so nesting decides and these cut "
            "correctly anyway"
        )
    if detached:
        notes.append(f"{len(detached)} subpath(s) outside the main outline")
    if specks:
        notes.append(f"{len(specks)} subpath(s) under {SPECK_SHARE:.1%} of the artwork")

    x0, y0, x1, y1 = boxes[outer]
    width, height = x1 - x0, y1 - y0
    if width <= 0 or height <= 0:
        problems.append("outline has no area; there is no artwork here to place")
    else:
        notes.append(
            f"{len(shapes)} shape(s), {len(subpaths)} subpath(s), aspect {width / height:.2f}"
        )

    return problems, notes


def _is_hole(index: int, subpaths: list, areas: list[float], boxes: list, evenodd: bool) -> bool:
    """Whether a subpath cuts or fills, by the rule the renderer will use.

    Drawing every subpath solid was the obvious shortcut and it would have made
    this tool lie about the one fault it exists to catch: a counter wound the
    wrong way looks identical to a correct one until something applies the fill
    rule. So the fill rule is applied here too.
    """
    container = None
    for other in range(len(subpaths)):
        if other == index or not _inside(boxes[index], boxes[other]):
            continue
        if container is None or abs(areas[other]) < abs(areas[container]):
            container = other
    if container is None:
        return False
    if evenodd:
        return not _is_hole(container, subpaths, areas, boxes, evenodd)
    return (areas[index] > 0) != (areas[container] > 0)


def _render(files: list[Path], out: Path) -> None:
    """Every file at full size and at print size, because looking is the check."""
    from PIL import Image, ImageDraw

    columns, cell, small = 4, 190, 44
    rows = (len(files) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell, rows * (cell + small)), "white")
    draw = ImageDraw.Draw(sheet)

    for index, file in enumerate(files):
        try:
            raw = file.read_text(encoding="utf-8")
            subpaths = [p for p in _flatten(combined_path(shapes_in(raw))) if len(p) >= 3]
        except (OSError, ValueError):
            continue
        if not subpaths:
            continue

        evenodd = "evenodd" in {r.lower() for r in FILL_RULE.findall(raw)}
        areas = [_area(p) for p in subpaths]
        boxes = [_box(p) for p in subpaths]
        # Largest first, so a hole is always painted after the mass it cuts.
        order = sorted(range(len(subpaths)), key=lambda i: -abs(areas[i]))

        xs = [p[0] for sub in subpaths for p in sub]
        ys = [p[1] for sub in subpaths for p in sub]
        span = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
        column, row = index % columns, index // columns

        for scale_px, offset_y in ((cell - 30, 0), (small - 12, cell)):
            factor = scale_px / span
            ox = column * cell + (cell - (max(xs) - min(xs)) * factor) / 2
            oy = row * (cell + small) + offset_y + 6
            for i in order:
                hole = _is_hole(i, subpaths, areas, boxes, evenodd)
                draw.polygon(
                    [
                        (ox + (x - min(xs)) * factor, oy + (y - min(ys)) * factor)
                        for x, y in subpaths[i]
                    ],
                    fill=(255, 255, 255) if hole else (34, 34, 34),
                )
        draw.text(
            (column * cell + 4, row * (cell + small) + cell + small - 12),
            file.stem[:26],
            fill=(120, 120, 120),
        )

    sheet.save(out)
    print(f"\nrendered {len(files)} file(s) to {out}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="an SVG file or a folder of them")
    parser.add_argument("--render", type=Path, help="write a contact sheet here")
    args = parser.parse_args(argv)

    files = sorted(args.target.glob("*.svg")) if args.target.is_dir() else [args.target]
    if not files:
        print("no SVG files found")
        return 1

    empty = 0
    for file in files:
        problems, notes = check(file)
        print(f"  {file.name}")
        for note in notes:
            print(f"      - {note}")
        for problem in problems:
            print(f"      ! {problem}")
        empty += bool(problems)

    tail = f", {empty} with no artwork in them" if empty else ""
    print(f"\n{len(files)} file(s) described{tail}")
    if args.render:
        _render(files, args.render)
    # Zero unless a file was literally empty. Describing artwork is not a test,
    # and a non-zero exit would turn this back into the gate it stopped being.
    return 1 if empty else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
