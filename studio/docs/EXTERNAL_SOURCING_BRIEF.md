# What has to come from outside

*A brief for sourcing. Everything listed here is something the engine needs and
I cannot make to a standard worth printing.*

The rule this list is written under: anything even slightly off goes out. Not
"good enough for now", not "passable at a small size". If it is not right, it is
on this list.

---

## 1. What I can make, so it is not paid for twice

Do not commission any of this.

**Parametric geometry.** Anything defined by a formula: circles, polygons of any
side count, stars of any point count, cogs, scalloped roundels, diamonds,
capsules, shields, arches, tickets, plaques, banners with swallowtail ends,
crosses, chevrons, arrows, sunbursts, glints, zigzag rules, dot rows, tapered
dividers, corner marks, brackets. These come out right first time because
correct is computable. Variation is free -- a 6-tooth cog and a 24-tooth cog are
one line apart.

**Print behaviour.** Halftone screens, distress speckle, knockouts, layering,
ink assignment, density budgeting.

**Everything structural.** Type setting as outlines, arcs, slots, composition
grammars, placement bounds, sizing, determinism, the licence gate, the database.

**Colour systems.** Palettes with contrast rules against garment colours. I can
derive these from the corpus measurements rather than guess.

---

## 2. Typefaces — the biggest single gap

Every design the engine makes is set in one face. That is why the sample sheets
all look related no matter how much the arrangement changes. Nothing else on
this list would improve the output as much.

**Needed: 8–12 families**, each with a full Latin character set, numerals,
punctuation and at minimum a regular and a bold.

| Class | What it is for | Priority |
|---|---|---|
| Athletic block, condensed | Collegiate arcs, sport, the workhorse | 1 |
| Slab collegiate / varsity | Crests, flanked words | 1 |
| Grotesque, wide and heavy | Oversized single-word fronts | 1 |
| Workwear / industrial sans | Stamps, stencils, utility | 2 |
| Stencil | The stencil grammar has no stencil face | 2 |
| Vintage script / signwriter | Ephemera, ticket stubs, hand-painted feel | 2 |
| Woodtype / Western display | Novelty, pub, poster | 3 |
| Typewriter / monospace | Labels, tags, small print | 3 |
| Blackletter | Band-merch register | 3 |
| Rounded soft sans | Lighter, friendlier jokes | 3 |

**Licence requirements, and these are hard requirements:**
- Commercial use on goods for sale, explicitly permitted
- Redistribution of the font file within a private repository permitted, or a
  licence that survives the file being vendored
- No per-seat or per-title fee that scales with print runs
- Open Font Licence is ideal and free of all of the above problems

**Format:** TTF or OTF. Variable fonts are fine and welcome. The engine converts
glyphs to outlines, so hinting does not matter but a complete `cmap` does — a
missing glyph is a hard refusal, not a substitution.

---

## 3. Illustration — the bulk of the work

I cannot draw anything representational. This is not modesty; six attempts at a
flame produced a pear three times.

**Needed: 400–800 marks.** Single-colour, print-ready, silhouette-led.

### 3a. Replacements for shapes I got wrong

These are in the archive now, marked as placeholders, and they are wrong:

| Element | What is wrong |
|---|---|
| `symbol_wings_0001` | Reads as a bat or a moustache. Needs feather steps that scan as a wing. |
| `symbol_flame_0001` | Reads as a pear. Needs an asymmetric flicker. |
| `symbol_wave_0001` | The curl is passable, the face is not. |
| `symbol_thong_0001` | Reads as a rugby ball. |
| `symbol_palm_0001` | Fronds are radial spokes, not leaves. |
| `symbol_mountains_0001` | Three even spikes, not a range. |

### 3b. Shapes that are merely adequate, so by the rule above they go too

| Element | Why |
|---|---|
| `symbol_anchor_0001` | Correct but stiff. No character. |
| `symbol_crown_0001` | Three triangles on a bar. |
| `symbol_boomerang_0001` | A curved wedge. |
| `symbol_stubby_0001` | Readable as a bottle, dull as a mark. |
| `symbol_tinnie_0001` | A chamfered rectangle. |
| `symbol_spanner_0001` | Blocky. A drawn one would have taper and a proper jaw. |
| `symbol_heart_0001` | Generic. |

### 3c. Subjects not yet attempted at all

Grouped so a commission can be scoped in batches.

**Australian vernacular** — the register the brand actually lives in.
Magpie, kookaburra, cockatoo, galah, kangaroo, wombat, blue heeler, goanna,
redback, bull ant, cane toad, esky, hills hoist, ute, roo bar, servo bowser,
milk crate, camp chair, snag on bread, meat pie, lamington, Chiko roll, zinc
stripe, bucket hat, boardies, work boot, high-vis, stubby holder, tinnie boat,
outboard, jetty, corrugated iron, water tank, windmill, salt bush, gum leaf,
wattle, banksia, bottlebrush, southern cross variants, hills of the divide.

**Trade and workwear.** Hammer, shifter, angle grinder, tape measure, level,
trowel, welding mask, hard hat, gloves, drill, chalk line, sawhorse.

**Pub and social.** Schooner, pot, pint, keg, tap, bottle opener, coaster, dart,
pool cue, jukebox, meat tray, raffle ticket, pokies, chook.

**Coast.** Board (short, mal, fish), fin, leg rope, wax block, sea urchin,
tinnie, crab, prawn, snapper, bream, tackle box, rod, sinker, life ring.

**Hands and figures.** Pointing hand, thumbs up, shaka, fist, open palm, holding
a can, arms crossed, silhouetted figure standing, sitting, walking, running.

**Generic marks that every apparel archive needs.** Skull, snake, eagle, wolf,
bear, lion, rose, laurel, oak leaf, lightning bolt (drawn, not geometric),
flames set (multiple), wings set (multiple), dice, cards, horseshoe, star field,
moon phases, planet, rocket, radio tower, satellite dish.

### 3d. Format requirements — non-negotiable, the ingestion refuses otherwise

- **SVG.** Not EPS, not AI, not PDF, not PNG.
- **Paths only.** No `<rect>`, `<circle>`, `<polygon>`, `<text>` or embedded
  raster. If the drawing tool exports primitives, convert to paths before
  sending.
- **Outlines, not strokes.** Every stroke expanded to a filled path. A stroke
  scales wrongly and separates wrongly.
- **No groups, no transforms, no clip paths, no masks, no filters.** These get
  flattened wrongly by somebody else's software at the worst moment.
- **One colour.** The engine assigns ink. Any fill colour in the file is
  discarded, so do not use colour to carry meaning.
- **Holes as counters,** wound opposite to the outer path, so they hold under
  the default fill rule.
- **Normalised viewBox**, origin at top-left, artwork filling it.
- **Under 4,000 drawing commands.** Beyond that it cannot be separated into a
  few inks without redrawing, and the ingestion refuses it.
- **Legible at 25mm.** Test it at that size before sending. Most detail that
  looks good on screen disappears on a left chest.

### 3e. Licence requirements — every item, individually

- Commercial use on goods for sale
- The item's own identifier at its source, not just the collection's
- A URL that resolves to that item
- The terms as written, quoted, not summarised
- Date checked

An item without an identifier cannot be re-checked later and will be stored as
unusable. This is not bureaucracy: a museum publishing open metadata has not
published every image in it under the same terms, and an out-of-copyright work
can have a scan carrying its own claim.

---

## 4. Textures

Procedural distress and halftone I can make. What I cannot make is texture that
looks like it came off a press.

**Needed: 30–60 texture plates.**

Ink loss on a dry screen, over-inked bleed, photocopy degradation at several
generations, dry brush, cracked plastisol on an old shirt, misregistration
offsets, halftone moiré, paper grain, canvas weave, screen mesh, spray stipple,
roller texture, letterpress bite, stamp-pad unevenness, worn vinyl cracking.

**Format:** 1-bit or greyscale PNG at 300dpi minimum, 200mm square or larger,
tileable where the texture is a field rather than an edge. These are used as
masks, so contrast matters more than tonal subtlety.

---

## 5. Patterns

**Needed: 40–80 repeat tiles.**

Gingham, houndstooth, argyle, tartan variants, ticking stripe, pinstripe, dot
grids, diamond lattice, chevron fields, wave repeats, camouflage-like abstract
fields, bandana paisley, tapa-style geometric, woodblock repeats, rope repeats,
chain-link, mesh, grid papers, topographic contours.

I can generate the strictly geometric ones (stripe, grid, check, chevron, dot).
Anything with a motif — paisley, floral, tapa, camouflage — has to be drawn.

**Format:** as illustration above, plus the tile's repeat unit stated explicitly
and proven seamless by tiling it 3×3 before sending.

---

## 6. Photography

The engine has an image slot and nothing to put in it. That is System A's
territory and is generated, but if photographic elements are wanted *inside*
designs — a halftoned face, a landscape knocked into a shape — those need
supplying as high-contrast images suitable for one-colour separation.

**Needed if wanted at all:** 50–100 images, high contrast, clear silhouette,
resolvable at 1-bit. Rights cleared for goods for sale, including any people in
them.

---

## 7. Priority, if it is being commissioned in stages

1. **Typefaces.** Nothing else changes the output as much. Even three faces
   would break the sameness.
2. **The thirteen shape replacements** in 3a and 3b. Small, well-specified, and
   they remove the placeholders that are currently in the archive pretending to
   be finished.
3. **Australian vernacular illustration.** This is the register the brand lives
   in and there is nothing in it.
4. **Textures.** Cheap to source, large visible effect.
5. **Trade, pub, coast illustration.** Volume.
6. **Patterns.** Useful but the engine gets less out of them than out of marks.
7. **Photography.** Only if photographic designs are actually wanted.

---

## 8. What to send back

For each item: the SVG (or font, or PNG), and one line of provenance —
source name, item identifier, URL, licence terms as written, date checked. A
spreadsheet or a JSON file alongside the assets is fine. The ingestion reads
them, records everything as unverified, and nothing becomes usable until the
terms are entered against the item.

If any of the format requirements in 3d are inconvenient for the supplier, say
so and I will write a converter. What cannot be worked around is the licence
trail, because these go on garments that are sold.
