#!/usr/bin/env python3
"""Is there a design on this surface, or is the garment bare?

Two earlier measurements disagreed by a factor of ten -- 1,221 frames bare (3%)
against 10,630 (32%) -- and both were wrong in different ways.

The first read the whole frame, so the studio backdrop counted as ground and any
garment on it looked inked. The second read inside the located garment box,
which is right, but used a fixed threshold that finds nothing on black and then
lumped "no print here" together with "print too small to read". Those are
opposite facts: one says the surface is empty, the other says it is printed and
the photograph is inadequate.

This measures one thing only: **ink on the garment**. Inside the garment box,
against the garment's own colour taken from its flanks, with a threshold scaled
to how much that colour already varies -- because a black tee under studio light
separates from its print by far less than a white one does.

Frames too small or too odd to judge are reported separately and never counted
as bare.

    python scripts/measure_bare.py
    python scripts/measure_bare.py --sample 40   # write a contact sheet to check by eye

The number is only worth having if the sheet shows bare garments on one side and
printed ones on the other, so --sample exists to make that checkable.

## This does not work, and the sample sheet is why

Run against 40,070 frames it reported 8.7% bare, and roughly fifteen of twenty
sampled "bare" frames were plainly printed: an all-over camo sweater, a hoodie
with a Mario graphic, two full-width back prints, a cap with a printed name, and
several pieces of flat artwork with no garment in them at all.

The cause is structural rather than a bad threshold. The garment's colour is
sampled from its flanks, so any design reaching the flanks *becomes* the
reference colour and everything then matches it. All-over prints, full-width
back prints and flat artwork all fail this way by construction.

Three measurements have now been attempted -- 3%, 32%, 8.7% -- all using colour
distance from a sampled ground, each breaking somewhere different. The
instrument is wrong, not the calibration.

What separates a printed garment from a blank one is **edge density**: a print
has boundaries, plain jersey does not, and camo has plenty. That needs no
knowledge of the garment's colour, which is the assumption that has failed every
time.

Kept so the next attempt starts from the failure rather than repeating it.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.garment_frame import ANALYSIS_SIZE, locate_garment

ROOT = Path(__file__).resolve().parent.parent
CORPORA = (ROOT / "var" / "design_corpus", ROOT / "var" / "design_corpus_flat")
OUT = ROOT / "var" / "preview"

# Ink share of the garment below which the surface is bare. A woven neck label
# or a care tag can clear a hair over zero, so this sits above nothing-at-all
# without reaching a genuine chest mark, which runs an order higher.
BARE_SHARE = 0.006

# Multiplier on the garment's own colour spread. Below the floor a smooth white
# tee would call its own shadows ink; the floor is what stops that.
THRESHOLD_FACTOR = 2.6
THRESHOLD_FLOOR = 34.0

# Pull in from the silhouette before reading anything: the outline carries edge
# shading, hem and sleeve seams, and every one of them clears any ink threshold.
EDGE_EROSION = 3


def ink_share(path: Path) -> float | None:
    """Share of the garment carrying ink, or None if the frame cannot be judged."""
    try:
        located = locate_garment(path)
        image = Image.open(path)
        image.load()
    except Exception:
        return None

    box = located.bounds or located.torso
    if box is None:
        return None
    top, bottom, left, right = box
    scale_x = image.width / ANALYSIS_SIZE
    scale_y = image.height / ANALYSIS_SIZE
    garment = image.convert("RGB").crop(
        (
            int(left * scale_x),
            int(top * scale_y),
            int(right * scale_x),
            int(bottom * scale_y),
        )
    )
    if min(garment.size) < 60:
        return None

    pixels = np.asarray(garment.resize((200, 200), Image.LANCZOS), dtype=np.float32)
    mask = np.ones((200, 200), dtype=bool)
    mask[:EDGE_EROSION] = mask[-EDGE_EROSION:] = False
    mask[:, :EDGE_EROSION] = mask[:, -EDGE_EROSION:] = False

    margin = max(6, 200 // 6)
    flanks = np.concatenate([pixels[:, :margin].reshape(-1, 3), pixels[:, -margin:].reshape(-1, 3)])
    colour = np.median(flanks, axis=0)
    spread = float(np.median(np.abs(flanks - colour).sum(axis=1)))
    threshold = max(THRESHOLD_FLOOR, spread * THRESHOLD_FACTOR)

    distance = np.sqrt(((pixels - colour) ** 2).sum(axis=2))
    return float(((distance > threshold) & mask).mean())


def frames() -> list[Path]:
    out: list[Path] = []
    for root in CORPORA:
        if not root.is_dir():
            continue
        for brand_dir in sorted(root.iterdir()):
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
                out.extend(product_dir / n for n in (product.get("images") or []))
    return out


def _sheet(paths: list[Path], title: str, out: Path) -> None:
    cell = 300
    cols = 5
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell + 26), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 6), title, fill=(180, 0, 0))
    for index, path in enumerate(paths):
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
        image.thumbnail((cell - 12, cell - 12), Image.LANCZOS)
        x = (index % cols) * cell
        y = (index // cols) * cell + 26
        sheet.paste(image, (x + (cell - image.width) // 2, y + (cell - image.height) // 2))
    sheet.save(out)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args(argv[1:])

    paths = frames()
    if args.limit:
        paths = paths[: args.limit]
    print(f"\njudging {len(paths)} frames...")

    bare: list[Path] = []
    printed: list[Path] = []
    unjudgeable: list[Path] = []
    for index, path in enumerate(paths):
        if index and index % 4000 == 0:
            print(f"  {index}...")
        share = ink_share(path)
        if share is None:
            unjudgeable.append(path)
        elif share < BARE_SHARE:
            bare.append(path)
        else:
            printed.append(path)

    total = len(paths) or 1
    print(f"\n{len(paths)} frames")
    print(f"  {len(printed):>6}  carry ink on the garment  ({len(printed) / total:.1%})")
    print(f"  {len(bare):>6}  bare                       ({len(bare) / total:.1%})")
    print(f"  {len(unjudgeable):>6}  cannot be judged           ({len(unjudgeable) / total:.1%})")

    if args.sample:
        random.seed(11)
        half = max(1, args.sample // 2)
        _sheet(random.sample(bare, min(half, len(bare))), "called BARE", OUT / "bare_check.png")
        _sheet(
            random.sample(printed, min(half, len(printed))),
            "called PRINTED",
            OUT / "printed_check.png",
        )
        print(f"\nwrote {OUT / 'bare_check.png'} and {OUT / 'printed_check.png'} -- look at them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
