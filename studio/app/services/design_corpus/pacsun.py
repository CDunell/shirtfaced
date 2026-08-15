"""PacSun men's graphic-tee evidence collector.

Acquisition only: real catalogue facts, images and provenance. Selection hints are
used transiently to avoid a first-N sample; they are never persisted as analysis.
"""
from __future__ import annotations

import html
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from .collector import build_manifest, extension_for, provenance_record, utc_now, write_json

BRAND_SLUG = "pacsun"
BRAND_NAME = "PacSun"
SITE_URL = "https://www.pacsun.com"
DEFAULT_START_URL = f"{SITE_URL}/mens/graphic-tees/"
REQUEST_DELAY = 0.45
USER_AGENT = "Mozilla/5.0 (compatible; ShirtfacedDesignResearch/1.0; +https://shirtfaced.wtf)"

# Explicit construction/noise exclusions. The category itself contains these.
NOISE = re.compile(r"\b(pack|solid|blank|basic|polo|rugby|jersey|knit|sweater|hoodie|button[- ]?up|scallop)\b", re.I)
TEE = re.compile(r"\b(t[- ]?shirt|tee|muscle t[- ]?shirt|oversized t[- ]?shirt|cropped boxy t[- ]?shirt)\b", re.I)
# Only a transient diversity aid. These labels never enter product.json.
MECHANISMS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("licensed", re.compile(r"metallica|star wars|godfather|eminem|wwe|ufc|marvel|south park|coca.?cola|ford|formula 1|the met|keith haring", re.I)),
    ("sport", re.compile(r"ufc|wwe|nba|nfl|raiders|racing|formula|champion|rodman", re.I)),
    ("music", re.compile(r"metallica|eminem|tour|metro boomin|band", re.I)),
    ("art", re.compile(r"haring|floral|angel|cherub|art|met|paper wings", re.I)),
    ("dark", re.compile(r"misery|ominous|reaper|skull|bloody|grunge|goth|saint", re.I)),
    ("brand", re.compile(r"pacsun|script|logo|handstyles|field of study|nightlab|huf", re.I)),
    ("character", re.compile(r"cat|cartoon|spider|character|south park", re.I)),
    ("auto", re.compile(r"ford|mustang|formula|race|chopper", re.I)),
)

@dataclass
class Product:
    name: str
    source_url: str
    brand: str = ""
    price: str = ""
    description: str = ""
    image_urls: list[str] = field(default_factory=list)

    @property
    def slug(self) -> str:
        path = urllib.parse.urlparse(self.source_url).path.rstrip("/").split("/")[-1]
        path = re.sub(r"\.html$", "", path, flags=re.I)
        clean = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")
        return clean or re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")


def canonical_url(url: str, base: str = SITE_URL) -> str:
    absolute = urllib.parse.urljoin(base, html.unescape(url))
    parsed = urllib.parse.urlsplit(absolute)
    return urllib.parse.urlunsplit((parsed.scheme or "https", parsed.netloc.lower(), parsed.path, "", ""))


def _fetch(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/json,image/*"})
    with urllib.request.urlopen(request, timeout=35) as response:
        return response.read(), response.headers.get_content_type()


def _jsonld(markup: str) -> list[dict]:
    rows: list[dict] = []
    for raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', markup, re.I | re.S):
        try:
            value = json.loads(html.unescape(raw).strip())
        except (ValueError, TypeError):
            continue
        values = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, dict):
                rows.append(item)
                graph = item.get("@graph")
                if isinstance(graph, list):
                    rows.extend(x for x in graph if isinstance(x, dict))
    return rows


def parse_category(markup: str, page_url: str) -> tuple[list[Product], str | None]:
    """Parse product links and the site's next-page URL without assuming increments."""
    products: dict[str, Product] = {}
    # Product anchors are the durable fallback when JSON-LD ItemLists are absent.
    for href, label in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', markup, re.I | re.S):
        text = re.sub(r"<[^>]+>", " ", label)
        text = html.unescape(re.sub(r"\s+", " ", text)).strip()
        url = canonical_url(href, page_url)
        if "pacsun.com" not in urllib.parse.urlsplit(url).netloc or not re.search(r"\.html$|/product/|/products/", urllib.parse.urlsplit(url).path, re.I):
            continue
        if not TEE.search(text):
            continue
        products.setdefault(url, Product(name=text, source_url=url))
    for node in _jsonld(markup):
        if str(node.get("@type", "")).lower() != "itemlist":
            continue
        for entry in node.get("itemListElement") or []:
            item = entry.get("item") if isinstance(entry, dict) else None
            if not isinstance(item, dict):
                continue
            url = canonical_url(str(item.get("url") or ""), page_url)
            name = str(item.get("name") or "").strip()
            if url and name and TEE.search(name):
                products.setdefault(url, Product(name=name, source_url=url))
    next_url = None
    next_match = re.search(r'<a[^>]+(?:rel=["\']next["\']|class=["\'][^"\']*(?:next|load-more)[^"\']*["\'])[^>]+href=["\']([^"\']+)', markup, re.I)
    if next_match:
        next_url = canonical_url(next_match.group(1), page_url)
    return list(products.values()), next_url


def is_graphic_candidate(product: Product) -> bool:
    return bool(TEE.search(product.name)) and not bool(NOISE.search(product.name))


def parse_product(markup: str, source_url: str, fallback_name: str = "") -> Product:
    product = Product(name=fallback_name, source_url=canonical_url(source_url))
    for node in _jsonld(markup):
        if str(node.get("@type", "")).lower() != "product":
            continue
        product.name = str(node.get("name") or product.name).strip()
        brand = node.get("brand")
        product.brand = str(brand.get("name") if isinstance(brand, dict) else brand or "").strip()
        product.description = re.sub(r"<[^>]+>", " ", str(node.get("description") or ""))
        product.description = html.unescape(re.sub(r"\s+", " ", product.description)).strip()
        images = node.get("image") or []
        if isinstance(images, str):
            images = [images]
        product.image_urls.extend(canonical_url(str(url), source_url) for url in images if url)
        offers = node.get("offers")
        offer = offers[0] if isinstance(offers, list) and offers else offers
        if isinstance(offer, dict):
            currency, price = offer.get("priceCurrency"), offer.get("price") or offer.get("lowPrice")
            if price:
                product.price = f"{currency or 'USD'} {price}"
        break
    # PacSun/Demandware pages commonly expose large CDN images in srcset even when
    # Product JSON-LD carries only the hero. Preserve order and unique URLs.
    for url in re.findall(r'https?://[^"\'\s,>]+\.(?:jpe?g|png|webp)(?:\?[^"\'\s,>]*)?', markup, re.I):
        if "pacsun" in url.lower() or "scene7" in url.lower() or "demandware" in url.lower():
            product.image_urls.append(html.unescape(url))
    product.image_urls = list(dict.fromkeys(product.image_urls))
    return product


def select_images(urls: Iterable[str], maximum: int = 3) -> list[str]:
    """Prefer distinct front/back/detail hints; otherwise first unique high-value frames."""
    unique = list(dict.fromkeys(urls))
    picked: list[str] = []
    for hint in ("front", "back", "detail", "alternate", "alt"):
        match = next((u for u in unique if hint in u.lower() and u not in picked), None)
        if match:
            picked.append(match)
    for url in unique:
        if len(picked) >= maximum:
            break
        if url not in picked and not re.search(r"swatch|thumbnail|icon", url, re.I):
            picked.append(url)
    return picked[:maximum]


def select_sample(candidates: list[Product], limit: int) -> list[Product]:
    """Deterministic round-robin over visible mechanisms, then fill remaining slots."""
    selected: list[Product] = []
    used: set[str] = set()
    for _, pattern in MECHANISMS:
        match = next((p for p in candidates if p.source_url not in used and pattern.search(f"{p.brand} {p.name}")), None)
        if match:
            selected.append(match); used.add(match.source_url)
        if len(selected) >= limit:
            return selected
    # Spread across catalogue order rather than taking the first remainder.
    remaining = [p for p in candidates if p.source_url not in used]
    if remaining:
        step = max(1, len(remaining) // max(1, limit - len(selected)))
        for product in remaining[::step]:
            if len(selected) >= limit: break
            selected.append(product); used.add(product.source_url)
    return selected


def discover(start_url: str = DEFAULT_START_URL, max_pages: int = 50, fetch: Callable[[str], tuple[bytes, str]] = _fetch) -> tuple[list[Product], list[dict[str, str]]]:
    products: dict[str, Product] = {}
    failures: list[dict[str, str]] = []
    url: str | None = canonical_url(start_url)
    seen_pages: set[str] = set()
    pages = 0
    while url and url not in seen_pages and pages < max_pages:
        seen_pages.add(url); pages += 1
        try:
            body, _ = fetch(url)
            rows, next_url = parse_category(body.decode("utf-8", errors="replace"), url)
        except Exception as exc:  # recorded acquisition failure, never silent
            failures.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
            break
        for row in rows:
            products.setdefault(row.source_url, row)
        url = next_url
        time.sleep(REQUEST_DELAY)
    return list(products.values()), failures


def enrich(products: list[Product], fetch: Callable[[str], tuple[bytes, str]] = _fetch) -> tuple[list[Product], list[dict[str, str]]]:
    result: list[Product] = []
    failures: list[dict[str, str]] = []
    for stub in products:
        try:
            body, _ = fetch(stub.source_url)
            result.append(parse_product(body.decode("utf-8", errors="replace"), stub.source_url, stub.name))
        except Exception as exc:
            failures.append({"url": stub.source_url, "error": f"{type(exc).__name__}: {exc}"})
        time.sleep(REQUEST_DELAY)
    return result, failures


def acquire(selected: list[Product], root: Path, refresh: bool = False, fetch: Callable[[str], tuple[bytes, str]] = _fetch) -> tuple[int, int, list[dict[str, str]]]:
    brand_dir = root / BRAND_SLUG
    write_json(brand_dir / "brand.json", {"brand_slug": BRAND_SLUG, "brand_name": BRAND_NAME, "site_url": SITE_URL, "acquired_at": utc_now(), "notes": "Current-market men's graphic tee evidence sample."})
    hashes: dict[str, Path] = {}
    saved_products = saved_images = 0
    failures: list[dict[str, str]] = []
    for product in selected:
        product_dir = brand_dir / "products" / product.slug
        if product_dir.exists() and not refresh:
            continue
        product_dir.mkdir(parents=True, exist_ok=True)
        source_id = f"{BRAND_SLUG}/{product.slug}"
        filenames: list[str] = []
        provenance: list[dict[str, object]] = []
        for source_url in select_images(product.image_urls):
            try:
                data, content_type = fetch(source_url)
            except Exception as exc:
                failures.append({"url": source_url, "error": f"{type(exc).__name__}: {exc}"}); continue
            record = provenance_record(source_id=source_id, image_stem=f"image-{len(filenames)+1:02d}", source_url=source_url, data=data, content_type=content_type)
            digest = str(record["content_hash"])
            if digest in hashes:
                continue
            ext = extension_for(content_type, source_url)
            filename = f"image-{len(filenames)+1:02d}{ext}"
            (product_dir / filename).write_bytes(data)
            hashes[digest] = product_dir / filename
            filenames.append(filename); provenance.append(record); saved_images += 1
            time.sleep(REQUEST_DELAY)
        if not filenames:
            failures.append({"url": product.source_url, "error": "no useful images downloaded"}); continue
        record = {"product_id": source_id, "brand_slug": BRAND_SLUG, "name": product.name, "source_url": product.source_url, "category": "tee", "price": product.price, "description": product.description, "images": filenames, "acquired_at": utc_now()}
        # DESIGN_CORPUS_SCHEMA currently has no manufacturer/licensor field. Do not invent one.
        write_json(product_dir / "product.json", record)
        write_json(product_dir / "provenance.json", provenance)
        saved_products += 1
    build_manifest(root)
    return saved_products, saved_images, failures
