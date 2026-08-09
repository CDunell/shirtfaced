#!/usr/bin/env python3
"""Measure the print forms each garment actually carries, instead of declaring them.

`design_range.py` lays every design out against a hardcoded table:

    Form("pocket",        0.24, 0.22, centre_x=0.28)
    Form("small_centred", 0.34, 0.26)
    Form("band",          0.92, 0.18)

Those numbers were invented. Nothing measured them -- they are a guess at what a
pocket print looks like, applied to every garment type alike, which is both the
derived-constraint failure this repository keeps paying for and a direct
contradiction of the constitution's section 13: a crop recalculates rather than
reusing tee placement, a cap front is embroidery-first.

Garment mockups make the real answer measurable. `mine_placement.py` records
where the print sits on each garment as a share of that garment. Cluster those
per category and the natural groups *are* the forms -- with a count behind each,
so a form nobody actually prints can be refused rather than offered.

    python scripts/derive_forms.py
    python scripts/derive_forms.py --min-evidence 12

Reads var/design_corpus/placement.json, writes var/design_corpus/forms.json.
Nothing is written into design_range.py automatically: swapping the engine's
geometry is a decision to take with the numbers in hand, not a side effect of
running a script.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist

ROOT = Path(__file__).resolve().parent.parent
PLACEMENT_PATH = ROOT / "var" / "design_corpus" / "placement.json"
FORMS_PATH = ROOT / "var" / "design_corpus" / "forms.json"

# The axes a form is actually made of: how big, and where.
#
# `top` is included because a chest print and a hem print of identical size are
# different forms, and `centre_x` because a pocket is defined by being off to
# one side. `height` and `width` carry scale.
AXES = ("top", "height", "width", "centre_x")

# Two placements belong to the same form when they sit within this distance in
# that four-dimensional space. 0.18 is a little under a fifth of a garment on
# every axis at once -- close enough that a pocket and a chest hit never merge,
# loose enough that the same form printed slightly higher or lower does not
# split into two.
CLUSTER_DISTANCE = 0.18

# A cluster below this many designs is one shop's habit, not a form.
MIN_EVIDENCE = 8

# Placements whose box had to span more than one ink cluster are excluded.
# mine_placement.py records this: the box may be the design, or it may be the
# design plus a fold shadow that survived the share test, and nothing measured
# so far separates those. Forms are worth deriving only from clean reads.
MAX_CLUSTERS = 1


def _name(centre: dict[str, float]) -> str:
    """A descriptive name for a measured form. Description, not prescription."""
    width, height, top, centre_x = (
        centre["width"],
        centre["height"],
        centre["top"],
        centre["centre_x"],
    )
    side = ""
    if centre_x < 0.42:
        side = ", left"
    elif centre_x > 0.58:
        side = ", right"

    if width > 0.75 and height > 0.6:
        return f"seam to seam{side}"
    if width > 0.6:
        return f"broad{side}" if height > 0.25 else f"band{side}"
    if width < 0.3 and height < 0.3:
        return f"small mark{side}" if top < 0.35 else f"small mark, low{side}"
    if height > 0.45:
        return f"tall panel{side}"
    return f"chest hit{side}"


def derive(records: list[dict[str, Any]], min_evidence: int) -> dict[str, Any]:
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record.get("clusters", 1) > MAX_CLUSTERS:
            continue
        by_category[record.get("category", "unknown")].append(record)

    out: dict[str, Any] = {}
    for category, rows in sorted(by_category.items(), key=lambda kv: -len(kv[1])):
        if len(rows) < min_evidence:
            out[category] = {
                "status": "insufficient_evidence",
                "clean_placements": len(rows),
                "needed": min_evidence,
            }
            continue

        matrix = np.array([[row[axis] for axis in AXES] for row in rows], dtype=float)
        if len(rows) == 1:
            labels = np.array([1])
        else:
            labels = fcluster(
                linkage(pdist(matrix), method="average"), CLUSTER_DISTANCE, criterion="distance"
            )

        forms = []
        for label in sorted(set(labels)):
            members = matrix[labels == label]
            if len(members) < min_evidence:
                continue
            centre = {
                axis: round(float(statistics.median(members[:, i])), 4)
                for i, axis in enumerate(AXES)
            }
            forms.append(
                {
                    "name": _name(centre),
                    "designs": len(members),
                    "share": round(len(members) / len(rows), 3),
                    **centre,
                    # The spread matters as much as the centre: a form the
                    # corpus agrees on tightly is worth more than one averaged
                    # out of scatter.
                    "spread": {
                        axis: round(float(members[:, i].std()), 4)
                        for i, axis in enumerate(AXES)
                    },
                }
            )

        forms.sort(key=lambda f: -f["designs"])
        covered = sum(f["designs"] for f in forms)
        out[category] = {
            "status": "measured" if forms else "no_form_reached_threshold",
            "clean_placements": len(rows),
            "covered_by_forms": covered,
            # Said out loud: placements that fell into clusters too small to be
            # called a form are not represented below.
            "unclustered": len(rows) - covered,
            "forms": forms,
        }
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-evidence", type=int, default=MIN_EVIDENCE)
    args = parser.parse_args(argv[1:])

    if not PLACEMENT_PATH.exists():
        print(
            f"No placements at {PLACEMENT_PATH}. Run scripts/mine_placement.py first.",
            file=sys.stderr,
        )
        return 1
    records = json.loads(PLACEMENT_PATH.read_text(encoding="utf-8"))

    result = derive(records, args.min_evidence)
    total_clean = sum(
        v.get("clean_placements", 0) for v in result.values() if isinstance(v, dict)
    )
    print(f"\n{len(records)} placements, {total_clean} clean enough to derive from\n")

    for category, block in result.items():
        if block["status"] != "measured":
            print(
                f"{category:<12} {block['status']} "
                f"({block.get('clean_placements', 0)} clean)"
            )
            continue
        print(
            f"{category}  ({block['clean_placements']} clean, "
            f"{block['unclustered']} unclustered)"
        )
        for form in block["forms"]:
            print(
                f"    {form['name']:<22} {form['designs']:>4} designs  {form['share']:>5.0%}  "
                f"w {form['width']:.3f}  h {form['height']:.3f}  "
                f"top {form['top']:.3f}  x {form['centre_x']:.3f}"
            )
        print()

    FORMS_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"written to {FORMS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
