# Sourcing list

What we are hunting for. Register is Australian vernacular — pubs, utes, the
coast, the trades, backyards.

Categories below are where the obvious holes are, not a boundary. Anything good
that is not on the list is still wanted.

---

## Typefaces

Every design is currently set in one face, which is the hardest limit on the
work. More faces changes the output more than anything else here.

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

**One real constraint.** The font file gets held in the repository and glyphs
are converted to outlines from that exact file. Whatever arrives has to be the
file that stays — different metrics mean different designs.

---

## Illustration

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
crossed. Figures standing, sitting, walking, running.

### Standard apparel marks

Skull, snake, eagle, wolf, bear, lion, rose, laurel, oak leaf, lightning bolt,
flames, wings, dice, cards, horseshoe, star field, moon phases, rocket, radio
tower.

### Redraws

Crude in-house versions exist and need replacing:

wings · flame · breaking wave · thong · palm · mountain range · anchor · crown ·
boomerang · stubby bottle · can · spanner · heart

---

## Textures

Ink loss on a dry screen, over-inked bleed, photocopy degradation at several
generations, dry brush, cracked plastisol, misregistration offsets, halftone
moiré, paper grain, canvas weave, screen mesh, spray stipple, roller texture,
letterpress bite, worn vinyl.

Raster suits these. Bigger and higher contrast is more useful than subtle.

---

## Patterns

Bandana paisley, floral repeats, tapa-style geometric, camouflage-like abstract
fields, woodblock repeats, rope repeats, topographic contours, gingham,
houndstooth, argyle, tartan, ticking stripe, bandana borders.

A seamless tile is directly usable. A non-repeating panel is still worth having
as source material.

---

## Format

**Send whatever exists.** SVG, EPS, AI, PDF, PNG, JPG, a photograph of a printed
shirt. Everything gets ingested, and conversion is our side of the line — the
pipeline already reads paths, rectangles, circles, ellipses, polygons and lines,
and anything it does not read yet gets a converter written for it.

Colour is kept, not stripped. The engine assigns its own inks per design, but
the palette a piece arrived in is information about it and is recorded.

Two things that are useful rather than required:

- **Vector where it exists.** Prints run from a 76mm yoke to a 400mm back, and
  vector scales across that range without resampling. Raster still ingests.
- **Higher resolution than seems necessary.** Detail can be thrown away later.
  It cannot be added.

No detail ceiling, no colour limit, no minimum size. The engine measures how
involved a piece of artwork is and places it accordingly — something intricate
is a large-print asset, not a reject.
