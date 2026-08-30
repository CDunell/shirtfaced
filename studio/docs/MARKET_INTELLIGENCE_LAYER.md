# SHIRTFACED STUDIO — Market Intelligence Layer

**Status:** Active integration boundary  
**Date:** 2026-08-12

## Purpose

Add external commercial evidence to the design engine without allowing marketplace
content to become Shirtfaced's creative direction.

The useful part of the Etsy/Amazon/Thunderbit workflow is not copying successful
listings. It is measuring which **structural treatments** repeatedly appear beside
commercial signals, then using that evidence as one input to Shirtfaced's existing
composition and approval loop.

The stack already had most of the hard parts:

- `collect_design_corpus.py` — brand product evidence with provenance.
- `collect_flat_artwork.py` / `collect_majors_browser.mjs` — marketplace and browser
  collection paths.
- `visual_pass_queue.py` + `ingest_observations.py` — visual description into the
  canonical design-observation schema.
- `mine_design_structure.py` / `compare_corpora.py` — deterministic structure mining
  and evidence comparison.
- `DESIGN_ENGINE_ADAPTATION.md` — composition learned from corpus evidence and owner
  approve/reject outcomes.
- `SHIRTFACED_END_TO_END_PUBLISHING_PIPELINE.md` — Stage 0 ideation/opportunity and the
  downstream marketing feedback contract.

This layer fills the missing commercial-evidence edge.

---

## Non-negotiable creative boundary

`CLAUDE.md` already states that the corpus settles register and does **not** set design
direction. That rule is stronger here because marketplace titles, phrases and subjects
are especially easy to copy accidentally.

Market intelligence **may influence**:

- layout archetype
- graphic archetype
- text/image integration
- type treatment
- print effect
- stroke / density
- number and relationship of treatment lanes
- confidence that a structural pattern is commercially evidenced

Market intelligence **must not supply**:

- a phrase or joke
- depicted subject matter
- a copied illustration concept
- a competitor composition reproduced substantially as-is
- a final design brief without Shirtfaced's authored creative input

Source titles, descriptions and subjects are retained for audit and analysis but are
not part of the generation fingerprint.

---

## Data flow

```text
THUNDERBIT / CSV / JSON / JSONL / FUTURE NATIVE COLLECTOR
  ↓
import_market_intelligence.py
  ↓
var/design_corpus_market/<source>/products/...
  ├─ product.json
  │   ├─ source evidence
  │   └─ commercial_signals
  ├─ provenance.json
  └─ listing images
  ↓
market_visual_queue.py
  ↓
EXISTING VISUAL PASS
  ↓
visual observation rows
  ↓
score_market_intelligence.py
  ↓
market_intelligence_report.json
  ↓
STRUCTURAL MARKET SIGNAL
  ↓
Stage 0 ideation / deterministic design engine
  ↓
OWNER APPROVE / REJECT
  ↓
existing approval-learning loop
```

Thunderbit is therefore an **adapter**, not part of the domain model. If it is replaced
with Playwright, an API or a marketplace-specific collector later, nothing downstream
changes.

---

## Corpus layout

The market corpus mirrors the existing design corpus closely enough to reuse the visual
pipeline while remaining physically separate:

```text
studio/var/design_corpus_market/
  etsy/
    brand.json
    products/
      etsy-<stable-hash>/
        product.json
        provenance.json
        image-01.jpg
        ...
  amazon/
    ...
  visual_queue.json
  market_intelligence_report.json
```

`studio/var/` is already gitignored. Marketplace images and source records remain local
research evidence and are not published with the application.

---

## `product.json` additions

The normal corpus fields remain, with these additions:

```json
{
  "market_query": "graphic tee",
  "commercial_signals": {
    "currency": "AUD",
    "rating": 4.8,
    "review_count": 1421,
    "sales_count": null,
    "rank": 12
  },
  "source_record": {}
}
```

`source_record` is the untouched normalised export row for audit. Unknown fields are not
thrown away merely because our first schema did not anticipate them.

Commercial fields are deliberately nullable. A missing sales count is **unknown**, not
zero.

---

## Demand scoring

`score_market_intelligence.py` compares each available commercial signal **within the
collected cohort**, rather than pretending review counts mean the same thing on Etsy and
Amazon.

Current weights before renormalisation:

| Signal | Weight | Reason |
|---|---:|---|
| sales count | 0.45 | closest direct demand proxy when exposed |
| review count | 0.35 | durable marketplace demand proxy |
| rating | 0.10 | quality/satisfaction evidence, weak as volume evidence |
| rank | 0.10 | relative platform signal when exposed |

Missing fields drop out and the remaining weights renormalise. They do not contribute a
fabricated zero.

The report uses the same confidence shrinkage already adopted by the design engine:

```text
confidence = n / (n + 10)
signal_strength = median_market_demand × confidence
```

This prevents one apparent winner from being treated as knowledge.

---

## Structural fingerprint

The current fingerprint contains only treatment fields already emitted by the visual
pass:

```text
graphic_archetype
layout_archetype
integration
type_case
print_effect
stroke
detail_density
type_styles[]
type_effects[]
treatment_lanes[]
```

Intentionally absent:

```text
subject_primary
subject_terms[]
text_content
product title
description
source copy
```

That absence is a guardrail, not an unfinished feature.

---

## Stage 0 contract

Market intelligence becomes one additional input to Stage 0:

```text
IdeaBrief
  authored concept / phrase / visual joke
  + Shirtfaced design archive
  + structural market signal (optional)
  + existing catalogue similarity
  + campaign/performance context
```

It may rank or recommend **how** an authored idea is treated. It does not generate the
idea itself.

Examples of valid output:

- "For this authored concept, image+text integrated treatments have stronger market
  evidence than detached caption treatments in the current cohort."
- "Two-line collegiate type is heavily represented but the evidence is broad rather
  than concentrated; do not treat it as a differentiator."
- "This layout has strong market evidence but poor Shirtfaced approval history; owner
  evidence wins."

Invalid output:

- "The market likes raccoons drinking beer, generate a raccoon drinking beer."
- "Copy this phrase but make it Australian."

---

## Thunderbit field recipe

For an Etsy/Amazon research run, ask Thunderbit for the fullest public evidence the page
actually exposes. Suggested columns:

```text
listing_id
listing_url
title
price
currency
rating
review_count
sales_count
rank
image_url
image_urls
```

Do not invent values the page does not expose. The importer accepts common field-name
variants and preserves the original row.

Example:

```bash
cd studio
python scripts/import_market_intelligence.py ~/Downloads/etsy.json \
  --source etsy \
  --query "graphic tee" \
  --download-images
python scripts/market_visual_queue.py
# run the existing visual description pass over var/design_corpus_market/visual_queue.json
python scripts/score_market_intelligence.py var/market-pass/
```

---

## Where this joins the future Marketing Engine

This layer measures **external market evidence before we have our own sales history**.
The Marketing Engine measures **our actual content, traffic and sales performance**.
They remain separate sources.

When Shirtfaced has sufficient first-party sales data, external market evidence should
become a weaker prior and owner/customer evidence should dominate:

```text
external market prior
  ↓
owner approve/reject evidence
  ↓
Shirtfaced traffic + sales evidence
```

The direction of travel is away from borrowed proxies and toward our own outcomes.

---

## Next implementation edge

The ingestion, visual-pass reuse and structural scoring path now exist. The next code
edge is small and explicit: expose `market_intelligence_report.json` to the Stage 0
concept/design service as a read-only ranking input, alongside owner approval history.

Do not connect it directly to image generation. The human-authored idea and the existing
approval gate stay between market evidence and artwork generation.
