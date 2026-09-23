#!/usr/bin/env python3
"""Keyword harvest — seeds.yaml -> tools/seo/data/keywords.json.

For each seed, pulls a real AU-localised SERP (via the `bdata` CLI, Bright
Data's SERP API), harvests People Also Ask questions and related searches as
further candidate queries, then scores every query (seed and expansion
alike) on its own SERP: how weak the current top-10 looks (forums/
marketplaces vs brand sites, title-match strength, whether a shopping pack
owns the page), and whether intent is transactional (mapped to a real page
on this site) or informational (a candidate for Stage 3's blog).

No volume numbers are claimed anywhere in this output -- Bright Data's SERP
API doesn't provide search volume, and pretending otherwise would be the
same fabrication problem as an invented size chart. Weakness is the
observable proxy, same choice mymixups' own harvest made.

Run: python tools/seo/harvest.py
Needs: `bdata` CLI on PATH, already authenticated (see brightdata-plugin).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SEEDS_PATH = Path(__file__).parent / "seeds.yaml"
OUT_PATH = Path(__file__).parent / "data" / "keywords.json"

# subprocess.run's default resolver can't find a Windows npm global's .cmd
# shim from a plain ["bdata", ...] argv the way a real shell would -- resolve
# the actual executable path once up front instead.
BDATA_BIN = shutil.which("bdata")
if not BDATA_BIN:
    sys.exit("bdata CLI not found on PATH -- see brightdata-plugin setup.")

# A SERP result on one of these domains doesn't compete with a brand page --
# counting it as "weak" is what makes weakness score mean something instead
# of just echoing how well-known the query is.
WEAK_DOMAINS = (
    "reddit.com", "quora.com", "pinterest.", "facebook.com", "instagram.com",
    "amazon.", "ebay.", "etsy.com", "youtube.com", "tiktok.com",
    "marketplace", "forum", "wikipedia.org",
)

# Real, sellable surface today -- only tees exist as actual stock (see
# docs/pre-golive.md: tanks/hoodies/hats/accessories are nav entries with
# nothing behind them). A transactional query maps to /shop only when it's
# plausibly about the thing that's actually for sale.
TRANSACTIONAL_HINTS = ("buy", "shop", "tee", "tees", "t-shirt", "t-shirts", "shirt")
PRODUCT_TERMS = ("tee", "tees", "t-shirt", "t-shirts", "shirt", "graphic tee", "graphic tees")


def run_search(query: str, retries: int = 2) -> dict | None:
    """One real SERP call. Returns None (not a fabricated empty result) if
    every attempt fails -- a caller must handle that explicitly, not treat
    it as a zero-result query. mymixups' own harvest lost 31/113 rows to
    exactly this shortcut (a failed call parsed as if it had succeeded)."""
    for attempt in range(retries + 1):
        try:
            proc = subprocess.run(
                [BDATA_BIN, "search", query, "--country", "au", "--json"],
                capture_output=True, text=True, timeout=60, check=False,
                encoding="utf-8", errors="replace",
            )
        except subprocess.TimeoutExpired:
            continue
        if proc.returncode != 0:
            continue
        # The CLI's first stdout line is the JSON payload; a trailing
        # "Searching..." status line or blank line can follow it, so only
        # the first line is ever parsed here.
        stdout = proc.stdout or ""
        first_line = stdout.strip().splitlines()[0] if stdout.strip() else ""
        if not first_line:
            continue
        try:
            data = json.loads(first_line)
        except json.JSONDecodeError:
            continue
        # A call that "succeeded" with zero organic results is the exact
        # silent-failure shape mymixups hit -- treat it as a failed attempt,
        # not a real empty SERP, and retry rather than record it as weak=10.
        if not data.get("organic"):
            continue
        return data
    return None


def domain_of(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower()


def title_match_strength(query: str, titles: list[str]) -> float:
    """Fraction of the query's significant words (len > 2) that appear in at
    least one of the top-10 titles -- a proxy for how directly the current
    results address this exact query, not just the topic generally."""
    words = [w for w in re.findall(r"[a-z]+", query.lower()) if len(w) > 2]
    if not words:
        return 0.0
    joined = " ".join(t.lower() for t in titles)
    hits = sum(1 for w in words if w in joined)
    return hits / len(words)


def score_weakness(serp: dict) -> int:
    """0 (dominated by strong brand results) to 10 (wide open) -- observable
    from the SERP itself, not a volume/competition number nobody here has
    access to."""
    organic = serp.get("organic", [])[:10]
    if not organic:
        return 0
    weak_count = sum(
        1 for r in organic if any(d in domain_of(r.get("link", "")) for d in WEAK_DOMAINS)
    )
    titles = [r.get("title", "") for r in organic]
    match = title_match_strength(serp.get("general", {}).get("query", ""), titles)
    shopping_pack = bool(serp.get("popular_products"))

    score = 0
    score += round((weak_count / len(organic)) * 5)  # up to 5 for forum/marketplace clutter
    score += round((1 - match) * 3)  # up to 3 for weak title-match
    score += 0 if shopping_pack else 2  # +2 if nothing's already claimed the transactional slot
    return max(0, min(10, score))


def classify_intent(query: str, serp: dict) -> str:
    q = query.lower()
    if serp.get("popular_products") or any(h in q for h in TRANSACTIONAL_HINTS):
        return "transactional"
    return "informational"


def mapped_url(query: str, intent: str) -> str | None:
    if intent != "transactional":
        return None
    return "/shop" if any(t in query.lower() for t in PRODUCT_TERMS) else None


@dataclass
class Row:
    query: str
    source_seed: str
    serp_snapshot_date: str
    weakness_score: int
    intent: str
    mapped_url: str | None

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "source_seed": self.source_seed,
            "serp_snapshot_date": self.serp_snapshot_date,
            "weakness_score": self.weakness_score,
            "intent": self.intent,
            "mapped_url": self.mapped_url,
        }


def expand_seed(seed: str) -> tuple[dict | None, list[str]]:
    """Seed's own SERP, plus every People-Also-Ask question and related-
    search phrase as further candidate queries -- deduplicated, seed itself
    excluded."""
    serp = run_search(seed)
    if serp is None:
        return None, []
    candidates: list[str] = []
    for item in serp.get("people_also_ask", []) or []:
        q = (item.get("question") or "").strip()
        if q:
            candidates.append(q)
    for item in serp.get("related", []) or []:
        q = (item.get("text") or "").strip()
        if q:
            candidates.append(q)
    seen = {seed.lower()}
    deduped = []
    for c in candidates:
        if c.lower() not in seen:
            seen.add(c.lower())
            deduped.append(c)
    return serp, deduped


def main() -> int:
    seeds_doc = yaml.safe_load(SEEDS_PATH.read_text(encoding="utf-8"))
    all_seeds = [s for group in seeds_doc.values() for s in group]

    today = date.today().isoformat()
    rows: list[Row] = []
    failures: list[str] = []

    for seed in all_seeds:
        print(f"[harvest] seed: {seed}")
        seed_serp, expansions = expand_seed(seed)
        if seed_serp is None:
            print(f"  FAILED after retries -- skipping seed and its expansions")
            failures.append(seed)
            continue

        rows.append(Row(
            query=seed,
            source_seed=seed,
            serp_snapshot_date=today,
            weakness_score=score_weakness(seed_serp),
            intent=classify_intent(seed, seed_serp),
            mapped_url=mapped_url(seed, classify_intent(seed, seed_serp)),
        ))

        for expansion in expansions:
            exp_serp = run_search(expansion)
            if exp_serp is None:
                failures.append(expansion)
                print(f"  expansion FAILED: {expansion}")
                continue
            intent = classify_intent(expansion, exp_serp)
            rows.append(Row(
                query=expansion,
                source_seed=seed,
                serp_snapshot_date=today,
                weakness_score=score_weakness(exp_serp),
                intent=intent,
                mapped_url=mapped_url(expansion, intent),
            ))
            print(f"  + {expansion}  (weakness={rows[-1].weakness_score}, {intent})")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps([r.to_dict() for r in rows], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\n[harvest] wrote {len(rows)} rows to {OUT_PATH}")
    if failures:
        print(f"[harvest] {len(failures)} queries failed after retries and were skipped, not recorded as zero-result: {failures}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
