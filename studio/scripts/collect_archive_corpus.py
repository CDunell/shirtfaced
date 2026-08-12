"""Collect archive graphic-apparel evidence from eBay listings.

``collect_design_corpus.py`` reads brand storefronts, which can only ever serve
what a brand sells *now*. The design vocabulary worth studying — late-80s skate
airbrush, mid-90s flat sarcasm, 70s surf woodcut — is out of production and often
the label is dead. None of it is on any ``/products.json``.

Second-hand listings are where it survives, and they are unusually good evidence:
the seller photographs the garment flat, and titles it with the era, because that
is what sells it. ``Vintage 90s Skateboard Tee XL Single Stitch`` carries the
decade, the cut and the construction in the string.

Writes ``var/design_archive/`` — a sibling of ``var/design_corpus/``, not part of
it. The corpus is what ``mine_design_structure.py`` measures to derive layout
medians; dropping worn, folded, decades-old listing photos into it would move
those medians without anyone choosing to. Same record shape, separate tree, so
joining the two later is a decision rather than an accident.

Requires eBay application credentials in the environment:

    EBAY_CLIENT_ID, EBAY_CLIENT_SECRET

Free to register at developer.ebay.com. Without them the script reports every
cell as skipped rather than guessing — same convention as the Shopify collector,
where a missing brand is a known gap and not a silent one.

    python scripts/collect_archive_corpus.py --dry-run     # show the queries, no creds needed
    python scripts/collect_archive_corpus.py               # all cells
    python scripts/collect_archive_corpus.py skate-1988-93 surf-1970s
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ARCHIVE_ROOT = Path(__file__).resolve().parent.parent / "var" / "design_archive"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
ITEM_URL = "https://api.ebay.com/buy/browse/v1/item/"

# US marketplace. The archive being chased is largely American in origin, and the
# US site carries the deepest inventory of it by a wide margin.
MARKETPLACE = "EBAY_US"

# Items kept per cell, and images kept per item.
#
# Unlike a storefront, search relevance decays with depth: the first fifty results
# for a vintage query are the era, and by result four hundred it is reproductions,
# unrelated garments and single-word title matches. The cap here is about precision,
# not politeness — which is why it has a default rather than the corpus collector's
# uncapped behaviour. Overridable for a deeper pull.
ITEMS_PER_CELL = int(os.environ.get("ARCHIVE_ITEMS_PER_CELL", "60"))
IMAGES_PER_ITEM = int(os.environ.get("ARCHIVE_IMAGES_PER_ITEM", "6"))

# Politeness delay between requests, in seconds.
REQUEST_DELAY = 0.4

# Listings that are not a garment carrying a graphic. Reproductions are excluded
# deliberately: a 2023 reprint of a 1990 graphic is a photograph of current
# manufacturing, and the print quality, ink and blank are all wrong for the era.
UNWANTED_PATTERN = re.compile(
    r"reprint|repro|bootleg|\bfake\b|replica|lot of|bundle|joblot|job lot|"
    r"sticker|poster|patch|keyring|magnet|mug|dvd|vhs|magazine|catalog(ue)?|"
    r"deck only|griptape|wheels|bearings|trucks",
    re.IGNORECASE,
)

# Era-and-scene cells. The unit of study is the cell, not the brand: a 1991 skate
# graphic is a 1991 skate graphic whoever printed it, and half the labels that
# defined the era no longer exist to have a storefront.
#
# Queries name brands because that is what actually surfaces the material — a
# search for "vintage skate tee" returns mostly this decade. Naming a label in a
# search string is how the evidence is found; it says nothing about what any
# design derived from the cell may contain. CLAUDE.md's standing rule applies:
# everything gets ingested, and the rights question is asked once, before release.
#
# cell slug -> (display name, tradition, queries)
CELLS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "skate-1988-93": (
        "Skate 1988-93",
        "skate",
        (
            "vintage 80s skateboard t-shirt single stitch",
            "vintage powell peralta t-shirt 80s",
            "vintage santa cruz skateboards shirt 80s",
            "vintage vision street wear t-shirt",
            "vintage 1990 skateboard tee",
            "vintage alva skates shirt",
        ),
    ),
    "skate-1994-99": (
        "Skate 1994-99",
        "skate",
        (
            "vintage 90s skateboard t-shirt single stitch",
            "vintage world industries t-shirt 90s",
            "vintage blind skateboards shirt 90s",
            "vintage girl skateboards tee 90s",
            "vintage chocolate skateboards shirt 90s",
            "vintage 90s skate tee flat print",
        ),
    ),
    "street-1990s": (
        "Streetwear 1990s",
        "streetwear",
        (
            "vintage 90s stussy t-shirt",
            "vintage freshjive t-shirt",
            "vintage 90s streetwear tee single stitch",
            "vintage x-large t-shirt 90s",
            "vintage 90s graphic tee script logo",
        ),
    ),
    "surf-1970s": (
        "Surf 1970s",
        "surf",
        (
            "vintage 70s surf t-shirt",
            "vintage hang ten t-shirt 70s",
            "vintage katin surf shirt",
            "vintage 1970s surfboard tee",
            "vintage op ocean pacific shirt 70s",
        ),
    ),
    "indie-label-1990s": (
        "Indie label merch 1990s",
        "band-merch",
        (
            "vintage sub pop t-shirt 90s",
            "vintage 90s indie band tee single stitch",
            "vintage matador records shirt",
            "vintage 90s photocopy zine tee",
            "vintage touch and go records shirt",
        ),
    ),
    "moto-kustom-1970s": (
        "Moto and kustom kulture 1970s",
        "moto",
        (
            "vintage 70s motorcycle t-shirt",
            "vintage hot rod t-shirt 70s",
            "vintage 1970s biker tee",
            "vintage drag racing t-shirt 70s",
        ),
    ),
}


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug[:70] or "item"


def _fetch(url: str, headers: dict[str, str] | None = None, timeout: int = 25) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def get_token() -> str | None:
    """An application token, or None if credentials are absent or rejected.

    Client-credentials grant: this reads public listing data and acts for no user,
    so there is no consent leg and no refresh token to store.
    """
    client_id = os.environ.get("EBAY_CLIENT_ID", "").strip()
    client_secret = os.environ.get("EBAY_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        return None

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        }
    ).encode()
    request = urllib.request.Request(
        OAUTH_URL,
        data=body,
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.loads(response.read()).get("access_token")
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return None


def search(token: str, query: str, limit: int) -> list[dict[str, Any]]:
    """One search page. Returns [] on failure rather than raising."""
    params = urllib.parse.urlencode(
        {
            "q": query,
            "limit": str(min(limit, 200)),
            # Clothing only. Without this, "vintage 90s skate" pulls in decks,
            # magazines and toys that match on words alone.
            "category_ids": "11450",
        }
    )
    try:
        raw = _fetch(
            f"{SEARCH_URL}?{params}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE,
            },
        )
        return json.loads(raw).get("itemSummaries") or []
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return []


def item_images(token: str, item_id: str) -> tuple[list[str], str]:
    """Every image URL for one listing, plus its web URL.

    The search summary carries a single image. Sellers of vintage garments
    routinely post six or more — front, back, tag, seams, flaws — and the tag and
    seam shots are what date the piece, so the detail call is worth making.
    """
    try:
        raw = _fetch(
            f"{ITEM_URL}{urllib.parse.quote(item_id, safe='')}",
            headers={
                "Authorization": f"Bearer {token}",
                "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE,
            },
        )
        detail = json.loads(raw)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return [], ""

    urls: list[str] = []
    primary = (detail.get("image") or {}).get("imageUrl")
    if primary:
        urls.append(primary)
    for extra in detail.get("additionalImages") or []:
        url = extra.get("imageUrl")
        if url and url not in urls:
            urls.append(url)
    return urls, detail.get("itemWebUrl") or ""


def collect_cell(
    token: str, slug: str, name: str, tradition: str, queries: tuple[str, ...]
) -> dict[str, Any]:
    """Collect one era/scene cell. Never raises on network failure."""
    cell_dir = ARCHIVE_ROOT / slug
    (cell_dir / "items").mkdir(parents=True, exist_ok=True)

    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    kept: list[dict[str, Any]] = []

    per_query = max(1, ITEMS_PER_CELL // len(queries)) * 3
    for query in queries:
        if len(kept) >= ITEMS_PER_CELL:
            break
        for summary in search(token, query, per_query):
            if len(kept) >= ITEMS_PER_CELL:
                break
            item_id = summary.get("itemId") or ""
            title = summary.get("title") or ""
            if not item_id or item_id in seen_ids:
                continue
            if UNWANTED_PATTERN.search(title):
                continue
            # Sellers list the same garment repeatedly, and multi-quantity sellers
            # list near-identical titles. One per title keeps the sample varied.
            title_key = re.sub(r"[^a-z0-9]+", "", title.lower())[:60]
            if title_key in seen_titles:
                continue
            seen_ids.add(item_id)
            seen_titles.add(title_key)
            kept.append({"item_id": item_id, "title": title, "query": query, "summary": summary})
        time.sleep(REQUEST_DELAY)

    if not kept:
        return {"cell_slug": slug, "status": "skipped", "reason": "no listings matched"}

    (cell_dir / "cell.json").write_text(
        json.dumps(
            {
                "cell_slug": slug,
                "cell_name": name,
                "design_tradition": tradition,
                "queries": list(queries),
                "source": "ebay_browse_api",
                "marketplace": MARKETPLACE,
                "acquired_at": _now(),
                # Browse returns listings that are live right now. Sold-price
                # history sits behind the Marketplace Insights API, which is
                # limited-access — so this corpus carries no demand signal, and
                # nothing downstream should read one into it.
                "demand_signal": None,
                "notes": "",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    item_count = 0
    image_count = 0
    for entry in kept:
        urls, web_url = item_images(token, entry["item_id"])
        time.sleep(REQUEST_DELAY)
        if not urls:
            continue

        item_slug = _slugify(entry["title"])
        item_dir = cell_dir / "items" / item_slug
        if item_dir.exists():
            continue
        item_dir.mkdir(parents=True, exist_ok=True)

        saved: list[str] = []
        provenance: list[dict[str, Any]] = []
        for index, url in enumerate(urls[:IMAGES_PER_ITEM], start=1):
            try:
                data = _fetch(url)
            except (urllib.error.URLError, TimeoutError, OSError):
                continue
            extension = ".png" if url.split("?")[0].lower().endswith(".png") else ".jpg"
            filename = f"image-{index:02d}{extension}"
            (item_dir / filename).write_bytes(data)
            saved.append(filename)
            provenance.append(
                {
                    "provenance_id": f"{slug}/{item_slug}/image-{index:02d}",
                    "source_id": f"{slug}/{item_slug}",
                    "acquired_at": _now(),
                    "acquisition_method": "ebay_browse_api",
                    "content_hash": f"sha256:{hashlib.sha256(data).hexdigest()}",
                    "byte_size": len(data),
                    "content_type": "image/png" if extension == ".png" else "image/jpeg",
                    # Which shot this is cannot be read from an eBay CDN filename;
                    # sellers do not label them. Left empty rather than guessed.
                    "shot_hint": "",
                    "source_url": url,
                }
            )
            time.sleep(REQUEST_DELAY)

        if not saved:
            item_dir.rmdir()
            continue

        (item_dir / "item.json").write_text(
            json.dumps(
                {
                    "item_id": f"{slug}/{item_slug}",
                    "cell_slug": slug,
                    # The seller's own words, verbatim. The era, cut and
                    # construction are in this string, and parsing them into
                    # fields here would be a guess presented as a fact — leave
                    # that to whatever reads the archive.
                    "listing_title": entry["title"],
                    "matched_query": entry["query"],
                    "ebay_item_id": entry["item_id"],
                    "source_url": web_url,
                    "images": saved,
                    "acquired_at": _now(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (item_dir / "provenance.json").write_text(
            json.dumps(provenance, indent=2), encoding="utf-8"
        )
        item_count += 1
        image_count += len(saved)

    if item_count == 0:
        return {"cell_slug": slug, "status": "skipped", "reason": "no images could be downloaded"}

    return {
        "cell_slug": slug,
        "status": "collected",
        "item_count": item_count,
        "image_count": image_count,
    }


def write_manifest(results: list[dict[str, Any]]) -> None:
    """Built once, after collection — never by a collector, to avoid racing writers."""
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    (ARCHIVE_ROOT / "manifest.json").write_text(
        json.dumps(
            {
                "generated_at": _now(),
                "cells": [
                    {
                        "cell_slug": r["cell_slug"],
                        "item_count": r["item_count"],
                        "image_count": r["image_count"],
                    }
                    for r in results
                    if r["status"] == "collected"
                ],
                "skipped": [
                    {"cell_slug": r["cell_slug"], "reason": r["reason"]}
                    for r in results
                    if r["status"] == "skipped"
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in argv

    selected = args or list(CELLS)
    unknown = [slug for slug in selected if slug not in CELLS]
    if unknown:
        print(f"Unknown cell slug(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"Known: {', '.join(CELLS)}", file=sys.stderr)
        return 2

    if dry_run:
        print(
            f"{len(selected)} cell(s), {ITEMS_PER_CELL} items each, "
            f"{IMAGES_PER_ITEM} images per item\n"
        )
        for slug in selected:
            name, tradition, queries = CELLS[slug]
            print(f"{slug}  ({tradition})  — {name}")
            for query in queries:
                print(f"    {query}")
            print()
        print(f"Writes to {ARCHIVE_ROOT}")
        return 0

    token = get_token()
    if not token:
        print(
            "No eBay token. Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET "
            "(free at developer.ebay.com), or run with --dry-run.",
            file=sys.stderr,
        )
        return 1

    results = []
    for slug in selected:
        name, tradition, queries = CELLS[slug]
        result = collect_cell(token, slug, name, tradition, queries)
        results.append(result)
        if result["status"] == "collected":
            print(
                f"  {slug:<22} {result['item_count']:>3} items  {result['image_count']:>4} images"
            )
        else:
            print(f"  {slug:<22} skipped — {result['reason'][:70]}")

    write_manifest(results)

    collected = [r for r in results if r["status"] == "collected"]
    print(
        f"\n{len(collected)}/{len(results)} cells, "
        f"{sum(r['item_count'] for r in collected)} items, "
        f"{sum(r['image_count'] for r in collected)} images"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
