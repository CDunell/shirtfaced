# Asset specification

What the engine needs and cannot generate. Register is Australian vernacular:
pubs, utes, the coast, the trades, backyards. Single colour, screen-print
logic — bold shapes, confident negative space, no reliance on fine detail.

---

## Typefaces — 8 to 12 families

Full Latin, numerals, punctuation, regular and bold minimum. Variable welcome.

| Class | Used for |
|---|---|
| Athletic block, condensed | Collegiate arcs, sport — the workhorse |
| Slab collegiate / varsity | Crests, flanked words |
| Grotesque, wide and heavy | Oversized single-word chest and back prints |
| Workwear / industrial sans | Stamps, utility marks |
| Stencil | Sprayed, crated, military-surplus |
| Signwriter script | Hand-painted, pub, ephemera |
| Woodtype / Western display | Poster, novelty |
| Typewriter / monospace | Labels, tags, small print |
| Blackletter | Band-merch |
| Rounded soft sans | Lighter material |

TTF or OTF. Full character set — the typesetter errors on a missing glyph
rather than substituting, so gaps surface as blocked work.

The file gets held in the repository and glyphs converted to outlines from it,
so whatever arrives has to be the file that stays.

---

## Illustration — 400 to 800 marks

### Australian vernacular

Magpie, kookaburra, cockatoo, galah, kangaroo, wombat, blue heeler, goanna,
redback, bull ant, cane toad. Esky, hills hoist, ute, roo bar, servo bowser,
milk crate, camp chair, water tank, windmill, corrugated iron, jetty. Snag on
bread, meat pie, lamington, Chiko roll. Zinc stripe, bucket hat, boardies, work
boot, high-vis, stubby holder. Gum leaf, wattle, banksia, bottlebrush, salt
bush. Southern Cross variants.

### Trade and workwear

Hammer, shifter, angle grinder, tape measure, level, trowel, welding mask, hard
hat, gloves, drill, chalk line, sawhorse.

### Pub and social

Schooner, pot, pint, keg, tap, bottle opener, coaster, dart, pool cue, jukebox,
meat tray, raffle ticket, chook.

### Coast

Board (short, mal, fish), fin, leg rope, wax block, tinnie, outboard, crab,
prawn, snapper, bream, tackle box, rod, sinker, life ring.

### Hands and figures

Pointing hand, thumbs up, shaka, fist, open palm, hand holding a can, arms
crossed. Figures standing, sitting, walking, running — silhouette only.

### Standard apparel marks

Skull, snake, eagle, wolf, bear, lion, rose, laurel, oak leaf, lightning bolt,
flames (set), wings (set), dice, cards, horseshoe, star field, moon phases,
rocket, radio tower.

### Redraws

Crude in-house versions exist and need replacing:

wings · flame · breaking wave · thong · palm · mountain range · anchor · crown ·
boomerang · stubby bottle · can · spanner · heart

---

## Textures — 30 to 60 plates

Ink loss on a dry screen, over-inked bleed, photocopy degradation at several
generations, dry brush, cracked plastisol, misregistration offsets, halftone
moiré, paper grain, canvas weave, screen mesh, spray stipple, roller texture,
letterpress bite, worn vinyl.

Greyscale or 1-bit PNG, 300dpi+, 200mm square minimum. Tileable where the
texture is a field rather than an edge. Contrast matters more than tone.

---

## Patterns — 40 to 80 tiles

Bandana paisley, floral repeats, tapa-style geometric, camouflage-like abstract
fields, woodblock repeats, rope repeats, topographic contours.

Motif patterns only. Stripe, grid, check, chevron and dot are generated
in-house.

Repeat unit stated. Seamless.

---

## Format

Vector, because everything scales between a 90mm chest print and a 400mm back
print.

- SVG, paths only
- Strokes expanded to filled outlines — unexpanded strokes scale and separate
  wrongly
- No groups, transforms, clip paths or masks — flattened unpredictably
  downstream
- One colour; inks are assigned per design, so colour in the file is discarded
- Holes as counters, wound against the outer path
- Artwork filling the viewBox, origin top-left

Other formats — EPS, AI, PDF, SVG full of primitives — are convertible. The
converter is our side of the line.

**Test everything at 25mm.** Detail that reads on screen disappears on a left
chest. What holds up small works everywhere.
