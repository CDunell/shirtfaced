#!/usr/bin/env python3
"""Convert a supplied Curb Stamps raster line drawing to a centreline SVG.

The converter changes stroke construction only. It skeletonises the source
alpha, traces the resulting pixel graph and applies the collection's shared
SVG stroke. It never generates or invents character geometry.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


VIEW_W, VIEW_H = 1200, 500
SAFE_W, SAFE_H = 1080, 300
STROKE = 4


def remove_low_crop_fragments(mask: np.ndarray) -> tuple[np.ndarray, int]:
    """Drop small disconnected text/crop debris below the creature.

    Some supplied icon crops include the very top of the name beneath the
    creature. Legitimate eyes and internal marks sit higher in the frame, so
    only small components wholly inside the bottom 18 percent are removed.
    """
    labels, count = ndimage.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
    if count < 2:
        return mask, 0
    areas = np.bincount(labels.ravel())[1:]
    largest = int(areas.max())
    cleaned = mask.copy()
    removed = 0
    cutoff = mask.shape[0] * 0.82
    for label_id, area in enumerate(areas, start=1):
        ys, _ = np.where(labels == label_id)
        if len(ys) and ys.min() >= cutoff and area < largest * 0.18:
            cleaned[labels == label_id] = False
            removed += 1
    return cleaned, removed


def thin(mask: np.ndarray) -> np.ndarray:
    """Vectorised Zhang-Suen thinning."""
    img = np.pad(mask.astype(np.uint8), 1)
    changed = True
    while changed:
        changed = False
        for step in (0, 1):
            p2 = img[:-2, 1:-1]
            p3 = img[:-2, 2:]
            p4 = img[1:-1, 2:]
            p5 = img[2:, 2:]
            p6 = img[2:, 1:-1]
            p7 = img[2:, :-2]
            p8 = img[1:-1, :-2]
            p9 = img[:-2, :-2]
            center = img[1:-1, 1:-1]
            neighbours = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            transitions = sum(
                edge.astype(np.uint8)
                for edge in (
                    (p2 == 0) & (p3 == 1), (p3 == 0) & (p4 == 1),
                    (p4 == 0) & (p5 == 1), (p5 == 0) & (p6 == 1),
                    (p6 == 0) & (p7 == 1), (p7 == 0) & (p8 == 1),
                    (p8 == 0) & (p9 == 1), (p9 == 0) & (p2 == 1),
                )
            )
            if step == 0:
                side = (p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)
            else:
                side = (p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0)
            remove = (center == 1) & (neighbours >= 2) & (neighbours <= 6) & (transitions == 1) & side
            if np.any(remove):
                center[remove] = 0
                changed = True
    return img[1:-1, 1:-1].astype(bool)


NEIGHBOURS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def adjacent(point: tuple[int, int], pixels: set[tuple[int, int]]) -> list[tuple[int, int]]:
    y, x = point
    result = []
    for dy, dx in NEIGHBOURS:
        candidate = (y + dy, x + dx)
        if candidate not in pixels:
            continue
        # A diagonal beside an orthogonal connection creates a false graph
        # junction on a one-pixel raster curve. Keep diagonals only when they
        # are the actual continuation of the stroke.
        if dy and dx and ((y + dy, x) in pixels or (y, x + dx) in pixels):
            continue
        result.append(candidate)
    return result


def trace_graph(skeleton: np.ndarray) -> list[list[tuple[int, int]]]:
    pixels = set(map(tuple, np.argwhere(skeleton)))
    graph = {p: adjacent(p, pixels) for p in pixels}
    nodes = {p for p, n in graph.items() if len(n) != 2}
    used: set[frozenset[tuple[int, int]]] = set()
    paths: list[list[tuple[int, int]]] = []

    # A tiny filled feature such as a dot eye can skeletonise to one pixel.
    # Preserve it as a zero-length round-capped stroke instead of silently
    # dropping the character's eye.
    for point, neighbours in graph.items():
        if not neighbours:
            paths.append([point, point])

    def walk(start: tuple[int, int], nxt: tuple[int, int]) -> list[tuple[int, int]]:
        path = [start, nxt]
        previous, current = start, nxt
        used.add(frozenset((start, nxt)))
        while current not in nodes:
            options = [p for p in graph[current] if p != previous]
            if not options:
                break
            candidate = options[0]
            edge = frozenset((current, candidate))
            if edge in used:
                break
            used.add(edge)
            path.append(candidate)
            previous, current = current, candidate
        return path

    for node in nodes:
        for neighbour in graph[node]:
            if frozenset((node, neighbour)) not in used:
                paths.append(walk(node, neighbour))

    for point in pixels:
        for neighbour in graph[point]:
            if frozenset((point, neighbour)) not in used:
                paths.append(walk(point, neighbour))
    return [p for p in paths if len(p) > 1]


def rdp(points: list[tuple[float, float]], epsilon: float) -> list[tuple[float, float]]:
    if len(points) < 3:
        return points
    start = np.array(points[0]); end = np.array(points[-1]); line = end - start
    body = np.array(points[1:-1])
    if np.allclose(line, 0):
        distances = np.linalg.norm(body - start, axis=1)
    else:
        relative = body - start
        distances = np.abs((line[0] * relative[:, 1] - line[1] * relative[:, 0]) / np.linalg.norm(line))
    index = int(np.argmax(distances)); maximum = float(distances[index])
    if maximum > epsilon:
        split = index + 1
        return rdp(points[: split + 1], epsilon)[:-1] + rdp(points[split:], epsilon)
    return [points[0], points[-1]]


def svg_path(points: list[tuple[float, float]]) -> str:
    if len(points) == 2:
        return f"M {points[0][0]:.2f} {points[0][1]:.2f} L {points[1][0]:.2f} {points[1][1]:.2f}"
    commands = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
    for index in range(1, len(points) - 1):
        cx, cy = points[index]
        nx, ny = points[index + 1]
        if index < len(points) - 2:
            ex, ey = (cx + nx) / 2, (cy + ny) / 2
        else:
            ex, ey = nx, ny
        commands.append(f"Q {cx:.2f} {cy:.2f} {ex:.2f} {ey:.2f}")
    return " ".join(commands)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--output", type=Path, required=True)
    # The supplied extracted PNGs have fully opaque line cores but some carry
    # semi-transparent generation noise along the edges. Trace only the core.
    parser.add_argument("--threshold", type=int, default=96)
    parser.add_argument("--simplify", type=float, default=1.15)
    args = parser.parse_args()

    rgba = Image.open(args.source).convert("RGBA")
    alpha = np.asarray(rgba)[:, :, 3]
    mask, removed_fragments = remove_low_crop_fragments(alpha >= args.threshold)
    skeleton = thin(mask)
    ys, xs = np.where(skeleton)
    if not len(xs):
        raise SystemExit("No opaque linework found")
    min_x, max_x, min_y, max_y = xs.min(), xs.max(), ys.min(), ys.max()
    scale = min(SAFE_W / max(1, max_x - min_x), SAFE_H / max(1, max_y - min_y))
    offset_x = (VIEW_W - (max_x - min_x) * scale) / 2 - min_x * scale
    offset_y = 200 - ((min_y + max_y) / 2) * scale

    traced = trace_graph(skeleton)
    transformed = []
    for path in traced:
        points = [(x * scale + offset_x, y * scale + offset_y) for y, x in path]
        transformed.append(rdp(points, args.simplify * scale))

    args.output.mkdir(parents=True, exist_ok=True)
    paths = "\n    ".join(f'<path d="{svg_path(p)}"/>' for p in transformed)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VIEW_W} {VIEW_H}">
  <g fill="none" stroke="currentColor" stroke-width="{STROKE}" stroke-linecap="round" stroke-linejoin="round">
    {paths}
  </g>
</svg>\n'''
    (args.output / f"{args.slug}.svg").write_text(svg)

    qa_svg = svg.replace("currentColor", "#00ffff")
    (args.output / f"{args.slug}-qa-vector.svg").write_text(qa_svg)

    # Magenta source layer for visual QA. When composited with the cyan SVG,
    # matching geometry reads close to white and drift remains coloured.
    source_alpha = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
    scaled = source_alpha.resize(
        (round(rgba.width * scale), round(rgba.height * scale)),
        Image.Resampling.LANCZOS,
    )
    qa_source = Image.new("RGBA", (VIEW_W, VIEW_H), (0, 0, 0, 0))
    magenta = Image.new("RGBA", scaled.size, (255, 0, 255, 0))
    magenta.putalpha(scaled)
    qa_source.alpha_composite(magenta, (round(offset_x), round(offset_y)))
    qa_source.save(args.output / f"{args.slug}-qa-original.png")
    metadata = {
        "source": str(args.source), "viewBox": [0, 0, VIEW_W, VIEW_H],
        "strokeWidth": STROKE, "printWidthMm": 240, "physicalStrokeMm": 0.8,
        "scale": scale, "offset": [offset_x, offset_y], "pathCount": len(transformed),
        "removedLowCropFragments": removed_fragments,
    }
    (args.output / f"{args.slug}.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
