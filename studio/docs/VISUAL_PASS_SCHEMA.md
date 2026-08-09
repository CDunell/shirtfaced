# Visual pass: criteria and output

What gets recorded for every design in the corpus, and where each field comes
from. Agreed before the pass runs, because a vocabulary improvised sheet by
sheet produces 3,000 rows that cannot be queried against each other.

## The one rule that shapes everything

**Measured and observed are kept apart and never mixed in a column.**

A measurement is produced by code and is reproducible: run it again on the same
file and it returns the same number. An observation is produced by a model
looking at a picture, and it is not reproducible — a different model, or the
same model on a different day, may say something else.

Both are useful. Silently blending them would mean nobody can tell which figures
survive a re-run, and this corpus has already had one case of a number that
looked solid and was measuring nothing.

So: measured fields carry no model attribution and can be recomputed at will.
Observed fields carry the model, the date and a confidence, and can be
recomputed only by another pass.

Nothing in here judges whether a design is good. The brands already voted by
shipping it; the job is to record what they shipped, not to rate it.

---

## A. Identity — from collection, already on disk

| field | type | source |
|---|---|---|
| `design_id` | uuid | generated |
| `brand_slug` | text | `brand.json` |
| `product_slug` | text | directory name |
| `image_path` | text | relative to corpus root |
| `source_url` | text | `product.json` |
| `tradition` | text | `brand.json` — streetwear, skate, au-surf, novelty … |
| `category` | text | `product.json` — shirt, hat, tote, drinkware … |
| `price` | text | `product.json`, populated on 98% of sampled products |
| `surface` | enum | `front` `back` `sleeve` `detail` `flat` `worn` — from `shot_hint` |

## B. Measured — deterministic, recomputable

From `mine_arrangement.py` and `mine_design_structure.py`. No model involved.

| field | type | meaning |
|---|---|---|
| `symmetry` | float 0–1 | ink surviving a left-right mirror |
| `containment` | float 0–1 | how much filling the outline's holes adds — badge vs stack |
| `alignment` | enum | `centred` `justified` `left` `right` |
| `arch_measured` | bool | top edge higher at centre than shoulders |
| `ink_count` | int | distinct ink values holding >4% of the design |
| `fill` | float 0–1 | ink density within its own bounding box |
| `aspect` | float | width ÷ height of the ink's bounding box |
| `element_count` | int | bands of ink separated by clear ground |
| `band_shape` | text | `single tall mass`, `lead above, support below`, … |
| `coverage` | float | ink as a share of the print area |

## C. Observed — subject and description

**The test this section has to pass: a competent designer holding only this row,
without the image, should be able to rebuild the design to a recognisable
tolerance.** Tags alone fail that test — `subject: animal, construction: badge`
describes ten thousand designs. So the row carries prose, and the tags exist to
make the prose queryable rather than to replace it.

| field | type | vocabulary |
|---|---|---|
| `description` | text | **Reconstruction-grade prose, 40–120 words.** What is depicted and how it is drawn; where every element sits relative to the others; how the type relates to the image; the colours and where they fall. Written so it could be handed to an illustrator as a brief. |
| `text_content` | text | **Every word appearing in the design, verbatim, in reading order, line breaks marked with `/`.** Without this nothing can be rebuilt. |
| `subject_primary` | enum | `character` `animal` `object` `vehicle` `landscape` `scene` `skull` `floral` `celestial` `food` `emblem` `typography` `abstract` `pattern` `none` |
| `subject_terms` | text[] | 2–5 free terms, lowercase singular |
| `depicts_people` | bool | |
| `references_property` | bool | parody, licence or fan reference to an existing property |
| `property_name` | text | what it references, where identifiable |

## D. Observed — construction

The one that matters most: how the parts are put together.

| field | type | vocabulary |
|---|---|---|
| `construction` | enum | `badge_circular` `badge_oval` `crest_shield` `banner_ribbon` `label_frame` `stacked_type` `arch_over_mass` `mass_only` `type_only` `panel_scene` `letterform_container` `pattern_field` |
| `integration` | enum | `none` `text_inside_shape` `text_around_shape` `text_arched_over` `text_arched_under` `text_over_image` `text_under_image` `image_inside_letterform` `text_baseline_rule` `text_in_banner` |
| `element_shapes` | text[] | `circle` `oval` `shield` `banner` `rule` `star` `burst` `rectangle` `arc` `organic` |
| `focal_position` | enum | `centre` `upper` `lower` `left` `right` |

## E. Observed — type

| field | type | vocabulary |
|---|---|---|
| `type_styles` | text[] | `grotesque` `condensed_sans` `rounded_sans` `slab` `serif_old_style` `serif_didone` `tuscan` `blackletter` `script_brush` `script_formal` `hand_lettered` `collegiate` `stencil` `pixel` `none` |
| `type_case` | enum | `upper` `lower` `mixed` `none` |
| `type_effects` | text[] | `outline` `drop_shadow` `inline` `distressed` `gradient` `arched` `none` |
| `type_lines` | int | lines of text in the design |

## F. Observed — colour and finish

| field | type | vocabulary |
|---|---|---|
| `ground` | enum | `black` `white` `cream` `grey` `navy` `colour` `heather` `transparent` |
| `palette_terms` | text[] | 2–5 terms, e.g. `washed orange`, `acid green` |
| `print_effect` | enum | `flat` `halftone` `distressed` `textured` `gradient` `photographic` |
| `stroke` | enum | `none` `thin` `medium` `heavy` |
| `detail_density` | enum | `low` `medium` `high` |

## G. Provenance — required on every observed row

| field | type | meaning |
|---|---|---|
| `described_by` | text | model identifier |
| `described_at` | timestamptz | |
| `sheet_id` | text | which contact sheet and cell, so any row can be re-checked by eye |
| `confidence` | enum | `high` `medium` `low` |
| `notes` | text | anything the vocabulary could not hold |

`confidence: low` is expected and wanted. A design too small or too busy to read
is recorded as unreadable rather than guessed at.

---

## Storage

One table, `design_observations`, alongside the existing archive tables. Enums
as Postgres enums so a typo fails at write rather than fanning out into a query
later. `subject_terms`, `element_shapes`, `type_styles`, `type_effects` and
`palette_terms` as `text[]`. Measured fields nullable, because a design can be
described before it is measured or the reverse.

Constraints worth having in the database rather than only in Python:

- `confidence <> 'high' OR subject_primary IS NOT NULL` — a confident row must say what it is
- `ink_count IS NULL OR ink_count >= 1`
- `symmetry IS NULL OR symmetry BETWEEN 0 AND 1`
- unique on `(image_path, described_by)` so a re-run replaces rather than duplicates

## Order of work

1. Migration and model.
2. Backfill A and B from the JSON already on disk — no model needed, ~3,000 rows.
3. Visual pass in sheets of 24, writing C–G.
4. First 200 reviewed against this vocabulary before continuing, in case a term
   is missing or a category is doing no work.
