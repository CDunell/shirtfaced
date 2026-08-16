#!/usr/bin/env python3
"""Derive immutable 9:16 coverage frames from an approved scene master.

No generation occurs here. Every coverage frame is an original-pixel crop of the
master, locked by source SHA256 and recorded in a manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--scene", required=True)
    parser.add_argument("--shot", required=True)
    parser.add_argument("--x", type=int, required=True)
    parser.add_argument("--y", type=int, default=0)
    parser.add_argument("--height", type=int, default=0, help="0 = full source height")
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    source = Path(args.source).resolve()
    if not source.is_file():
        raise SystemExit(f"missing source: {source}")
    actual = sha256(source)
    if actual != args.expected_sha256:
        raise SystemExit(f"source SHA mismatch: expected {args.expected_sha256}, got {actual}")

    with Image.open(source) as image:
        image.load()
        sw, sh = image.size
        crop_h = args.height or sh
        crop_w = round(crop_h * 9 / 16)
        if crop_w * 16 != crop_h * 9:
            # Preserve exact pixels and exact 9:16 by reducing height to the nearest
            # multiple that gives an integer width. Never resize the master.
            crop_h = (crop_h // 16) * 16
            crop_w = crop_h * 9 // 16
        x0, y0 = args.x, args.y
        x1, y1 = x0 + crop_w, y0 + crop_h
        if x0 < 0 or y0 < 0 or x1 > sw or y1 > sh:
            raise SystemExit(
                f"crop outside source: source={sw}x{sh}, crop=({x0},{y0})-({x1},{y1})"
            )
        crop = image.crop((x0, y0, x1, y1))
        if crop.size != (crop_w, crop_h):
            raise SystemExit("unexpected crop dimensions")

        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        out_dir = Path(args.out_root).resolve() / args.scene / "coverage" / args.shot
        out_dir.mkdir(parents=True, exist_ok=True)
        frame = out_dir / "frame.png"
        crop.save(frame, format="PNG")

    manifest = {
        "scene": args.scene,
        "shot": args.shot,
        "generated_at": stamp,
        "operation": "original_pixels_crop_only",
        "source_path": str(source),
        "source_sha256": actual,
        "source_dimensions": [sw, sh],
        "crop_box": [x0, y0, x1, y1],
        "crop_dimensions": [crop_w, crop_h],
        "aspect_ratio": "9:16",
        "frame_sha256": sha256(frame),
        "resized": False,
        "provider_called": False,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"FRAME={frame}")
    print(f"MANIFEST={out_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
