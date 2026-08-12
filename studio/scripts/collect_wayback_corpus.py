"""Collect archive graphic evidence from the Wayback Machine.

The sibling of ``collect_archive_corpus.py``, and the one that needs no
credentials. Both write ``var/design_archive/``.

Where the eBay collector finds a reseller's photograph of a surviving garment,
this finds the brand's *own* artwork from the period — the ads, the graphic
pages, the site furniture — because their websites were archived while the era
was current. A 2001 World Industries ad pulled from their own server is the
graphic as it was drawn: print quality, correct colour, no fold, no fade, no
seller's kitchen lighting.

Most of the labels that defined these eras are dead or unrecognisable, so their
storefronts cannot be collected. Their 1998 storefronts can.

Two things to know about the yield.

*It is mixed.* A brand site holds its ads and its graphics, but also team
photographs, navigation furniture and whatever the webmaster left in ``/images``.
A verified pull returned a period ad at 104KB alongside a snapshot of somebody in
a garden at 20KB. Only a floor is applied here — enough to drop spacers and
buttons — and everything above it is kept and recorded. Judging which images are
design evidence is a reading problem, not a collection one.

*A domain is not a brand.* Domains change hands, and the Wayback Machine records
whoever held one at the time. ``shortys.com`` in 1998-2003 was a restaurant, and
the first run put fifteen photographs of its dining room into the skate cell.
Nothing in the data reveals this — the CDX rows are valid images from a live
domain in the right window. Every domain added to ``CELLS`` needs one image
opened and looked at before it is trusted, and no heuristic substitutes for that.

*archive.org rate-limits and times out.* 504s on CDX are routine, not failure.
Requests retry with backoff, and a domain that never answers is reported as a
skipped gap rather than silently dropped.

    python scripts/collect_wayback_corpus.py --dry-run
    python scripts/collect_wayback_corpus.py                    # all cells
    python scripts/collect_wayback_corpus.py skate-1994-99
"""

from __future__ import annotations

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

CDX_URL = "https://web.archive.org/cdx/search/cdx"

# ``id_`` asks for the original bytes rather than the rewritten, banner-wrapped
# page the Wayback UI serves.
SNAPSHOT_URL = "https://web.archive.org/web/{timestamp}id_/{original}"

# Bytes below which an image is site furniture rather than artwork. A 1999 site is
# mostly single-pixel spacers, rollover buttons and rule lines, all comfortably
# under this. Verified: the floor keeps a 104KB ad and an 18KB graphic, and drops
# the nav set entirely.
#
# It is a floor, not a filter on merit — a small graphic is still a graphic. The
# rose photograph at 20KB survives it, and should: deciding that is reading, and
# reading happens after collection.
MIN_IMAGE_BYTES = int(os.environ.get("WAYBACK_MIN_IMAGE_BYTES", "8000"))

# Snapshots examined per domain, and images kept from them.
CDX_LIMIT = int(os.environ.get("WAYBACK_CDX_LIMIT", "3000"))
IMAGES_PER_DOMAIN = int(os.environ.get("WAYBACK_IMAGES_PER_DOMAIN", "40"))

REQUEST_DELAY = 0.5
RETRIES = 3
BACKOFF = 4.0

# Era cells, matching collect_archive_corpus.py so the two sources land in one
# tree. Each domain carries the years worth pulling: a label's site in 2011 is not
# evidence about 1994 even if the domain survived.
#
# cell slug -> (display name, tradition, ((domain, from_year, to_year), ...))
CELLS: dict[str, tuple[str, str, tuple[tuple[str, int, int], ...]]] = {
    "skate-1988-93": (
        "Skate 1988-93",
        "skate",
        (
            ("powellperalta.com", 1996, 2002),
            ("alvaskates.com", 1997, 2004),
            ("visionskateboards.com", 1997, 2004),
            ("santacruzskateboards.com", 1997, 2002),
        ),
    ),
    "skate-1994-99": (
        "Skate 1994-99",
        "skate",
        (
            ("worldindustries.com", 1998, 2003),
            ("blindskateboards.com", 1998, 2004),
            ("girlskateboards.com", 1998, 2003),
            ("chocolateskateboards.com", 1998, 2003),
            ("toymachine.com", 1998, 2003),
            # shortys.com removed: verified 2026-08-13, it served a restaurant in
            # this window, not the skate company, and returned fifteen photographs
            # of a dining room. See "a domain is not a brand" in the module
            # docstring -- every domain added here needs one image eyeballed
            # before it is trusted.
            ("birdhouseskateboards.com", 1998, 2003),
        ),
    ),
    "street-1990s": (
        "Streetwear 1990s",
        "streetwear",
        (
            ("freshjive.com", 1997, 2003),
            ("xlarge.com", 1997, 2003),
            ("stussy.com", 1997, 2002),
            ("eckounltd.com", 1998, 2003),
            ("phatfarm.com", 1998, 2003),
        ),
    ),
    "surf-1970s": (
        "Surf heritage",
        "surf",
        (
            ("hangten.com", 1997, 2004),
            ("oceanpacific.com", 1997, 2004),
            ("katinusa.com", 1999, 2006),
        ),
    ),
    "indie-label-1990s": (
        "Indie label merch 1990s",
        "band-merch",
        (
            ("subpop.com", 1996, 2003),
            ("matadorrecords.com", 1996, 2003),
            ("touchandgorecords.com", 1997, 2004),
            ("dischord.com", 1996, 2003),
        ),
    ),
}


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:70] or "item"


def _fetch(url: str, timeout: int = 90) -> bytes:
    """Fetch with backoff. archive.org 504s under load as a matter of course."""
    last: Exception | None = None
    for attempt in range(RETRIES):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last = error
            if attempt < RETRIES - 1:
                time.sleep(BACKOFF * (attempt + 1))
    raise last if last else RuntimeError("unreachable")


def cdx_images(domain: str, from_year: int, to_year: int) -> list[dict[str, Any]]:
    """Archived images for one domain in one window, largest first.

    ``collapse=urlkey`` keeps one snapshot per distinct URL — a site crawled
    forty times would otherwise return the same masthead forty times.
    """
    params = urllib.parse.urlencode(
        {
            "url": f"{domain}*",
            "output": "json",
            "from": str(from_year),
            "to": str(to_year),
            "filter": "statuscode:200",
            "collapse": "urlkey",
            "limit": str(CDX_LIMIT),
            "fl": "timestamp,original,mimetype,length",
        }
    )
    try:
        raw = _fetch(f"{CDX_URL}?{params}")
    except (urllib.error.URLError, TimeoutError, OSError):
        return []
    if not raw.strip():
        return []
    try:
        rows = json.loads(raw)
    except json.JSONDecodeError:
        return []

    images = []
    for row in rows[1:]:
        if len(row) < 4:
            continue
        timestamp, original, mimetype, length = row[0], row[1], row[2] or "", row[3] or "0"
        if "image" not in mimetype:
            continue
        try:
            size = int(length)
        except ValueError:
            continue
        if size < MIN_IMAGE_BYTES:
            continue
        images.append(
            {"timestamp": timestamp, "original": original, "mimetype": mimetype, "length": size}
        )

    # Largest first. Not a merit judgement — the biggest files are simply the most
    # likely to be artwork rather than furniture, and the per-domain cap has to
    # spend itself somewhere.
    images.sort(key=lambda row: row["length"], reverse=True)
    return images


def collect_domain(cell_slug: str, domain: str, from_year: int, to_year: int) -> dict[str, Any]:
    """Collect one domain into its cell. Never raises."""
    found = cdx_images(domain, from_year, to_year)
    if not found:
        return {"domain": domain, "status": "skipped", "reason": "no archived images matched"}

    item_slug = f"{_slugify(domain)}-{from_year}-{to_year}"
    item_dir = ARCHIVE_ROOT / cell_slug / "items" / item_slug
    item_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    provenance: list[dict[str, Any]] = []
    for index, row in enumerate(found[:IMAGES_PER_DOMAIN], start=1):
        url = SNAPSHOT_URL.format(timestamp=row["timestamp"], original=row["original"])
        try:
            data = _fetch(url, timeout=60)
        except (urllib.error.URLError, TimeoutError, OSError):
            continue
        # A Wayback miss can answer 200 with an HTML error page. The magic bytes
        # decide what this actually is, not the CDX row that promised an image.
        if not (
            data[:3] == b"\xff\xd8\xff"
            or data[:8] == b"\x89PNG\r\n\x1a\n"
            or data[:6] in (b"GIF87a", b"GIF89a")
        ):
            continue

        if data[:3] == b"\xff\xd8\xff":
            extension, content_type = ".jpg", "image/jpeg"
        elif data[:8] == b"\x89PNG\r\n\x1a\n":
            extension, content_type = ".png", "image/png"
        else:
            extension, content_type = ".gif", "image/gif"

        filename = f"image-{index:02d}{extension}"
        (item_dir / filename).write_bytes(data)
        saved.append(filename)
        provenance.append(
            {
                "provenance_id": f"{cell_slug}/{item_slug}/image-{index:02d}",
                "source_id": f"{cell_slug}/{item_slug}",
                "acquired_at": _now(),
                "acquisition_method": "wayback_cdx",
                "content_hash": f"sha256:{hashlib.sha256(data).hexdigest()}",
                "byte_size": len(data),
                "content_type": content_type,
                "shot_hint": "",
                # Both URLs kept: what was fetched, and what it was on the live web.
                "source_url": url,
                "original_url": row["original"],
                # When the crawler saw it. The nearest thing to a date this
                # material has, and the reason the cell can claim an era at all.
                "snapshot_timestamp": row["timestamp"],
            }
        )
        time.sleep(REQUEST_DELAY)

    if not saved:
        return {"domain": domain, "status": "skipped", "reason": "no images could be downloaded"}

    (item_dir / "item.json").write_text(
        json.dumps(
            {
                "item_id": f"{cell_slug}/{item_slug}",
                "cell_slug": cell_slug,
                "listing_title": f"{domain} {from_year}-{to_year}",
                "source_domain": domain,
                "snapshot_window": [from_year, to_year],
                "source_url": f"https://web.archive.org/web/{from_year}*/{domain}",
                "images": saved,
                # What was seen versus what was kept. A cap that hides how much it
                # dropped reads as completeness.
                "candidates_found": len(found),
                "candidates_kept": len(saved),
                "acquired_at": _now(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (item_dir / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return {
        "domain": domain,
        "status": "collected",
        "image_count": len(saved),
        "candidates": len(found),
    }


def collect_cell(slug: str, name: str, tradition: str, domains: tuple) -> dict[str, Any]:
    cell_dir = ARCHIVE_ROOT / slug
    (cell_dir / "items").mkdir(parents=True, exist_ok=True)

    results = [collect_domain(slug, domain, lo, hi) for domain, lo, hi in domains]
    collected = [r for r in results if r["status"] == "collected"]

    (cell_dir / "cell.json").write_text(
        json.dumps(
            {
                "cell_slug": slug,
                "cell_name": name,
                "design_tradition": tradition,
                "domains": [
                    {"domain": d, "from": lo, "to": hi, "status": r["status"]}
                    for (d, lo, hi), r in zip(domains, results, strict=True)
                ],
                "source": "wayback_cdx",
                "acquired_at": _now(),
                "demand_signal": None,
                "notes": "",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    if not collected:
        return {"cell_slug": slug, "status": "skipped", "reason": "no domains yielded images"}
    return {
        "cell_slug": slug,
        "status": "collected",
        "item_count": len(collected),
        "image_count": sum(r["image_count"] for r in collected),
        "domains": results,
    }


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    selected = args or list(CELLS)
    unknown = [slug for slug in selected if slug not in CELLS]
    if unknown:
        print(f"Unknown cell slug(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"Known: {', '.join(CELLS)}", file=sys.stderr)
        return 2

    if "--dry-run" in argv:
        print(
            f"{len(selected)} cell(s), up to {IMAGES_PER_DOMAIN} images per domain, "
            f"floor {MIN_IMAGE_BYTES} bytes\n"
        )
        for slug in selected:
            name, tradition, domains = CELLS[slug]
            print(f"{slug}  ({tradition})  {name}")
            for domain, lo, hi in domains:
                print(f"    {domain:<32} {lo}-{hi}")
            print()
        print(f"Writes to {ARCHIVE_ROOT}")
        return 0

    results = []
    for slug in selected:
        name, tradition, domains = CELLS[slug]
        print(f"{slug}")
        result = collect_cell(slug, name, tradition, domains)
        results.append(result)
        for row in result.get("domains", []):
            if row["status"] == "collected":
                print(
                    f"    {row['domain']:<32} {row['image_count']:>3} kept "
                    f"of {row['candidates']:>4} candidates"
                )
            else:
                print(f"    {row['domain']:<32} skipped — {row['reason'][:44]}")

    collected = [r for r in results if r["status"] == "collected"]
    print(
        f"\n{len(collected)}/{len(results)} cells, "
        f"{sum(r['image_count'] for r in collected)} images"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
