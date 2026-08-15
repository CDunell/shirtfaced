"""Join per-design measurements with phrase length into var/design_corpus/joined.json.

``app/services/design_advisor.py``'s ``advise()`` recommends scale role,
coverage, ink count and placement from the corpus, bucketed by how many words
the design's name carries -- but nothing produced the file it reads
(``joined.json``). ``mine_design_patterns.py`` measures the same corpus and
writes an aggregate report, not per-design rows, and never looks at a
product's name at all.

This walks the same corpus, reuses ``mine_design_patterns.py``'s measurement
function and ``design_advisor.py``'s word-counting logic unchanged -- no
description here is remeasured or reparsed a second way -- and writes one row
per printed design: tradition, phrase word count, coverage, ink count,
placement band, light-on-dark.

    python scripts/join_design_patterns.py
    python scripts/join_design_patterns.py --limit 200
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # studio/, for app.*

from corpus_tiers import is_excluded
from mine_design_patterns import CORPUS_ROOT, _analyse, _placement_band

from app.services.design_advisor import phrase_words

OUTPUT_PATH = CORPUS_ROOT / "joined.json"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="stop after N images")
    args = parser.parse_args(argv[1:])

    if not CORPUS_ROOT.exists():
        print("No corpus found. Run scripts/collect_design_corpus.py first.", file=sys.stderr)
        return 2

    rows: list[dict[str, object]] = []
    refused = 0
    seen = 0
    for brand_dir in sorted(CORPUS_ROOT.iterdir()):
        if is_excluded(brand_dir.name):
            continue
        brand_file = brand_dir / "brand.json"
        if not brand_file.is_file():
            continue
        brand = json.loads(brand_file.read_text(encoding="utf-8-sig"))
        tradition = brand.get("design_tradition", "unknown")

        # Nothing is skipped for its photography. See mine_design_patterns.py:
        # the edge test measures a worn garment as readily as a flat one, so the
        # blanket skip that used to sit here would now be throwing away evidence.

        products_dir = brand_dir / "products"
        if not products_dir.is_dir():
            continue
        for product_dir in sorted(products_dir.iterdir()):
            product_file = product_dir / "product.json"
            if not product_file.is_file():
                continue
            product = json.loads(product_file.read_text(encoding="utf-8-sig"))
            # The first image is the primary product shot, same convention as
            # mine_design_patterns.py -- later ones are alternate angles of
            # the same design and would double-count it.
            images = product.get("images") or []
            if not images:
                continue
            result = _analyse(product_dir / images[0])
            if result is None or "refused" in result:
                refused += 1
                continue
            if not result.get("has_print"):
                continue

            words = phrase_words(product.get("name", ""))
            rows.append(
                {
                    "t": tradition,
                    "w": len(words),
                    "cov": result["print_coverage"],
                    "ink": result["ink_colours"],
                    "band": _placement_band(result["centroid_y"]),
                    "lod": result["light_on_dark"],
                }
            )
            seen += 1
            if seen % 250 == 0:
                print(f"  {seen} analysed...", flush=True)
            if args.limit and seen >= args.limit:
                break
        if args.limit and seen >= args.limit:
            break

    OUTPUT_PATH.write_text(json.dumps(rows), encoding="utf-8")
    print(f"\n{len(rows)} printed designs joined (measured and phrase-lengthed)")
    print(f"written to {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
