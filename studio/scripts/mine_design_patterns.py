"""Measure design parameters across the evidence corpus.

``DESIGN_REVIEW_SCORECARD.md`` §12 asks for its thresholds to be calibrated
against real work rather than left as derived guesses, and
``SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md`` names scale roles (S0-S4) and a
screen-print-first colour discipline without ever dimensioning either. This
measures what the corpus actually does, per design tradition, so those numbers
come from evidence instead of assertion.

Deterministic: no model, no network. Same corpus in, same numbers out.

What it measures per image, and the honest limits of each:

* **garment colour** -- the modal colour of the image border, which is the
  garment or the backdrop. Reliable on flat-lay and torso crops, weaker where a
  model's face or a busy background fills the edge.
* **print colour count** -- distinct colours in the print region after
  quantisation. A proxy for ink count, and an over-count on photographic or
  heavily distressed prints, which is itself worth knowing.
* **print coverage** -- share of the garment region differing from the garment
  colour. The measurable half of what the constitution calls scale role.
* **placement** -- centroid of the print region, as thirds. Distinguishes a
  chest hit from a full front without reading the product copy.
* **value polarity** -- whether the print is lighter or darker than the garment.

None of these read the *design*. They read its physical parameters, which is
the half a machine can measure honestly.

    python scripts/mine_design_patterns.py
    python scripts/mine_design_patterns.py --limit 200      # quick pass
"""

from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_tiers import is_excluded

CORPUS_ROOT = Path(__file__).resolve().parent.parent / "var" / "design_corpus"
REPORT_PATH = CORPUS_ROOT / "design_patterns.json"

# Analysis resolution. Large enough to keep a print's shape and colour count
# meaningful, small enough that five thousand images finish in minutes.
ANALYSIS_SIZE = 256

# How far a pixel's colour must sit from the garment colour to count as print,
# in 0-255 Euclidean RGB. Below this is fabric shading, not ink.
PRINT_DISTANCE = 60.0

# Quantisation level for the ink count. Screen printing works in flat spot
# colours, so near-identical shades are one ink, not several.
COLOUR_BUCKETS = 6

# A print region smaller than this share of the garment is noise -- a seam, a
# care label, a highlight -- not a graphic.
MIN_PRINT_COVERAGE = 0.004


def _analyse(path: Path) -> dict[str, Any] | None:
    try:
        image = Image.open(path).convert("RGB")
    except Exception:
        return None

    image = image.resize((ANALYSIS_SIZE, ANALYSIS_SIZE), Image.LANCZOS)
    pixels = np.asarray(image, dtype=np.float32)

    # The garment or backdrop colour, taken from the border where a print
    # almost never reaches.
    edge = np.concatenate(
        [
            pixels[:12, :, :].reshape(-1, 3),
            pixels[-12:, :, :].reshape(-1, 3),
            pixels[:, :12, :].reshape(-1, 3),
            pixels[:, -12:, :].reshape(-1, 3),
        ]
    )
    ground = np.median(edge, axis=0)

    # The torso box. Deliberately tight: a wider crop catches the model's head,
    # arms and background, and every one of those differs from the garment
    # colour, so they read as ink. An earlier, looser box scored a small
    # left-chest skull print at 44% coverage.
    centre = pixels[90:200, 80:176, :]
    garment = np.median(centre.reshape(-1, 3), axis=0)

    distance = np.sqrt(((centre - garment) ** 2).sum(axis=2))
    print_mask = distance > PRINT_DISTANCE

    # Coverage against garment pixels, not against the whole box. Anything far
    # enough from the garment colour to be skin or background is neither
    # garment nor ink, and counting it in the denominator understates a print
    # while counting it as ink overstates one.
    off_garment = distance > PRINT_DISTANCE * 3.0
    garment_pixels = int((~off_garment).sum())
    print_mask = print_mask & ~off_garment
    coverage = float(print_mask.sum() / max(garment_pixels, 1))

    if coverage < MIN_PRINT_COVERAGE:
        return {
            "garment_rgb": [round(float(v)) for v in garment],
            "ground_rgb": [round(float(v)) for v in ground],
            "print_coverage": round(coverage, 4),
            "has_print": False,
        }

    ink = centre[print_mask]

    # Quantise before counting: a screen print is flat spot colour, so shades
    # within a bucket are one ink.
    step = 256 / COLOUR_BUCKETS
    quantised = (ink // step).astype(np.int16)
    keyed = quantised[:, 0] * COLOUR_BUCKETS**2 + quantised[:, 1] * COLOUR_BUCKETS + quantised[:, 2]
    counts = collections.Counter(keyed.tolist())
    # Colours holding less than 5% of the ink are edge antialiasing, not inks.
    significant = [c for c in counts.values() if c / len(keyed) >= 0.05]

    rows, cols = np.nonzero(print_mask)
    centroid_y = float(rows.mean()) / print_mask.shape[0]
    centroid_x = float(cols.mean()) / print_mask.shape[1]

    garment_luma = float(garment @ np.array([0.2126, 0.7152, 0.0722]))
    ink_luma = float(ink.mean(axis=0) @ np.array([0.2126, 0.7152, 0.0722]))

    return {
        "garment_rgb": [round(float(v)) for v in garment],
        "ground_rgb": [round(float(v)) for v in ground],
        "has_print": True,
        "print_coverage": round(coverage, 4),
        "ink_colours": len(significant),
        "centroid_x": round(centroid_x, 3),
        "centroid_y": round(centroid_y, 3),
        "garment_luma": round(garment_luma, 1),
        "ink_luma": round(ink_luma, 1),
        "light_on_dark": ink_luma > garment_luma,
    }


def _placement_band(centroid_y: float) -> str:
    if centroid_y < 0.42:
        return "upper"
    if centroid_y > 0.58:
        return "lower"
    return "centre"


def _garment_family(rgb: list[int]) -> str:
    r, g, b = rgb
    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
    spread = max(rgb) - min(rgb)
    if spread < 28:
        if luma < 70:
            return "black"
        if luma > 185:
            return "white"
        return "grey"
    if r > g and r > b:
        return "warm"
    if b > r and b > g:
        return "cool"
    return "other"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="stop after N images")
    args = parser.parse_args(argv[1:])

    if not CORPUS_ROOT.exists():
        print("No corpus found. Run scripts/collect_design_corpus.py first.", file=sys.stderr)
        return 2

    records: list[dict[str, Any]] = []
    seen = 0
    for brand_dir in sorted(CORPUS_ROOT.iterdir()):
        if is_excluded(brand_dir.name):
            continue
        brand_file = brand_dir / "brand.json"
        if not brand_file.is_file():
            continue
        brand = json.loads(brand_file.read_text(encoding="utf-8"))
        tradition = brand.get("design_tradition", "unknown")

        products_dir = brand_dir / "products"
        if not products_dir.is_dir():
            continue
        for product_dir in sorted(products_dir.iterdir()):
            product_file = product_dir / "product.json"
            if not product_file.is_file():
                continue
            product = json.loads(product_file.read_text(encoding="utf-8"))
            # The first image is the primary product shot; later ones are
            # alternate angles of the same design and would double-count it.
            images = product.get("images") or []
            if not images:
                continue
            result = _analyse(product_dir / images[0])
            if result is None:
                continue
            result["brand_slug"] = brand.get("brand_slug", brand_dir.name)
            result["tradition"] = tradition
            result["category"] = product.get("category", "unknown")
            records.append(result)
            seen += 1
            if seen % 250 == 0:
                print(f"  {seen} analysed...", flush=True)
            if args.limit and seen >= args.limit:
                break
        if args.limit and seen >= args.limit:
            break

    printed = [r for r in records if r.get("has_print")]
    report: dict[str, Any] = {
        "designs_analysed": len(records),
        "designs_with_detectable_print": len(printed),
        "by_tradition": {},
        "overall": {},
    }

    def summarise(rows: list[dict[str, Any]]) -> dict[str, Any]:
        with_print = [r for r in rows if r.get("has_print")]
        if not with_print:
            return {"designs": len(rows), "with_print": 0}
        coverage = sorted(r["print_coverage"] for r in with_print)
        inks = sorted(r["ink_colours"] for r in with_print)
        return {
            "designs": len(rows),
            "with_print": len(with_print),
            "print_coverage": {
                "median": round(statistics.median(coverage), 4),
                "p10": round(coverage[int(len(coverage) * 0.10)], 4),
                "p90": round(coverage[int(len(coverage) * 0.90)], 4),
            },
            "ink_colours": {
                "median": statistics.median(inks),
                "p90": inks[int(len(inks) * 0.90)],
            },
            "placement": dict(
                collections.Counter(
                    _placement_band(r["centroid_y"]) for r in with_print
                ).most_common()
            ),
            "garment_colour": dict(
                collections.Counter(
                    _garment_family(r["garment_rgb"]) for r in with_print
                ).most_common()
            ),
            "light_on_dark_pct": round(
                100 * sum(1 for r in with_print if r["light_on_dark"]) / len(with_print), 1
            ),
        }

    report["overall"] = summarise(records)
    by_tradition: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for record in records:
        by_tradition[record["tradition"]].append(record)
    for tradition, rows in sorted(by_tradition.items(), key=lambda kv: -len(kv[1])):
        report["by_tradition"][tradition] = summarise(rows)

    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    overall = report["overall"]
    print(f"\n{len(records)} designs analysed, {len(printed)} with a detectable print\n")
    print(
        f"print coverage   median {overall['print_coverage']['median']:.1%}"
        f"   p10 {overall['print_coverage']['p10']:.1%}"
        f"   p90 {overall['print_coverage']['p90']:.1%}"
    )
    print(
        f"ink colours      median {overall['ink_colours']['median']}"
        f"   p90 {overall['ink_colours']['p90']}"
    )
    print(f"placement        {overall['placement']}")
    print(f"garment colour   {overall['garment_colour']}")
    print(f"light on dark    {overall['light_on_dark_pct']}%")
    print(f"\nwritten to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
