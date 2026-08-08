# Sourcing list

What we are hunting for.

## Where this list comes from

The first version of this document was written from imagination. It asked for
magpies, kookaburras, cockatoos, galahs, goannas, cane toads, hills hoists,
lamingtons and Chiko rolls, on the reasoning that Shirtfaced is Australian and
humour-led, so its artwork should depict Australian things. Twelve of those were
drawn and delivered. Every one of them reads as souvenir-shop iconography,
because that is what the list was.

We have 12,151 product images from 188 apparel brands in `var/design_corpus/`,
including thirty streetwear brands, twenty skate, ten Australian streetwear and
three Australian humour. The list should have been derived from those in the
first place. This version is.

Two kinds of evidence sit behind it. The mined numbers are in
`var/design_corpus/design_structure.json` and cover 1,166 designs. The subject
observations come from looking at roughly 180 products across 36 brands in the
streetwear, skate, Australian streetwear and Australian humour traditions —
enough to be confident about what recurs, not enough to put a percentage on it.

## What the corpus actually shows

**Designs are small.** Of 1,166 mined designs, 577 are a single element and 899
are one or two. Seven or eight elements appear four times in the whole set. The
median design carries four words, and that holds at every element count.

**They are type-led.** The dominant object on a streetwear garment is a
wordmark: set straight, arched, condensed, in blackletter, in athletic script,
in collegiate slab. Stüssy, Neighborhood, Pleasures, Born X Raised, Thrasher,
Deathwish, Primitive, Nena and Pasadena — the graphic *is* the name, and the
craft is in the lettering.

**Most garments carry almost nothing.** A very large share of what these brands
sell is a plain blank with a small embroidered or printed mark at left chest.
That is the volume product. The big back print is the exception.

**Where illustration appears it is one of four things.** A brand-owned character
or mascot, invented rather than observed — the Toy Machine monster, the
RipNDip cat, the Deathwish skull. Tattoo and occult flash — skulls, roses,
daggers, reapers, crosses, stars, flames, wings, snakes. A sports or
institutional crest. Or a rectangular photographic or collage panel dropped into
the chest like a plate.

**No brand in the corpus depicts its own country's wildlife or food.** Not the
Australian streetwear brands, not the Australian humour brands. The register
that was asked for does not appear in any of the evidence we hold.

The symbols already drawn — flame, crown, heart, anchor, wings, breaking wave —
sit inside the tattoo-flash lineage above and are on register. The vernacular
illustration brief was the wrong turn, not the symbol work.

---

## Typefaces

Every design is currently set in one face, which is the hardest limit on the
work. Given that the median design is one element and four words, more faces
changes the output more than anything else on this list.

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
| Blackletter | Band-merch, and far more common in the corpus than expected |
| Athletic script | Chain-stitch and varsity lettering |
| Rounded soft sans | Lighter material |

**One real constraint.** The font file gets held in the repository and glyphs
are converted to outlines from that exact file. Whatever arrives has to be the
file that stays — different metrics mean different designs.

---

## Lettering furniture

The parts a wordmark is built with, which the corpus uses constantly and the
archive barely has.

Arch and curve baselines at several radii. Condensed and extended containers.
Drop shadows, offsets, outlines, inline strokes, bevels. Underline rules with
end caps. Brackets, slashes, asterisks, daggers, registration and trademark
marks. Numerals as display objects. Small-caps label bars. Two- and
three-letter monogram containers.

---

## Emblems for the small mark

The left-chest mark is the highest-volume graphic these brands print, and it has
to survive at 60–90 mm. Small crests, shields, ovals, rosettes, seals, boxed
logotypes, stars, crosses, pennants, circular stamps with type on the ring.

---

## Illustration

### Tattoo and flash

Skull, snake, eagle, wolf, panther, rose, dagger, dice, cards, horseshoe,
swallow, anchor, lightning, flame, wings, hourglass, hand of fate, banner
scroll, laurel, crescent moon, star field. Traditional and fine-line both.

### Occult and horror

Reaper, cross, inverted arch, moon phases, candle, eye, serpent, thorn, flame
sigil. Recurs heavily across skate and Australian alt.

### Character and mascot

A drawn character with a face and a posture that could be *ours* — a figure with
enough personality to appear on twenty designs and be recognised each time. The
corpus is emphatic that these are invented, not observed. See
`docs/foundations/CHARACTERS.md`, which is a name list and nothing more.

### Panels and plates

Rectangular photographic or collage panels, halftone-screened, with a border.
Torn-edge and taped-corner treatments. Globe wireframes, grids, contour and
topographic fields, star charts.

### Hands and figures

Pointing hand, thumbs up, fist, open palm, hand holding a can, arms crossed.
Figures standing, sitting, walking, running.

### Redraws

Crude in-house versions exist and need replacing:

wings · thong · boomerang · can · spanner

The remaining eight — flame, palm, crown, anchor, stubby bottle, heart, mountain
range, breaking wave — are done.

### Not this

No wildlife, no native flora, no national food, no domestic infrastructure. Not
because Australia is off-limits, but because depicting it literally is the
souvenir register and no brand we are measuring against works that way. What is
Australian about Shirtfaced belongs in the words and the characters, which are
System A's business, not in a catalogue of fauna.

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

**And no structural rules.** Briefs sent from here have twice carried conditions
that were invented rather than derived: a single closed path, a required `id`, no
detached subpaths, and a test at 25–30mm. The converter merges any number of
shapes into one path; nothing reads the id; detached subpaths are legitimate;
ingested artwork fills even-odd so winding direction does not matter; and the
size test was removed once already before being written back in.

The rule this document is under is the one that governs intake generally:
everything comes in, the engine copes, and whether a finished design may be sold
is asked once, before release. A condition on what may arrive is not a standard,
it is a smaller archive.
