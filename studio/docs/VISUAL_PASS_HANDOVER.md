# Visual pass — handover brief

You are describing other people's shipped garment designs so an engine can
arrange supplied elements the way good brands repeatedly arrange theirs.

**11,206 products. 1,246 sheets at nine per sheet.** Your output is JSON rows
that load into Postgres and get queried as precedent.

---

## What this is for, and what it is not for

The engine will be handed artwork, text and font choices by the owner. Its only
job is **arrangement** — typography, scale, placement, framing, production
treatment — informed by how comparable material has been handled before.

So the corpus is **precedent to retrieve against, never frequency to average.**

Do not produce counts, medians or "most common" anything. A row saying *the
wordmark is set inside the floral field in the same ink, so it reads as a
signature buried in the pattern* is usable. "42.8% of designs have an arched top
edge" is not — it can only ever generate the design that looks like everything
and belongs to nobody.

Nothing you write should judge whether a design is good. The brands already
voted by shipping it.

---

## Read the original file. Never a crop.

An earlier pass cropped to the print first and described the crop. The crop was
sometimes a hoodie placket, sometimes a wordmark sliced mid-letter, sometimes a
strip of sleeve — and all of it was described confidently.

Cropping also throws away exactly what a photograph uniquely carries: the cut,
the wash, the garment colour, and which zone the print sits in.

Sheets are built for you by `scripts/product_sheet.py`, nine products at
2000×2000, 640px each. That size was measured, not chosen:

| px per design | what survives |
|---|---|
| 250 | gross type only — **construction values came out wrong** |
| 356 | garment, zone, scale, archetype. No text |
| **640** | all of the above **plus text at S2 and above** |

Micro woven labels and neck tags are still not legible at 640px. Do not
transcribe them; record that a label is present.

---

## One row per product, not per frame

40,070 frames are 11,206 products — 3.6 frames of one design, seen front, back,
flat and on a model.

The sheet shows each product's best frame. Its other frames are listed in the
sheet's `.json` under `frames`, best first. **Open them whenever one frame
cannot answer the question.**

This matters more than it sounds. A rash guard was described from its back,
recorded as having no graphic, and had to be corrected when its front turned up
two frames later carrying a chest wordmark.

"Best" is only as good as its evidence. 1,675 of 11,206 products carry the
store's own `shot_hint`; for the other 85% the ranking falls back to how much of
the frame the garment fills, which is a proxy for the closest look at the print
and is not the same thing. A tight crop of a cap's interior sweatband fills its
frame more completely than a photograph of the cap front does, so it wins. Sheet
300, cell 2700 is exactly that: a care label ranked first for a trucker cap whose
design is on another frame.

So when the top frame is a label, a sweatband, a hem, a folded stack or a fabric
close-up, that is the ranking failing rather than a product without a design.
Open the rest before recording anything, and never record a bare zone from a
frame that was never showing the design in the first place.

> **A single frame can say what is on its own zones. It can say nothing about
> the product.** `graphic_archetype` and `layout_archetype` are product-level.

If only a front frame exists, the design is front-only. If only a back frame
exists, back-only. Brands photograph what they print.

---

## Vocabularies — all closed, all from existing repo documents

Do not invent terms. Two prior research passes already collided by inventing
parallel G1–G9 systems, and there is a reconciliation note in the repo about the
damage. If something genuinely does not fit, put it in `notes` and flag it.

**Zones** — from `design_range.py`:
`full_front` `full_back` `centre_chest` `centre_back` `left_chest`
`upper_back_yoke` `outer_back_neck` `inner_neck_label` `short_sleeve`
`long_sleeve` `pocket` `cap_front` `cap_side` `cap_back`

On a flat lay the viewer's right is the wearer's **left**. A chest mark on the
right of the picture is `left_chest`.

**Zone state** — Constitution §5. Every zone gets exactly one:
- `active graphic zone` — carries the design
- `permanent identity zone` — brand furniture: neck labels, care tags
- `intentional negative space` — deliberately empty

A blank chest and a woven neck label are both unprinted by the design and are
**not the same thing**.

**Zone content**: `bare` `image_only` `text_only` `image_and_text`

**Zone fill**: `trace` `quarter` `half` `most` `full` `bleeds`

**Scale role** — Constitution §7: `S0` micro signature · `S1` chest identifier ·
`S2` emblem · `S3` hero · `S4` jumbo (approaches seams or uses the body as the
field)

**Hierarchy** — Constitution §9.3: `H1` hero · `H2` support · `H3` signature

**Graphic archetype** — Constitution §8, product level:
`image-led hero` · `typographic hero` · `emblem or badge` ·
`image-and-title lockup` · `poster or editorial panel` · `symbolic icon system` ·
`collage with controlled frame` · `character or object portrait` ·
`all-over or jumbo field` · `none`

**Layout archetype** — Constitution §6, product level:
`A1` small front identifier / large back hero · `A2` front hero / small rear
signature · `A3` front hero / clean back · `A4` clean or micro front / back hero ·
`A5` unequal front and back · `A6` image / language split · `A7` multi-zone ·
`A8` jumbo field · `blank` (no graphic anywhere)

**Treatment lanes** — `SHIRTFACED_CREATIVE_BRAIN.md` §11, array, one or more:
`smiley alone` · `lowercase wordmark alone` · `wordmark and smiley lockup` ·
`stacked lockup` · `horizontal lockup` · `outline type` · `tonal grey on black` ·
`tiny chest or incidental mark` · `oversized back statement` ·
`integrated type crossing imagery` · `caption beneath photography` ·
`caption above photography` · `type embedded inside the composition` ·
`small observation against a large image` · `loud phrase with minimal imagery` ·
`image only` · `text only` · `image and text` · `illustration` ·
`straight photography` · `distressed treatment` · `clean treatment` ·
`collegiate treatment` · `restrained premium` · `loud club or team adjacent`

---

## Do not record

- **Intent.** You cannot know what the maker meant. No "dominant proposition".
- **Reading distance.** You cannot judge from a photograph how something reads
  at three metres. It is a review test, not a property of the design.
- **Coordinates.** Which zone, and how much of it is filled. Exact position is
  the compositor's business.
- **Anything you cannot see.** If a colourway elsewhere tells you the text says
  "Stussy" but this frame is illegible, leave `text_content` empty and say so in
  `notes`. Inference dressed as observation is the single worst thing you can
  put in this table.

---

## Row format

```json
{
  "image": "design_corpus/brand/products/slug/image-01.jpg",
  "corpus": "brand",
  "brand": "brand-slug",
  "product": "product-slug",
  "name": "PRODUCT NAME",
  "tradition": "streetwear",
  "described_by": "your-model-id",

  "presentation": "flat_lay | on_model | hanging | folded",
  "view": "front | back | detail | side",
  "garment": "cut and construction in a phrase",
  "garment_colour": "washed charcoal",
  "backdrop": "off-white seamless",

  "graphic_archetype": "typographic hero",
  "layout_archetype": "A2",
  "treatment_lanes": ["tiny chest or incidental mark", "tonal grey on black"],

  "zones": [
    {
      "zone": "left_chest",
      "state": "active graphic zone",
      "scale_role": "S1",
      "hierarchy": "H1",
      "content": "text_only",
      "fill": "quarter",
      "description": "What is in this zone and how it sits."
    }
  ],

  "description": "40-120 words. Reconstruction grade -- see below.",
  "text_content": "Every word, verbatim, reading order, line breaks as /",
  "subject_primary": "typography",
  "subject_terms": ["wordmark", "tag"],
  "depicts_people": false,
  "references_property": false,
  "property_name": "",

  "integration": "none | text_inside_shape | text_around_shape | text_arched_over | text_arched_under | text_over_image | text_under_image | image_inside_letterform | text_baseline_rule | text_in_banner",
  "element_shapes": ["circle", "banner"],
  "type_styles": ["hand_lettered"],
  "type_case": "upper | lower | mixed | none",
  "type_effects": ["outline", "distressed"],
  "type_lines": 1,
  "palette_terms": ["washed charcoal", "tonal black"],
  "print_effect": "flat | halftone | distressed | textured | gradient | photographic",
  "stroke": "none | thin | medium | heavy",
  "detail_density": "low | medium | high",

  "confidence": "high | medium | low",
  "notes": "Anything the vocabulary could not hold, and anything you are unsure of."
}
```

One file per product, `row-NNNNNN.json`, or an array of them. Filenames do not
matter; `image` does.

---

## The description has to survive the image being deleted

A competent designer holding only the row, without the picture, should be able
to rebuild the design recognisably.

Three rules, each learned by failing a reconstruction test:

**Sequences get an explicit direction.** "Top to bottom: brick red, burnt orange,
tan, cream." A bare list gets read in whatever order the writer scanned, and a
rebuild came out with the stripes inverted.

**Relative size gets a number, not an adjective.** "Line two at roughly 0.9 the
cap height of line one." *Smaller* rebuilt at half size.

**Position gets a fraction where it matters.** "Stripes occupy the left 0.62 of
the width, ship overlaps their right end."

Every 20 sheets or so, take one row, rebuild the design from the text alone, and
compare. It is the only check that proves a description is a specification
rather than a caption.

---

## Things that will bite you

**Marketplace furniture.** Print-on-demand listings carry seller annotation
baked into the image: `FRONT-` / `-BACK` labels, a white or yellow caption block
reading "FRONT AND BACK PRINT!!", watermark bars. Roughly one in six of the flat
corpus. **It is not part of the design.** Record it in `notes`, set
`confidence: low`, and do not let it into the zones.

**Model photos in the flat corpus.** One source served 146 images that were
uniform, 600×600, on clean white, and every one was a cropped torso shot of a
model. Nothing in the numbers gave it away. If a "flat artwork" frame shows a
person wearing the garment, say so in `notes`.

**Blanks are data.** A garment with no graphic is a real finding, not a skip.
`graphic_archetype: "none"`, `layout_archetype: "blank"`, zones marked
`intentional negative space`. Keep it short — a blank tee gets three lines, not
three paragraphs. Do not spend paragraphs on neck-label tonality.

**Colourways are a design choice, not an anomaly.** Same artwork in four colours
is four rows. Record and move on; do not theorise about contrast rules.

**Never write a placeholder path.** 41 rows were once written with a literal
`...` in the `image` field and could not be joined back to the files they
described. The ingest now refuses them outright.

---

## Ingest

```bash
python scripts/ingest_observations.py path/to/rows/
python scripts/ingest_observations.py path/to/rows/ --dry-run
```

Upserts on `(image_path, described_by)` — re-describing replaces, a different
model gets its own row, so two models' readings coexist without merging. That is
why `described_by` must be your own model id and not copied.

It refuses rather than guesses: placeholder paths, unknown zones, unknown
states, unknown fills, unknown lanes, unknown scale roles or hierarchies, and
`confidence: high` with an empty subject or description.

**Run `--dry-run` first.** A dry run once refused all four rows in a batch and
was right to — they had been classified against the Constitution while the table
still held an invented vocabulary.

## Where everything actually is

The corpus is 13GB and lives only on the workstation. `var/` is gitignored, so
none of it is in the repository and none of it is on the server.

```
brief          C:\shirtfaced\studio\docs\VISUAL_PASS_HANDOVER.md
sheet builder  C:\shirtfaced\studio\scripts\product_sheet.py
sheets out     C:\shirtfaced\studio\var\preview\psheet
corpus         C:\shirtfaced\studio\var\design_corpus
               C:\shirtfaced\studio\var\design_corpus_flat
```

**Sheets 1–600 are already built and waiting** — that is your range. The
ordering is deterministic, so sheet 400 always holds the same nine products on
every run and a row traces back to a cell. Build more only if you pass 600.

```
cd C:\shirtfaced\studio
python scripts/product_sheet.py 1 --through 40   # sheet-0001..0040, png + json
python scripts/product_sheet.py --count          # 11,206 products, 1,246 sheets
```

Choosing which frame best shows a design means locating the garment in it, and at
50ms across 40,070 frames that is a 34-minute walk. It is done once and written
to `psheet/catalogue.json`; every build after that reads it and is immediate.

If a run starts by printing `ranking every frame`, the cache is missing and it is
earning it -- let it finish rather than killing it, or the next invocation starts
over from nothing. `--rebuild` forces the walk, and is only right after the
corpus has grown.

Build a range with `--through`. Looping the command once per sheet paid the 34
minutes every time, which is where twenty-two hours would have gone.

## The database is on the server, the corpus is not

Dry runs work locally -- they are pure validation and never open a connection:

```
python scripts/ingest_observations.py <your-rows-dir> --dry-run
```

The real write happens on the Oracle box, so rows have to be copied there first.
The key is at the repository root, not under `studio/` -- running these after
`cd studio` with a relative path will fail:

```
scp -i C:\shirtfaced\.secrets\oracle.key -r <your-rows-dir> ubuntu@161.33.31.74:/tmp/
ssh -i C:\shirtfaced\.secrets\oracle.key ubuntu@161.33.31.74 "cd /home/ubuntu/shirtfaced-studio && set -a && . ./.env && set +a && ./.venv/bin/python scripts/ingest_observations.py /tmp/<your-rows-dir>/"
```

Set `described_by` to your own model id. The upsert key is
`(image_path, described_by)`, so your rows sit beside anyone else's rather than
overwriting them -- which is the whole reason two describers can run at once.

---

## Quality bar

`confidence: low` is expected and wanted. A design too small, too busy or too
obscured to read honestly is recorded as such. **The one unacceptable output is
a confident row that is wrong**, because nothing downstream can tell it from a
correct one.

If a term does not fit, do not stretch it. Put the case in `notes` and flag it —
the vocabulary has already been extended twice by exactly that route.
