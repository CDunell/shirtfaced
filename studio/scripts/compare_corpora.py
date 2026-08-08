#!/usr/bin/env python3
"""Does the brand corpus agree with flat artwork about how a design is arranged?

The brand corpus is measured off photographs: a garment on a model, where a
collar, a shoulder seam, a fold and the photograph's own halftone all clear an
ink threshold meant for print. Everything read from it is an inference, and
there has never been anything to check that inference against.

Flat artwork is the same measurement made directly -- on marketplaces the design
*is* the product, published isolated on white. It is a weaker design population
and its register is wrong for us, which is exactly why it is never merged: what
it is good for is telling us whether the *geometry* we read off photographs is
real or an artefact of reading photographs.

Agreement means the brand numbers can be trusted as placement evidence.
Disagreement localises the damage -- if flat artwork puts a single mass at 0.10
from the top and photographs say 0.19, the miner is finding a collar.

    python scripts/compare_corpora.py

Reads both mines; writes nothing. Needs `mine_design_structure.py` to have been
run with and without `--flat`.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "var" / "design_corpus"

# Below this many designs a share is noise and is reported but not judged.
MIN_DESIGNS = 25

# Sources whose render normalises the artwork to its own bounding box, which
# makes `top`, `height` and `width` incomparable with the brand corpus.
#
# The first run of this script reported "7/12 measurements agree" off a trimmed
# Threadless render. It was measuring nothing: trimming crops to the design's
# extent, so a single-element design fills its field by construction -- flat
# height 0.801 against brand 0.281, two different denominators. The agreements
# were confounded the same way, because trimmed artwork starts at top 0 and
# centres at 0.5 whatever it depicts.
#
# Redbubble's `flat,WxH,f-pad` fits the design into a fixed square, which is the
# same normalisation, and its pad colour is not ours to change. So Redbubble is
# a shape-distribution source only. Threadless is collected untrimmed and is the
# one source whose geometry answers the question.
NORMALISED_TRADITION = "flat_artwork_normalised"

# What counts as the same answer. Slot geometry is a fraction of the print area,
# so 4 points is roughly a centimetre on a tee -- tighter than the difference
# between a collar and a print, looser than measurement jitter.
TOLERANCE = 0.04


def _load(name: str) -> dict[str, Any] | None:
    path = CORPUS / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _shares(shapes: dict[str, int]) -> dict[str, float]:
    total = sum(shapes.values()) or 1
    return {shape: count / total for shape, count in shapes.items()}


def _slot(layout: dict[str, Any]) -> dict[str, float] | None:
    slots = layout.get("slots") or []
    return slots[0] if slots else None


def _geometry_by_elements(raw: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """First-slot medians per element count, from sources that keep their canvas.

    Built from the per-design records rather than the mine's summary, because
    the summary aggregates every flat source together -- and one of them fits
    each design into a fixed square, which fills the field by construction. That
    was being averaged into the geometry while a printed warning said it should
    not be.
    """
    grouped: dict[str, list[dict[str, float]]] = {}
    for record in raw:
        if record.get("tradition") == NORMALISED_TRADITION:
            continue
        bands = record.get("bands") or []
        if not bands:
            continue
        grouped.setdefault(str(record.get("elements")), []).append(bands[0])

    out: dict[str, dict[str, float]] = {}
    for key, bands in grouped.items():
        out[key] = {
            "designs": len(bands),
            **{
                field: round(statistics.median(b[field] for b in bands), 3)
                for field in ("top", "height", "width", "centre_x")
            },
        }
    return out


def main() -> int:
    brand = _load("design_structure.json")
    flat = _load("design_structure_flat.json")

    if brand is None:
        print("no brand mine — run mine_design_structure.py", file=sys.stderr)
        return 1
    if flat is None:
        print(
            "no flat mine — run:\n"
            "  node scripts/collect_majors_browser.mjs --flat --limit 150\n"
            "  python scripts/mine_design_structure.py --flat",
            file=sys.stderr,
        )
        return 1

    print(f"brand corpus  {brand['designs_analysed']:>5} designs   (photographs, inferred)")
    print(f"flat artwork  {flat['designs_analysed']:>5} designs   (isolated, direct)")

    if flat["designs_analysed"] < MIN_DESIGNS:
        print(f"\nflat corpus under {MIN_DESIGNS} designs — too thin to judge against.")
        return 1

    print("\nshape distribution")
    print(f"  {'shape':<38} {'brand':>7} {'flat':>7} {'gap':>7}")
    brand_shares = _shares(brand["shapes_overall"])
    flat_shares = _shares(flat["shapes_overall"])
    shapes = sorted(set(brand_shares) | set(flat_shares), key=lambda s: -brand_shares.get(s, 0))
    for shape in shapes:
        b = brand_shares.get(shape, 0.0)
        f = flat_shares.get(shape, 0.0)
        print(f"  {shape:<38} {b:>7.1%} {f:>7.1%} {f - b:>+7.1%}")

    flat_raw = _load("design_structure_flat_raw.json") or []
    flat_geometry = _geometry_by_elements(flat_raw)
    kept = sum(g["designs"] for g in flat_geometry.values())
    dropped = len(flat_raw) - kept
    print(
        f"\nfirst-slot geometry, by element count"
        f"   ({kept} canvas-preserving designs; {dropped} normalised, excluded)"
    )
    print(f"  {'elements':<10} {'field':<10} {'brand':>7} {'flat':>7} {'gap':>7}  verdict")
    disagreements = 0
    compared = 0
    for key in sorted(set(brand["layouts"]) & set(flat_geometry)):
        b_layout = brand["layouts"][key]
        f_slot = flat_geometry[key]
        if min(b_layout["designs"], f_slot["designs"]) < MIN_DESIGNS:
            continue
        b_slot = _slot(b_layout)
        if not b_slot:
            continue
        for field in ("top", "height", "width", "centre_x"):
            gap = f_slot[field] - b_slot[field]
            agrees = abs(gap) <= TOLERANCE
            compared += 1
            if not agrees:
                disagreements += 1
            print(
                f"  {key:<10} {field:<10} {b_slot[field]:>7.3f} {f_slot[field]:>7.3f} "
                f"{gap:>+7.3f}  {'agrees' if agrees else 'DIFFERS'}"
            )

    if not compared:
        print("\n  nothing comparable — no element count has enough designs in both.")
        return 1

    print(f"\n{compared - disagreements}/{compared} measurements agree within {TOLERANCE:.2f}.")
    if disagreements == 0:
        print("Geometry read off photographs matches geometry read off the artwork itself.")
    else:
        print(
            "Where they differ, the flat number is the more direct measurement.\n"
            "A brand `top` sitting materially lower is the signature of a collar\n"
            "being counted as part of the design."
        )
    print(
        f"\nGeometry is only meaningful from a source whose render preserves the\n"
        f"artwork's own canvas. Normalised sources ({NORMALISED_TRADITION})\n"
        f"contribute to the shape distribution above and must not be read here --\n"
        f"they fill their field by construction, whatever they depict."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
