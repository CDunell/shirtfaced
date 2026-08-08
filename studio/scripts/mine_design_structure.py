"""Learning composition, not just quantity, from the corpus.

Aggregate statistics -- median coverage, median ink count -- describe how much of
a garment a design uses. They say nothing about *arrangement*, which is the
actual question when someone hands you a phrase, a photo and a logo and asks
where each one goes.

This reads the vertical structure of every printed design: the print is split
into horizontal bands of ink separated by clear garment, and each band's
position, height and width is recorded. That recovers the stack -- an arched
word over an image over a small line of type is three bands with characteristic
proportions, and it is a different composition from one centred emblem even when
both cover the same area.

Those stacks are then grouped by band count, so the question "what do three
elements usually look like" has an answer drawn from thousands of designs
rather than from taste.

    python scripts/mine_design_structure.py
    python scripts/mine_design_structure.py --limit 300
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.garment_frame import locate_garment

CORPUS_ROOT = Path(__file__).resolve().parent.parent / "var" / "design_corpus"
REPORT_PATH = CORPUS_ROOT / "design_structure.json"
# Per-design records, so templates can be clustered rather than averaged.
RAW_PATH = CORPUS_ROOT / "design_structure_raw.json"

ANALYSIS_SIZE = 256

GARMENT_WORDS = re.compile(
    r"\b(tee|t-?shirts?|hoodie|sweat ?shirt|crew ?neck|jumper|cap|hat|beanie|"
    r"long ?sleeve|pullover|sweater|oversized|crop|shirt|stubby|holder|koozie)\b",
    re.IGNORECASE,
)

# A row counts as carrying ink when this share of it is print. Below it the row
# is garment with a stray antialiased pixel, and treating that as an element
# would split every design into noise.
ROW_INK_THRESHOLD = 0.14

# Bands closer together than this (as a share of torso height) are one element
# whose interior has a gap -- the counter of an O, the space between two lines
# of the same word -- not two elements.
MERGE_GAP = 0.02

# A band shorter than this is a stray highlight, not a design element.
MIN_BAND_HEIGHT = 0.035

# A garment edge, not a print. A collar, a hem, a shoulder shadow and the curve
# under a sleeve all clear the ink threshold, run the width of the torso, are
# thin, and are one smooth unbroken shape. Real full-width type is also thin and
# also spans the torso -- and breaks into letters, so its largest piece holds
# almost none of the ink.
#
# Calibrated against forty-five bands labelled by eye, with the measurements
# written in the same pass that drew them: it removes nine of the twenty-one
# garment edges in that sample and none of the twenty-four design elements.
#
# It does not catch the other noise class -- halftone photograph texture and
# dotted washes, which are low share rather than high -- so roughly half the
# contamination survives this.
EDGE_SHARE = 0.80
EDGE_MAX_HEIGHT = 0.18
EDGE_MIN_WIDTH = 0.70


def _flat_on_white(path: Path) -> bool:
    """Whether this frame is the garment alone on a plain studio field.

    Not a quality judgement: a photograph of a model in a room contains a face,
    hair, a background and a floor, and every one of them clears an ink
    threshold tuned for print. The same garment shot flat on white contains the
    garment.
    """
    try:
        image = Image.open(path).convert("RGB").resize((140, 140), Image.LANCZOS)
    except Exception:
        return False
    pixels = np.asarray(image, dtype=np.float32)
    border = np.concatenate(
        [
            pixels[:5].reshape(-1, 3),
            pixels[-5:].reshape(-1, 3),
            pixels[:, :5].reshape(-1, 3),
            pixels[:, -5:].reshape(-1, 3),
        ]
    )
    if border.std(axis=0).mean() >= 6 or border.mean() <= 232:
        return False
    inked = (np.abs(pixels - border.mean(axis=0)).sum(axis=2) > 90).mean()
    # An empty field and a frame filled edge to edge are both unusable.
    return 0.02 < inked < 0.55


def _garment_colour(centre: np.ndarray) -> np.ndarray:
    margin = max(4, centre.shape[1] // 6)
    flanks = np.concatenate(
        [centre[:, :margin, :].reshape(-1, 3), centre[:, -margin:, :].reshape(-1, 3)]
    )
    return np.median(flanks, axis=0)


def _components(block: np.ndarray) -> tuple[float, float]:
    """How the ink in a band is broken up, and how much sits in one piece.

    A line of type is many separate letters, so no single piece holds much of
    the ink. A mark or a photograph is one dominant shape with specks around it.
    That is a property of structure rather than of proportion, which matters
    because proportion is wrong exactly where it counts: heavy block type at
    image proportions reads as an image.

    Returns pieces per unit width, and the largest piece's share of the ink.
    The second is the one that carries -- the first also counts halftone speckle,
    which is why a photograph can come back with more pieces than a word.
    """
    if block.size == 0 or block.shape[1] < 2:
        return 0.0, 0.0
    labelled, count = ndimage.label(block)
    if count == 0:
        return 0.0, 0.0
    sizes = ndimage.sum(block, labelled, range(1, count + 1))
    total = float(sizes.sum()) or 1.0
    return round(count / block.shape[1], 4), round(float(sizes.max()) / total, 4)


def _transitions(block: np.ndarray) -> float:
    """Ink-to-gap changes across a typical row, normalised by width.

    What the geometry cannot say. A slot 0.89 wide by 0.49 tall is a mass and
    one 0.92 by 0.16 is a line of words, which works until heavy block type
    arrives at image proportions -- and then aspect calls it an image, and
    density does not separate them either: inside the ambiguous aspect band the
    density distribution is unimodal.

    Structure does separate them. Letters alternate ink and gap many times
    across a row; a photograph or a solid mark alternates a handful. Measured on
    the median row so one ragged edge cannot carry the number, and divided by
    the band's own width so it stays a ratio -- every other dimension here is
    dimensionless for the same reason.
    """
    if block.size == 0 or block.shape[1] < 2:
        return 0.0
    changes = np.abs(np.diff(block.astype(np.int8), axis=1)).sum(axis=1)
    return round(float(np.median(changes)) / block.shape[1], 4)


def _bands(mask: np.ndarray) -> list[dict[str, float]]:
    """Horizontal runs of ink, top to bottom, as fractions of the torso box."""
    height, width = mask.shape
    row_ink = mask.mean(axis=1)
    inked = row_ink > ROW_INK_THRESHOLD

    runs: list[tuple[int, int]] = []
    start: int | None = None
    for y, on in enumerate(inked):
        if on and start is None:
            start = y
        elif not on and start is not None:
            runs.append((start, y))
            start = None
    if start is not None:
        runs.append((start, height))

    merged: list[tuple[int, int]] = []
    for run in runs:
        if merged and (run[0] - merged[-1][1]) / height <= MERGE_GAP:
            merged[-1] = (merged[-1][0], run[1])
        else:
            merged.append(run)

    bands: list[dict[str, float]] = []
    for top, bottom in merged:
        if (bottom - top) / height < MIN_BAND_HEIGHT:
            continue
        block = mask[top:bottom, :]
        cols = np.nonzero(block.any(axis=0))[0]
        if cols.size == 0:
            continue
        inked = block[:, cols[0] : cols[-1] + 1]
        pieces, largest = _components(inked)
        band_height = (bottom - top) / height
        band_width = (cols[-1] - cols[0] + 1) / width
        if (
            largest >= EDGE_SHARE
            and band_height <= EDGE_MAX_HEIGHT
            and band_width >= EDGE_MIN_WIDTH
        ):
            continue
        bands.append(
            {
                "top": round(top / height, 3),
                "height": round((bottom - top) / height, 3),
                "width": round((cols[-1] - cols[0] + 1) / width, 3),
                "centre_x": round(float(cols.mean()) / width, 3),
                "density": round(float(block.mean()), 3),
                "transitions": _transitions(inked),
                "pieces": pieces,
                "largest_share": largest,
            }
        )
    return bands


def _analyse(path: Path) -> list[dict[str, float]] | None:
    # The torso is located per image rather than assumed. A fixed box lands on
    # the garment in a flat lay and on a model's face or the floor in a worn
    # shot, and the corpus holds both; a small left-breast print measured as
    # 93.8% "full front" that way. Frames where the garment cannot be located
    # confidently are refused here rather than measured wrongly.
    frame = locate_garment(path)
    if not frame.measurable:
        return None
    try:
        image = (
            Image.open(path).convert("RGB").resize((ANALYSIS_SIZE, ANALYSIS_SIZE), Image.LANCZOS)
        )
    except Exception:
        return None
    pixels = np.asarray(image, dtype=np.float32)
    rows, columns = frame.torso_slices()
    centre = pixels[rows, columns, :]
    garment = _garment_colour(centre)
    distance = np.sqrt(((centre - garment) ** 2).sum(axis=2))
    off_garment = distance > 180.0
    mask = (distance > 60.0) & ~off_garment
    if mask.sum() / max(int((~off_garment).sum()), 1) < 0.004:
        return None
    return _bands(mask)


def _shape_of(bands: list[dict[str, float]]) -> str:
    """A readable name for what this stack is doing.

    Named from the proportions rather than assumed: the corpus decides which
    shapes are common, this only labels them consistently.
    """
    count = len(bands)
    if count == 0:
        return "none"
    if count == 1:
        band = bands[0]
        if band["height"] > 0.55:
            return "single tall mass"
        if band["width"] < 0.45:
            return "single compact mark"
        return "single wide mass"
    tallest = max(range(count), key=lambda i: bands[i]["height"])
    if count == 2:
        return "lead above, support below" if tallest == 0 else "support above, lead below"
    if tallest == 0:
        return "lead on top, stacked support"
    if tallest == count - 1:
        return "stacked support, lead at base"
    return "framed centre — support above and below"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args(argv[1:])

    if not CORPUS_ROOT.is_dir():
        print("No corpus. Run scripts/collect_design_corpus.py first.", file=sys.stderr)
        return 2

    records: list[dict[str, Any]] = []
    seen = 0
    for brand_dir in sorted(CORPUS_ROOT.iterdir()):
        brand_file = brand_dir / "brand.json"
        if not brand_file.is_file():
            continue
        brand = json.loads(brand_file.read_text(encoding="utf-8"))
        tradition = brand.get("design_tradition", "unknown")
        products = brand_dir / "products"
        if not products.is_dir():
            continue
        for product_dir in sorted(products.iterdir()):
            product_file = product_dir / "product.json"
            if not product_file.is_file():
                continue
            product = json.loads(product_file.read_text(encoding="utf-8"))
            images = product.get("images") or []
            if not images:
                continue
            # Every frame that can be measured, not just the first.
            #
            # One frame per product was one photograph's opinion treated as the
            # product's structure: a fold across the chest, a shadow under a
            # sleeve or a hand in front of the print became an element of the
            # design. The corpus holds four to six shots per product precisely
            # so a measurable one is present.
            #
            # The frame yielding the fewest elements wins. Noise only ever adds
            # bands -- a shadow cannot hide a print -- so the cleanest reading of
            # the same garment is the one with least of it.
            # Flat studio frames first, where the product has one. Forty-three
            # per cent do, and on those the room, the model and their skin are
            # simply not in the picture -- which is most of what the band
            # extraction was fighting. What remains is the garment's own edges.
            flat = [name for name in images if _flat_on_white(product_dir / name)]
            frames = flat or list(images)

            readings = [
                found
                for name in frames
                if (found := _analyse(product_dir / name))
            ]
            if not readings:
                continue
            # The frame yielding fewest elements wins. Noise only ever adds
            # bands -- a shadow cannot hide a print -- so the cleanest reading of
            # the same garment is the one with least of it.
            bands = min(readings, key=len)
            words = [
                w
                for w in re.findall(
                    r"[A-Za-z0-9']+", GARMENT_WORDS.sub("", product.get("name", ""))
                )
                if len(w) > 1
            ]
            records.append(
                {
                    "tradition": tradition,
                    "words": len(words),
                    "elements": len(bands),
                    "shape": _shape_of(bands),
                    "bands": bands,
                }
            )
            seen += 1
            if seen % 400 == 0:
                print(f"  {seen} analysed...", flush=True)
            if args.limit and seen >= args.limit:
                break
        if args.limit and seen >= args.limit:
            break

    # Group by element count: "what does a three-element design look like" is the
    # question someone with a logo, a photo and a tagline is actually asking.
    by_count: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_count[record["elements"]].append(record)

    layouts: dict[str, Any] = {}
    for count, rows in sorted(by_count.items()):
        if count == 0 or len(rows) < 20:
            continue
        slots = []
        for index in range(count):
            slots.append(
                {
                    "slot": index + 1,
                    "top": round(statistics.median(r["bands"][index]["top"] for r in rows), 3),
                    "height": round(
                        statistics.median(r["bands"][index]["height"] for r in rows), 3
                    ),
                    "width": round(statistics.median(r["bands"][index]["width"] for r in rows), 3),
                    "centre_x": round(
                        statistics.median(r["bands"][index]["centre_x"] for r in rows), 3
                    ),
                }
            )
        layouts[str(count)] = {
            "designs": len(rows),
            "shapes": dict(Counter(r["shape"] for r in rows).most_common(4)),
            "slots": slots,
            "by_tradition": dict(Counter(r["tradition"] for r in rows).most_common(6)),
            "median_words": statistics.median(r["words"] for r in rows),
        }

    report = {
        "designs_analysed": len(records),
        "element_count_distribution": dict(sorted(Counter(r["elements"] for r in records).items())),
        "layouts": layouts,
        "shapes_overall": dict(Counter(r["shape"] for r in records).most_common(10)),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    RAW_PATH.write_text(json.dumps(records), encoding="utf-8")

    print(f"\n{len(records)} designs\n")
    print("elements per design:", report["element_count_distribution"])
    print("\ncommonest compositions:")
    for shape, n in list(report["shapes_overall"].items())[:6]:
        print(f"  {n:>5}  {shape}")
    print(f"\nwritten to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
