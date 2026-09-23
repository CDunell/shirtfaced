#!/usr/bin/env python3
"""Stage 4 — measurement. Same split mymixups' own performance.py landed on,
because the two halves have different prerequisites:

--ranks   Real SERP position for shirtfaced.wtf against every query in
          keywords.json, via the same Bright Data call harvest.py already
          uses. Needs nothing but the bdata CLI. Answers a question Search
          Console can't: where this site sits for a query it gets zero
          impressions for yet (i.e. before it's even indexed for that term).

--console Pulls Google Search Console. NOT WIRED YET, and can't be from
          here -- shirtfaced.wtf has no google-site-verification TXT record
          on its DNS (checked against docs/dns.md's real record list), so
          there's no property to pull from. Standing it up needs the owner
          directly:
            1. Add shirtfaced.wtf as a domain property in Search Console
               (needs the owner's Google account).
            2. Put the TXT value Search Console hands back on the Cloudflare
               zone (see docs/dns.md).
            3. Create a GCP service account, add its email as a read-only
               user on the property.
            4. Set GOOGLE_APPLICATION_CREDENTIALS to that account's key file.
          Impressions accrue from verification onward, not retroactively --
          the sooner the property exists, the sooner any of this is
          measurable. This flag exits with that explanation rather than
          pretending to pull data that doesn't exist yet.

Run: python tools/seo/performance.py --ranks
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KEYWORDS_PATH = Path(__file__).parent / "data" / "keywords.json"
OUT_PATH = Path(__file__).parent / "data" / "performance.json"

BDATA_BIN = shutil.which("bdata")


def our_rank(query: str, domain: str = "shirtfaced.wtf") -> int | None:
    if not BDATA_BIN:
        return None
    proc = subprocess.run(
        [BDATA_BIN, "search", query, "--country", "au", "--json"],
        capture_output=True, text=True, timeout=60, check=False,
        encoding="utf-8", errors="replace",
    )
    stdout = proc.stdout or ""
    first_line = stdout.strip().splitlines()[0] if stdout.strip() else ""
    if not first_line:
        return None
    try:
        serp = json.loads(first_line)
    except json.JSONDecodeError:
        return None
    for i, result in enumerate(serp.get("organic", []), start=1):
        link = result.get("link", "")
        if domain in re.sub(r"^https?://(www\.)?", "", link).split("/")[0]:
            return i
    return None


def run_ranks() -> None:
    if not KEYWORDS_PATH.exists():
        sys.exit(f"{KEYWORDS_PATH} doesn't exist -- run harvest.py first.")
    rows = json.loads(KEYWORDS_PATH.read_text(encoding="utf-8"))

    results = []
    for row in rows:
        query = row["query"]
        rank = our_rank(query)
        print(f"[performance] {query!r}: {'not in top 10' if rank is None else f'#{rank}'}")
        results.append({
            "query": query,
            "checked": date.today().isoformat(),
            "rank": rank,
            "mapped_url": row.get("mapped_url"),
        })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"[performance] wrote {len(results)} rows to {OUT_PATH}")


def run_console() -> None:
    print(
        "Search Console isn't wired: shirtfaced.wtf has no google-site-\n"
        "verification TXT record on its DNS zone yet (see docs/dns.md for\n"
        "the real current record list). Four steps to stand it up, and only\n"
        "the first needs you directly:\n"
        "  1. Add shirtfaced.wtf as a domain property in Search Console\n"
        "     (your Google account).\n"
        "  2. Put the TXT value it hands back on the Cloudflare zone.\n"
        "  3. Create a GCP service account, add it as a read-only user on\n"
        "     the property.\n"
        "  4. Set GOOGLE_APPLICATION_CREDENTIALS to that account's key.\n"
        "Impressions accrue from verification onward, not retroactively."
    )
    sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranks", action="store_true")
    parser.add_argument("--console", action="store_true")
    args = parser.parse_args()

    if not args.ranks and not args.console:
        parser.print_help()
        return 1
    if args.ranks:
        run_ranks()
    if args.console:
        run_console()
    return 0


if __name__ == "__main__":
    sys.exit(main())
