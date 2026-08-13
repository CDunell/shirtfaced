"""Expose ``var/design_archive/`` to the vintage research service.

``vintage_research.py`` reads one directory per listing under
``VINTAGE_EVIDENCE_ROOT``: a ``record.json`` plus its images as siblings. The
archive collectors write a different shape -- ``<source>/<kind>/<slug>/`` with
``item.json`` or ``product.json``. Same idea, different nesting.

This writes the archive into the service's shape so both corpora can be read
through one root. It does not move or copy the collectors' output: images are
hard-linked, so 18,000 files cost inodes rather than gigabytes, and the archive
tree stays the single place they actually live.

Two constraints from the reader, both load-bearing:

*Directory names must be all digits* -- ``evidence_records()`` skips anything
else. Archive slugs are words, so each piece gets a synthetic numeric id derived
from a sha1 of its archive path. Deterministic, so a re-run overwrites rather
than duplicating, and started at 9e14 to sit far above eBay's twelve-digit
listing ids where the two can never collide.

*Filters compare brand, era_claim and tradition by exact lowercased equality.*
So those three fields decide whether a piece is reachable through the UI at all.
Where the archive does not know one, it is written as an empty string rather
than guessed -- an unfiltered query still returns it, and a filtered one
correctly does not.

What is deliberately not claimed: ``sold``. The eBay corpus carries sold
listings; nothing here is sold, and marking it so would put a verification on
records that never earned one. It is written ``"False"``.

    python scripts/adapt_archive_to_evidence.py --dry-run
    python scripts/adapt_archive_to_evidence.py --out var/vintage-evidence-merged
    VINTAGE_EVIDENCE_ROOT=studio/var/vintage-evidence-merged  # then point the service
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

STUDIO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_ROOT = STUDIO_ROOT / "var" / "design_archive"
DEFAULT_OUT = STUDIO_ROOT / "var" / "vintage-evidence-merged"

# Synthetic ids start here: above every real eBay listing id (twelve digits, low
# hundreds of billions), so a merged root can hold both without a collision.
ID_BASE = 900_000_000_000_000
ID_SPAN = 99_999_999_999

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

YEAR_RE = re.compile(r"\b(19[6-9]\d|200\d)\b")
DECADE_RE = re.compile(r"\b(?:19)?([2-9]0)'?s\b", re.IGNORECASE)


def decade_of(title: str) -> str:
    """The decade a title states, or "" when it states none. Never inferred."""
    year = YEAR_RE.search(title or "")
    if year:
        return f"{int(year.group(1)) // 10 * 10}s"
    decade = DECADE_RE.search(title or "")
    if decade:
        value = int(decade.group(1))
        return f"20{value:02d}s" if value < 20 else f"19{value}s"
    return ""


def synthetic_id(archive_path: str) -> str:
    digest = hashlib.sha1(archive_path.encode("utf-8")).hexdigest()
    return str(ID_BASE + int(digest[:16], 16) % ID_SPAN)


def source_traditions() -> dict[str, str]:
    """Tradition per archive source, from whichever manifest that source wrote."""
    traditions: dict[str, str] = {}
    for source_dir in sorted(p for p in ARCHIVE_ROOT.iterdir() if p.is_dir()):
        for name in ("cell.json", "brand.json"):
            path = source_dir / name
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            value = data.get("design_tradition") or ""
            if value:
                traditions[source_dir.name] = value
                break
    return traditions


def archive_pieces() -> list[dict[str, Any]]:
    """Every collected piece, with its record and its images on disk."""
    traditions = source_traditions()
    pieces: list[dict[str, Any]] = []
    for record_path in sorted(ARCHIVE_ROOT.glob("*/*/*/*.json")):
        if record_path.name not in {"item.json", "product.json"}:
            continue
        try:
            data = json.loads(record_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        directory = record_path.parent
        images = sorted(
            p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
        )
        if not images:
            continue
        source = record_path.parent.parent.parent.name
        title = data.get("listing_title") or data.get("name") or ""
        # Streetwear Archive files each scan under a brand category; the resellers
        # do not, and a brand guessed from a title would be wrong often enough to
        # poison an exact-match filter.
        categories = data.get("categories") or []
        brand = categories[0] if categories else ""
        pieces.append(
            {
                "archive_path": str(directory.relative_to(ARCHIVE_ROOT)).replace("\\", "/"),
                "source": source,
                "title": title,
                "brand": brand,
                "tradition": traditions.get(source, ""),
                "era_claim": decade_of(title),
                "source_url": data.get("source_url") or "",
                "images": images,
            }
        )
    return pieces


def write_evidence(out_root: Path, pieces: list[dict[str, Any]]) -> dict[str, int]:
    out_root.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).date().isoformat()
    written = linked = copied = 0

    for piece in pieces:
        listing_id = synthetic_id(piece["archive_path"])
        directory = out_root / listing_id
        directory.mkdir(exist_ok=True)

        stored = 0
        for index, image in enumerate(piece["images"], start=1):
            target = directory / f"image-{index:02d}{image.suffix.lower()}"
            if target.exists():
                stored += 1
                continue
            try:
                os.link(image, target)
                linked += 1
            except OSError:
                # Different volume, or a filesystem without hard links. Copying
                # is correct but costs the bytes, so it is counted separately.
                shutil.copy2(image, target)
                copied += 1
            stored += 1

        (directory / "record.json").write_text(
            json.dumps(
                {
                    "id": f"ARCHIVE-{listing_id}",
                    "marketplace": "archive",
                    "listing_id": listing_id,
                    # Nothing here is a sold listing. Saying otherwise would put a
                    # verification on records that never earned one.
                    "sold": "False",
                    "title": piece["title"],
                    "brand": piece["brand"],
                    "tradition": piece["tradition"],
                    "era_claim": piece["era_claim"],
                    "source_url": piece["source_url"],
                    "retrieved": now,
                    "collector": f"archive-adapter/{piece['source']}",
                    "stored_image_count": str(stored),
                    # Back-reference so any piece surfaced through the service can
                    # be traced to the collector output and its sha256 provenance.
                    "archive_source": piece["source"],
                    "archive_path": piece["archive_path"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        written += 1

    return {"records": written, "linked": linked, "copied": copied}


def main(argv: list[str]) -> int:
    if not ARCHIVE_ROOT.is_dir():
        print(f"No archive at {ARCHIVE_ROOT}", file=sys.stderr)
        return 1

    out_root = DEFAULT_OUT
    if "--out" in argv:
        try:
            out_root = Path(argv[argv.index("--out") + 1]).resolve()
        except IndexError:
            print("--out needs a path", file=sys.stderr)
            return 2

    pieces = archive_pieces()
    if not pieces:
        print("Archive holds no pieces with images.", file=sys.stderr)
        return 1

    dated = sum(1 for p in pieces if p["era_claim"])
    branded = sum(1 for p in pieces if p["brand"])
    images = sum(len(p["images"]) for p in pieces)

    if "--dry-run" in argv:
        print(f"{len(pieces)} pieces, {images} images")
        print(f"  {dated} carry a decade ({dated * 100 // len(pieces)}%)")
        print(f"  {branded} carry a brand ({branded * 100 // len(pieces)}%)")
        print(f"  would write to {out_root}")
        for piece in pieces[:5]:
            print(
                f"    {synthetic_id(piece['archive_path'])}  "
                f"{piece['era_claim'] or '----':<6} {piece['title'][:52]}"
            )
        return 0

    result = write_evidence(out_root, pieces)
    print(
        f"{result['records']} records, {result['linked']} hard-linked, "
        f"{result['copied']} copied -> {out_root}"
    )
    print(f"  {dated} carry a decade, {branded} carry a brand")
    print(f"\nPoint the service at it:\n  VINTAGE_EVIDENCE_ROOT={out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
