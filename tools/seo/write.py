#!/usr/bin/env python3
"""Article generator — one informational keyword row from
tools/seo/data/keywords.json -> content/blog/<slug>.mdx, status: draft.

Grounds the article in the current top-10 for its query (so it's not just
regurgitating training-data knowledge about a topic that may have moved on),
writes it in shirtfaced's own Storefront voice (docs/foundations/
BRAND_VOICE.md §2 — dry, deadpan, self-aware, plays regret for laughs), and
requires at least two real /products/[slug] links, same rule mymixups' own
write.py enforces for /mixups/[slug] links: an article that doesn't link the
real catalogue is filler, not something this pipeline exists to produce.

Never auto-publishes. Every article lands as status: draft and stays there
until a human reads it and flips the frontmatter to approved -- see
src/lib/blog.ts, which only ever reads approved posts.

Run: python tools/seo/write.py "<exact query from keywords.json>"
Needs: ANTHROPIC_API_KEY, bdata CLI authenticated (for grounding).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parents[2]
KEYWORDS_PATH = Path(__file__).parent / "data" / "keywords.json"
CONTENT_DIR = ROOT / "content" / "blog"
PRODUCTS_PATH = ROOT / "src" / "lib" / "products-data.generated.ts"
BRAND_VOICE_PATH = ROOT / "docs" / "foundations" / "BRAND_VOICE.md"
POSITIONING_PATH = ROOT / "docs" / "foundations" / "POSITIONING.md"

BDATA_BIN = shutil.which("bdata")


def load_keyword_row(query: str) -> dict:
    rows = json.loads(KEYWORDS_PATH.read_text(encoding="utf-8"))
    for row in rows:
        if row["query"].lower() == query.lower():
            return row
    sys.exit(f"'{query}' not found in {KEYWORDS_PATH} -- run harvest.py first.")


def ground_from_serp(query: str) -> str:
    """Real top-3 organic pages, scraped for actual current content -- not
    what an LLM already believes about the topic. A page that fails to
    scrape is skipped, not silently replaced with nothing said about it."""
    if not BDATA_BIN:
        return ""
    proc = subprocess.run(
        [BDATA_BIN, "search", query, "--country", "au", "--json"],
        capture_output=True, text=True, timeout=60, check=False,
        encoding="utf-8", errors="replace",
    )
    stdout = proc.stdout or ""
    first_line = stdout.strip().splitlines()[0] if stdout.strip() else ""
    if not first_line:
        return ""
    try:
        serp = json.loads(first_line)
    except json.JSONDecodeError:
        return ""

    grounding_parts = []
    for result in (serp.get("organic") or [])[:3]:
        url = result.get("link")
        if not url:
            continue
        scrape = subprocess.run(
            [BDATA_BIN, "scrape", url],
            capture_output=True, text=True, timeout=60, check=False,
            encoding="utf-8", errors="replace",
        )
        if scrape.returncode == 0 and scrape.stdout.strip():
            grounding_parts.append(f"### {result.get('title', url)}\n{scrape.stdout.strip()[:3000]}")
    return "\n\n".join(grounding_parts)


def real_products() -> list[dict]:
    """Read straight from the generated catalogue rather than re-deriving
    product data -- same file src/lib/products.ts itself reads from."""
    text = PRODUCTS_PATH.read_text(encoding="utf-8")
    match = re.search(r"export const products: Product\[\] = (\[.*\]);", text, re.S)
    if not match:
        return []
    # The file is JSON-compatible (JSON.stringify output), just with a
    # TS export wrapper around it.
    return json.loads(match.group(1))


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def build_prompt(query: str, grounding: str, products: list[dict]) -> str:
    brand_voice = BRAND_VOICE_PATH.read_text(encoding="utf-8")
    positioning = POSITIONING_PATH.read_text(encoding="utf-8")
    product_list = "\n".join(f"- {p['name']} — /products/{p['slug']} — {p.get('blurb', '')}" for p in products)

    return f"""You are writing one blog article for shirtfaced (shirtfaced.wtf), an
Australian humour-led high-end streetwear brand. Target query: "{query}"

Ground the article in what's actually true today, using the real search-result
content below -- don't rely on stale general knowledge about this topic.

REAL CURRENT SEARCH CONTENT FOR THIS QUERY:
{grounding or "(no grounding content retrieved -- write from the brand's own real positioning only, do not invent facts about competitors or the market)"}

BRAND VOICE (follow exactly -- this article is Storefront voice, per §2/§6):
{brand_voice}

POSITIONING (what shirtfaced is and is not -- do not violate §2's rule against
depicting Australian wildlife/food/national symbols, and do not invent claims
this document says are undecided):
{positioning}

REAL PRODUCTS available to link (pick at least 2 that are genuinely relevant
to this article's topic -- do not link a product that has nothing to do with
what the article is about):
{product_list}

Write a complete article (600-1000 words) that:
1. Actually answers/serves the query "{query}" -- informational intent, not a
   thinly-veiled product pitch.
2. Is written entirely in Storefront voice -- dry, deadpan, self-aware, never
   explains the joke, never forces slang.
3. Links at least 2 of the real products above, inline, using markdown links
   to their real /products/[slug] path, where it's actually relevant to what
   you're saying -- not bolted on.
4. Makes no factual claim about shirtfaced that isn't already established in
   the positioning/voice docs above or the grounding content -- no invented
   founding story, no invented specs, no invented claims about competitors.
5. Has a real, specific title (not generic filler) and a one-sentence meta
   description.

Output ONLY the article body in Markdown (no frontmatter, no title as an H1 --
the page renders the title separately). Start straight into the first paragraph."""


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("usage: python tools/seo/write.py \"<query>\"")
    query = sys.argv[1]

    row = load_keyword_row(query)
    if row["intent"] != "informational":
        print(f"warning: '{query}' is classified transactional, not informational -- "
              f"mapped_url is {row['mapped_url']!r}. This pipeline writes articles for "
              f"informational gaps; a transactional query's copy belongs on that real page, "
              f"not a blog post competing with it.")

    print(f"[write] grounding '{query}' from its real current SERP...")
    grounding = ground_from_serp(query)

    products = real_products()
    prompt = build_prompt(query, grounding, products)

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    print("[write] generating with claude-opus-5...")
    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    body = "".join(block.text for block in response.content if block.type == "text").strip()

    # Title: first line if it reads like one, else derive from the query.
    first_line = body.split("\n", 1)[0].strip().lstrip("#").strip()
    title = first_line if 0 < len(first_line) < 90 else query.capitalize()
    slug = slugify(title)

    linked_products = [p["slug"] for p in products if f"/products/{p['slug']}" in body]
    if len(linked_products) < 2:
        print(f"[write] WARNING: only {len(linked_products)} real product link(s) found in "
              f"the draft -- rule 3 asked for at least 2. Review before approving.")

    frontmatter = {
        "title": title,
        "slug": slug,
        "description": row["query"],
        "date": date.today().isoformat(),
        "keywords": [row["query"]],
        "products": linked_products,
        "status": "draft",
    }

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CONTENT_DIR / f"{slug}.mdx"
    fm_lines = "\n".join(
        f'{k}: {json.dumps(v)}' for k, v in frontmatter.items()
    )
    out_path.write_text(f"---\n{fm_lines}\n---\n\n{body}\n", encoding="utf-8")
    print(f"[write] wrote {out_path} (status: draft -- read it, then flip to approved)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
