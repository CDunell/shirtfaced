#!/usr/bin/env python3
"""Contact sheets for the visual pass, one cell per product.

The unit is the product, not the frame. 40,070 frames across the two corpora
represent 11,206 products -- 3.6 frames each, all of one design seen front,
back, flat and on a model. A design earns one description; its other frames say
which zones are used and are consulted rather than each earning a paragraph.

Two things this fixes.

Nine per sheet at 2000x2000, which is 640px per product. That was measured, not
guessed: at 250px construction values came out wrong (a crest recorded as a
circular badge, a distressed print recorded as flat) and no text was legible; at
356px type and zone survived but text did not; at 640px text is legible at S2
and above. An earlier six-up was built at 1500x1000 and gave 500px, so it was
paying for six cells and getting less than nine.

And the frame is chosen by the store's own shot_hint -- flat, then detail, then
close-up, then front -- which has been recorded in every provenance file since
collection and went unread for months.

    python scripts/product_sheet.py 1
    python scripts/product_sheet.py 1 --through 40
    python scripts/product_sheet.py --count

Writes var/preview/psheet/sheet-NNNN.png and .json. Deterministic ordering, so
sheet 400 holds the same products on every run and a row traces back to a cell.

Ranking a frame means locating the garment in it, measured at 50ms, and there
are 40,070 of them -- 34 minutes to walk the corpus. That ran on every
invocation, because the area cache lived in memory and died with the process, so
building forty sheets one at a time cost twenty-two hours of re-deciding facts
that had not changed. The ranking is now written to catalogue.json and read back;
`--rebuild` is how it gets redone after the corpus grows.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.garment_frame import locate_garment

ROOT = Path(__file__).resolve().parent.parent
CORPORA = {
    "brand": ROOT / "var" / "design_corpus",
    "flat": ROOT / "var" / "design_corpus_flat",
}
OUT = ROOT / "var" / "preview" / "psheet"
CATALOGUE = OUT / "catalogue.json"

PER_SHEET = 9
COLS = 3
CELL = 666

# The store's own labels, best first. A print crop beats a torso crop beats a
# whole body.
#
# Only 1,675 of 11,206 products carry a label, so for 85% of the corpus the
# fallback decides which frame gets read -- and the fallback was filename order.
# That is how a rash guard was described from its back, recorded as blank, and
# had to be corrected when its front turned up two frames later.
#
# `subject_area` is the fix and costs nothing new: locate_garment already
# computes how much of a frame the garment fills, and the frame filling most of
# the picture is the closest look at the print. The same signal the structure
# miner uses.
HINT_RANK = {
    "flat": 0,
    "detail": 1,
    "close-up": 2,
    "front": 3,
    "back": 5,
    "worn": 6,
    "full-body": 7,
}


def _hints(product_dir: Path) -> dict[str, str]:
    provenance = product_dir / "provenance.json"
    if not provenance.is_file():
        return {}
    try:
        records = json.loads(provenance.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[str, str] = {}
    for record in records:
        stem = str(record.get("provenance_id", "")).rsplit("/", 1)[-1]
        hint = str(record.get("shot_hint", ""))
        for suffix in (".jpg", ".png", ".webp", ".jpeg"):
            out[f"{stem}{suffix}"] = hint
    return out


_AREA_CACHE: dict[Path, float] = {}


def _subject_area(path: Path) -> float:
    """How much of the frame the garment fills. Cached -- this is the slow part."""
    if path not in _AREA_CACHE:
        try:
            _AREA_CACHE[path] = float(locate_garment(path).subject_area)
        except Exception:
            _AREA_CACHE[path] = 0.0
    return _AREA_CACHE[path]


def catalogue(rebuild: bool = False) -> list[dict[str, Any]]:
    """Every product, frames ranked. Read from disk unless asked to rebuild."""
    if not rebuild and CATALOGUE.is_file():
        try:
            return json.loads(CATALOGUE.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            pass  # Corrupt or half-written: fall through and earn it again.
    return _walk()


def _walk() -> list[dict[str, Any]]:
    """The 34-minute pass. Called once, then cached."""
    rows: list[dict[str, Any]] = []
    for corpus, root in CORPORA.items():
        if not root.is_dir():
            continue
        for brand_dir in sorted(root.iterdir()):
            brand_file = brand_dir / "brand.json"
            if not brand_file.is_file():
                continue
            try:
                brand = json.loads(brand_file.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue
            products = brand_dir / "products"
            if not products.is_dir():
                continue
            for product_dir in sorted(products.iterdir()):
                product_file = product_dir / "product.json"
                if not product_file.is_file():
                    continue
                try:
                    product = json.loads(product_file.read_text(encoding="utf-8-sig"))
                except (OSError, json.JSONDecodeError):
                    continue
                images = product.get("images") or []
                if not images:
                    continue
                hints = _hints(product_dir)
                ranked = sorted(
                    images,
                    key=lambda n: (
                        HINT_RANK.get(hints.get(n, ""), 4),
                        -_subject_area(product_dir / n),
                        n,
                    ),
                )
                rows.append(
                    {
                        "corpus": corpus,
                        "brand": brand_dir.name,
                        "product": product_dir.name,
                        "name": product.get("name", ""),
                        "tradition": brand.get("design_tradition", ""),
                        "category": product.get("category", ""),
                        "price": str(product.get("price", "")),
                        "source_url": product.get("source_url", ""),
                        # Every frame, best first. The sheet shows the first;
                        # the rest are there to be opened when one is not enough.
                        # Forward slashes always. These get copied straight into
                        # a row's `image` field, and a describer on Windows would
                        # otherwise paste backslashes into a path the rest of the
                        # pipeline writes with slashes.
                        "frames": [
                            (product_dir / n).relative_to(root.parent).as_posix() for n in ranked
                        ],
                        "hints": [hints.get(n, "") for n in ranked],
                    }
                )
    return rows


def build(sheet_no: int, per_sheet: int, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    start = (sheet_no - 1) * per_sheet
    if start >= len(rows):
        return None
    chunk = rows[start : start + per_sheet]

    grid_rows = (len(chunk) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * CELL, grid_rows * CELL), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)

    for index, row in enumerate(chunk):
        path = ROOT / "var" / row["frames"][0]
        try:
            image = Image.open(path)
            image.load()
        except Exception:
            continue
        if image.mode in ("RGBA", "LA") or "transparency" in image.info:
            flat = Image.new("RGBA", image.size, (255, 255, 255, 255))
            flat.alpha_composite(image.convert("RGBA"))
            image = flat
        image = image.convert("RGB")
        image.thumbnail((CELL - 26, CELL - 26), Image.LANCZOS)
        x = (index % COLS) * CELL
        y = (index // COLS) * CELL
        sheet.paste(
            image, (x + (CELL - image.width) // 2, y + 24 + (CELL - 24 - image.height) // 2)
        )
        draw.rectangle([x, y, x + CELL - 1, y + CELL - 1], outline=(215, 215, 215))
        draw.rectangle([x, y, x + 46, y + 22], fill=(20, 20, 20))
        draw.text((x + 16, y + 6), str(start + index + 1), fill=(255, 255, 255))
        row["cell"] = start + index + 1

    OUT.mkdir(parents=True, exist_ok=True)
    stem = f"sheet-{sheet_no:04d}"
    sheet.save(OUT / f"{stem}.png")
    (OUT / f"{stem}.json").write_text(json.dumps(chunk, indent=1), encoding="utf-8")
    return {
        "sheet": sheet_no,
        "of": (len(rows) + per_sheet - 1) // per_sheet,
        "products": len(chunk),
        "px_each": CELL - 26,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sheet", type=int, nargs="?", default=1)
    parser.add_argument("--per-sheet", type=int, default=PER_SHEET)
    parser.add_argument("--count", action="store_true")
    parser.add_argument("--through", type=int, default=0, help="build a range, one catalogue read")
    parser.add_argument(
        "--rebuild", action="store_true", help="re-rank frames after the corpus grows"
    )
    args = parser.parse_args(argv[1:])

    if args.rebuild or not CATALOGUE.is_file():
        print("ranking every frame -- about 34 minutes, then cached...", file=sys.stderr)
        rows = _walk()
        OUT.mkdir(parents=True, exist_ok=True)
        CATALOGUE.write_text(json.dumps(rows), encoding="utf-8")
        print(f"wrote {CATALOGUE}", file=sys.stderr)
    else:
        rows = catalogue()

    if args.count:
        frames = sum(len(r["frames"]) for r in rows)
        labelled = sum(1 for r in rows if r["hints"] and r["hints"][0])
        print(f"{len(rows)} products, {frames} frames")
        print(f"{labelled} products have a labelled best frame")
        print(f"{(len(rows) + args.per_sheet - 1) // args.per_sheet} sheets at {args.per_sheet}-up")
        return 0

    for sheet_no in range(args.sheet, max(args.through, args.sheet) + 1):
        built = build(sheet_no, args.per_sheet, rows)
        if built is None:
            print("past the end", file=sys.stderr)
            return 1 if sheet_no == args.sheet else 0
        print(json.dumps(built), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
