# SHIRTFACED — The Element Archive

*Geometry separated from aesthetics, so designs become outputs and the archive
becomes the asset.*

**Status:** Design document, written before the build. Supersedes the generative
role of the mined corpus described in `DESIGN_ENGINE_ADAPTATION.md`; see §6 for
exactly what survives and what does not.

---

## 1. The premise

A folder of finished designs teaches imitation of finished designs. What is
wanted instead is a library of *parts and rules* from which designs can be
assembled deterministically, so that:

```
seed + template + supplied content + palette  →  always the same composition
```

The permanent asset is then **elements, grammars, constraints, palettes,
transformations, placement rules and seeds**. Finished artwork is a disposable
output, regenerable at any time from the tuple that produced it.

The consequence worth stating plainly: a collegiate arch is not a JPEG that says
SHIRTFACED. It is a recipe with a text path, a cap-height ratio, tracking, and
a declaration of how many inks it tolerates. The word is supplied separately and
is never part of the element.

---

## 2. The finding that changes the plan

The fourteen proposed families are not one kind of thing, and treating them as
one is what would make this a year of scraping.

**Four are ingestible.** They are artwork with a taxonomy — a drawing of a hand
is a drawing of a hand, and the work is classification and licence provenance.

| Family | Why ingestible |
|---|---|
| `illustration_parts/` | Subject matter cannot be derived; it must be drawn or found |
| `symbols/` | Same, though many are simple enough to author |
| `ornaments/` | Historical printers' ornaments are exactly this |
| `patterns/` | Motif sources, though tiling geometry is authored |

**Ten are authored.** They are parametric geometry or render recipes, and no
amount of scanning produces them. A shield with an aspect, a stroke, a corner
radius, an inset and a distress level is code. Vectorising a raster badge into
labelled slots is a hard, lossy, per-item problem that would produce worse
results than writing the shield.

| Family | Why authored |
|---|---|
| `frames/` | Parametric shapes: aspect, stroke, radius, inset |
| `type_layouts/` | Pure geometry: paths, ratios, tracking, alignment |
| `wordmarks/` | Treatments applied to supplied text |
| `badges/` | Rings, dividers and text zones are constructions |
| `textures/` | Halftone, grain, ink loss are algorithms |
| `print_effects/` | Knockout, trapping, offset are render recipes |
| `patches_labels/` | Physical dimensions and stitch margins |
| `placements/` | Garment coordinates and print bounds |
| `composition_templates/` | Slots and constraints |
| `colour_systems/` | Named inks and contrast rules |

**So the archive is mostly code, not collection.** Ingestion is the minority of
the work. This is good news for determinism: authored geometry is exactly
reproducible in a way a traced scan never is. It does mean no scraper finishes
this, which is a statement about the shape of the work and not about its size.

---

## 3. Every element carries its provenance, and the gate is at release

Rights are checked once, on a finished design, before it is released -- the
`rights_cleared_for_sale` hard gate in the design workflow.

They are deliberately **not** checked at intake. Gating intake means the archive
can only hold what has already been cleared, which means it cannot learn from
anything; and the question is not answerable about a reference in the first
place. Looking at other people's work is how design has always been done, and
this repository already holds 9,519 competitor product photographs on exactly
that basis.

What is recorded per element is where it came from -- source, item identifier,
URL, and the terms if anyone has looked them up. That is a record, and it is
what makes the release review possible.

Three rules, in order of how often they are got wrong:

1. **"Old scan" is not "public domain."** The underlying work may be out of
   copyright while the scan, the arrangement, or the accompanying database
   carries its own claim, and this varies by jurisdiction. Shirtfaced is
   Australian and may sell into the US, EU and UK; the intersection governs.
2. **Collection-level licences do not apply to items.** An institution
   publishing open metadata is not thereby publishing every image under the
   same terms. Designation is per object and must be read per object.
3. **A licence is a recorded fact with a source, not a flag.** `commercial_ok:
   true` with no provenance is an assertion. The record must name the source,
   the source's identifier, the licence, and when it was checked.

Elements whose terms nobody has looked up are fully usable for designing,
studying and learning from. `unverified()` is a worklist for the release
review, not a blocklist.

---

## 4. The element record

```json
{
  "id": "badge_shield_0142",
  "family": "badge",
  "subtype": "workwear_shield",
  "geometry": "svg",
  "symmetry": "vertical",
  "slots": ["primary_text", "secondary_text", "symbol"],
  "ink_min": 1,
  "ink_max": 3,
  "complexity": 0.34,
  "style_tags": ["institutional", "workwear", "utilitarian"],
  "compatible_treatments": ["clean", "distressed", "embroidered"],
  "exclusions": ["photographic"],
  "licence": {
    "status": "verified",
    "terms": "CC0",
    "source": "smithsonian",
    "source_id": "...",
    "source_url": "...",
    "checked_at": "2026-08-08",
    "commercial_use": true
  }
}
```

`slots` is what makes an element composable rather than decorative: it declares
where supplied content goes. An element with no slots can only be placed, never
filled.

`exclusions` is what makes the grammar work. It is cheaper and more honest to
say what an element refuses than to enumerate what it permits.

---

## 5. Determinism, and what it actually demands

`seed + template + content + palette → identical output` is a strong property
and it is only true if every step is pinned:

- Font **files**, versioned and vendored. A font update silently changes metrics
  and therefore every composition.
- Rasterisation settings fixed, and the renderer's version recorded in the
  output's provenance.
- One seeded random source threaded explicitly through every transformation.
  No ambient randomness anywhere, which is the same discipline as the workflow
  scripts that forbid `Math.random()` for the same reason.
- Integer or exactly-representable geometry where possible; where not, rounding
  fixed at a single point rather than at each call site.

The test is not "it looks the same." It is **byte-identical output for the same
tuple**, asserted in CI. Anything weaker will drift and nobody will notice until
a reprint does not match the original.

---

## 6. What survives from the corpus work

Honest accounting, because the corpus cost real effort.

**Does not survive as generative material.** The k-means templates over band
stacks in `learn_design_templates.py` are the statistical shadow of other
brands' finished designs. They will be superseded by authored
`composition_templates/` with explicit slots and constraints, which is a
strictly better object: it says what it permits rather than where ink happened
to land.

**Survives, and is worth more in this architecture than the last.**

- `garment_frame.py` — locating a garment and refusing unmeasurable frames is
  how any reference material gets measured at all, now or later.
- The mined statistics — coverage, ink counts, light-on-dark share, band
  structure — become **constraints and validation bounds**. An authored
  composition can be checked against the envelope that shipping garments
  occupy. That is a better use than generation.
- `composition_engine.py` — the *machinery* stands: synthesis before scoring,
  refusal with reason codes, shrinkage confidence, approval as the training
  signal. What changes is that it selects among authored templates rather than
  learned centroids. The templates were always meant to be replaceable; the
  engine was not.

**The approval loop matters more, not less.** With authored templates the
question "which of our own constructions do we actually approve" is the only
signal that is about us rather than about other brands.

---

## 7. Sequencing

Not a smaller target -- an ordering, and the reason is correctness rather than
cost. Determinism and licence provenance cannot be retrofitted onto an archive
that already holds three thousand elements: the first is a property of every
render path, and the second would mean re-checking every item already ingested.
Both have to hold at element one or they never hold.

So the first thing built is the narrowest thing that proves them:

> **A `type_layouts/` element with real slots, filled with a supplied phrase,
> rendered twice from the same seed to byte-identical output — and an element
> with an unverified licence refused by the composer.**

If determinism does not hold at one element, it will not hold at three thousand.
If the licence gate is not load-bearing from the first element, it will be
retrofitted onto an archive already full of unverified material.

Volume comes after both hold. The owner's own sizing — 2,000–3,000 clean
elements across 12–15 families, quality over volume — is the target, and
nothing about it is reachable until the two properties above are true.
