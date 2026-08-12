"""Index the archive by what its sources already say about each piece.

``var/design_archive/`` holds thousands of images across a dozen collectors and
no way to find anything in it. The material worth pulling out -- a 1978 Stones
tour tee, a 1994 Powell graphic -- is in there, but only its filename knows.

Every source labels its own stock, and labels it well, because that is what
sells it or files it:

    Vintage 1993 Metallica No Where Else To Roam     (Sell Merchandise)
    1969 Woodstock Peace Staff Windbreaker Jacket    (Wyco)
    Powell Peralta Fire Balls VTG 1994               (Streetwear Archive)

So this reads the titles the collectors recorded and writes an index over them.
It does not look at a single pixel, and it infers nothing: a decade is recorded
when the title states one and left null when it does not. A title that says
"vintage" and no more is undated here, because it is undated in fact -- the
alternative is a guess that later reads as a finding.

    python scripts/index_archive.py                       # summary by decade
    python scripts/index_archive.py --decade 1970s
    python scripts/index_archive.py --grep "grateful dead"
    python scripts/index_archive.py --write               # index.json at the root
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ARCHIVE_ROOT = Path(__file__).resolve().parent.parent / "var" / "design_archive"

# Four-digit years first: an explicit 1993 beats a vague "90s" in the same title.
# Bounded 1960-2009 -- earlier is not graphic-apparel, later is not archive, and
# an unbounded pattern matches prices, sizes and product codes.
YEAR_RE = re.compile(r"\b(19[6-9]\d|200\d)\b")
DECADE_RE = re.compile(r"\b(?:19)?([2-9]0)'?s\b", re.IGNORECASE)


def decade_of(title: str) -> str | None:
    """The decade this title states, or None. Never inferred."""
    year = YEAR_RE.search(title or "")
    if year:
        return f"{int(year.group(1)) // 10 * 10}s"
    decade = DECADE_RE.search(title or "")
    if decade:
        value = int(decade.group(1))
        # Two-digit decades are ambiguous by nature: "90s" is 1990s, "00s" is
        # 2000s. Anything from 20 to 90 reads as twentieth century, which is the
        # only reading these sources ever intend.
        return f"20{value:02d}s" if value < 20 else f"19{value}s"
    return None


def rows() -> list[dict[str, Any]]:
    """One row per collected piece, from whatever record its collector wrote."""
    out: list[dict[str, Any]] = []
    for record in sorted(ARCHIVE_ROOT.glob("*/*/*/*.json")):
        if record.name not in {"item.json", "product.json"}:
            continue
        try:
            data = json.loads(record.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        # The two record shapes name their title differently. Both are the
        # source's own words and neither is normalised here.
        title = data.get("listing_title") or data.get("name") or ""
        out.append(
            {
                "source": record.parent.parent.parent.name,
                "id": data.get("item_id") or data.get("product_id") or record.parent.name,
                "title": title,
                "decade": decade_of(title),
                "categories": data.get("categories") or [],
                "images": len(data.get("images") or []),
                "path": str(record.parent.relative_to(ARCHIVE_ROOT)),
            }
        )
    return out


def main(argv: list[str]) -> int:
    if not ARCHIVE_ROOT.exists():
        print(f"No archive at {ARCHIVE_ROOT}", file=sys.stderr)
        return 1
    data = rows()
    if not data:
        print("Archive holds no records yet.", file=sys.stderr)
        return 1

    if "--write" in argv:
        (ARCHIVE_ROOT / "index.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"{len(data)} rows -> {ARCHIVE_ROOT / 'index.json'}")
        return 0

    selected = data
    if "--decade" in argv:
        try:
            want = argv[argv.index("--decade") + 1]
        except IndexError:
            print("--decade needs a value, e.g. 1970s", file=sys.stderr)
            return 2
        selected = [r for r in selected if r["decade"] == want]
    if "--grep" in argv:
        try:
            term = argv[argv.index("--grep") + 1].lower()
        except IndexError:
            print("--grep needs a term", file=sys.stderr)
            return 2
        selected = [
            r
            for r in selected
            if term in r["title"].lower() or any(term in c.lower() for c in r["categories"])
        ]

    if "--decade" in argv or "--grep" in argv:
        for row in selected[:200]:
            print(f"  {row['decade'] or '----':<6} {row['images']:>2}img  {row['title'][:64]}")
            print(f"         {row['path']}")
        print(f"\n{len(selected)} pieces, {sum(r['images'] for r in selected)} images")
        return 0

    dated = [r for r in data if r["decade"]]
    sources = {r["source"] for r in data}
    print(f"{len(data)} pieces, {sum(r['images'] for r in data)} images, {len(sources)} sources")
    print(f"{len(dated)} dated by their source ({len(dated) * 100 // len(data)}%)\n")
    for decade, count in sorted(Counter(r["decade"] for r in dated).items()):
        images = sum(r["images"] for r in data if r["decade"] == decade)
        print(f"  {decade:<8} {count:>5} pieces  {images:>6} images")
    print("\nby source:")
    for source, count in Counter(r["source"] for r in data).most_common():
        dated_here = sum(1 for r in data if r["source"] == source and r["decade"])
        print(f"  {source:<24} {count:>5} pieces  {dated_here:>5} dated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
