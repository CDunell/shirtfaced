#!/usr/bin/env python3
"""Where the print sits on the garment, learned from mockups rather than photographs.

Everything the corpus knows about arrangement so far is composition *inside* a
print area: what an element looks like relative to the other elements of the same
design. It knows nothing about placement, because it was measured off product
photographs where the print area itself had to be inferred around a collar, a
fold and a shadow. Every template it produced is centred, centre_x 0.49 to 0.51 --
not because designs are always centred, but because a centred guess is what
falls out of a torso crop.

Placement is the question the engine actually has to answer. Given a phrase and
an image, it decides pocket or chest or full-front, left or centred, and at what
scale, for every garment type. There has been no evidence to decide it from.

A garment mockup supplies it directly. Cotton Bureau renders the design onto a
blank garment on a transparent background, so:

  - the garment's exact extent is the alpha channel, not an estimate;
  - the garment's colour is known, because it is most of what is inside;
  - what differs from that colour, inside the silhouette, is the print.

Measurements are shares of the *garment's* bounding box, never the image's, so a
pocket print reads as a small mark high and left whatever canvas it arrived on.

    python scripts/mine_placement.py
    python scripts/mine_placement.py --overlay 12

`--overlay` writes annotated images to var/preview/placement/ so the detected
print box can be looked at. Five separate errors in this corpus were caught by
rendering rather than by a number, and one of them was a checker that drew every
circle as a lens.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_tiers import is_excluded  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FLAT_ROOT = ROOT / "var" / "design_corpus_flat"
REPORT_PATH = ROOT / "var" / "design_corpus" / "placement.json"
OVERLAY_DIR = ROOT / "var" / "preview" / "placement"

ANALYSIS_SIZE = 320

# Sources that render a design onto a blank garment on transparency. Only these
# can be read for placement -- a flat artwork file has no garment to place on,
# and a photograph has no alpha to read the garment from.
MOCKUP_TRADITION = "garment_mockup"

# How far to pull in from the garment's edge before looking for print.
#
# A mockup's silhouette carries a darker rim -- the render's own edge shading,
# plus hem and sleeve seams -- and every one of those differs from the garment's
# body colour by more than any sane ink threshold. Left in, they ring the whole
# outline and swamp the print. Two percent of the garment's width clears the rim
# without reaching any placement a design would actually use; a pocket print sits
# nowhere near the edge.
EDGE_EROSION = 0.02

# How far a pixel must sit from the garment's own colour to count as print.
INK_DISTANCE = 60.0

# Below this share of the garment, what was found is speckle -- render noise or
# a fabric texture -- rather than a print.
MIN_PRINT_SHARE = 0.002

# Marks are merged across this many pixels before being grouped, so the letters
# of a word become one cluster rather than twelve.
MERGE_DILATION = 3

# A cluster must hold this share of the largest cluster's ink to be part of the
# design.
#
# The first version kept anything above 2% and half the boxes ran to the hem.
# The mask showed why: a draped mockup creases across the lower body, and those
# fold shadows clear any sane ink threshold. Contrast does not separate them --
# a fold came back at 118 against the print's 149 -- but size does, decisively.
# Measured on three garments the print cluster held 7x, 7x and 95x the ink of
# the next thing down, with folds sitting at y 0.78-0.95 and Cotton Bureau's own
# neck label at y 0.06-0.13.
#
# The cost is real and worth stating: a genuine second element smaller than a
# quarter of the main print -- a small word at the hem under a large chest
# graphic -- is dropped from the box. That is the better error. Keeping it means
# every fold in the corpus reads as part of the design, which is what the
# overlays showed.
DOMINANT_SHARE = 0.25


def _garment_and_print(path: Path) -> tuple[np.ndarray, np.ndarray] | None:
    """The garment silhouette and the print on it, as boolean masks."""
    try:
        image = Image.open(path).convert("RGBA")
    except Exception:
        return None
    image = image.resize((ANALYSIS_SIZE, ANALYSIS_SIZE), Image.LANCZOS)
    pixels = np.asarray(image, dtype=np.float32)

    garment = pixels[:, :, 3] > 128
    if garment.mean() < 0.05:
        return None

    # Pull in from the outline before reading colour or ink.
    erode = max(1, int(ANALYSIS_SIZE * EDGE_EROSION))
    body = ndimage.binary_erosion(garment, iterations=erode)
    if body.sum() < 100:
        return None

    rgb = pixels[:, :, :3]
    # The garment is most of what is inside it, so its colour is the median --
    # robust to a print covering a third of the body in a way a mean is not.
    colour = np.median(rgb[body], axis=0)
    ink = (np.sqrt(((rgb - colour) ** 2).sum(axis=2)) > INK_DISTANCE) & body
    return garment, ink


def _print_box(ink: np.ndarray) -> tuple[int, int, int, int, int] | None:
    """Bounding box of the print, with fold shadows and the neck label excluded."""
    # Merge first, so a word is one cluster and not one per letter -- otherwise
    # the largest "blob" is a single fat letter and everything else falls under
    # the share threshold.
    merged = ndimage.binary_dilation(ink, iterations=MERGE_DILATION)
    labelled, count = ndimage.label(merged)
    if count == 0:
        return None

    # Score clusters by the ink they actually contain, not by their dilated area.
    sizes = ndimage.sum(ink, labelled, range(1, count + 1))
    if not sizes.size or sizes.max() <= 0:
        return None
    keep = sizes >= sizes.max() * DOMINANT_SHARE
    kept = np.isin(labelled, np.flatnonzero(keep) + 1) & ink

    rows = np.where(kept.any(axis=1))[0]
    cols = np.where(kept.any(axis=0))[0]
    if not rows.size or not cols.size:
        return None
    return int(rows[0]), int(rows[-1]), int(cols[0]), int(cols[-1]), int(keep.sum())


def analyse(path: Path) -> dict[str, float] | None:
    """Placement of the print, as shares of the garment's bounding box."""
    found = _garment_and_print(path)
    if found is None:
        return None
    garment, ink = found

    if ink.sum() / max(1, garment.sum()) < MIN_PRINT_SHARE:
        return None

    g_rows = np.where(garment.any(axis=1))[0]
    g_cols = np.where(garment.any(axis=0))[0]
    g_top, g_bottom = int(g_rows[0]), int(g_rows[-1])
    g_left, g_right = int(g_cols[0]), int(g_cols[-1])
    g_height = max(1, g_bottom - g_top + 1)
    g_width = max(1, g_right - g_left + 1)

    box = _print_box(ink)
    if box is None:
        return None
    top, bottom, left, right, clusters = box

    return {
        # All relative to the garment, never the image.
        "top": round((top - g_top) / g_height, 4),
        "height": round((bottom - top + 1) / g_height, 4),
        "left": round((left - g_left) / g_width, 4),
        "width": round((right - left + 1) / g_width, 4),
        "centre_x": round(((left + right) / 2 - g_left) / g_width, 4),
        "centre_y": round(((top + bottom) / 2 - g_top) / g_height, 4),
        "coverage": round(float(ink.sum()) / float(garment.sum()), 4),
        # How many clusters the box had to span. One is a clean read. More than
        # one means either a genuine multi-part design or a fold shadow that
        # survived the share test, and nothing here can tell those apart --
        # contrast, density, vertical position and template-stacking were all
        # tried and none separates them. Recorded so a consumer can weight or
        # exclude the uncertain ones rather than being handed a number that
        # looks as solid as the rest.
        "clusters": clusters,
    }


def _overlay(path: Path, out: Path) -> bool:
    """Draw the detected garment box and print box, so they can be checked."""
    found = _garment_and_print(path)
    if found is None:
        return False
    garment, ink = found
    box = _print_box(ink)
    if box is None:
        return False

    image = Image.open(path).convert("RGBA").resize((ANALYSIS_SIZE, ANALYSIS_SIZE), Image.LANCZOS)
    flat = Image.new("RGBA", image.size, (255, 255, 255, 255))
    flat.alpha_composite(image)
    canvas = flat.convert("RGB")
    draw = ImageDraw.Draw(canvas)

    g_rows = np.where(garment.any(axis=1))[0]
    g_cols = np.where(garment.any(axis=0))[0]
    draw.rectangle(
        [int(g_cols[0]), int(g_rows[0]), int(g_cols[-1]), int(g_rows[-1])],
        outline=(0, 140, 255),
        width=2,
    )
    top, bottom, left, right, _ = box
    draw.rectangle([left, top, right, bottom], outline=(255, 0, 90), width=2)

    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return True


def _placement_name(record: dict[str, float]) -> str:
    """A human name for where this sits, so the output can be read at a glance."""
    centre_x, top, width = record["centre_x"], record["top"], record["width"]
    off_centre = abs(centre_x - 0.5) > 0.12
    if width > 0.7:
        return "full front"
    if width > 0.45:
        return "chest, broad"
    if off_centre and top < 0.45:
        return "left chest" if centre_x < 0.5 else "right chest"
    if top < 0.30:
        return "high centre"
    return "chest, small" if width < 0.3 else "chest, centred"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overlay", type=int, default=0, help="write N annotated images")
    args = parser.parse_args(argv[1:])

    # FLAT_ROOT's garment_mockup brand is Cotton Bureau, on the excluded list
    # (see corpus_tiers.py) -- a marketplace, not a curated brand. Excluding it
    # here is expected to leave this script with nothing, not a bug. It cannot
    # simply be pointed at real brands' photography instead: `_garment_and_print`
    # locates the garment from the image's own alpha channel, which cutout
    # mockup renders have and photographed product shots generally do not.
    records: list[dict[str, Any]] = []
    refused = 0
    for brand_dir in sorted(FLAT_ROOT.iterdir()) if FLAT_ROOT.is_dir() else []:
        if is_excluded(brand_dir.name):
            continue
        brand_file = brand_dir / "brand.json"
        if not brand_file.is_file():
            continue
        brand = json.loads(brand_file.read_text(encoding="utf-8"))
        if brand.get("design_tradition") != MOCKUP_TRADITION:
            continue
        products = brand_dir / "products"
        if not products.is_dir():
            continue
        for product_dir in sorted(products.iterdir()):
            product_file = product_dir / "product.json"
            if not product_file.is_file():
                continue
            product = json.loads(product_file.read_text(encoding="utf-8"))
            category = product.get("category") or "unknown"
            for name in product.get("images") or []:
                measured = analyse(product_dir / name)
                if measured is None:
                    refused += 1
                    continue
                records.append(
                    {
                        "brand": brand.get("brand_slug", brand_dir.name),
                        "product": product_dir.name,
                        "category": category,
                        "placement": _placement_name(measured),
                        **measured,
                    }
                )

    if not records:
        print(
            f"No garment mockups found under {FLAT_ROOT}.\n"
            "Collect a source tagged garment_mockup first:\n"
            "  node scripts/collect_majors_browser.mjs --flat cottonbureau",
            file=sys.stderr,
        )
        return 1

    print(f"\n{len(records)} placements measured, {refused} refused\n")

    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_category[record["category"]].append(record)

    for category, rows in sorted(by_category.items(), key=lambda kv: -len(kv[1])):
        print(f"{category}  ({len(rows)})")
        for field in ("top", "height", "width", "centre_x", "coverage"):
            values = sorted(r[field] for r in rows)
            median = values[len(values) // 2]
            print(f"    {field:<9} median {median:.3f}   range {values[0]:.3f} to {values[-1]:.3f}")
        for name, count in Counter(r["placement"] for r in rows).most_common():
            print(f"      {count:>3}  {name}")
        print()

    if args.overlay:
        written = 0
        for record in records[: args.overlay]:
            source = FLAT_ROOT / record["brand"] / "products" / record["product"]
            images = list(source.glob("image-*"))
            if images and _overlay(images[0], OVERLAY_DIR / f"{record['product'][:40]}.png"):
                written += 1
        print(f"{written} overlays written to {OVERLAY_DIR}")

    REPORT_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"written to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
