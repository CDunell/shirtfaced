#!/usr/bin/env python3
"""Rank every frame in the corpus by how much reference it actually carries.

33,052 images sit across the two corpora. Describing them in collection order
would spend the first several thousand rows on one band's back catalogue in
seven colourways, and a flat list gives no way to stop early with the useful
part done.

Nothing is thrown away for being cheap or ugly -- that judgement is not this
script's to make, and the register question is answered by the `tradition`
field, not by dropping frames. What is dropped is material that carries no
reference at all:

Every frame is queued and described. `state` says what is on the surface, which
is a fact about the design rather than about the reading:

  bare              no design on this surface. A blank back is how you know a
                    design is front-only.
  image_only        imagery, no text.
  text_only         type, no imagery.
  image_and_text    both.

An earlier version called low-resolution frames "unreadable" and dropped them
along with the bare ones. That was two mistakes at once: it threw away the
front-only signal, and it labelled a property of the picture as a property of
the design.

What remains is ordered so the most legible view of each distinct design comes
first: the store's own detail and flat shots, then whatever frame holds the
largest print.

    python scripts/visual_pass_queue.py --build
    python scripts/visual_pass_queue.py --stats

Writes var/design_corpus/visual_queue.json.
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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.garment_frame import ANALYSIS_SIZE, locate_garment

ROOT = Path(__file__).resolve().parent.parent
CORPORA = {
    "brand": ROOT / "var" / "design_corpus",
    "flat": ROOT / "var" / "design_corpus_flat",
}
QUEUE_PATH = ROOT / "var" / "design_corpus" / "visual_queue.json"

# How legible a print has to be before describing it is worth anything. Below
# this the crop is a smear and a description of it would be invention.
MIN_PRINT_PIXELS = 150

# Ink must hold this share of the located print area for a frame to carry a
# design at all. Under it the frame is a blank back or a placket.
MIN_INK_SHARE = 0.012

# Perceptual hash size for spotting the same artwork in another colourway.
HASH_SIZE = 12

# Frames the store itself labelled, best first.
HINT_RANK = {
    "flat": 0,
    "detail": 1,
    "close-up": 2,
    "front": 3,
    "back": 4,
    "worn": 6,
    "full-body": 7,
}


def _ink_box(path: Path) -> tuple[Image.Image, float] | None:
    """The printed area of a frame, and how much of it is ink."""
    try:
        located = locate_garment(path)
        image = Image.open(path).convert("RGB")
    except Exception:
        return None

    # Whole garment, not the torso. A print that bleeds past the torso box gets
    # sliced in half otherwise -- a wordmark cropped mid-letter was how this
    # first showed up.
    box = located.bounds or located.torso
    if box is None:
        return None
    top_a, bottom_a, left_a, right_a = box
    sx, sy = image.width / ANALYSIS_SIZE, image.height / ANALYSIS_SIZE
    garment = image.crop((int(left_a * sx), int(top_a * sy), int(right_a * sx), int(bottom_a * sy)))
    if garment.width < 40 or garment.height < 40:
        return None

    small = np.asarray(garment.resize((200, 200), Image.LANCZOS), dtype=np.float32)
    margin = max(5, small.shape[1] // 6)
    flanks = np.concatenate([small[:, :margin].reshape(-1, 3), small[:, -margin:].reshape(-1, 3)])
    colour = np.median(flanks, axis=0)
    spread = float(np.median(np.abs(flanks - colour).sum(axis=1)))
    # A dark garment photographed under studio light separates from its print by
    # far less than a white one. A fixed threshold finds nothing on black, which
    # is why a blank placket and a printed black tee looked identical.
    threshold = max(38.0, spread * 2.6)
    ink = np.sqrt(((small - colour) ** 2).sum(axis=2)) > threshold
    share = float(ink.mean())
    if share < MIN_INK_SHARE:
        # Bare surface. The caller needs to know this happened, not merely that
        # nothing came back -- a blank back is the front-only signal.
        return ("bare", None, share)

    rows = np.where(ink.any(axis=1))[0]
    cols = np.where(ink.any(axis=0))[0]
    if not rows.size or not cols.size:
        return None
    pad = 12
    y0, y1 = max(0, rows[0] - pad) / 200, min(200, rows[-1] + pad) / 200
    x0, x1 = max(0, cols[0] - pad) / 200, min(200, cols[-1] + pad) / 200
    crop = garment.crop(
        (
            int(x0 * garment.width),
            int(y0 * garment.height),
            int(x1 * garment.width),
            int(y1 * garment.height),
        )
    )
    # Content type is decided by looking, not here. This only reports that
    # something is printed and hands back the crop to be described.
    return ("printed", crop, share)


def _fingerprint(crop: Image.Image) -> str:
    """A hash of the artwork's shape, blind to garment colour.

    Colourways of one design differ in hue and barely in structure, so the hash
    is taken from a normalised greyscale gradient rather than from pixels.
    """
    grey = np.asarray(
        crop.convert("L").resize((HASH_SIZE + 1, HASH_SIZE), Image.LANCZOS), dtype=np.float32
    )
    bits = grey[:, 1:] > grey[:, :-1]
    return "".join("1" if b else "0" for b in bits.ravel())


def build() -> dict[str, Any]:
    seen: dict[str, str] = {}
    queue: list[dict[str, Any]] = []
    dropped: Counter[str] = Counter()

    for source, root in CORPORA.items():
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
            tradition = brand.get("design_tradition", "")
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
                hints = _hints(product_dir)
                for name in product.get("images") or []:
                    path = product_dir / name
                    found = _ink_box(path)
                    if found is None:
                        dropped["frame unusable"] += 1
                        continue
                    state, crop, share = found
                    hint = hints.get(name, "")
                    if crop is not None:
                        fingerprint = _fingerprint(crop)
                        # Recorded, never skipped. A colourway is still a frame
                        # that has to be looked at and described; the flag says
                        # the artwork has been seen before, and that is all.
                        row_duplicate = fingerprint in seen
                        seen.setdefault(fingerprint, str(path))
                    queue.append(
                        {
                            "source": source,
                            "brand": brand_dir.name,
                            "product": product_dir.name,
                            "image": name,
                            "tradition": tradition,
                            "category": product.get("category", ""),
                            "price": str(product.get("price", "")),
                            "name": product.get("name", ""),
                            "hint": hint,
                            "ink_share": round(share, 4),
                            "state": state,
                            "describe": True,
                            "duplicate_artwork": bool(locals().get("row_duplicate", False)),
                            "crop_px": min(crop.size) if crop is not None else 0,
                            "rank": (
                                HINT_RANK.get(hint, 5),
                                -(min(crop.size) if crop is not None else 0),
                            ),
                        }
                    )

    queue.sort(key=lambda r: (r["rank"][0], r["rank"][1]))
    for row in queue:
        row.pop("rank", None)
    return {"queue": queue, "dropped": dict(dropped)}


def _hints(product_dir: Path) -> dict[str, str]:
    provenance = product_dir / "provenance.json"
    if not provenance.is_file():
        return {}
    try:
        records = json.loads(provenance.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    out = {}
    for record in records:
        stem = str(record.get("provenance_id", "")).rsplit("/", 1)[-1]
        out[f"{stem}.jpg"] = str(record.get("shot_hint", ""))
        out[f"{stem}.png"] = str(record.get("shot_hint", ""))
        out[f"{stem}.webp"] = str(record.get("shot_hint", ""))
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args(argv[1:])

    if args.build:
        result = build()
        QUEUE_PATH.write_text(json.dumps(result, indent=1), encoding="utf-8")
        queue = result["queue"]
        print(f"\n{len(queue)} frames worth describing, {sum(result['dropped'].values())} dropped")
        for reason, n in result["dropped"].items():
            print(f"   {n:>6}  {reason}")
        print(f"\n   {(len(queue) + 5) // 6} sheets at 6 per sheet\n")
        for hint, n in Counter(r["hint"] or "(unlabelled)" for r in queue).most_common():
            print(f"   {n:>6}  {hint}")
        print()
        for trad, n in Counter(r["tradition"] for r in queue).most_common(10):
            print(f"   {n:>6}  {trad}")
        return 0

    if args.stats and QUEUE_PATH.exists():
        result = json.loads(QUEUE_PATH.read_text(encoding="utf-8-sig"))
        print(f"{len(result['queue'])} queued, dropped: {result['dropped']}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
