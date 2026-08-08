#!/usr/bin/env python3
"""Collect flat artwork, where the design is the product rather than a photo of one.

`collect_design_corpus.py` gathers brand product photographs, and everything
measured from them is an inference: a model in a room wearing a printed shirt,
where a collar, a shoulder seam, a fold and the photograph's own halftone all
clear an ink threshold tuned for print. Half the bands the miner finds on those
frames are garment edges.

Print-on-demand marketplaces publish the design itself -- flat, isolated,
usually on white or transparent -- because there the design *is* the product.
The same measurement becomes direct instead of inferred.

The trade-off is register and it is real: this is a different design population
to Stussy or WTAPS and weaker on average. It is collected as a *separate*
source, tagged `flat_artwork`, and never merged blind. What we want from it is
placement and combination -- how a design is arranged -- and whether that agrees
with what the brand corpus says is the question worth answering before either is
trusted further.

    python scripts/collect_flat_artwork.py --source teepublic --limit 200
    python scripts/collect_flat_artwork.py --list

Written to `var/design_corpus_flat/`, mirroring the layout in
DESIGN_CORPUS_SCHEMA.md so the same miner can read either.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "var" / "design_corpus_flat"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# One request per source at a time, with a gap. This is research collection off
# public listing pages, not a mirror: sampling is the point, and a corpus is not
# worth being rude for.
REQUEST_DELAY = 1.5

# Enough to measure layout at. The originals are large and we are recording
# proportions, not reproducing artwork.
TARGET_WIDTH = 900


class Source:
    """One marketplace, and how to read a design out of it."""

    def __init__(self, slug: str, name: str, search: str, note: str) -> None:
        self.slug = slug
        self.name = name
        self.search = search
        self.note = note


SOURCES: dict[str, Source] = {
    "teepublic": Source(
        "teepublic",
        "TeePublic",
        "https://www.teepublic.com/t-shirts?query={query}&page={page}",
        "Designs listed as flat artwork; garment is a rendered mock behind it.",
    ),
    "threadless": Source(
        "threadless",
        "Threadless",
        "https://www.threadless.com/search?q={query}&page={page}",
        "Artist marketplace; designs shown flat on the listing.",
    ),
    "redbubble": Source(
        "redbubble",
        "Redbubble",
        "https://www.redbubble.com/shop/{query}+t-shirts?page={page}",
        "Largest volume; listings render the design isolated.",
    ),
}

# What to sample. Broad and neutral on purpose -- these are queries about the
# kind of garment, not about subject matter, because subject is the one thing
# this corpus must not be allowed to teach us.
QUERIES = (
    "graphic tee",
    "vintage tee",
    "typography shirt",
    "skate shirt",
    "streetwear",
)

IMAGE_URL = re.compile(r'https://[^"\'\s]+?\.(?:jpg|jpeg|png)(?:\?[^"\'\s]*)?', re.IGNORECASE)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _fetch(url: str, timeout: int = 25) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _looks_like_artwork(url: str) -> bool:
    """Filter obvious furniture out of a page's image URLs.

    Marketplace pages carry avatars, badges, sprites and payment logos in the
    same markup as the designs. Cheap to exclude by name, and anything that slips
    through is caught later by the flat-on-white check the miner already does.
    """
    lowered = url.lower()
    if any(
        junk in lowered
        for junk in ("avatar", "logo", "icon", "sprite", "badge", "banner", "flag", "payment")
    ):
        return False
    return any(hint in lowered for hint in ("design", "artwork", "preview", "image", "product"))


def collect(source: Source, limit: int) -> dict[str, Any]:
    """Sample one marketplace. Returns what was taken and what refused."""
    brand_dir = OUT / source.slug
    (brand_dir / "products").mkdir(parents=True, exist_ok=True)
    (brand_dir / "brand.json").write_text(
        json.dumps(
            {
                "brand_slug": source.slug,
                "brand_name": source.name,
                "site_url": source.search.split("/shop")[0].split("/t-shirts")[0],
                "acquired_at": _now(),
                # Not a design tradition. This corpus is a source of layout
                # evidence and explicitly not of register -- see the module
                # docstring, and POSITIONING.md on why the two are different.
                "design_tradition": "flat_artwork",
                "notes": source.note,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    taken = 0
    seen: set[str] = set()
    refusals: list[str] = []

    for query in QUERIES:
        if taken >= limit:
            break
        for page in (1, 2, 3):
            if taken >= limit:
                break
            url = source.search.format(query=urllib.parse.quote_plus(query), page=page)
            try:
                markup = _fetch(url).decode("utf-8", "replace")
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as error:
                refusals.append(f"{url}: {type(error).__name__}")
                continue

            candidates = [
                u for u in dict.fromkeys(IMAGE_URL.findall(markup)) if _looks_like_artwork(u)
            ]
            for image_url in candidates:
                if taken >= limit:
                    break
                key = hashlib.sha256(image_url.encode()).hexdigest()[:16]
                if key in seen:
                    continue
                seen.add(key)

                try:
                    data = _fetch(image_url)
                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
                    continue
                if len(data) < 8000:
                    # A thumbnail or a spacer, not a design worth measuring.
                    continue

                product_dir = brand_dir / "products" / key
                product_dir.mkdir(parents=True, exist_ok=True)
                extension = ".png" if image_url.lower().split("?")[0].endswith(".png") else ".jpg"
                (product_dir / f"image-01{extension}").write_bytes(data)
                (product_dir / "product.json").write_text(
                    json.dumps(
                        {
                            "product_id": f"{source.slug}/{key}",
                            "brand_slug": source.slug,
                            "name": query,
                            "source_url": url,
                            "category": "tee",
                            "price": "",
                            "description": "",
                            "images": [f"image-01{extension}"],
                            "acquired_at": _now(),
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                (product_dir / "provenance.json").write_text(
                    json.dumps(
                        [
                            {
                                "provenance_id": f"{source.slug}/{key}/image-01",
                                "source_id": f"{source.slug}/{key}",
                                "acquired_at": _now(),
                                "acquisition_method": "marketplace_listing",
                                "content_hash": f"sha256:{hashlib.sha256(data).hexdigest()}",
                                "byte_size": len(data),
                                "content_type": "image/png"
                                if extension == ".png"
                                else "image/jpeg",
                                "source_url": image_url,
                            }
                        ],
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                taken += 1
                time.sleep(REQUEST_DELAY)
            time.sleep(REQUEST_DELAY)

    return {"source": source.slug, "taken": taken, "refusals": refusals}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(SOURCES), help="which marketplace")
    parser.add_argument("--limit", type=int, default=150, help="designs to take")
    parser.add_argument("--list", action="store_true", help="show the sources and stop")
    args = parser.parse_args(argv[1:])

    if args.list or not args.source:
        for source in SOURCES.values():
            print(f"{source.slug:<12} {source.name:<14} {source.note}")
        return 0

    result = collect(SOURCES[args.source], args.limit)
    print(f"{result['source']}: {result['taken']} designs")
    for refusal in result["refusals"][:5]:
        print(f"  refused {refusal}")
    if not result["taken"]:
        print(
            "\nNothing collected. These listings are rendered client-side, so a plain\n"
            "fetch sees a shell with no design URLs in it -- collect_majors_browser.mjs\n"
            "exists for exactly that case and is the next thing to point at this.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
