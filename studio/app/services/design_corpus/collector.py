"""Shared persistence/provenance helpers for design-corpus acquisition."""
from __future__ import annotations

import hashlib
import json
import mimetypes
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def provenance_record(*, source_id: str, image_stem: str, source_url: str, data: bytes,
                      content_type: str = "image/jpeg", acquisition_method: str = "web_scrape",
                      acquired_at: str | None = None) -> dict[str, object]:
    return {
        "provenance_id": f"{source_id}/{image_stem}",
        "source_id": source_id,
        "acquired_at": acquired_at or utc_now(),
        "acquisition_method": acquisition_method,
        "content_hash": sha256_bytes(data),
        "byte_size": len(data),
        "content_type": content_type,
        "source_url": source_url,
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_manifest(root: Path) -> dict[str, object]:
    """Derive manifest deterministically from corpus contents; never hand-count."""
    brands: list[dict[str, object]] = []
    if root.is_dir():
        for brand_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            products_dir = brand_dir / "products"
            product_dirs = sorted(p for p in products_dir.iterdir() if p.is_dir()) if products_dir.is_dir() else []
            image_count = 0
            product_count = 0
            for product_dir in product_dirs:
                record = product_dir / "product.json"
                if not record.is_file():
                    continue
                product_count += 1
                try:
                    images = json.loads(record.read_text(encoding="utf-8")).get("images", [])
                except (OSError, ValueError):
                    images = []
                image_count += sum(1 for name in images if (product_dir / str(name)).is_file())
            if product_count:
                brands.append({"brand_slug": brand_dir.name, "product_count": product_count, "image_count": image_count})
    manifest = {"generated_at": utc_now(), "brands": brands}
    write_json(root / "manifest.json", manifest)
    return manifest


def extension_for(content_type: str, url: str) -> str:
    guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
    if guessed in {".jpg", ".jpeg", ".png", ".webp"}:
        return ".jpg" if guessed == ".jpeg" else guessed
    suffix = Path(url.split("?", 1)[0]).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
