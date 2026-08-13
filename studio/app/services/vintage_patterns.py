"""Retrieve proven visual structures from the retained vintage sold-listing corpus.

This service deliberately separates two concerns:
1. vintage evidence supplies structure / visual grammar;
2. Shirtfaced concepts supply original subject matter and copy.

The retrieval is deterministic and works without an LLM. It ranks retained sold
listings using their metadata and exposes the retained listing photography as
references for a later multimodal/design-generation step.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path("/home/ubuntu/shirtfaced-research/vintage-ebay-images")
TOKEN_RE = re.compile(r"[a-z0-9]+")
STOP = {
    "a", "an", "and", "the", "of", "for", "with", "shirt", "shirts", "tee", "tshirt",
    "t", "mens", "men", "womens", "women", "size", "vintage", "graphic", "black", "white",
}


def _root() -> Path:
    return Path(os.environ.get("VINTAGE_EVIDENCE_ROOT", str(DEFAULT_ROOT))).resolve()


def _tokens(value: str) -> set[str]:
    return {t for t in TOKEN_RE.findall(value.lower()) if len(t) > 1 and t not in STOP}


def _record_dirs() -> list[Path]:
    root = _root()
    if not root.is_dir():
        return []
    return [p for p in root.iterdir() if p.is_dir() and p.name.isdigit()]


def _read_record(directory: Path) -> dict[str, Any] | None:
    try:
        record = json.loads((directory / "record.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    images = sorted(
        p.name for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )
    if not images:
        return None
    listing_id = str(record.get("listing_id") or directory.name)
    return {
        **record,
        "listing_id": listing_id,
        "images": [f"/vintage-evidence/image/{listing_id}/{name}" for name in images[:12]],
    }


def _garment(title: str) -> str:
    t = title.lower()
    if "hoodie" in t or "hooded" in t:
        return "hoodie"
    if "sweatshirt" in t or "crewneck" in t:
        return "sweatshirt"
    if "long sleeve" in t or "longsleeve" in t:
        return "long-sleeve tee"
    if "jersey" in t:
        return "jersey"
    if "cap" in t or "hat" in t:
        return "headwear"
    return "tee"


def _traits(title: str) -> list[str]:
    t = title.lower()
    traits: list[str] = []
    checks = (
        ("all over", "all-over print"), ("aop", "all-over print"),
        ("front back", "front-and-back"), ("double sided", "front-and-back"),
        ("back print", "large-back candidate"), ("back graphic", "large-back candidate"),
        ("pocket", "small-front candidate"), ("logo", "logo-led"),
        ("skull", "illustration-led"), ("cartoon", "character-led"),
        ("flame", "flame motif"), ("tribal", "tribal motif"),
        ("distressed", "distressed"), ("single stitch", "period construction"),
    )
    for needle, label in checks:
        if needle in t and label not in traits:
            traits.append(label)
    return traits


def retrieve_pattern(query: str, *, limit: int = 12) -> dict[str, Any]:
    """Return the strongest retained evidence set for a structural query."""
    qtokens = _tokens(query)
    ranked: list[tuple[float, dict[str, Any]]] = []
    for directory in _record_dirs():
        record = _read_record(directory)
        if not record:
            continue
        hay = " ".join(str(record.get(k) or "") for k in ("title", "brand", "tradition", "era_claim"))
        rtokens = _tokens(hay)
        overlap = len(qtokens & rtokens)
        score = float(overlap * 4)
        # Broad relevance bonuses keep surf/skate/street evidence useful even for
        # Shirtfaced concepts whose subject matter is intentionally unrelated.
        tradition = str(record.get("tradition") or "").lower()
        if any(x in tradition for x in ("skate", "surf", "street")):
            score += 2.0
        if record.get("stored_image_count") or record.get("images"):
            score += 1.0
        if overlap or score >= 3:
            ranked.append((score, record))
    ranked.sort(key=lambda item: (item[0], len(item[1].get("images") or [])), reverse=True)
    matches = [record for _, record in ranked[: max(1, min(limit, 30))]]

    eras = Counter(str(r.get("era_claim") or "unknown") for r in matches)
    traditions = Counter(str(r.get("tradition") or "unknown") for r in matches)
    garments = Counter(_garment(str(r.get("title") or "")) for r in matches)
    traits = Counter(trait for r in matches for trait in _traits(str(r.get("title") or "")))

    evidence = [
        {
            "listing_id": str(r.get("listing_id")),
            "brand": r.get("brand"),
            "title": r.get("title"),
            "era": r.get("era_claim"),
            "tradition": r.get("tradition"),
            "source_url": r.get("source_url"),
            "images": r.get("images", []),
        }
        for r in matches
    ]
    return {
        "query": query,
        "match_count": len(matches),
        "structure": {
            "dominant_era": eras.most_common(1)[0][0] if eras else None,
            "dominant_tradition": traditions.most_common(1)[0][0] if traditions else None,
            "dominant_garment": garments.most_common(1)[0][0] if garments else None,
            "recurring_title_traits": [name for name, _ in traits.most_common(8)],
            "instruction": (
                "Use these references for composition, scale, placement, typography/illustration balance, "
                "print economy and period visual grammar only. Do not copy logos, slogans, characters, "
                "brand identifiers or a single listing's exact composition. Shirtfaced supplies original content."
            ),
        },
        "evidence": evidence,
    }


def concept_pattern_query(concept: Any) -> str:
    """Turn a DesignConcept into the structural half of the two-part query."""
    fields = [
        str(getattr(concept, "title", "") or ""),
        str(getattr(concept, "concept_text", "") or ""),
        " ".join(getattr(concept, "tags", []) or []),
        " ".join(getattr(concept, "treatment_lanes", []) or []),
        " ".join(getattr(concept, "garments", []) or []),
    ]
    return " ".join(part for part in fields if part).strip()


def two_part_bundle(structure_query: str, creative_query: str, *, limit: int = 12) -> dict[str, Any]:
    """Return an explicit two-part design brief without blending source and subject."""
    pattern = retrieve_pattern(structure_query, limit=limit)
    return {
        "part_1_structure": pattern,
        "part_2_original_content": creative_query,
        "combined_instruction": (
            "Build an original Shirtfaced design using PART 2 for subject matter/copy and PART 1 only as "
            "evidence for visual structure. Synthesize across multiple references; never reproduce a source design."
        ),
    }
