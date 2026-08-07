# SHIRTFACED STUDIO — Design Evidence Corpus Schema

## Status
Active — governs `var/design_corpus/`

## Purpose

`app/services/design_scoring.py` scores a filled-in review; it has no opinion on
what "good" looks like beyond the rubric's own text. Feature extraction — looking
at an actual design and forming that judgement — needs something to compare
against. This is the schema for that comparison corpus: real graphic-apparel
products, from real brands, with real images, gathered as internal design-research
evidence.

`docs/research/*.md`'s existing corpus (Represent, Fear of God ESSENTIALS, and so
on) is prose findings *about* these brands. This corpus is the underlying visual
evidence those findings could be re-derived from, and that a future extractor can
be pointed at directly.

## Storage

`var/design_corpus/` — gitignored (`studio/.gitignore`: `var/`), same convention as
`assets_root` for generated images. Internal research cache, not redistributed:
images stay local, are not published, and are not committed. Every record keeps its
source URL, so nothing here is evidence without a traceable origin.

Sampling, not mirroring: representative graphic-led products per brand (roughly
8–15), not full catalogues. This is comparison evidence, not a competitor archive.

```
var/design_corpus/
  manifest.json
  <brand-slug>/
    brand.json
    products/
      <product-slug>/
        product.json
        provenance.json
        image-01.jpg
        image-02.jpg
        ...
```

## `manifest.json`

Built after collection, not written by individual collectors (avoids concurrent
writers racing on one file). One row per brand.

```json
{
  "generated_at": "2026-08-07T00:00:00Z",
  "brands": [
    { "brand_slug": "represent", "product_count": 12, "image_count": 14 }
  ]
}
```

## `<brand-slug>/brand.json`

```json
{
  "brand_slug": "represent",
  "brand_name": "Represent",
  "site_url": "https://au.representclo.com",
  "acquired_at": "2026-08-07T00:00:00Z",
  "notes": ""
}
```

`brand_slug` is lowercase, hyphenated, filesystem-safe — the join key across every
file in this brand's tree.

## `<brand-slug>/products/<product-slug>/product.json`

```json
{
  "product_id": "represent/owners-club-tee",
  "brand_slug": "represent",
  "name": "Owners Club Tee",
  "source_url": "https://au.representclo.com/products/owners-club-tee",
  "category": "tee",
  "price": "AUD 90",
  "description": "Product page description text, verbatim.",
  "images": ["image-01.jpg", "image-02.jpg"],
  "acquired_at": "2026-08-07T00:00:00Z"
}
```

`category` is a free-text label at collection time (`tee`, `hoodie`, `cap`, ...) —
not yet mapped to `SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md`'s own categories.
That mapping is feature-extraction's job, not collection's.

## `<brand-slug>/products/<product-slug>/provenance.json`

One record per image file, shaped after `hunter_core`'s `ProvenanceRecord` —
the same acquisition-metadata discipline, reused rather than reinvented:

```json
[
  {
    "provenance_id": "represent/owners-club-tee/image-01",
    "source_id": "represent/owners-club-tee",
    "acquired_at": "2026-08-07T00:00:00Z",
    "acquisition_method": "web_scrape",
    "content_hash": "sha256:...",
    "byte_size": 245112,
    "content_type": "image/jpeg",
    "source_url": "https://au.representclo.com/cdn/shop/files/....jpg"
  }
]
```

`content_hash` is the actual file's SHA-256 — collision-checkable, and the thing
that would let a future dedup pass recognise the same product photo reused across
two different pages.

## What this does not do

No classification, no scoring, no archetype tagging happens at collection time.
Collection's only job is: real product, real images, real provenance, correctly
filed. Turning that into features `design_scoring.py` can score against is a
separate, unbuilt step — see `docs/foundations` for the design-scoring-engine
notes on why that split is deliberate (extraction is the hard problem; this corpus
is what extraction will eventually run against).
