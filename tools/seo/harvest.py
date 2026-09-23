#!/usr/bin/env python3
"""Keyword harvest — seeds.yaml -> tools/seo/data/keywords.jsonl.

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

CRASH SAFETY: every row is appended to keywords.jsonl and flushed to disk
the moment it's scored -- not batched in memory and written once at the end.
A run that's killed, times out, or loses its terminal partway through keeps
every row it already paid for. Re-running the script skips queries already
present in keywords.jsonl rather than re-harvesting them (delete the file,
or a specific line, to force a re-harvest of something).

Run: python tools/seo/harvest.py
Needs: `bdata` CLI on PATH, already authenticated (see brightdata-plugin).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

# Unbuffered stdout regardless of how this is invoked (piped to a file,
# backgrounded, etc.) -- progress should be visible live, not sitting in a
# buffer until the process exits. That silence previously looked identical
# to a hang from the outside.
sys.stdout.reconfigure(line_buffering=True)

ROOT = Path(__file__).resolve().parents[2]
SEEDS_PATH = Path(__file__).parent / "seeds.yaml"
JSONL_PATH = Path(__file__).parent / "data" / "keywords.jsonl"
JSON_PATH = Path(__file__).parent / "data" / "keywords.json"

BDATA_BIN = shutil.which("bdata")
if not BDATA_BIN:
    sys.exit("bdata CLI not found on PATH -- see brightdata-plugin setup.")

WEAK_DOMAINS = (
    "reddit.com", "quora.com", "pinterest.", "facebook.com", "instagram.com",
    "amazon.", "ebay.", "etsy.com", "youtube.com", "tiktok.com",
    "marketplace", "forum", "wikipedia.org",
)

# A query word alone was the bug: "Why are graphic tees so expensive?" has
# "tees" in it and is not transactional. Direct commercial intent (buy it,
# find it cheap, find a seller near you) overrides everything else, even a
# question form -- "where can I buy graphic tees" is still transactional.
COMMERCIAL_INTENT = (
    "buy", "shop", "for sale", "price", "prices", "cheap", "cheapest",
    "discount", "deal", "near me", "shipping", "delivery", "order",
)
# A question mark or a leading interrogative/auxiliary word marks a query as
# asking something, not shopping for something -- checked only after the
# commercial-intent override above, so it can't relabel "where to buy X" as
# informational just because it starts with "where".
QUESTION_STARTERS = (
    "why", "how", "what", "who", "when", "where", "which", "is", "are",
    "can", "do", "does", "should", "will", "was", "were",
)
PRODUCT_TERMS = ("tee", "tees", "t-shirt", "t-shirts", "shirt", "graphic tee", "graphic tees")


def run_search(query: str, retries: int = 2) -> dict | None:
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
        stdout = proc.stdout or ""
        first_line = stdout.strip().splitlines()[0] if stdout.strip() else ""
        if not first_line:
            continue
        try:
            data = json.loads(first_line)
        except json.JSONDecodeError:
            continue
        if not data.get("organic"):
            continue
        return data
    return None


def domain_of(url: str) -> str:
    return re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower()


def title_match_strength(query: str, titles: list[str]) -> float:
    words = [w for w in re.findall(r"[a-z]+", query.lower()) if len(w) > 2]
    if not words:
        return 0.0
    joined = " ".join(t.lower() for t in titles)
    hits = sum(1 for w in words if w in joined)
    return hits / len(words)


def score_weakness(serp: dict) -> int:
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
    score += round((weak_count / len(organic)) * 5)
    score += round((1 - match) * 3)
    score += 0 if shopping_pack else 2
    return max(0, min(10, score))


def classify_intent(query: str, serp: dict) -> str:
    """Priority order, each step only reached if the one above didn't decide:
    1. A shopping pack on the SERP or explicit commercial-intent wording
       ("buy", "price", "near me", ...) -> transactional, even in question
       form ("where can I buy graphic tees" is still transactional).
    2. A question mark or a leading interrogative/auxiliary word -> the
       query is asking something, not shopping -- informational.
    3. A short query containing a product term with no question form -> a
       category/navigational query ("graphic tees australia") -> transactional.
    4. Otherwise informational -- the safer default when genuinely unsure,
       so an uncertain row doesn't get pointed at /shop it may not belong on.
    """
    q = query.lower().strip()
    if serp.get("popular_products") or any(h in q for h in COMMERCIAL_INTENT):
        return "transactional"
    first_word = re.split(r"\s+", q, maxsplit=1)[0] if q else ""
    if q.endswith("?") or first_word in QUESTION_STARTERS:
        return "informational"
    if any(t in q for t in PRODUCT_TERMS):
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


def score_query(query: str, source_seed: str, serp: dict, today: str) -> Row:
    intent = classify_intent(query, serp)
    return Row(
        query=query,
        source_seed=source_seed,
        serp_snapshot_date=today,
        weakness_score=score_weakness(serp),
        intent=intent,
        mapped_url=mapped_url(query, intent),
    )


def append_row(row: Row) -> None:
    """Append-and-flush -- the durability guarantee this whole script exists
    to provide. json.dumps + write + flush + os.fsync, not buffered I/O left
    to the OS's own discretion about when it actually hits disk."""
    JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with JSONL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row.to_dict(), ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def load_done_queries() -> set[str]:
    if not JSONL_PATH.exists():
        return set()
    done = set()
    for line in JSONL_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            done.add(json.loads(line)["query"].lower())
        except (json.JSONDecodeError, KeyError):
            continue  # a truncated last line from a killed run -- ignore, don't crash on it
    return done


def expand_seed(seed: str) -> tuple[dict | None, list[str]]:
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


def consolidate_json() -> int:
    """keywords.json is a convenience snapshot regenerated from the real
    source of truth (the .jsonl) -- never written to directly, so it's never
    the thing that's at risk of a partial write."""
    rows = []
    if JSONL_PATH.exists():
        for line in JSONL_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(rows)


def main() -> int:
    seeds_doc = yaml.safe_load(SEEDS_PATH.read_text(encoding="utf-8"))
    all_seeds = [s for group in seeds_doc.values() for s in group]
    today = date.today().isoformat()

    done = load_done_queries()
    if done:
        print(f"[harvest] resuming -- {len(done)} queries already in {JSONL_PATH.name}, skipping those")

    failures: list[str] = []

    for seed in all_seeds:
        seed_done = seed.lower() in done
        print(f"[harvest] seed: {seed}" + (" (already scored, checking its expansions)" if seed_done else ""))

        # Re-derive the expansion list even for an already-scored seed --
        # a run killed after the seed but partway through its expansions
        # would otherwise orphan whatever expansions hadn't been reached
        # yet, since the expansion list itself is never persisted, only
        # each row that resulted from one. One redundant SERP call for an
        # already-done seed is a small, worthwhile price for never silently
        # leaving expansions unprocessed.
        seed_serp, expansions = expand_seed(seed)
        if seed_serp is None:
            print(f"  FAILED after retries -- skipping seed and its expansions")
            failures.append(seed)
            continue

        if not seed_done:
            row = score_query(seed, seed, seed_serp, today)
            append_row(row)
            done.add(seed.lower())
            print(f"  seed scored (weakness={row.weakness_score}, {row.intent})")

        for expansion in expansions:
            if expansion.lower() in done:
                continue
            exp_serp = run_search(expansion)
            if exp_serp is None:
                failures.append(expansion)
                print(f"  expansion FAILED: {expansion}")
                continue
            exp_row = score_query(expansion, seed, exp_serp, today)
            append_row(exp_row)
            done.add(expansion.lower())
            print(f"  + {expansion}  (weakness={exp_row.weakness_score}, {exp_row.intent})")

    total = consolidate_json()
    print(f"\n[harvest] {total} total rows in {JSON_PATH} (source of truth: {JSONL_PATH.name})")
    if failures:
        print(f"[harvest] {len(failures)} queries failed after retries and were skipped, not recorded as zero-result: {failures}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
