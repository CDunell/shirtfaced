"""Collect archive evidence from WordPress-backed design archives.

Generalises ``collect_streetwear_archive.py``, which this replaces. Two sources
turned out to be WordPress within an hour of each other, and a third copy of the
same walker is how this repository has burned days before now.

Two strategies, because the two sites hold their material differently.

``posts`` -- Streetwear Archive files every scan as a post with a brand category
and tags. The meaning lives on the post; media titles are camera filenames like
``IMG_7653``. So walk posts and resolve their media.

``page`` -- Go Media publish one archive page carrying every design as an inline
image, named for the client: ``pyknic-tawdry-hepburn``, ``caliban-two-skulls``.
No taxonomy, but the filename is the label, so parse the page and keep the name.

Both write ``var/design_archive/``. Neither needs credentials. robots.txt checked
for each before adding: a site whose robots names ``anthropic-ai`` or
``ClaudeBot`` under ``Disallow: /`` does not belong in this file, whatever it
holds. dan-mumford.com was refused on exactly that basis on 2026-08-13.

    python scripts/collect_wp_archives.py --dry-run
    python scripts/collect_wp_archives.py streetwear-archive
    python scripts/collect_wp_archives.py go-media --limit 120
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ARCHIVE_ROOT = Path(__file__).resolve().parent.parent / "var" / "design_archive"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

PER_PAGE = 100
REQUEST_DELAY = 0.35
RETRIES = 3
BACKOFF = 3.0

IMAGE_MAGIC = (
    (b"\xff\xd8\xff", ".jpg", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", ".png", "image/png"),
    (b"GIF87a", ".gif", "image/gif"),
    (b"GIF89a", ".gif", "image/gif"),
)

# slug -> config. ``upload_hosts`` is what an image URL must start with to count
# as the site's own material rather than a widget, avatar or advert.
SITES: dict[str, dict[str, Any]] = {
    "streetwear-archive": {
        "name": "Streetwear Archive (collector community)",
        "strategy": "posts",
        "api": "https://streetweararchive.com/wp-json/wp/v2",
        "tradition": "mixed",
        "site_url": "https://streetweararchive.com",
        "upload_hosts": ("https://streetweararchive.com/wp-content/uploads/",),
    },
    "go-media": {
        "name": "Go Media apparel archive",
        "strategy": "page",
        "page_url": "https://gomedia.com/our-work/graphic-design/go-media-apparel-archive/",
        "tradition": "band-merch",
        "site_url": "https://gomedia.com",
        # Their uploads sit on S3 under a second hostname.
        "upload_hosts": (
            "https://s3.gomedia.us/wp-content/uploads/",
            "https://gomedia.com/wp-content/uploads/",
        ),
    },
}


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:70] or "item"


def _fetch(url: str, timeout: int = 45) -> tuple[bytes, dict[str, str]]:
    last: Exception | None = None
    for attempt in range(RETRIES):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read(), dict(response.headers)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last = error
            if attempt < RETRIES - 1:
                time.sleep(BACKOFF * (attempt + 1))
    raise last if last else RuntimeError("unreachable")


def _json(url: str) -> Any:
    body, _ = _fetch(url)
    return json.loads(body)


def _full_size(url: str) -> str:
    """WordPress serves ``-507x550`` derivatives beside the original."""
    return re.sub(r"-\d{2,4}x\d{2,4}(\.[a-zA-Z]{3,4})$", r"\1", url)


def _write_item(cell_dir: Path, item_slug: str, urls: list[str], meta: dict[str, Any]) -> int:
    """Download an item's images and record it. Returns images saved."""
    item_dir = cell_dir / "items" / item_slug
    if (item_dir / "item.json").exists():
        return 0
    item_dir.mkdir(parents=True, exist_ok=True)

    saved: list[str] = []
    provenance: list[dict[str, Any]] = []
    for url in urls:
        try:
            data, _ = _fetch(url, timeout=60)
        except (urllib.error.URLError, TimeoutError, OSError):
            continue
        match = next((m for m in IMAGE_MAGIC if data.startswith(m[0])), None)
        if not match:
            continue
        _, extension, content_type = match
        digest = hashlib.sha256(data).hexdigest()
        if any(p["content_hash"].endswith(digest) for p in provenance):
            continue
        filename = f"image-{len(saved) + 1:02d}{extension}"
        (item_dir / filename).write_bytes(data)
        saved.append(filename)
        provenance.append(
            {
                "provenance_id": f"{item_slug}/image-{len(saved):02d}",
                "source_id": item_slug,
                "acquired_at": _now(),
                "acquisition_method": meta["acquisition_method"],
                "content_hash": f"sha256:{digest}",
                "byte_size": len(data),
                "content_type": content_type,
                "shot_hint": "",
                "source_url": url,
            }
        )
        time.sleep(REQUEST_DELAY)

    if not saved:
        return 0
    (item_dir / "item.json").write_text(
        json.dumps({**meta, "images": saved, "acquired_at": _now()}, indent=2),
        encoding="utf-8",
    )
    (item_dir / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return len(saved)


def taxonomy_names(api: str, kind: str) -> dict[int, str]:
    names: dict[int, str] = {}
    page = 1
    while True:
        try:
            rows = _json(f"{api}/{kind}?per_page={PER_PAGE}&page={page}")
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
            break
        if not rows:
            break
        for row in rows:
            names[row["id"]] = row.get("name") or ""
        if len(rows) < PER_PAGE:
            break
        page += 1
        time.sleep(REQUEST_DELAY)
    return names


def collect_posts(slug: str, config: dict[str, Any], limit: int) -> dict[str, Any]:
    api = config["api"]
    cell_dir = ARCHIVE_ROOT / slug
    (cell_dir / "items").mkdir(parents=True, exist_ok=True)

    categories = taxonomy_names(api, "categories")
    tags = taxonomy_names(api, "tags")

    posts: list[dict[str, Any]] = []
    page = 1
    while True:
        try:
            rows = _json(f"{api}/posts?per_page={PER_PAGE}&page={page}&_embed=wp:featuredmedia")
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
            break
        if not rows:
            break
        posts.extend(rows)
        if (limit and len(posts) >= limit) or len(rows) < PER_PAGE:
            break
        page += 1
        time.sleep(REQUEST_DELAY)
    posts = posts[:limit] if limit else posts
    if not posts:
        return {"status": "skipped", "reason": "no posts returned"}

    hosts = tuple(config["upload_hosts"])
    pattern = re.compile("|".join(re.escape(h) for h in hosts) + r"[^\"'\s\\)]+")

    items = images = 0
    for post in posts:
        title = re.sub(r"<[^>]+>", "", (post.get("title") or {}).get("rendered") or "").strip()
        urls: list[str] = []
        for media in (post.get("_embedded") or {}).get("wp:featuredmedia") or []:
            if media.get("source_url"):
                urls.append(media["source_url"])
        for match in pattern.findall((post.get("content") or {}).get("rendered") or ""):
            for candidate in (_full_size(match), match):
                if candidate not in urls:
                    urls.append(candidate)
        if not urls:
            continue
        saved = _write_item(
            cell_dir,
            f"{post.get('id')}-{_slugify(title)}",
            urls,
            {
                "item_id": f"{slug}/{post.get('id')}-{_slugify(title)}",
                "cell_slug": slug,
                "listing_title": title,
                "categories": [categories.get(c, str(c)) for c in post.get("categories") or []],
                "tags": [tags.get(t, str(t)) for t in post.get("tags") or []],
                "post_id": post.get("id"),
                "posted_at": post.get("date"),
                "source_url": post.get("link"),
                "acquisition_method": "wp_rest_posts",
            },
        )
        if saved:
            items += 1
            images += saved
    return {"status": "collected", "seen": len(posts), "item_count": items, "image_count": images}


def collect_page(slug: str, config: dict[str, Any], limit: int) -> dict[str, Any]:
    """One page whose inline images are the archive. Filename carries the label."""
    cell_dir = ARCHIVE_ROOT / slug
    (cell_dir / "items").mkdir(parents=True, exist_ok=True)
    try:
        body, _ = _fetch(config["page_url"])
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {"status": "skipped", "reason": f"{type(error).__name__}"}

    html = body.decode("utf-8", "ignore")
    hosts = tuple(config["upload_hosts"])
    pattern = re.compile(
        "(?:" + "|".join(re.escape(h) for h in hosts) + r")[^\"'\s\\)]+?\.(?:jpg|jpeg|png|gif)",
        re.IGNORECASE,
    )

    seen: set[str] = set()
    urls: list[str] = []
    for match in pattern.findall(html):
        full = _full_size(match)
        if full not in seen:
            seen.add(full)
            urls.append(full)
    if limit:
        urls = urls[:limit]
    if not urls:
        return {"status": "skipped", "reason": "no uploads images found on page"}

    items = images = 0
    for url in urls:
        # The filename is the only label this strategy gets. Recorded as-is:
        # "pyknic-tawdry-hepburn" names a client and a design, and inventing more
        # structure than that would be a guess.
        name = _slugify(re.sub(r"\.[a-z]{3,4}$", "", url.rsplit("/", 1)[-1], flags=re.I))
        saved = _write_item(
            cell_dir,
            name,
            [url],
            {
                "item_id": f"{slug}/{name}",
                "cell_slug": slug,
                "listing_title": name.replace("-", " "),
                "categories": [],
                "tags": [],
                "source_url": config["page_url"],
                "acquisition_method": "wp_page_images",
            },
        )
        if saved:
            items += 1
            images += saved
    return {"status": "collected", "seen": len(urls), "item_count": items, "image_count": images}


def write_cell(slug: str, config: dict[str, Any], result: dict[str, Any]) -> None:
    (ARCHIVE_ROOT / slug).mkdir(parents=True, exist_ok=True)
    (ARCHIVE_ROOT / slug / "cell.json").write_text(
        json.dumps(
            {
                "cell_slug": slug,
                "cell_name": config["name"],
                "design_tradition": config["tradition"],
                "source": f"wp_{config['strategy']}",
                "source_url": config["site_url"],
                "seen": result.get("seen"),
                "acquired_at": _now(),
                "demand_signal": None,
                "notes": "Taxonomy is the source's own; not mapped to design_corpus slugs.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    limit = int(os.environ.get("WP_ARCHIVE_LIMIT", "0"))
    if "--limit" in argv:
        try:
            limit = int(argv[argv.index("--limit") + 1])
        except (IndexError, ValueError):
            print("--limit needs a number", file=sys.stderr)
            return 2
        args = [a for a in args if a != str(limit)]

    selected = args or list(SITES)
    unknown = [s for s in selected if s not in SITES]
    if unknown:
        print(f"Unknown site(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"Known: {', '.join(SITES)}", file=sys.stderr)
        return 2

    if "--dry-run" in argv:
        for slug in selected:
            config = SITES[slug]
            print(f"{slug:<22} {config['strategy']:<6} {config['site_url']}")
        print(f"\nLimit: {limit or 'none'}   Writes to {ARCHIVE_ROOT}")
        return 0

    for slug in selected:
        config = SITES[slug]
        collector = collect_posts if config["strategy"] == "posts" else collect_page
        result = collector(slug, config, limit)
        write_cell(slug, config, result)
        if result["status"] == "collected":
            print(
                f"  {slug:<22} {result['item_count']:>4} items  "
                f"{result['image_count']:>5} images  (of {result['seen']} seen)"
            )
        else:
            print(f"  {slug:<22} skipped — {result['reason'][:56]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
