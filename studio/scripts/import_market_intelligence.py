#!/usr/bin/env python3
"""Import marketplace research exports into Shirtfaced's evidence corpus.

This is the ingestion edge for Thunderbit (or any CSV/JSON/JSONL exporter). It
normalises listing data into the same product/provenance shape used by the design
corpora, while keeping commercial signals separate from visual observations.

Nothing in this file turns marketplace copy or depicted subject matter into a
creative brief. Titles/descriptions are retained as source evidence only. The
existing visual pass is responsible for describing design structure; the market
intelligence scorer then joins structure to demand proxies.

Examples:

    python scripts/import_market_intelligence.py etsy.json --source etsy --query "graphic tee"
    python scripts/import_market_intelligence.py amazon.csv --source amazon --download-images

Writes ``var/design_corpus_market/<source>/...``. The directory is gitignored by
Studio's existing ``var/`` rule.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "var" / "design_corpus_market"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

ALIASES: dict[str, tuple[str, ...]] = {
    "id": ("id", "listing_id", "product_id", "asin", "sku"),
    "url": ("url", "listing_url", "product_url", "link", "source_url"),
    "title": ("title", "name", "product_name", "listing_title"),
    "description": ("description", "product_description", "listing_description"),
    "price": ("price", "current_price", "sale_price"),
    "currency": ("currency", "currency_code"),
    "rating": ("rating", "stars", "average_rating"),
    "review_count": ("review_count", "reviews", "ratings_count", "rating_count"),
    "sales_count": ("sales_count", "sales", "sold", "units_sold"),
    "rank": ("rank", "best_seller_rank", "bestseller_rank", "position"),
    "image": ("image", "image_url", "primary_image", "thumbnail", "photo"),
    "images": ("images", "image_urls", "photos"),
}


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _clean_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _read(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    text = path.read_text(encoding="utf-8-sig")
    if suffix in {".jsonl", ".ndjson"}:
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    loaded = json.loads(text)
    if isinstance(loaded, list):
        return [row for row in loaded if isinstance(row, dict)]
    if isinstance(loaded, dict):
        for key in ("rows", "data", "results", "items", "listings"):
            value = loaded.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        return [loaded]
    raise ValueError(f"Unsupported JSON root in {path}")


def _normalise_keys(row: dict[str, Any]) -> dict[str, Any]:
    return {_clean_key(str(key)): value for key, value in row.items()}


def _pick(row: dict[str, Any], field: str, default: Any = "") -> Any:
    for alias in ALIASES[field]:
        key = _clean_key(alias)
        value = row.get(key)
        if value not in (None, "", []):
            return value
    return default


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower().replace(",", "")
    multiplier = 1.0
    if text.endswith("k"):
        multiplier, text = 1_000.0, text[:-1]
    elif text.endswith("m"):
        multiplier, text = 1_000_000.0, text[:-1]
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group()) * multiplier if match else None


def _image_urls(row: dict[str, Any]) -> list[str]:
    out: list[str] = []
    many = _pick(row, "images", [])
    if isinstance(many, list):
        out.extend(str(value) for value in many if value)
    elif isinstance(many, str):
        stripped = many.strip()
        if stripped.startswith("["):
            try:
                loaded = json.loads(stripped)
                if isinstance(loaded, list):
                    out.extend(str(value) for value in loaded if value)
            except json.JSONDecodeError:
                pass
        if not out:
            out.extend(part.strip() for part in re.split(r"[|;\n]", stripped) if part.strip())
    one = _pick(row, "image", "")
    if one:
        out.insert(0, str(one))
    return list(dict.fromkeys(url for url in out if url.startswith(("http://", "https://"))))


def _fetch(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read(), response.headers.get_content_type()


def _extension(content_type: str, url: str) -> str:
    if "png" in content_type or url.lower().split("?")[0].endswith(".png"):
        return ".png"
    if "webp" in content_type or url.lower().split("?")[0].endswith(".webp"):
        return ".webp"
    return ".jpg"


def _slug(source: str, listing_id: str, url: str, title: str) -> str:
    stable = listing_id or url or title
    digest = hashlib.sha256(stable.encode("utf-8")).hexdigest()[:16]
    return f"{source}-{digest}"


def _iter_rows(path: Path) -> Iterable[dict[str, Any]]:
    for raw in _read(path):
        yield _normalise_keys(raw)


def import_rows(
    path: Path,
    source: str,
    query: str,
    download_images: bool,
) -> dict[str, int]:
    source = _clean_key(source).replace("_", "-")
    source_dir = OUT / source
    products_dir = source_dir / "products"
    products_dir.mkdir(parents=True, exist_ok=True)
    acquired_at = _now()

    counts = {"rows": 0, "written": 0, "images": 0, "image_failures": 0, "refused": 0}
    for row in _iter_rows(path):
        counts["rows"] += 1
        listing_id = str(_pick(row, "id", ""))
        url = str(_pick(row, "url", ""))
        title = str(_pick(row, "title", ""))
        if not (listing_id or url or title):
            counts["refused"] += 1
            continue

        product_slug = _slug(source, listing_id, url, title)
        product_dir = products_dir / product_slug
        product_dir.mkdir(parents=True, exist_ok=True)
        urls = _image_urls(row)
        local_images: list[str] = []
        provenance: list[dict[str, Any]] = []

        if download_images:
            for index, image_url in enumerate(urls[:6], start=1):
                try:
                    data, content_type = _fetch(image_url)
                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
                    counts["image_failures"] += 1
                    continue
                if len(data) < 4_000:
                    counts["image_failures"] += 1
                    continue
                name = f"image-{index:02d}{_extension(content_type, image_url)}"
                (product_dir / name).write_bytes(data)
                local_images.append(name)
                counts["images"] += 1
                provenance.append(
                    {
                        "provenance_id": f"{source}/{product_slug}/{Path(name).stem}",
                        "source_id": f"{source}/{product_slug}",
                        "acquired_at": acquired_at,
                        "acquisition_method": "market_intelligence_import",
                        "content_hash": f"sha256:{hashlib.sha256(data).hexdigest()}",
                        "byte_size": len(data),
                        "content_type": content_type,
                        "source_url": image_url,
                    }
                )

        product = {
            "product_id": f"{source}/{product_slug}",
            "brand_slug": source,
            "name": title,
            "source_url": url,
            "category": "market_listing",
            "price": str(_pick(row, "price", "")),
            "description": str(_pick(row, "description", "")),
            "images": local_images,
            "image_urls": urls,
            "acquired_at": acquired_at,
            "market_query": query,
            "commercial_signals": {
                "currency": str(_pick(row, "currency", "")),
                "rating": _number(_pick(row, "rating", "")),
                "review_count": _number(_pick(row, "review_count", "")),
                "sales_count": _number(_pick(row, "sales_count", "")),
                "rank": _number(_pick(row, "rank", "")),
            },
            # Kept for audit/re-analysis, explicitly not a creative input.
            "source_record": row,
        }
        (product_dir / "product.json").write_text(json.dumps(product, indent=2), encoding="utf-8")
        (product_dir / "provenance.json").write_text(
            json.dumps(provenance, indent=2), encoding="utf-8"
        )
        counts["written"] += 1

    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "brand.json").write_text(
        json.dumps(
            {
                "brand_slug": source,
                "brand_name": source.title(),
                "site_url": "",
                "acquired_at": acquired_at,
                "design_tradition": "market_intelligence",
                "notes": "Commercial research source. Never use source copy or subjects as creative direction.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return counts


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Thunderbit/other CSV, JSON or JSONL export")
    parser.add_argument("--source", required=True, help="etsy, amazon, etc")
    parser.add_argument("--query", default="", help="search/query that produced the export")
    parser.add_argument(
        "--download-images",
        action="store_true",
        help="download up to six listing images so the existing visual pass can analyse them",
    )
    args = parser.parse_args(argv[1:])

    try:
        counts = import_rows(args.path, args.source, args.query, args.download_images)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"import failed: {error}", file=sys.stderr)
        return 2

    print(
        f"{counts['written']} listings written from {counts['rows']} rows; "
        f"{counts['images']} images, {counts['image_failures']} image failures, "
        f"{counts['refused']} refused"
    )
    if args.download_images:
        print("next: python scripts/visual_pass_queue.py --build")
    return 0 if counts["written"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
