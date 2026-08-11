#!/usr/bin/env python3
"""The deterministic structure of a design: what repeats, not what it depicts.

What a design shows is subjective and none of this engine's business. How it is
put together is not: symmetry, containment, alignment, ink count, how the mass
sits in its field. Those are countable, and the top brands have already voted on
which of them ship by putting them in their catalogues over and over.

So no taste is required and none is used. The only question asked is which
structures repeat often enough to be a signal rather than a coincidence.

`mine_design_structure.py` slices a design into horizontal bands, which answers
"how many things, stacked how". That is too coarse to arrange from -- it cannot
tell an arch from a block, a circle badge from a box rule, justified type from
centred. This measures the properties that distinguish them:

  symmetry      how closely the left half mirrors the right
  containment   whether a closed outline rings the design -- badge, crest, frame
  alignment     whether element edges line up left, right, both, or neither
  inks          how many distinct ink values the design uses
  fill          how much of its own bounding box the ink occupies
  aspect        the proportion of that box
  arch          whether the top edge of the mass curves rather than running flat

    python scripts/mine_arrangement.py
    python scripts/mine_arrangement.py --source flat

Reads the collected corpora, writes var/design_corpus/arrangement.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_tiers import is_excluded  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FLAT_ROOT = ROOT / "var" / "design_corpus_flat"
REPORT_PATH = ROOT / "var" / "design_corpus" / "arrangement.json"

SIZE = 256

# Sources whose frames are the artwork itself, and nothing else.
#
# `garment_mockup` was in this set and had to come out. A mockup is a design
# composited onto a blank garment, so measuring its shape measures the *tee* --
# and a tee silhouette mirrors almost perfectly. It scored 94.9% near-symmetric
# against real artwork's 15.8%, and averaging the two reported 58.7% symmetry
# for the corpus, which inverted the actual finding: symmetric construction is
# the minority, about one design in six.
#
# Mockups can be read for arrangement, but only after cropping to the print box
# that mine_placement.py already computes. Until that join exists they stay out
# rather than quietly doubling the corpus with garment outlines.
ARTWORK_TRADITIONS = {"flat_artwork", "flat_artwork_normalised"}

# Distance from the field colour before a pixel counts as ink.
INK_DISTANCE = 60.0

# Ink must cover at least this much of the frame to be a design rather than dust.
MIN_COVER = 0.004


def _ink_mask(path: Path) -> np.ndarray | None:
    """The design's ink, against whatever field it was published on."""
    try:
        opened = Image.open(path)
        opened.load()
    except Exception:
        return None

    if opened.mode in ("RGBA", "LA") or "transparency" in opened.info:
        alpha = opened.convert("RGBA").getchannel("A").resize((SIZE, SIZE), Image.LANCZOS)
        mask = np.asarray(alpha, dtype=np.float32) > 128
        if MIN_COVER < mask.mean() < 0.98:
            return mask

    try:
        image = opened.convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    except Exception:
        return None
    pixels = np.asarray(image, dtype=np.float32)
    edge = max(3, SIZE // 40)
    border = np.concatenate(
        [
            pixels[:edge].reshape(-1, 3),
            pixels[-edge:].reshape(-1, 3),
            pixels[:, :edge].reshape(-1, 3),
            pixels[:, -edge:].reshape(-1, 3),
        ]
    )
    if border.std(axis=0).mean() > 24:
        return None
    field = np.median(border, axis=0)
    mask = np.sqrt(((pixels - field) ** 2).sum(axis=2)) > INK_DISTANCE
    return mask if mask.mean() > MIN_COVER else None


def _crop(mask: np.ndarray) -> np.ndarray | None:
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if not rows.size or not cols.size:
        return None
    return mask[rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1]


def _symmetry(box: np.ndarray) -> float:
    """How much of the ink survives being mirrored left to right.

    A badge, a crest, an arch over a block: all near-symmetric. A design that
    reads left to right is not. This is the single cheapest signal separating
    the two, and it needs no idea of what is depicted.
    """
    flipped = box[:, ::-1]
    union = (box | flipped).sum()
    return round(float((box & flipped).sum() / union), 4) if union else 0.0


def _containment(box: np.ndarray) -> float:
    """How much of the design's own bounding box its filled outline covers.

    A ring, a crest or a frame encloses its contents, so filling the holes adds
    a great deal. Loose type adds almost nothing. This is what separates a badge
    from a stack without needing to recognise either.
    """
    filled = ndimage.binary_fill_holes(box)
    if not filled.any():
        return 0.0
    return round(float((filled.sum() - box.sum()) / filled.sum()), 4)


def _alignment(box: np.ndarray) -> str:
    """Whether the rows of ink share a left edge, a right edge, both, or neither."""
    lefts, rights = [], []
    for row in box:
        cols = np.where(row)[0]
        if cols.size:
            lefts.append(cols[0])
            rights.append(cols[-1])
    if len(lefts) < 8:
        return "unknown"
    width = box.shape[1] or 1
    left_tight = float(np.std(lefts)) / width < 0.06
    right_tight = float(np.std(rights)) / width < 0.06
    if left_tight and right_tight:
        return "justified"
    if left_tight:
        return "left"
    if right_tight:
        return "right"
    return "centred"


def _arch(box: np.ndarray) -> bool:
    """Whether the mass's top edge curves rather than running flat.

    An arched word is one of the most repeated devices in this whole corpus and
    band-slicing cannot see it at all: an arch and a flat line occupy the same
    band. The top edge of the ink is higher in the middle than at the shoulders.
    """
    tops = []
    for column in box.T:
        rows = np.where(column)[0]
        tops.append(rows[0] if rows.size else np.nan)
    tops = np.array(tops, dtype=float)
    if np.isnan(tops).mean() > 0.4:
        return False
    third = max(1, len(tops) // 3)
    middle = np.nanmean(tops[third : 2 * third])
    shoulders = np.nanmean(np.concatenate([tops[:third], tops[-third:]]))
    if np.isnan(middle) or np.isnan(shoulders):
        return False
    # Middle sitting higher than the shoulders by a real fraction of the height.
    return bool((shoulders - middle) > box.shape[0] * 0.08)


def _inks(path: Path, mask: np.ndarray) -> int:
    """How many distinct ink values the design uses, coarsely quantised."""
    try:
        image = Image.open(path).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    except Exception:
        return 0
    pixels = np.asarray(image, dtype=np.uint8)[mask]
    if not pixels.size:
        return 0
    quantised = (pixels // 48).astype(np.int16)
    keys = quantised[:, 0] * 36 + quantised[:, 1] * 6 + quantised[:, 2]
    counts = Counter(keys.tolist())
    total = sum(counts.values())
    # An ink has to hold a real share; below that it is antialiasing or texture.
    return sum(1 for _, n in counts.items() if n / total > 0.04)


def measure(path: Path) -> dict[str, Any] | None:
    mask = _ink_mask(path)
    if mask is None:
        return None
    box = _crop(mask)
    if box is None or box.size == 0 or min(box.shape) < 16:
        return None
    return {
        "symmetry": _symmetry(box),
        "containment": _containment(box),
        "alignment": _alignment(box),
        "arch": _arch(box),
        "inks": _inks(path, mask),
        "fill": round(float(box.mean()), 4),
        "aspect": round(float(box.shape[1] / box.shape[0]), 4),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args(argv[1:])

    # FLAT_ROOT's ARTWORK_TRADITIONS brands are exactly the six excluded
    # marketplace slugs -- excluding them here is expected to leave this
    # script with nothing, not a bug to work around. Real brands' photography
    # isn't cropped to the print box yet (mine_placement.py does that
    # separately), so mixing it in here would measure garment-outline
    # symmetry and call it design arrangement -- the exact mistake this
    # exclusion pass exists to stop making. Report the shortfall rather than
    # papering over it with data the measurement was never built to read.
    records: list[dict[str, Any]] = []
    for brand_dir in sorted(FLAT_ROOT.iterdir()) if FLAT_ROOT.is_dir() else []:
        if is_excluded(brand_dir.name):
            continue
        brand_file = brand_dir / "brand.json"
        if not brand_file.is_file():
            continue
        brand = json.loads(brand_file.read_text(encoding="utf-8-sig"))
        if brand.get("design_tradition") not in ARTWORK_TRADITIONS:
            continue
        products = brand_dir / "products"
        if not products.is_dir():
            continue
        for product_dir in sorted(products.iterdir()):
            product_file = product_dir / "product.json"
            if not product_file.is_file():
                continue
            product = json.loads(product_file.read_text(encoding="utf-8-sig"))
            for name in (product.get("images") or [])[:1]:
                measured = measure(product_dir / name)
                if measured:
                    # The source file travels with the measurement. Without it a
                    # finding cannot be traced back to a design, so nothing it
                    # says can be checked by looking -- which is the only check
                    # that has reliably caught anything in this corpus.
                    records.append(
                        {
                            "brand": brand_dir.name,
                            "product": product_dir.name,
                            "image": str((product_dir / name).relative_to(FLAT_ROOT)),
                            "tradition": brand.get("design_tradition", ""),
                            "price": product.get("price", ""),
                            "category": product.get("category", ""),
                            **measured,
                        }
                    )
            if args.limit and len(records) >= args.limit:
                break
        if args.limit and len(records) >= args.limit:
            break

    if not records:
        print(
            f"No artwork found under {FLAT_ROOT} once excluded brands are removed. "
            "That is the whole of what this script has ever measured -- see "
            "corpus_tiers.py. It needs real, flat (non-mockup) artwork from "
            "curated brands before it can produce anything again.",
            file=sys.stderr,
        )
        return 1

    total = len(records)
    print(f"\n{total} designs measured for arrangement structure\n")

    def share(label: str, n: int) -> None:
        print(f"   {n:>5}  {n / total:>5.1%}  {label}")

    print("symmetry (left half mirrors right)")
    share("near-symmetric  (>0.80)", sum(1 for r in records if r["symmetry"] > 0.80))
    share("part-symmetric  (0.60-0.80)", sum(1 for r in records if 0.60 < r["symmetry"] <= 0.80))
    share("asymmetric      (<0.60)", sum(1 for r in records if r["symmetry"] <= 0.60))

    print("\ncontainment (a closed outline rings the design)")
    share("enclosed  badge/crest/frame (>0.35)", sum(1 for r in records if r["containment"] > 0.35))
    part = sum(1 for r in records if 0.15 < r["containment"] <= 0.35)
    share("part-enclosed        (0.15-0.35)", part)
    share("open                     (<0.15)", sum(1 for r in records if r["containment"] <= 0.15))

    print("\nalignment of ink rows")
    for label, n in Counter(r["alignment"] for r in records).most_common():
        share(label, n)

    print("\narched top edge")
    share("arched", sum(1 for r in records if r["arch"]))
    share("flat", sum(1 for r in records if not r["arch"]))

    print("\ninks used")
    for n_inks, n in sorted(Counter(r["inks"] for r in records).items()):
        share(f"{n_inks} ink" + ("s" if n_inks != 1 else ""), n)

    print("\nproportion of the design's own box")
    for label, lo, hi in [
        ("tall   (aspect < 0.8)", 0.0, 0.8),
        ("square (0.8 - 1.25)", 0.8, 1.25),
        ("wide   (> 1.25)", 1.25, 99.0),
    ]:
        share(label, sum(1 for r in records if lo <= r["aspect"] < hi))

    REPORT_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"\nwritten to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
