"""Collect the design evidence corpus from Shopify storefronts.

Most graphic-apparel brands run Shopify, which serves a public, unauthenticated
``/products.json`` — structured product data with image URLs, titles, descriptions,
prices and tags. No API key, no HTML scraping, no bot-detection fight, and it is the
store's own data rather than something inferred from rendered markup.

That makes collection a deterministic script rather than an agent task: same brand
list in, same corpus out, re-runnable when a range changes, and auditable.

Writes ``var/design_corpus/`` per ``docs/DESIGN_CORPUS_SCHEMA.md``. Brands whose
store is not Shopify (or blocks the endpoint) are reported as skipped rather than
guessed at — a brand missing from the corpus is a known gap, not a silent one.

    python scripts/collect_design_corpus.py            # all brands
    python scripts/collect_design_corpus.py threadheads stussy
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CORPUS_ROOT = Path(__file__).resolve().parent.parent / "var" / "design_corpus"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# Products per brand. The corpus is comparison evidence, not a catalogue mirror.
PRODUCTS_PER_BRAND = 12

# Images per product. The primary shot carries the graphic; a second is usually the
# back print or an alternate colourway, both useful. More than that is bulk without
# additional design information.
IMAGES_PER_PRODUCT = 2

# Requested image width in pixels. Comfortably above what any of the scorecard's
# visual tests need — the thumbnail, blur and silhouette tests all reduce detail
# rather than demand it — and roughly 30x smaller than a full-resolution original.
IMAGE_WIDTH = 1200

# Politeness delay between requests to one store, in seconds.
REQUEST_DELAY = 0.4

# Graphic-led product types only. A blank basic tells us nothing about graphic
# construction, which is the entire point of the corpus.
WANTED_TYPE_PATTERN = re.compile(
    r"t[- ]?shirt|tee|hoodie|sweat|crew|long ?sleeve|jumper|jersey", re.IGNORECASE
)

# Products whose graphic is incidental or absent.
UNWANTED_PATTERN = re.compile(
    r"blank|plain|gift card|sticker|tote|sock|beanie|cap|hat|short|pant|jean|"
    r"jacket|bag|keyring|patch|pin|candle|mug|bottle",
    re.IGNORECASE,
)

# brand slug -> (display name, storefront base URL)
BRANDS: dict[str, tuple[str, str]] = {
    # Australian — the closest comparables, and the ones the brand actually competes with.
    "threadheads": ("Threadheads", "https://threadheads.com.au"),
    "thrills": ("Thrills", "https://thrills.co"),
    "barney-cools": ("Barney Cools", "https://barneycools.com"),
    "afends": ("Afends", "https://afends.com"),
    "misfit": ("Misfit", "https://misfitshapes.com"),
    "riot-society": ("Riot Society", "https://riotsociety.com"),
    "culture-kings": ("Culture Kings", "https://culturekings.com.au"),
    "santa-cruz-au": ("Santa Cruz Australia", "https://santacruzskateboards.com.au"),
    # Australian humour / novelty / slogan-led — the nearest thing to Shirtfaced's
    # own category, where the graphic is the joke rather than a brand mark.
    "dangerfield": ("Dangerfield", "https://dangerfield.com.au"),
    "beserk": ("Beserk", "https://beserk.com.au"),
    "the-tshirt-co": ("The T-Shirt Co", "https://www.thetshirtco.com.au"),
    "nena-and-pasadena": ("Nena & Pasadena", "https://nenaandpasadena.com.au"),
    "kiss-chacey": ("Kiss Chacey", "https://kisschacey.com.au"),
    "mr-simple": ("Mr Simple", "https://mrsimple.com.au"),
    "stm-goods": ("STM Goods", "https://stmgoods.com.au"),
    # Australian surf — graphic-led heritage, and the closest large-scale local
    # comparables for print-on-garment conventions.
    "rip-curl": ("Rip Curl", "https://ripcurl.com.au"),
    "billabong": ("Billabong", "https://www.billabong.com.au"),
    "quiksilver": ("Quiksilver", "https://www.quiksilver.com.au"),
    # Global streetwear / graphic-led — the documented research corpus.
    "stussy": ("Stüssy", "https://www.stussy.com"),
    "obey": ("Obey", "https://obeyclothing.com"),
    "represent": ("Represent", "https://au.representclo.com"),
    "brain-dead": ("Brain Dead", "https://wearebraindead.com"),
    "pleasures": ("Pleasures", "https://pleasuresnow.com"),
    "online-ceramics": ("Online Ceramics", "https://onlineceramics.com"),
    "market-studios": ("Market Studios", "https://market-studios.com"),
    "sporty-and-rich": ("Sporty & Rich", "https://sportyandrich.com"),
    "golf-wang": ("Golf Wang", "https://golfwang.com"),
    "born-x-raised": ("Born X Raised", "https://bornxraised.com"),
    "anti-social-social-club": ("Anti Social Social Club", "https://antisocialsocialclub.com"),
    "rvca": ("RVCA", "https://www.rvca.com"),
    "brixton": ("Brixton", "https://brixton.com"),
    "huf": ("HUF", "https://hufworldwide.com"),
    "primitive": ("Primitive Skateboarding", "https://primitiveskate.com"),
    "the-hundreds": ("The Hundreds", "https://thehundreds.com"),
    "diamond-supply": ("Diamond Supply Co", "https://diamondsupplyco.com"),
    "thrasher": ("Thrasher", "https://shop.thrashermagazine.com"),
    "volcom": ("Volcom", "https://www.volcom.com"),
    "polar-skate": ("Polar Skate Co", "https://polarskateco.com"),
    "quasi": ("Quasi Skateboards", "https://quasiskateboards.com"),
    "dime": ("Dime MTL", "https://dimemtl.com"),
    "last-resort-ab": ("Last Resort AB", "https://lastresortab.com"),
    "welcome-skateboards": ("Welcome Skateboards", "https://welcomeskateboards.com"),
    "chocolate": ("Chocolate Skateboards", "https://chocolateskateboards.com"),
    "baker": ("Baker Skateboards", "https://bakerskateboards.com"),
    "deathwish": ("Deathwish Skateboards", "https://deathwishskateboards.com"),
    "toy-machine": ("Toy Machine", "https://toymachine.com"),
    "zero": ("Zero Skateboards", "https://zeroskateboards.com"),
    "roark": ("Roark", "https://www.roark.com"),
    "katin": ("Katin USA", "https://katinusa.com"),
    "salty-crew": ("Salty Crew", "https://saltycrew.com"),
    "rhythm": ("Rhythm", "https://rhythmlivin.com"),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _fetch(url: str, timeout: int = 25) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _is_graphic_led(product: dict[str, Any]) -> bool:
    haystack = f"{product.get('product_type', '')} {product.get('title', '')}"
    if UNWANTED_PATTERN.search(haystack):
        return False
    return bool(WANTED_TYPE_PATTERN.search(haystack))


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


# Garment words trailing a product handle. Many brands sell one artwork across a
# whole garment range -- Threadheads' first twelve matches were three designs on
# four garments each -- and for a corpus about graphic construction that is 4x
# redundancy, not 4x evidence.
GARMENT_SUFFIX = re.compile(
    r"[-_ ]*(oversized[-_ ]?)?(t[-_ ]?shirt|tee|hoodie|sweatshirt|sweater|crew(neck)?|"
    r"jumper|long[-_ ]?sleeve|pullover|jersey)s?$",
    re.IGNORECASE,
)


def _design_key(handle: str) -> str:
    """The artwork a handle belongs to, with its garment suffix removed.

    ``lets-start-a-cult-hoodie`` and ``lets-start-a-cult-t-shirt`` are one design.
    Handles with no garment suffix are returned unchanged and so stay distinct.
    """
    stripped = GARMENT_SUFFIX.sub("", handle).strip("-_ ")
    return stripped or handle


def collect_brand(slug: str, name: str, site_url: str) -> dict[str, Any]:
    """Collect one brand. Returns a result row; never raises on network failure."""
    try:
        raw = _fetch(f"{site_url}/products.json?limit=250")
        products = json.loads(raw).get("products", [])
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError) as error:
        return {"brand_slug": slug, "status": "skipped", "reason": f"{type(error).__name__}: {error}"}

    if not products:
        return {"brand_slug": slug, "status": "skipped", "reason": "no products returned"}

    candidates = [p for p in products if _is_graphic_led(p) and p.get("images")]
    if not candidates:
        return {"brand_slug": slug, "status": "skipped", "reason": "no graphic-led products matched"}

    # One product per artwork. Keeps the first garment carrying each design, so a
    # brand contributes twelve designs rather than three designs four times over.
    wanted: list[dict[str, Any]] = []
    seen_designs: set[str] = set()
    for product in candidates:
        key = _design_key(product.get("handle") or "")
        if key in seen_designs:
            continue
        seen_designs.add(key)
        wanted.append(product)

    brand_dir = CORPUS_ROOT / slug
    (brand_dir / "products").mkdir(parents=True, exist_ok=True)
    (brand_dir / "brand.json").write_text(
        json.dumps(
            {
                "brand_slug": slug,
                "brand_name": name,
                "site_url": site_url,
                "acquired_at": _now(),
                "notes": "",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    product_count = 0
    image_count = 0
    for product in wanted[:PRODUCTS_PER_BRAND]:
        handle = product.get("handle") or str(product.get("id"))
        product_dir = brand_dir / "products" / handle
        product_dir.mkdir(parents=True, exist_ok=True)

        saved_images: list[str] = []
        provenance: list[dict[str, Any]] = []
        for index, image in enumerate(product.get("images", [])[:IMAGES_PER_PRODUCT], start=1):
            src = image.get("src")
            if not src:
                continue
            # Shopify's CDN resizes on request. Originals run to 12MB PNGs, which is
            # tens of gigabytes across the corpus and no more design information: the
            # graphic, its silhouette and its type are all legible well below that.
            sized = f"{src}{'&' if '?' in src else '?'}width={IMAGE_WIDTH}"
            try:
                data = _fetch(sized)
            except (urllib.error.URLError, TimeoutError, OSError):
                continue

            extension = ".png" if src.split("?")[0].lower().endswith(".png") else ".jpg"
            filename = f"image-{index:02d}{extension}"
            (product_dir / filename).write_bytes(data)
            saved_images.append(filename)
            provenance.append(
                {
                    "provenance_id": f"{slug}/{handle}/image-{index:02d}",
                    "source_id": f"{slug}/{handle}",
                    "acquired_at": _now(),
                    "acquisition_method": "shopify_products_json",
                    "content_hash": f"sha256:{hashlib.sha256(data).hexdigest()}",
                    "byte_size": len(data),
                    "content_type": "image/png" if extension == ".png" else "image/jpeg",
                    # The URL actually fetched, width parameter included -- the hash
                    # above is of this response, not of the unresized original.
                    "source_url": sized,
                }
            )
            time.sleep(REQUEST_DELAY)

        if not saved_images:
            continue

        variants = product.get("variants") or [{}]
        (product_dir / "product.json").write_text(
            json.dumps(
                {
                    "product_id": f"{slug}/{handle}",
                    "brand_slug": slug,
                    "name": product.get("title", ""),
                    "source_url": f"{site_url}/products/{handle}",
                    "category": (product.get("product_type") or "").lower() or "unknown",
                    "price": str(variants[0].get("price") or ""),
                    "description": _strip_html(product.get("body_html", ""))[:2000],
                    "images": saved_images,
                    "acquired_at": _now(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (product_dir / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")

        product_count += 1
        image_count += len(saved_images)

    if product_count == 0:
        return {"brand_slug": slug, "status": "skipped", "reason": "no images could be downloaded"}

    return {
        "brand_slug": slug,
        "status": "collected",
        "product_count": product_count,
        "image_count": image_count,
    }


def write_manifest(results: list[dict[str, Any]]) -> None:
    """Built once, after collection — never by a collector, to avoid racing writers."""
    CORPUS_ROOT.mkdir(parents=True, exist_ok=True)
    (CORPUS_ROOT / "manifest.json").write_text(
        json.dumps(
            {
                "generated_at": _now(),
                "brands": [
                    {
                        "brand_slug": r["brand_slug"],
                        "product_count": r["product_count"],
                        "image_count": r["image_count"],
                    }
                    for r in results
                    if r["status"] == "collected"
                ],
                "skipped": [
                    {"brand_slug": r["brand_slug"], "reason": r["reason"]}
                    for r in results
                    if r["status"] == "skipped"
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main(argv: list[str]) -> int:
    selected = argv[1:] or list(BRANDS)
    unknown = [slug for slug in selected if slug not in BRANDS]
    if unknown:
        print(f"Unknown brand slug(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    results = []
    for slug in selected:
        name, site_url = BRANDS[slug]
        result = collect_brand(slug, name, site_url)
        results.append(result)
        if result["status"] == "collected":
            print(f"  {slug:<28} {result['product_count']:>3} products  {result['image_count']:>3} images")
        else:
            print(f"  {slug:<28} skipped — {result['reason'][:70]}")

    write_manifest(results)

    collected = [r for r in results if r["status"] == "collected"]
    print(
        f"\n{len(collected)}/{len(results)} brands, "
        f"{sum(r['product_count'] for r in collected)} products, "
        f"{sum(r['image_count'] for r in collected)} images"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
