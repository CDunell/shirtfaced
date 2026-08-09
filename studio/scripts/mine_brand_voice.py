#!/usr/bin/env python3
"""Each brand's voice, gathered from what the brand already says about itself.

Voice was previously treated here as something the owner would have to declare.
That was wrong: every brand worth collecting has one, either stated in its own
copy or readable from its genre and register, and the corpus has been carrying
the evidence since collection -- 587 of 647 sampled products hold the brand's
own product description and nothing has read a word of it.

Three sources, in the order they are trusted:

  stated      the brand's own product copy, aggregated per brand
  derived     register measured from that copy -- who it addresses, how loudly,
              how long its sentences run, whether it swears
  classified  the design tradition the brand was collected under, used when a
              brand publishes no copy at all

Nothing here judges whether a voice is good, and nothing invents one. A brand
that says nothing is recorded as saying nothing.

    python scripts/mine_brand_voice.py
    python scripts/mine_brand_voice.py --min-words 40

Writes var/design_corpus/brand_voice.json.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CORPUS_ROOTS = (
    ROOT / "var" / "design_corpus",
    ROOT / "var" / "design_corpus_flat",
)
REPORT_PATH = ROOT / "var" / "design_corpus" / "brand_voice.json"

TAG = re.compile(r"<[^>]+>")
WORD = re.compile(r"[A-Za-z']+")
SENTENCE = re.compile(r"[.!?]+")

# Words that describe the garment rather than the brand. Left in, every brand
# sounds identical because every brand sells a cotton unisex crew neck.
GARMENT_NOISE = {
    "shirt",
    "shirts",
    "tshirt",
    "tee",
    "tees",
    "hoodie",
    "hoodies",
    "sweatshirt",
    "cotton",
    "polyester",
    "fabric",
    "fit",
    "size",
    "sizes",
    "unisex",
    "mens",
    "womens",
    "wash",
    "machine",
    "cold",
    "dry",
    "print",
    "printed",
    "design",
    "quality",
    "soft",
    "comfortable",
    "crew",
    "neck",
    "sleeve",
    "sleeves",
    "garment",
    "product",
    "colour",
    "color",
    "black",
    "white",
    "grey",
    "gray",
    "blue",
    "please",
    "available",
    "made",
    "material",
    "care",
    "model",
    "wearing",
    "chest",
    "length",
}

STOP = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "you",
    "your",
    "our",
    "are",
    "was",
    "have",
    "has",
    "will",
    "from",
    "not",
    "but",
    "all",
    "can",
    "out",
    "get",
    "its",
    "it's",
    "they",
    "them",
    "their",
    "when",
    "what",
    "who",
    "how",
    "why",
    "one",
    "just",
    "more",
    "than",
    "then",
    "into",
    "over",
    "some",
    "any",
    "each",
    "been",
    "were",
    "would",
    "could",
    "should",
    "there",
    "here",
    "about",
    "which",
    "while",
}

SECOND_PERSON = {"you", "your", "yours", "you're", "yourself"}
FIRST_PERSON = {"we", "our", "us", "ours", "we're", "i", "my"}
PROFANITY = {"shit", "fuck", "fucking", "bloody", "bastard", "arse", "piss", "damn", "hell"}


def _clean(text: str) -> str:
    return TAG.sub(" ", text or "")


def _collect() -> tuple[dict[str, list[str]], dict[str, str]]:
    """Every brand's product copy, and the tradition it was collected under."""
    copy: dict[str, list[str]] = {}
    tradition: dict[str, str] = {}
    for root in CORPUS_ROOTS:
        if not root.is_dir():
            continue
        for brand_dir in sorted(root.iterdir()):
            brand_file = brand_dir / "brand.json"
            if not brand_file.is_file():
                continue
            try:
                brand = json.loads(brand_file.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError):
                continue
            slug = brand.get("brand_slug", brand_dir.name)
            tradition[slug] = brand.get("design_tradition", "")
            products = brand_dir / "products"
            if not products.is_dir():
                continue
            texts = copy.setdefault(slug, [])
            for product_dir in products.iterdir():
                product_file = product_dir / "product.json"
                if not product_file.is_file():
                    continue
                try:
                    product = json.loads(product_file.read_text(encoding="utf-8-sig"))
                except (OSError, json.JSONDecodeError):
                    continue
                blob = _clean(product.get("description", ""))
                if blob.strip():
                    texts.append(blob)
    return copy, tradition


def _register(words: list[str], sentences: int) -> dict[str, Any]:
    """How the brand speaks, as counts rather than adjectives."""
    total = len(words) or 1
    lowered = [w.lower() for w in words]
    return {
        "words": len(words),
        "words_per_sentence": round(len(words) / max(1, sentences), 1),
        "addresses_reader": round(sum(1 for w in lowered if w in SECOND_PERSON) / total, 4),
        "speaks_as_we": round(sum(1 for w in lowered if w in FIRST_PERSON) / total, 4),
        "swears": round(sum(1 for w in lowered if w in PROFANITY) / total, 5),
        # Shouting is a real register signal in this category.
        "shouted_words": round(sum(1 for w in words if len(w) > 2 and w.isupper()) / total, 4),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-words", type=int, default=30)
    args = parser.parse_args(argv[1:])

    copy, tradition = _collect()
    if not copy:
        print("No corpus found.", file=sys.stderr)
        return 1

    # Corpus-wide frequency, so a brand's distinctive words can be told from the
    # words every apparel brand uses.
    per_brand_words: dict[str, list[str]] = {}
    per_brand_sentences: dict[str, int] = {}
    document_count: Counter[str] = Counter()
    for slug, texts in copy.items():
        blob = " ".join(texts)
        words = [w for w in WORD.findall(blob) if len(w) > 2]
        keep = [w for w in words if w.lower() not in STOP and w.lower() not in GARMENT_NOISE]
        per_brand_words[slug] = keep
        per_brand_sentences[slug] = max(1, len(SENTENCE.findall(blob)))
        for term in {w.lower() for w in keep}:
            document_count[term] += 1

    brands = len(copy) or 1
    out: dict[str, Any] = {}
    for slug, words in sorted(per_brand_words.items()):
        if len(words) < args.min_words:
            out[slug] = {
                "source": "classified",
                "voice": tradition.get(slug, "") or "unknown",
                "words": len(words),
                "note": "no usable product copy; falling back to collection tradition",
            }
            continue

        counts = Counter(w.lower() for w in words)
        total = sum(counts.values()) or 1
        # Terms this brand uses far more than the corpus does.
        distinctive = sorted(
            (
                (term, (n / total) * math.log(brands / (1 + document_count[term])))
                for term, n in counts.items()
                if n >= 3
            ),
            key=lambda kv: -kv[1],
        )
        out[slug] = {
            "source": "stated",
            "tradition": tradition.get(slug, ""),
            "register": _register(words, per_brand_sentences[slug]),
            "distinctive_terms": [term for term, _ in distinctive[:12]],
        }

    REPORT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")

    stated = [s for s, v in out.items() if v["source"] == "stated"]
    print(
        f"\n{len(out)} brands: {len(stated)} with stated copy, "
        f"{len(out) - len(stated)} falling back to their collection tradition\n"
    )

    for slug in sorted(stated, key=lambda s: -out[s]["register"]["words"])[:12]:
        v = out[slug]
        r = v["register"]
        print(
            f"{slug:<24} {v['tradition']:<16} {r['words']:>6} words  "
            f"{r['words_per_sentence']:>5} w/sent  you {r['addresses_reader']:.3f}  "
            f"we {r['speaks_as_we']:.3f}"
        )
        print(f"    {', '.join(v['distinctive_terms'][:8])}")

    print(f"\nwritten to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
