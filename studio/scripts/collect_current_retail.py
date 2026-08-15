"""Collect what is on the shelf right now, from City Beach.

Named by the owner on 15 August 2026: hundreds of modern t-shirt designs, as its
own tradition rather than folded into the vintage corpus. ``advise(tradition=...)``
exists precisely because a brewery prints differently from a skate brand and
averaging them produces a design belonging to neither; current retail and 1990s
archive stock are that same distance apart. So this writes ``current-retail`` and
nothing else touches it.

**Why a second collector rather than another row in ``collect_design_corpus.py``.**
That script reads Shopify's ``/products.json``. City Beach runs Salesforce
Commerce Cloud, so it has no such endpoint and the existing collector reports it
skipped -- which is what "add City Beach to BRANDS" would actually have achieved.
SFCC's storefront serves its own grid controller instead, and every product tile
in it carries two JSON attributes: ``data-gtmdata`` (id, brand, name, category,
price) and ``data-productdetails`` (the image URLs). Structured data, publicly
served, no rendered-markup guessing -- the same deterministic-script argument the
Shopify collector makes, against a different platform.

Everything downstream is unchanged: the schema is ``docs/DESIGN_CORPUS_SCHEMA.md``,
the miners walk directories and read ``brand.json`` for the tradition, and the
patterns deciding what counts as a graphic-led surface are imported from the
Shopify collector rather than restated here, so the two cannot drift.

**Read this before trusting a number measured off this corpus.**
``mine_design_patterns.py`` cannot measure these photographs, and the numbers it
produces from them are not evidence. Collection is sound -- real products, real
labels, real provenance -- but City Beach shoots every product worn, full body,
and ``_analyse`` was written for flat-lays and torso crops. Checked by painting
its print mask back over the image, three separate failures show up:

* **Drape reads as ink.** A plain beige tee scored 31% print coverage; the mask
  was the fold shadows down the front. The distance threshold that separates ink
  from fabric was set for flat garments, and a worn one shades past it.
* **The torso box does not fit this framing.** It is a fixed crop of the resized
  image. On these shots it lands under a chest print and over the model's arms,
  hair and the background behind the shoulder, all of which measure as ink.
* **A light print on a dark garment is discarded.** It sits far enough from the
  garment colour to trip the off-garment cut-off, which exists to remove skin and
  background, so a white print on a black tee measures as no print at all. A
  Formula 1 tee with a full-front graphic scored 0.3%.

The first is fixable by measuring hue rather than brightness -- rescaling each
pixel to the garment's own luminance collapses drape to nothing and was verified
to do so. The other two are not threshold work: they need the garment found in
the frame and the print found within it, rather than both assumed. Until that
exists, this corpus is a library of real reference images to look at, not a
source of medians. Nothing here is wired into ``advise()``; ``joined.json`` is
built only when somebody runs the joiner.

    python scripts/collect_current_retail.py                  # everything
    python scripts/collect_current_retail.py --limit 40       # a quick look
    python scripts/collect_current_retail.py --query t-shirt  # one surface
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from collect_design_corpus import (
    CORPUS_ROOT,
    IMAGE_WIDTH,
    REQUEST_DELAY,
    UNWANTED_PATTERN,
    WANTED_TYPE_PATTERN,
    _fetch,
    _now,
    write_manifest,
)

BRAND_SLUG = "city-beach"
BRAND_NAME = "City Beach"
SITE_URL = "https://www.citybeach.com/au"
TRADITION = "current-retail"

# The storefront's own grid controller. The site id is City Beach's, read off the
# analytics payload in its homepage rather than guessed.
GRID = (
    "https://www.citybeach.com/on/demandware.store"
    "/Sites-CityBeachAustralia-Site/en_AU/Search-UpdateGrid"
)

# The surfaces Shirtfaced sells on, as a shopper would search for them. Category
# ids were tried first and refused every value the site's own analytics payload
# reports (``mens-clothing-tops-t/shirt`` included); free text is what this
# storefront actually answers.
QUERIES: tuple[str, ...] = (
    "t-shirt",
    "tee",
    "hoodie",
    "crew jumper",
    "cap",
    "bucket hat",
    "beanie",
)

# Rows per request, and where to stop. A page past the end returns the grid
# furniture and no tiles at all, which is the real stopping condition -- this
# ceiling only bounds a run whose query never runs dry.
PAGE_SIZE = 48
MAX_START = 8000

# ``20195827-40`` is design 20195827 in colourway 40. One artwork across six
# colours is 6x redundancy rather than 6x evidence, so the base id is the design
# and the first colourway seen carries it -- the same call ``_design_key`` makes
# for Shopify handles, against a different id shape.
COLOURWAY = re.compile(r"-\d+$")

# What the store's own filename says a shot is. FT and BK are the front and back
# of the garment; LT, RT and TP are angles, and SW is a colour swatch a few dozen
# pixels wide. The miners measure ``images[0]``, so the front has to be first --
# a corpus that measured swatches would report every design as tiny and inkless.
SHOT_CODES: dict[str, str] = {
    "FT": "front",
    "BK": "back",
    "LT": "left",
    "RT": "right",
    "TP": "top",
    "SW": "swatch",
}
SHOT_ORDER: dict[str, int] = {"front": 0, "back": 1, "left": 2, "right": 3, "top": 4}
SHOT_FILENAME = re.compile(r"-([A-Z0-9]{2})-[A-Z]{2}\.(?:jpg|jpeg|png)", re.IGNORECASE)

PRODUCT_HREF = re.compile(r'href="(/au/([a-z0-9-]+)/([0-9-]+)\.html)"', re.IGNORECASE)

# Filesystem-safe, and stable across runs so a re-collection overwrites rather
# than accumulating a second copy under a slightly different name.
UNSAFE = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    return UNSAFE.sub("-", text.lower()).strip("-")


def _attr(markup: str, name: str) -> list[dict[str, Any]]:
    """Every occurrence of one JSON-carrying attribute, decoded.

    A tile whose JSON will not parse is skipped rather than failing the page:
    one malformed record should not cost the other forty-seven.
    """
    found: list[dict[str, Any]] = []
    for raw in re.findall(rf'{name}="([^"]*)"', markup):
        try:
            value = json.loads(html.unescape(raw))
        except ValueError:
            continue
        if isinstance(value, dict):
            found.append(value)
    return found


def _shot(url: str) -> str:
    match = SHOT_FILENAME.search(url.split("?")[0])
    return SHOT_CODES.get(match.group(1).upper(), "") if match else ""


def _is_wanted(name: str, category: str) -> bool:
    """Whether this is one of the surfaces Shirtfaced prints on.

    The patterns come from the Shopify collector unchanged. Notably absent is any
    filter for undecorated basics -- City Beach stocks blanks labels, and an
    AS Colour Staple Tee has no graphic to hold evidence of. That is deliberate:
    ``join_design_patterns.py`` already drops every design its measurement finds
    no print on, which is a measured judgement rather than a guess from a title.
    """
    haystack = f"{category} {name}"
    if UNWANTED_PATTERN.search(haystack):
        return False
    return bool(WANTED_TYPE_PATTERN.search(haystack))


def read_page(query: str, start: int) -> list[dict[str, Any]]:
    """One grid page, as joined product records. Empty when the query runs out."""
    url = f"{GRID}?q={query.replace(' ', '+')}&start={start}&sz={PAGE_SIZE}"
    try:
        markup = _fetch(url, timeout=40).decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return []

    # Metadata and images arrive on different elements, joined on the product id.
    # The counts do not match -- the grid carries detail blocks for tiles it has
    # no analytics for -- so this keeps only ids that appear in both.
    meta = {row["id"]: row for row in _attr(markup, "data-gtmdata") if row.get("id")}
    hrefs = {pid: (path, slug) for path, slug, pid in PRODUCT_HREF.findall(markup)}

    products: list[dict[str, Any]] = []
    for detail in _attr(markup, "data-productdetails"):
        pid = str(detail.get("productID") or "")
        row = meta.get(pid)
        if row is None:
            continue
        images = [
            str(image.get("url") or "")
            for image in detail.get("images") or []
            if isinstance(image, dict) and image.get("url")
        ]
        images = [url for url in images if _shot(url) != "swatch"]
        if not images:
            continue
        images.sort(key=lambda url: SHOT_ORDER.get(_shot(url), 9))

        path, slug = hrefs.get(pid, ("", ""))
        products.append(
            {
                "product_id": pid,
                "design_id": COLOURWAY.sub("", pid),
                "brand": str(row.get("brand") or "").strip(),
                "name": str(row.get("name") or "").strip(),
                "category": str(row.get("category") or "").strip().lower() or "unknown",
                "price": str(row.get("price") or ""),
                "source_url": f"https://www.citybeach.com{path}" if path else "",
                "slug": slug,
                "images": images,
            }
        )
    return products


def discover(queries: tuple[str, ...], limit: int) -> list[dict[str, Any]]:
    """Walk every query to exhaustion, one record per design."""
    designs: dict[str, dict[str, Any]] = {}
    for query in queries:
        start = 0
        while start < MAX_START and (not limit or len(designs) < limit):
            page = read_page(query, start)
            if not page:
                break
            for product in page:
                if product["design_id"] in designs:
                    continue
                if not _is_wanted(product["name"], product["category"]):
                    continue
                designs[product["design_id"]] = product
                if limit and len(designs) >= limit:
                    break
            print(f"  {query:<12} start={start:<5} {len(designs)} designs", flush=True)
            start += PAGE_SIZE
            time.sleep(REQUEST_DELAY)
        if limit and len(designs) >= limit:
            break
    return list(designs.values())


def store(products: list[dict[str, Any]]) -> tuple[int, int]:
    """Write the corpus tree. Returns products and images actually saved."""
    brand_dir = CORPUS_ROOT / BRAND_SLUG
    (brand_dir / "products").mkdir(parents=True, exist_ok=True)
    (brand_dir / "brand.json").write_text(
        json.dumps(
            {
                "brand_slug": BRAND_SLUG,
                "brand_name": BRAND_NAME,
                "site_url": SITE_URL,
                "design_tradition": TRADITION,
                # City Beach shoots every product worn, full body. That is
                # what makes this corpus reference imagery rather than a source
                # of medians: mine_design_patterns.py reads a flat-laid garment
                # and cannot read a worn one, so it skips these and says how
                # many it skipped rather than averaging shadow into the numbers.
                "photography": "worn",
                "acquired_at": _now(),
                "notes": (
                    "A multi-label retailer, not a label. Every product records the "
                    "brand that actually made it in product.json's retail_brand, and "
                    "the tradition is its own so these never move a brand tradition's "
                    "medians. See corpus_tiers.py on why this one retailer is not "
                    "excluded."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    saved_products = 0
    saved_images = 0
    for product in products:
        slug = product["slug"] or _slug(f"{product['brand']} {product['name']}")
        handle = f"{slug}-{product['design_id']}" if slug else product["design_id"]
        product_dir = brand_dir / "products" / handle
        product_dir.mkdir(parents=True, exist_ok=True)

        filenames: list[str] = []
        provenance: list[dict[str, Any]] = []
        for index, source in enumerate(product["images"], start=1):
            # Demandware resizes on request, the same trick the Shopify collector
            # uses. The stored width matches it so the two corpora measure alike.
            base = source.split("?")[0]
            sized = f"{base}?sw={IMAGE_WIDTH}&q=85"
            try:
                data = _fetch(sized)
            except (urllib.error.URLError, TimeoutError, OSError):
                continue

            extension = ".png" if base.lower().endswith(".png") else ".jpg"
            filename = f"image-{index:02d}{extension}"
            (product_dir / filename).write_bytes(data)
            filenames.append(filename)
            provenance.append(
                {
                    "provenance_id": f"{BRAND_SLUG}/{handle}/image-{index:02d}",
                    "source_id": f"{BRAND_SLUG}/{handle}",
                    "acquired_at": _now(),
                    "acquisition_method": "sfcc_search_grid",
                    "content_hash": f"sha256:{hashlib.sha256(data).hexdigest()}",
                    "byte_size": len(data),
                    "content_type": "image/png" if extension == ".png" else "image/jpeg",
                    "shot_hint": _shot(source),
                    "source_url": sized,
                }
            )
            time.sleep(REQUEST_DELAY)

        if not filenames:
            continue

        (product_dir / "product.json").write_text(
            json.dumps(
                {
                    "product_id": f"{BRAND_SLUG}/{handle}",
                    "brand_slug": BRAND_SLUG,
                    # The label whose design this actually is. City Beach stocks
                    # other people's work, and filing it under the shop's name is
                    # the exact error corpus_tiers.py's tier 3 describes.
                    "retail_brand": product["brand"],
                    "name": product["name"],
                    "source_url": product["source_url"],
                    "category": product["category"],
                    "price": f"AUD {product['price']}" if product["price"] else "",
                    "description": "",
                    "images": filenames,
                    "acquired_at": _now(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (product_dir / "provenance.json").write_text(
            json.dumps(provenance, indent=2), encoding="utf-8"
        )
        saved_products += 1
        saved_images += len(filenames)
        if saved_products % 25 == 0:
            print(f"  stored {saved_products} products...", flush=True)

    return saved_products, saved_images


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="stop after N designs")
    parser.add_argument("--query", action="append", help="one surface, repeatable")
    args = parser.parse_args(argv[1:])

    queries = tuple(args.query) if args.query else QUERIES
    print(f"Reading {BRAND_NAME} — {', '.join(queries)}")
    found = discover(queries, args.limit)
    if not found:
        print("Nothing matched. The grid returned no tiles.", file=sys.stderr)
        return 1

    print(f"\n{len(found)} designs found. Downloading images...")
    products, images = store(found)

    # Rebuilt from the tree, so this run indexes itself without dropping the
    # Shopify brands it never touched -- and the reverse, which is what happened
    # the first time the Shopify collector ran after City Beach existed.
    write_manifest()

    print(f"\n{products} products, {images} images -> {CORPUS_ROOT / BRAND_SLUG}")
    print(f"tradition: {TRADITION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
