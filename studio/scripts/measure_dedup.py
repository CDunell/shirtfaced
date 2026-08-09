#!/usr/bin/env python3
"""How much of the corpus is the same design again, and how much is bare.

Two numbers decide the size of the visual pass, and both were guesses. 33,052
frames is the raw count; what matters is how many *distinct printed designs*
that represents. Colourways of one artwork need describing once, and a bare
back needs a line from code rather than a paragraph from a model.

An earlier fingerprint required an exact bit match and collapsed 2% of the
corpus, which was obviously wrong -- the same design shot at a slightly
different angle or exposure escaped it. This measures the real rate across a
range of hamming thresholds so the choice is made on evidence rather than on a
number that felt about right.

    python scripts/measure_dedup.py
    python scripts/measure_dedup.py --limit 4000

Writes nothing. Reports only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CORPORA = (ROOT / "var" / "design_corpus", ROOT / "var" / "design_corpus_flat")

# Perceptual hash side. 8 gives 64 bits, which is the usual choice for
# near-duplicate work and coarse enough to survive a re-shoot.
HASH_SIDE = 8

# A frame with less ink than this carries no design to describe.
BARE_INK = 0.012

THRESHOLDS = (0, 4, 8, 12, 16)


def _prepare(path: Path) -> tuple[int, float] | None:
    """Perceptual hash as an int, and how much of the frame is ink."""
    try:
        image = Image.open(path)
        image.load()
    except Exception:
        return None

    if image.mode in ("RGBA", "LA") or "transparency" in image.info:
        flat = Image.new("RGBA", image.size, (255, 255, 255, 255))
        flat.alpha_composite(image.convert("RGBA"))
        image = flat
    grey = image.convert("L")

    # Ink share against the frame's own border, which is the garment or the
    # studio field depending on the source. Coarse on purpose.
    small = np.asarray(grey.resize((64, 64), Image.LANCZOS), dtype=np.float32)
    border = np.concatenate(
        [small[:4].ravel(), small[-4:].ravel(), small[:, :4].ravel(), small[:, -4:].ravel()]
    )
    ink = float((np.abs(small - np.median(border)) > 34).mean())

    # dHash: horizontal gradient, tolerant of exposure and slight scale shifts.
    tiny = np.asarray(grey.resize((HASH_SIDE + 1, HASH_SIDE), Image.LANCZOS), dtype=np.float32)
    bits = (tiny[:, 1:] > tiny[:, :-1]).ravel()
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return value, ink


def _frames(limit: int) -> list[Path]:
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
                for name in product.get("images") or []:
                    out.append(product_dir / name)
                    if limit and len(out) >= limit:
                        return out
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args(argv[1:])

    frames = _frames(args.limit)
    print(f"\nreading {len(frames)} frames...")

    hashes: list[int] = []
    bare = 0
    unreadable = 0
    for index, path in enumerate(frames):
        if index and index % 2000 == 0:
            print(f"  {index}...")
        prepared = _prepare(path)
        if prepared is None:
            unreadable += 1
            continue
        value, ink = prepared
        if ink < BARE_INK:
            bare += 1
            continue
        hashes.append(value)

    print(f"\n{len(frames)} frames")
    print(f"  {unreadable:>6}  unreadable")
    print(f"  {bare:>6}  bare (no design to describe)")
    print(f"  {len(hashes):>6}  carry a design\n")

    # Greedy clustering at each threshold. O(n * clusters), which is fine
    # because clusters collapse fast.
    for threshold in THRESHOLDS:
        seeds: list[int] = []
        for value in hashes:
            for seed in seeds:
                if bin(value ^ seed).count("1") <= threshold:
                    break
            else:
                seeds.append(value)
        share = len(seeds) / max(1, len(hashes))
        sheets = (len(seeds) + 8) // 9
        print(
            f"  hamming <= {threshold:>2}: {len(seeds):>6} distinct "
            f"({share:>5.1%})   {sheets:>5} sheets at 9-up"
        )

    print()
    print("Threshold 0 is exact-match, which is what the earlier 2% figure used.")
    print("A colourway survives 0 and should not survive 8 or 12.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
