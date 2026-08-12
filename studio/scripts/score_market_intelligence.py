#!/usr/bin/env python3
"""Join market demand proxies to Shirtfaced's existing visual observations.

The market can inform *which structural treatments appear to carry demand*.
It cannot choose the joke, phrase, depicted subject or creative direction. Those
fields are intentionally excluded from the fingerprint below even when the
visual pass has described them.

Input is one JSON/JSONL file (or directory of JSON files) containing visual-pass
rows for ``var/design_corpus_market``. Output is a ranked structural report with
traceable listing evidence and no generated concepts.

    python scripts/score_market_intelligence.py var/market-pass/
    python scripts/score_market_intelligence.py rows.json \
        --output var/design_corpus_market/report.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
MARKET_ROOT = ROOT / "var" / "design_corpus_market"
DEFAULT_OUTPUT = MARKET_ROOT / "market_intelligence_report.json"

# These fields describe treatment/register, not content. Do not add subject,
# phrase, description or source title here without an explicit owner decision.
FINGERPRINT_FIELDS = (
    "graphic_archetype",
    "layout_archetype",
    "integration",
    "type_case",
    "print_effect",
    "stroke",
    "detail_density",
)
FINGERPRINT_ARRAYS = ("type_styles", "type_effects", "treatment_lanes")


def _load_rows(target: Path) -> list[dict[str, Any]]:
    files = sorted(target.glob("*.json")) if target.is_dir() else [target]
    rows: list[dict[str, Any]] = []
    for path in files:
        text = path.read_text(encoding="utf-8-sig")
        if path.suffix.lower() in {".jsonl", ".ndjson"}:
            rows.extend(json.loads(line) for line in text.splitlines() if line.strip())
            continue
        loaded = json.loads(text)
        if isinstance(loaded, list):
            rows.extend(row for row in loaded if isinstance(row, dict))
        elif isinstance(loaded, dict):
            candidate = loaded.get("rows") or loaded.get("results") or loaded.get("queue")
            if isinstance(candidate, list):
                rows.extend(row for row in candidate if isinstance(row, dict))
            else:
                rows.append(loaded)
    return rows


def _products() -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    if not MARKET_ROOT.is_dir():
        return out
    for source_dir in MARKET_ROOT.iterdir():
        products = source_dir / "products"
        if not products.is_dir():
            continue
        for product_dir in products.iterdir():
            path = product_dir / "product.json"
            if not path.is_file():
                continue
            try:
                product = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue
            out[(source_dir.name, product_dir.name)] = product
    return out


def _num(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def _percentiles(values: list[float], *, reverse: bool = False) -> dict[float, float]:
    if not values:
        return {}
    ordered = sorted(set(values), reverse=reverse)
    if len(ordered) == 1:
        return {ordered[0]: 0.5}
    return {value: index / (len(ordered) - 1) for index, value in enumerate(ordered)}


def _cohort_scores(products: Iterable[dict[str, Any]]) -> dict[str, dict[float, float]]:
    signals = [product.get("commercial_signals") or {} for product in products]
    fields = ("sales_count", "review_count", "rating", "rank")
    out: dict[str, dict[float, float]] = {}
    for field in fields:
        values = [_num(signal.get(field)) for signal in signals]
        clean = [value for value in values if value is not None]
        out[field] = _percentiles(clean, reverse=field == "rank")
    return out


def _demand(
    product: dict[str, Any],
    cohort: dict[str, dict[float, float]],
) -> tuple[float, list[str]]:
    signal = product.get("commercial_signals") or {}
    # Relative within the collected cohort. Missing signals do not become zero;
    # the remaining weights renormalise so absence is not fabricated weakness.
    weights = {"sales_count": 0.45, "review_count": 0.35, "rating": 0.10, "rank": 0.10}
    numerator = 0.0
    denominator = 0.0
    used: list[str] = []
    for field, weight in weights.items():
        value = _num(signal.get(field))
        if value is None or value not in cohort[field]:
            continue
        numerator += cohort[field][value] * weight
        denominator += weight
        used.append(field)
    return (round(numerator / denominator, 4), used) if denominator else (0.0, [])


def _fingerprint(row: dict[str, Any]) -> tuple[str, ...]:
    parts = [
        str(row.get(field, "") or "unknown").strip().lower()
        for field in FINGERPRINT_FIELDS
    ]
    for field in FINGERPRINT_ARRAYS:
        values = row.get(field) or []
        normalised = sorted(
            str(value).strip().lower() for value in values if str(value).strip()
        )
        parts.append("+".join(normalised) or "none")
    return tuple(parts)


def build_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    products = _products()
    cohort = _cohort_scores(products.values())
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    unmatched = 0

    for row in rows:
        source = str(row.get("brand") or row.get("brand_slug") or "")
        product_slug = str(row.get("product") or row.get("product_slug") or "")
        product = products.get((source, product_slug))
        if product is None:
            unmatched += 1
            continue
        demand, used = _demand(product, cohort)
        grouped[_fingerprint(row)].append(
            {
                "source": source,
                "product_slug": product_slug,
                "source_url": product.get("source_url", ""),
                "demand": demand,
                "signals_used": used,
            }
        )

    groups: list[dict[str, Any]] = []
    for fingerprint, evidence in grouped.items():
        demands = [entry["demand"] for entry in evidence if entry["signals_used"]]
        median_demand = statistics.median(demands) if demands else 0.0
        # Saturation is reported, not treated as intrinsically bad: seeing a
        # structure often may mean convention rather than creative exhaustion.
        evidence_count = len(evidence)
        confidence = evidence_count / (evidence_count + 10)
        groups.append(
            {
                "fingerprint": dict(
                    zip((*FINGERPRINT_FIELDS, *FINGERPRINT_ARRAYS), fingerprint)
                ),
                "evidence_count": evidence_count,
                "market_demand": round(median_demand, 4),
                "confidence": round(confidence, 4),
                "signal_strength": round(median_demand * confidence, 4),
                "evidence": sorted(
                    evidence,
                    key=lambda item: item["demand"],
                    reverse=True,
                )[:12],
            }
        )

    groups.sort(
        key=lambda group: (group["signal_strength"], group["evidence_count"]),
        reverse=True,
    )
    return {
        "purpose": "market demand evidence for structural design treatments",
        "creative_boundary": (
            "May inform register/layout/treatment ranking. Must not supply phrases, jokes, "
            "depicted subjects or creative direction. Human design approval remains mandatory."
        ),
        "observations_received": len(rows),
        "observations_matched": sum(group["evidence_count"] for group in groups),
        "observations_unmatched": unmatched,
        "groups": groups,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv[1:])

    if not MARKET_ROOT.is_dir():
        print("no market corpus — run import_market_intelligence.py first", file=sys.stderr)
        return 1
    rows = _load_rows(args.observations)
    if not rows:
        print("no observation rows found", file=sys.stderr)
        return 1
    report = build_report(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"{report['observations_matched']} observations matched; "
        f"{len(report['groups'])} structural groups; written to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
