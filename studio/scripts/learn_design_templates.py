"""Learning the corpus's recurring layout templates, instead of averaging them.

``mine_design_structure.py`` records the band stack of every printed design and
reports the median slot positions per element count. That median is a bad
summary: three-element designs are not one shape, they are several -- an arch
over an image over a small caption, three stacked lines of type, a big
illustration with a rule above and below -- and averaging those produces a
layout that matches none of them.

This clusters the stacks instead, so what comes out is "three-element designs
come in these four families, with this many examples each" rather than one
blended shape. That is the difference between computing a mean and finding a
pattern.

k-means, written out rather than imported, because the only dependency in this
project's analysis path is numpy and a clustering library is not worth adding
for forty lines. Initialisation is k-means++ and the seed is fixed, so the same
corpus produces the same templates every run.

    python scripts/learn_design_templates.py
    python scripts/learn_design_templates.py --clusters 5
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

CORPUS_ROOT = Path(__file__).resolve().parent.parent / "var" / "design_corpus"
STRUCTURE_PATH = CORPUS_ROOT / "design_structure_raw.json"
REPORT_PATH = CORPUS_ROOT / "design_templates.json"

SEED = 7


def _features(bands: list[dict[str, float]]) -> list[float]:
    """A design's stack as a flat vector: each band's top, height and width.

    Normalised to the print's own extent so two designs with the same shape at
    different sizes on the garment cluster together -- the template is the
    arrangement, and scale is chosen separately.
    """
    top = min(b["top"] for b in bands)
    bottom = max(b["top"] + b["height"] for b in bands)
    span = max(bottom - top, 1e-6)
    vector: list[float] = []
    for band in bands:
        vector.extend(
            [
                (band["top"] - top) / span,
                band["height"] / span,
                band["width"],
            ]
        )
    return vector


def _kmeans(points: np.ndarray, k: int, iterations: int = 60) -> tuple[np.ndarray, np.ndarray]:
    """k-means with k-means++ seeding. Deterministic for a fixed seed."""
    rng = np.random.default_rng(SEED)
    n = len(points)
    k = min(k, n)

    centres = [points[rng.integers(n)]]
    for _ in range(k - 1):
        distance = np.min(
            np.stack([((points - c) ** 2).sum(axis=1) for c in centres]), axis=0
        )
        total = distance.sum()
        if total <= 0:
            centres.append(points[rng.integers(n)])
            continue
        centres.append(points[rng.choice(n, p=distance / total)])
    centroids = np.stack(centres)

    labels = np.zeros(n, dtype=int)
    for _ in range(iterations):
        distances = np.stack([((points - c) ** 2).sum(axis=1) for c in centroids])
        new_labels = distances.argmin(axis=0)
        if (new_labels == labels).all():
            break
        labels = new_labels
        for index in range(len(centroids)):
            member = points[labels == index]
            if len(member):
                centroids[index] = member.mean(axis=0)
    return labels, centroids


def _describe(slots: list[dict[str, float]]) -> str:
    """Name a template from its proportions, so the output reads as design talk."""
    count = len(slots)
    heights = [s["height"] for s in slots]
    widths = [s["width"] for s in slots]
    lead = heights.index(max(heights))

    if count == 1:
        if widths[0] > 0.8 and heights[0] > 0.5:
            return "full block — one mass filling the print area"
        if widths[0] < 0.5:
            return "compact mark — narrow, centred"
        return "wide band — full width, shallow"

    dominant = max(heights) / max(sum(heights) / count, 1e-6)
    if count == 2:
        if dominant > 1.6:
            return "lead and caption" if lead == 0 else "caption and lead"
        return "two even bands — paired lines"
    if count >= 3:
        if lead == 0:
            return "headline over stacked support"
        if lead == count - 1:
            return "stacked support over a base mass"
        if dominant > 1.5:
            return "banner, hero, footer — framed centre"
        return "even stack — repeated bands"
    return f"{count}-band stack"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clusters", type=int, default=4, help="templates per element count")
    args = parser.parse_args(argv[1:])

    if not STRUCTURE_PATH.is_file():
        print(
            f"No raw structure at {STRUCTURE_PATH}.\n"
            "Run scripts/mine_design_structure.py --raw first.",
            file=sys.stderr,
        )
        return 2

    records = json.loads(STRUCTURE_PATH.read_text(encoding="utf-8"))
    by_count: dict[int, list[dict[str, Any]]] = {}
    for record in records:
        by_count.setdefault(len(record["bands"]), []).append(record)

    families: dict[str, Any] = {}
    for count, rows in sorted(by_count.items()):
        # Below this there is not enough to distinguish a template from a one-off.
        if count == 0 or len(rows) < 30:
            continue
        points = np.array([_features(r["bands"]) for r in rows], dtype=np.float64)
        wanted = min(args.clusters, max(2, len(rows) // 25))
        labels, _ = _kmeans(points, wanted)

        templates = []
        for index in range(labels.max() + 1):
            members = [rows[i] for i in range(len(rows)) if labels[i] == index]
            if len(members) < 8:
                continue
            slots = []
            for slot_index in range(count):
                bands = [m["bands"][slot_index] for m in members]
                slots.append(
                    {
                        "slot": slot_index + 1,
                        "top": round(statistics.median(b["top"] for b in bands), 3),
                        "height": round(statistics.median(b["height"] for b in bands), 3),
                        "width": round(statistics.median(b["width"] for b in bands), 3),
                        "centre_x": round(statistics.median(b["centre_x"] for b in bands), 3),
                    }
                )
            templates.append(
                {
                    # Stable identity. Descriptive names collide -- k-means finds
                    # two distinct "wide band" centroids that differ in
                    # proportion -- and approvals keyed by name would pool two
                    # different arrangements into one score.
                    "id": f"{count}-{index}",
                    "name": _describe(slots),
                    "designs": len(members),
                    "share": round(len(members) / len(rows), 3),
                    "slots": slots,
                    "traditions": dict(Counter(m["tradition"] for m in members).most_common(4)),
                    "median_words": statistics.median(m["words"] for m in members),
                }
            )
        templates.sort(key=lambda t: -t["designs"])
        if templates:
            families[str(count)] = {"designs": len(rows), "templates": templates}

    report = {"source_designs": len(records), "families": families}
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"{len(records)} designs\n")
    for count, entry in families.items():
        print(f"{count} element(s) — {entry['designs']} designs")
        for template in entry["templates"]:
            share = template["share"]
            top_tradition = next(iter(template["traditions"]), "—")
            print(
                f"    {template['designs']:>4} ({share:>5.0%})  {template['name']:<42}"
                f"  commonest in {top_tradition}"
            )
        print()
    print(f"written to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
