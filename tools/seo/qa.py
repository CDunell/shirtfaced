#!/usr/bin/env python3
"""QA gate — a lint pass over every draft in content/blog/*.mdx, run before a
human reads it. A pre-filter only: passing QA doesn't approve a post, it just
means a human's review time isn't spent catching mechanical mistakes.
Publishing stays a human decision either way (flip status to approved by
hand) -- this script never changes that field.

Checks:
- Every /products/[slug] link resolves against the real catalogue.
- At least 2 real product links (see write.py's own generation rule).
- No duplicate title or description against another post already in the dir.
- Word count in a sane range (400-1500) -- too short isn't a real article,
  too long wasn't asked for.
- Has an actual title/description/date in frontmatter, not empty strings.
- No unresolved markdown link syntax (a stray `[text](` with no closing paren
  content, the kind of thing that slips through hand-editing).

Run: python tools/seo/qa.py
Exits non-zero if anything fails, same convention as a normal lint step.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = ROOT / "content" / "blog"
PRODUCTS_PATH = ROOT / "src" / "lib" / "products-data.generated.ts"


def real_product_slugs() -> set[str]:
    text = PRODUCTS_PATH.read_text(encoding="utf-8")
    match = re.search(r"export const products: Product\[\] = (\[.*\]);", text, re.S)
    if not match:
        return set()
    return {p["slug"] for p in json.loads(match.group(1))}


def parse_post(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\n(.*?)\n---\n\n(.*)$", raw, re.S)
    if not fm_match:
        return {}, raw
    return yaml.safe_load(fm_match.group(1)) or {}, fm_match.group(2)


def main() -> int:
    if not CONTENT_DIR.exists():
        print("[qa] no content/blog directory yet -- nothing to check.")
        return 0

    paths = sorted(CONTENT_DIR.glob("*.mdx"))
    if not paths:
        print("[qa] no drafts found.")
        return 0

    valid_slugs = real_product_slugs()
    seen_titles: dict[str, Path] = {}
    seen_descriptions: dict[str, Path] = {}
    failures: list[str] = []

    for path in paths:
        fm, body = parse_post(path)
        label = path.name

        for field in ("title", "description", "date"):
            if not fm.get(field):
                failures.append(f"{label}: missing or empty frontmatter field '{field}'")

        title = fm.get("title", "")
        if title:
            if title in seen_titles:
                failures.append(f"{label}: duplicate title, also used by {seen_titles[title].name}")
            seen_titles[title] = path

        description = fm.get("description", "")
        if description:
            if description in seen_descriptions:
                failures.append(f"{label}: duplicate description, also used by {seen_descriptions[description].name}")
            seen_descriptions[description] = path

        word_count = len(re.findall(r"\S+", body))
        if not (400 <= word_count <= 1500):
            failures.append(f"{label}: word count {word_count} outside 400-1500")

        product_links = re.findall(r"/products/([a-z0-9-]+)", body)
        bad_links = [slug for slug in product_links if slug not in valid_slugs]
        for slug in bad_links:
            failures.append(f"{label}: links /products/{slug}, which doesn't exist in the real catalogue")
        if len(set(product_links) - set(bad_links)) < 2:
            failures.append(f"{label}: fewer than 2 valid real product links (found {len(set(product_links) - set(bad_links))})")

        if re.search(r"\[[^\]]+\]\(\s*\)", body):
            failures.append(f"{label}: contains an empty markdown link target")

        status = fm.get("status")
        if status not in ("draft", "approved"):
            failures.append(f"{label}: status is {status!r}, must be 'draft' or 'approved'")

    if failures:
        print(f"[qa] {len(failures)} issue(s):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(f"[qa] {len(paths)} draft(s) checked, all clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
