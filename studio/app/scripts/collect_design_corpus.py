"""Collect one current-market design evidence source.

    cd studio
    python -m app.scripts.collect_design_corpus pacsun --dry-run
    python -m app.scripts.collect_design_corpus pacsun --limit 15
"""
from __future__ import annotations

import argparse
from pathlib import Path

from app.services.design_corpus import pacsun

ROOT = Path(__file__).resolve().parents[2] / "var" / "design_corpus"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", choices=["pacsun"])
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--start-url", default=pacsun.DEFAULT_START_URL)
    args = parser.parse_args(argv)
    limit = min(15, max(12, args.limit))

    discovered, failures = pacsun.discover(args.start_url)
    rejected = [p for p in discovered if not pacsun.is_graphic_candidate(p)]
    candidates = [p for p in discovered if pacsun.is_graphic_candidate(p)]
    enriched, detail_failures = pacsun.enrich(candidates)
    candidates = [p for p in enriched if p.image_urls]
    selected = pacsun.select_sample(candidates, min(limit, len(candidates)))
    failures.extend(detail_failures)
    expected_images = sum(len(pacsun.select_images(p.image_urls)) for p in selected)

    print(f"catalogue products discovered: {len(discovered)}")
    print(f"rejected as non-graphic/noise: {len(rejected)}")
    print(f"graphic candidates: {len(candidates)}")
    print(f"selected sample: {len(selected)}")
    print(f"expected image count: {expected_images}")
    for product in selected:
        print(f"- {product.name} — {product.source_url}")
    if failures:
        print(f"crawl/detail failures: {len(failures)}")
        for failure in failures:
            print(f"! {failure['url']} — {failure['error']}")
    if args.dry_run:
        return 0 if selected else 1

    products, images, acquisition_failures = pacsun.acquire(selected, ROOT, refresh=args.refresh)
    failures.extend(acquisition_failures)
    print(f"products selected/stored: {products}")
    print(f"images downloaded: {images}")
    print(f"failures: {len(failures)}")
    print(f"corpus path: {ROOT / pacsun.BRAND_SLUG}")
    return 0 if 12 <= products <= 15 and not acquisition_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
