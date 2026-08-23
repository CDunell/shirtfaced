#!/usr/bin/env python3
"""Extract complete creature-only sources from supplied legacy lockups."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def first_ink_run(alpha: np.ndarray, threshold: int = 32) -> tuple[int, int]:
    active = (alpha >= threshold).any(axis=1)
    start = None
    for y, present in enumerate(active):
        if present and start is None:
            start = y
        elif not present and start is not None:
            return start, y - 1
    if start is None:
        raise ValueError("No artwork found")
    return start, len(active) - 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Directory containing {slug}-logo.png files")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    count = 0
    for path in sorted(args.source.glob("*-logo.png")):
        slug = path.name.removesuffix("-logo.png")
        image = Image.open(path).convert("RGBA")
        alpha = np.asarray(image)[:, :, 3]
        top, bottom = first_ink_run(alpha)
        ys, xs = np.where(alpha[top : bottom + 1] >= 32)
        left, right = int(xs.min()), int(xs.max())
        top += int(ys.min())
        bottom = top + int(ys.max() - ys.min())
        padding = 12
        box = (
            max(0, left - padding), max(0, top - padding),
            min(image.width, right + padding + 1), min(image.height, bottom + padding + 1),
        )
        image.crop(box).save(args.output / f"{slug}.png")
        count += 1
    print(f"Extracted {count} complete creature sources to {args.output}")


if __name__ == "__main__":
    main()
