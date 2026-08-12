#!/usr/bin/env python3
"""Build the existing visual-pass queue for market-intelligence listings.

This deliberately reuses ``visual_pass_queue`` rather than inventing a second
image-analysis path. The only difference is the corpus root and output file.

    python scripts/market_visual_queue.py

Writes ``var/design_corpus_market/visual_queue.json``. Describe those frames with
the same visual pass used for the brand/flat corpora, then feed the resulting
JSON rows to ``score_market_intelligence.py``.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import visual_pass_queue

ROOT = Path(__file__).resolve().parent.parent
MARKET_ROOT = ROOT / "var" / "design_corpus_market"
QUEUE_PATH = MARKET_ROOT / "visual_queue.json"


def main() -> int:
    if not MARKET_ROOT.is_dir():
        print(
            "no market corpus — run import_market_intelligence.py first",
            file=sys.stderr,
        )
        return 1

    original = visual_pass_queue.CORPORA
    try:
        visual_pass_queue.CORPORA = {"market": MARKET_ROOT}
        result = visual_pass_queue.build()
    finally:
        visual_pass_queue.CORPORA = original

    queue = result["queue"]
    QUEUE_PATH.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"{len(queue)} market frames queued; {sum(result['dropped'].values())} dropped")
    for source, count in Counter(row["brand"] for row in queue).most_common():
        print(f"  {count:>6}  {source}")
    print(f"written to {QUEUE_PATH}")
    return 0 if queue else 1


if __name__ == "__main__":
    raise SystemExit(main())
