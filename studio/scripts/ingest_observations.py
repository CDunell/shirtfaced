#!/usr/bin/env python3
"""Load visual-pass rows into the database.

The pass writes one JSON object per frame, described from the original image.
This puts them in Postgres, where they can actually be queried -- which is the
whole point, and which had not been done: the schema existed and nothing had
ever been written through it.

Upsert, not insert. A frame re-described by the same model replaces its row and
its zones; a different model gets its own row, so two readings of the same frame
coexist without merging. That is enforced by the unique key on
(image_path, described_by) rather than by hoping the caller behaves.

    python scripts/ingest_observations.py var/preview/vpass_direct/
    python scripts/ingest_observations.py rows.json --dry-run

Runs where the database is reachable. On the Oracle box that is locally; from a
workstation it is not, which is why this takes a path rather than assuming it
can see the corpus.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.observation_models import (
    FILLS,
    ZONE_CONTENT,
    ZONE_STATES,
    ZONES,
    DesignObservation,
    ObservationZone,
)

# Fields copied straight across. Anything not here stays in `raw`, so a schema
# that gains a field later does not lose the rows written before it existed.
SCALARS = (
    "corpus",
    "brand_slug",
    "product_slug",
    "product_name",
    "tradition",
    "category",
    "price",
    "source_url",
    "presentation",
    "garment",
    "garment_colour",
    "backdrop",
    "description",
    "text_content",
    "subject_primary",
    "property_name",
    "graphic_archetype",
    "layout_archetype",
    "integration",
    "type_case",
    "print_effect",
    "stroke",
    "detail_density",
    "confidence",
    "notes",
    "described_by",
)
ARRAYS = (
    "subject_terms",
    "element_shapes",
    "type_styles",
    "type_effects",
    "palette_terms",
    "bare_zones",
)
BOOLS = ("depicts_people", "references_property")


def _rows(target: Path) -> list[dict[str, Any]]:
    files = sorted(target.glob("*.json")) if target.is_dir() else [target]
    out: list[dict[str, Any]] = []
    for path in files:
        try:
            loaded = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as error:
            print(f"  skipped {path.name}: {error}", file=sys.stderr)
            continue
        out.extend(loaded if isinstance(loaded, list) else [loaded])
    return out


def _normalise(row: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]], list[str]]:
    """Split a row into scalar fields, zones, and complaints about it."""
    problems: list[str] = []
    image = str(row.get("image", "") or row.get("image_path", "")).replace("\\", "/")
    if not image:
        problems.append("no image path")
    if "..." in image:
        # A placeholder path was written into rows once and made them unjoinable.
        problems.append(f"placeholder path: {image}")

    brand = row.get("brand") or row.get("brand_slug") or ""
    product = row.get("product") or row.get("product_slug") or ""
    corpus = row.get("corpus") or ("flat" if "design_corpus_flat" in image else "brand")

    fields: dict[str, Any] = {
        "image_path": image,
        "corpus": corpus,
        "brand_slug": brand,
        "product_slug": product,
        "product_name": row.get("name", "") or row.get("product_name", ""),
    }
    for key in SCALARS:
        if key in fields:
            continue
        fields[key] = row.get(key, "") or ""
    for key in ARRAYS:
        value = row.get(key) or []
        fields[key] = [str(v) for v in value] if isinstance(value, list) else []
    for key in BOOLS:
        fields[key] = bool(row.get(key, False))
    fields["type_lines"] = int(row.get("type_lines", 0) or 0)
    fields["confidence"] = row.get("confidence") or "medium"
    fields["raw"] = row

    if not fields["described_by"]:
        problems.append("no described_by")
    if fields["confidence"] not in ("high", "medium", "low"):
        problems.append(f"bad confidence: {fields['confidence']}")
    if fields["confidence"] == "high" and not (fields["subject_primary"] and fields["description"]):
        problems.append("high confidence but subject or description empty")
    for zone in fields["bare_zones"]:
        if zone not in ZONES:
            problems.append(f"unknown bare zone: {zone}")

    zones: list[dict[str, str]] = []
    for entry in row.get("zones") or []:
        zone = str(entry.get("zone", ""))
        state = str(entry.get("state", ""))
        content = str(entry.get("content", ""))
        fill = str(entry.get("fill", ""))
        scale_role = str(entry.get("scale_role") or "")
        hierarchy = str(entry.get("hierarchy") or "")
        if zone not in ZONES:
            problems.append(f"unknown zone: {zone}")
            continue
        if state not in ZONE_STATES:
            problems.append(f"unknown zone state: {state}")
            continue
        if content not in ZONE_CONTENT:
            problems.append(f"unknown zone content: {content}")
            continue
        if fill not in FILLS:
            problems.append(f"unknown fill: {fill}")
            continue
        if scale_role not in ("", "S0", "S1", "S2", "S3", "S4"):
            problems.append(f"unknown scale role: {scale_role}")
            continue
        if hierarchy not in ("", "H1", "H2", "H3"):
            problems.append(f"unknown hierarchy: {hierarchy}")
            continue
        zones.append(
            {
                "zone": zone,
                "state": state,
                "content": content,
                "fill": fill,
                "scale_role": scale_role,
                "hierarchy": hierarchy,
                "description": entry.get("description", ""),
            }
        )
    return fields, zones, problems


def ingest(session: Session, rows: list[dict[str, Any]], dry_run: bool) -> dict[str, int]:
    counts = {"written": 0, "replaced": 0, "refused": 0, "zones": 0}
    for row in rows:
        fields, zones, problems = _normalise(row)
        if problems:
            counts["refused"] += 1
            print(f"  REFUSED {fields.get('image_path', '?')}")
            for problem in problems:
                print(f"      {problem}")
            continue
        if dry_run:
            counts["written"] += 1
            counts["zones"] += len(zones)
            continue

        existing = session.scalar(
            select(DesignObservation).where(
                DesignObservation.image_path == fields["image_path"],
                DesignObservation.described_by == fields["described_by"],
            )
        )
        if existing is not None:
            for key, value in fields.items():
                setattr(existing, key, value)
            existing.zones.clear()
            session.flush()
            observation = existing
            counts["replaced"] += 1
        else:
            observation = DesignObservation(**fields)
            session.add(observation)
            counts["written"] += 1
        session.flush()
        for zone in zones:
            session.add(ObservationZone(observation_id=observation.id, **zone))
            counts["zones"] += 1
    if not dry_run:
        session.commit()
    return counts


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv[1:])

    rows = _rows(args.path)
    if not rows:
        print(f"No rows found at {args.path}", file=sys.stderr)
        return 1
    print(f"\n{len(rows)} rows from {args.path}")

    if args.dry_run:
        counts = ingest(None, rows, dry_run=True)  # type: ignore[arg-type]
    else:
        # Imported late so --dry-run needs no database at all.
        from app.db.session import get_engine

        with Session(get_engine()) as session:
            counts = ingest(session, rows, dry_run=False)

    print(
        f"\n{counts['written']} written, {counts['replaced']} replaced, "
        f"{counts['refused']} refused, {counts['zones']} zone rows"
    )
    return 1 if counts["refused"] and not counts["written"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
