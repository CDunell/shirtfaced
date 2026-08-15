"""Measure design parameters across the evidence corpus.

``DESIGN_REVIEW_SCORECARD.md`` §12 asks for its thresholds to be calibrated
against real work rather than left as derived guesses, and
``SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md`` names scale roles (S0-S4) and a
screen-print-first colour discipline without ever dimensioning either. This
measures what the corpus actually does, per design tradition, so those numbers
come from evidence instead of assertion.

Deterministic: no model, no network. Same corpus in, same numbers out.

What it measures per image, and the honest limits of each:

* **garment colour** -- the median colour of the garment region, found by
  segmentation rather than sampled from a fixed crop.
* **print colour count** -- distinct colours in the print region after
  quantisation. A proxy for ink count, and an over-count on photographic or
  heavily distressed prints, which is itself worth knowing.
* **print coverage** -- share of the garment the print covers. The measurable
  half of what the constitution calls scale role.
* **placement** -- centroid of the print, as thirds *of the garment*, not of the
  frame. Distinguishes a chest hit from a full front without reading the copy.
* **value polarity** -- whether the print is lighter or darker than the garment.

None of these read the *design*. They read its physical parameters, which is
the half a machine can measure honestly.

**How the garment is found, and why it is not a fixed box.** This used to crop a
fixed rectangle out of the resized image and call it the torso. That produced
three failures, each caught by painting the mask back over the photograph:
a plain worn tee scored 31% coverage because the crop read fold shadows as ink;
a CCS tee with a graphic across the chest scored zero because the crop began 35%
down the frame and the print sat at 28%; and a white print on a black tee scored
zero because it tripped the cut-off that removes skin and background.

So the garment is located instead of assumed:

1. the backdrop colour comes from the four corners -- the border ring runs
   through the model on a worn shot, and on a graduated backdrop its median is a
   colour that appears nowhere;
2. the subject is what differs from the backdrop, largest connected region;
3. the garment is the part of the subject matching the fabric colour once
   *brightness is divided out* -- a fold is the fabric colour times a scalar, so
   levelling collapses it, while ink keeps its own hue;
4. the print is what the garment encloses. Filling holes finds it. A white print
   inside a black tee is a hole like any other, which is what fixes the third
   failure; a bare arm across the chest runs out to the frame edge, stays
   connected to the exterior, and is never filled.

**What it refuses.** Worn full-body photography is not measurable this way and
the attempt was abandoned on evidence, not taste: across every fabric tolerance
from 34 to 90, a plain worn tee scored 0.152 to 0.057 while a worn tee with a
real chest print scored 0.128 to 0.100. The two never separate. Rather than
infer the photography per image -- tried, and a tan bikini top reads 95% "skin"
-- each source records what it shoots in ``brand.json``'s ``photography`` field,
and worn sources are skipped and counted rather than quietly averaged in.

Fine line work sits at the floor: a one-pixel-stroke chest drawing measures
around 0.05% ink at any resolution, which is real but below anything that can be
told from noise. It is reported as no detectable print.

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
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_tiers import is_excluded

CORPUS_ROOT = Path(__file__).resolve().parent.parent / "var" / "design_corpus"
REPORT_PATH = CORPUS_ROOT / "design_patterns.json"

# Analysis resolution. Raised from 256, where a small chest mark measured 0.6%
# and measures 0.8% here; large enough to keep a print's shape meaningful, small
# enough that the whole corpus finishes in about a minute.
ANALYSIS_SIZE = 384

LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

# How far from the backdrop colour a pixel must sit to be part of the subject.
# Raw distance, deliberately: levelling is for telling a fold from a print, and
# against a backdrop it is actively wrong -- rescaling a black tee to a white
# ground's brightness makes the two look alike, and a black tee on white
# segmented as 8% garment when this was levelled.
BACKGROUND_DISTANCE = 42.0

# How far a pixel may sit from the garment colour, once brightness is divided
# out, and still be the same fabric. Swept from 34 to 90 against real worn and
# flat photography; 34 is where flat-lay prints measure truest.
GARMENT_CHROMA = 34.0

# Quantisation level for the ink count. Screen printing works in flat spot
# colours, so near-identical shades are one ink.
COLOUR_BUCKETS = 6

# A print region smaller than this share of the garment is a seam, a care label
# or a button, not a graphic.
MIN_PRINT_COVERAGE = 0.002

# A graphic sits inboard of the silhouette. Beyond this the region is against the
# garment's edge and reads as the shaded side of it rather than as ink.
CENTRE_BAND = (0.22, 0.78)

# One region covering more than half the garment is not a chest graphic.
MAX_SINGLE_REGION = 0.50

# Brightness ratios no fold reaches, used to catch a print that has no hue for
# the chroma test to find -- black ink on a grey tee, which levelling otherwise
# rescales into the fabric and loses.
#
# This test was tried once before segmentation existed and had to be abandoned:
# without a garment mask it caught the backdrop and the model, and a plain worn
# tee measured 15% ink. Inside a located garment it is safe, because everything
# that is not fabric or ink has already gone.
TONAL_LOW = 0.45
TONAL_HIGH = 1.80

# How much of the subject may be something other than the garment before the
# frame is refused. On a flat-lay the garment *is* the subject and this sits at
# 0.00 to 0.07; a body wearing it puts a head, arms and legs in frame and it runs
# 0.18 to 0.92. Measured across both, which is how the "US shops shoot flat"
# assumption was caught being only mostly true -- the surf shops mix worn shots
# in, and a per-source declaration cannot see that. A two-tone garment can trip
# this and be refused; refusing a measurable frame is the cheap mistake.
MAX_SUBJECT_OUTSIDE_GARMENT = 0.18


def _levelled(pixels: np.ndarray, colour: np.ndarray) -> np.ndarray:
    """Distance to ``colour`` with brightness divided out.

    A fold is the fabric colour times a scalar -- same hue, less light -- so
    rescaling every pixel to the reference brightness collapses drape to nothing.
    Ink has a hue of its own and survives. This is the whole reason a plain worn
    tee no longer measures 31% coverage.
    """
    reference = float(colour @ LUMA)
    luma = pixels @ LUMA
    scaled = pixels * (reference / np.clip(luma, 1.0, None))[..., None]
    return np.sqrt(((scaled - colour) ** 2).sum(axis=-1))


def _analyse(path: Path) -> dict[str, Any] | None:
    """Measure one product image, or say why it could not be measured.

    Returns ``None`` only when the file will not open. Everything else comes back
    as a dict, carrying either measurements or a ``refused`` reason -- a refusal
    is an answer, and one that can be counted.
    """
    try:
        image = (
            Image.open(path).convert("RGB").resize((ANALYSIS_SIZE, ANALYSIS_SIZE), Image.LANCZOS)
        )
    except Exception:
        return None

    pixels = np.asarray(image, dtype=np.float32)
    edge = ANALYSIS_SIZE // 13

    # Corners, not the border ring. The ring runs through the model on a worn
    # shot, and across a graduated backdrop its median is a colour that appears
    # nowhere in the frame.
    corner = np.concatenate(
        [
            pixels[:edge, :edge].reshape(-1, 3),
            pixels[:edge, -edge:].reshape(-1, 3),
            pixels[-edge:, :edge].reshape(-1, 3),
            pixels[-edge:, -edge:].reshape(-1, 3),
        ]
    )
    ground = np.median(corner, axis=0)

    subject = np.sqrt(((pixels - ground) ** 2).sum(axis=2)) > BACKGROUND_DISTANCE
    if subject.sum() < ANALYSIS_SIZE * 2:
        return {"refused": "no subject", "detail": "nothing stands out from the backdrop"}
    labels, count = ndimage.label(subject)
    if count > 1:
        sizes = ndimage.sum(subject, labels, range(1, count + 1))
        subject = labels == (int(np.argmax(sizes)) + 1)

    # The fabric colour, from a ring just inside the silhouette rather than from
    # the middle of the garment.
    #
    # Sampling the middle is the obvious thing and it inverts on a large front
    # print: the median of a band the graphic fills *is* the graphic, after which
    # the fabric measures as ink and the ink as fabric. A print covering a
    # quarter of the garment measured zero that way. Shoulders, sleeves and side
    # seams are the parts a print does not reach, so the fabric is read there.
    depth = ndimage.distance_transform_edt(subject)
    assert depth is not None
    deepest = float(depth.max())
    ring = subject & (depth > 1.5) & (depth < max(deepest * 0.22, 3.0))
    if ring.sum() < 100:
        ring = subject
    if ring.sum() < 100:
        return {"refused": "no torso band", "detail": "the subject has no measurable middle"}
    garment_colour = np.median(pixels[ring], axis=0)

    # Fabric is what matches the garment in hue once brightness is divided out,
    # and is not far brighter or darker than any fold could account for. The
    # second half is what keeps a black print on a grey tee: it has no hue of its
    # own, so the chroma test alone rescales it into the fabric and loses it.
    fabric_luma = max(float(garment_colour @ LUMA), 1.0)
    ratio = (pixels @ LUMA) / fabric_luma
    tonal = (ratio < TONAL_LOW) | (ratio > TONAL_HIGH)
    garment = subject & (_levelled(pixels, garment_colour) < GARMENT_CHROMA) & ~tonal
    labels, count = ndimage.label(garment)
    if count == 0:
        return {"refused": "no garment region", "detail": "no dominant fabric colour"}
    sizes = ndimage.sum(garment, labels, range(1, count + 1))
    garment = labels == (int(np.argmax(sizes)) + 1)

    # A print is a region the garment encloses, so filling holes finds it. This
    # is what recovers a light print on a dark garment: it is a hole like any
    # other, where the old distance cut-off threw it out with the background.
    solid = ndimage.binary_fill_holes(garment)
    assert solid is not None
    print_mask = solid & ~garment
    garment_area = int(solid.sum())

    # If much of what stands out from the backdrop is not the garment, something
    # is wearing it, and every earlier attempt to measure that honestly failed.
    outside = float((subject & ~solid).sum() / max(int(subject.sum()), 1))
    if outside > MAX_SUBJECT_OUTSIDE_GARMENT:
        return {
            "refused": "not a garment-only frame",
            "detail": f"{outside:.0%} of the subject is not the garment",
        }

    # Deliberately not filtered by region size, though it is the obvious next
    # move: seams, buttons, drawstrings and the weave of a straw hat all come
    # through as small holes and inflate coverage a little. Dropping components
    # under 0.02% of the garment cleans those up and takes 39% of a lettering
    # print with them -- "KCDC BROOKLYN" is twelve separate letter-shaped
    # regions, each individually small. A filter that quietly under-measures
    # typographic work is the wrong trade for a brand whose graphics are mostly
    # words. Measured before rejecting: at 0.0002 the plain control goes 0.0002
    # to 0.0000 while the lettering goes 0.0153 to 0.0094.
    if garment_area < ANALYSIS_SIZE * 4:
        return {"refused": "garment too small", "detail": "garment fills too little of the frame"}

    coverage = float(print_mask.sum() / garment_area)
    result: dict[str, Any] = {
        "garment_rgb": [round(float(v)) for v in garment_colour],
        "ground_rgb": [round(float(v)) for v in ground],
        "print_coverage": round(coverage, 4),
        "has_print": coverage >= MIN_PRINT_COVERAGE,
    }
    if not result["has_print"]:
        return result

    garment_rows, garment_cols = np.nonzero(solid)
    g_top = garment_rows.min()
    g_height = max(garment_rows.max() - g_top, 1)
    g_left = garment_cols.min()
    g_width = max(garment_cols.max() - g_left, 1)
    print_rows, print_cols = np.nonzero(print_mask)
    centroid_x = float((print_cols.mean() - g_left) / g_width)
    centroid_y = float((print_rows.mean() - g_top) / g_height)

    # Does the answer look like a graphic? A shadow is a long region against one
    # edge; a print is compact and inboard.
    if not (CENTRE_BAND[0] <= centroid_x <= CENTRE_BAND[1]):
        result["refused"] = "edge shading"
        result["detail"] = f"region sits {centroid_x:.0%} across the garment"
        return result
    parts, part_count = ndimage.label(print_mask)
    if part_count:
        biggest = float(ndimage.sum(print_mask, parts, range(1, part_count + 1)).max())
        if biggest / garment_area > MAX_SINGLE_REGION:
            result["refused"] = "region too large"
            result["detail"] = f"one region covers {biggest / garment_area:.0%} of the garment"
            return result

    ink = pixels[print_mask]
    step = 256 / COLOUR_BUCKETS
    quantised = (ink // step).astype(np.int16)
    keyed = quantised[:, 0] * COLOUR_BUCKETS**2 + quantised[:, 1] * COLOUR_BUCKETS + quantised[:, 2]
    counts = np.unique(keyed, return_counts=True)[1]

    garment_luma = float(garment_colour @ LUMA)
    ink_luma = float(ink.mean(axis=0) @ LUMA)
    result.update(
        {
            # Colours holding less than 5% of the ink are edge antialiasing.
            "ink_colours": int((counts / len(keyed) >= 0.05).sum()),
            "centroid_x": round(centroid_x, 3),
            "centroid_y": round(centroid_y, 3),
            "garment_luma": round(garment_luma, 1),
            "ink_luma": round(ink_luma, 1),
            "light_on_dark": ink_luma > garment_luma,
        }
    )
    return result


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
    # Counted, never silently dropped. A corpus that says what it could not read
    # is worth more than one that quietly averages its own mistakes in.
    skipped_worn: dict[str, int] = {}
    refusals: dict[str, int] = {}
    seen = 0
    for brand_dir in sorted(CORPUS_ROOT.iterdir()):
        if is_excluded(brand_dir.name):
            continue
        brand_file = brand_dir / "brand.json"
        if not brand_file.is_file():
            continue
        brand = json.loads(brand_file.read_text(encoding="utf-8"))
        tradition = brand.get("design_tradition", "unknown")

        # Worn full-body photography is not measurable here, and the source says
        # which it is rather than the pixels being asked to confess it.
        if brand.get("photography", "flat") == "worn":
            products = brand_dir / "products"
            skipped_worn[brand_dir.name] = len(list(products.iterdir())) if products.is_dir() else 0
            continue

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
                refusals["unreadable file"] = refusals.get("unreadable file", 0) + 1
                continue
            if "refused" in result:
                refusals[result["refused"]] = refusals.get(result["refused"], 0) + 1
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
        "skipped_worn_photography": skipped_worn,
        "refused": dict(sorted(refusals.items(), key=lambda kv: -kv[1])),
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
    print(f"\n{len(records)} designs analysed, {len(printed)} with a detectable print")
    if skipped_worn:
        named = ", ".join(f"{k} ({v})" for k, v in sorted(skipped_worn.items()))
        print(f"{sum(skipped_worn.values())} skipped, worn photography: {named}")
    if refusals:
        print(f"{sum(refusals.values())} refused by the measurement:")
        for reason, n in report["refused"].items():
            print(f"    {n:>5}  {reason}")
    print()
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
