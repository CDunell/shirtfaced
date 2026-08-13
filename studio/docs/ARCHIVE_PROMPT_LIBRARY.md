# Archive Prompt Library

Generation prompts derived from `var/design_archive/` — 18,633 images across 22
sources, indexed by `scripts/index_archive.py`.

## Status

Working document. Cells are added as they are read. Every prompt here has been
written from images actually opened, never from a title or a count.

## Method

Adapted from the owner's proven Etsy prompt, which reads:

> *"You are a print on demand design research expert. Based on these photos of
> best selling designs, generate 10 design ideas and prompts... using trendy
> color palettes, design elements, font styles, and popular sayings..."*

Three changes, each with a reason.

**Four axes became three.** `popular_sayings` is dropped. In this archive the
sayings are band names, tour dates and brand marks — precisely the layer that
cannot carry over. Extracting it would produce an axis where every value is
unusable. What survives from it is text *treatment*, which folds into
`font_styles`.

**Screenshots became cells.** The original reads a dozen best-seller
screenshots. These read an era-and-register cell of hundreds of pieces, so an
axis records a *rule* that recurs across the cell rather than what is visible in
one image.

**The output suffix changed.** The original ends every prompt with `flat graphic
design, no background, transparent PNG, print on demand ready`. Tested
2026-08-13: image generators have no alpha channel and bake a background in
regardless — the first render came back black artwork on a black ground,
unusable. Replaced with an explicit white ground, keyed out afterwards.

**Art carries no lettering.** Type is set in vector after, so it spells
correctly, uses a face chosen once for the whole range, and prints crisp at any
size. The saying can change without regenerating the artwork.

## Cell selection

Decade alone is too coarse. The 1980s cell holds a festival billing tee and a
hand-drawn souvenir roundel that share a decade and nothing else. Cells below
are era **and** register.

---

## `skate-street-moto-1990s`

897 pieces / 6,746 images. Read: Metallica Pushead cutoff, Harley "Survival of
the Fittest" 1991, Bad Company 1991 tour, World Industries oval badge (2001),
Powell Peralta Fire Balls 1994, Toy Machine wholesale ad 2002.

**`color_palette`** — Dark garment ground is assumed, not chosen: black, faded
navy, washed charcoal. Print palettes are narrow and set against it, either a
single spot colour or one complementary pair (orange/blue, amber/cyan). Nothing
is crisp; colour arrives already faded by wash. Full colour is airbrush-blended,
never flat fill.

**`design_elements`** — An animal or skull as hero, rendered with menace, filling
the chest. Volume built two ways by register: airbrush gradient modelling in
colour, fine ink hatching and stipple in monochrome. A radiating structure behind
the subject — flames, rib-spokes, rays — pushing it forward. Ribbon banners.
Emblem lockups anchoring the base. Night scene-setting with silhouette
foregrounds: ridgelines, bare trees, headstones. The artist's signature sits
inside the artwork.

**`font_styles`** — Blackletter riding a ribbon banner. Stacked outlined display
caps with speed rules. Eroded stencil type overprinted *across* the artwork
rather than beside it. A tiny credit line at the base. Type arcs to follow the
artwork's contour rather than sitting on a straight baseline.

### Prompts

1. Boar's head three-quarter view, tusks up, bristles individually drawn, airbrush gradient modelling in two colours only — burnt orange and steel blue. Empty ribbon banner arcing above the head. Artwork on pure white, no scene backdrop, no garment, no drop shadow.

2. Ram skull front-on, curled horns filling the width, twenty tapering flame tongues radiating behind as a halo. Single spot colour, dense ink hatching for volume, no gradient. Pure black on pure white, maximum contrast.

3. Hornet in flight, wings blurred by hand-drawn speed lines, abdomen segmented in fine stipple. Contained in a hexagon emblem with an empty lower banner. Two colours, amber and black, on pure white.

4. Stag on a ridgeline at night, antlers silhouetted against a low moon, bare tree behind, headstones mid-ground, water foreground as flat cyan ripples. Black, cyan, bone. On pure white, no garment.

5. Snake coiled through a motorcycle wheel rim, scales as repeating hand-inked crescents, spokes radiating from behind. Empty emblem plate at the base. Single colour black on pure white.

6. Bat with wings fully spread, membranes veined and hatched, a small skull shape formed in the chest fur. Radiating rays behind. Pure black on pure white, no grey.

7. Bull head with a nose ring, breath steaming, airbrushed in orange and teal only, deep shadow under the jaw. Empty scroll banner beneath. On pure white, no backdrop.

8. Vulture perched on a bleached cattle skull in desert scrub, sun disc behind as concentric hand-cut rings. Silhouette foreground. Black, sand, rust. On pure white.

9. Clenched fist gripping a broken chain, links in heavy outline, forearm tendons hatched. Eroded and pitted throughout as though the print has cracked with age. Single colour black on pure white.

10. Horse skull in profile, flames pouring from eye socket and nasal cavity, mane as flowing ink strokes. Vertical oval containment, empty band around the perimeter. Black on pure white, maximum contrast.

---

## `festival-billing-1980s`

Read: Monsters of Rock Euro Tour 1984, Van Halen raglan 1984, Iron Maiden 1988,
Metallica Damaged Justice 1988, Dazz Band Joystick World Tour 1983.

**`color_palette`** — Black ground. Four to six spot colours used as *coding*
rather than blending: red, green, yellow, white, each act in its own colour. No
gradients anywhere. Colours knock out cleanly against black with no halo.

**`design_elements`** — A billing block: the whole print is a stacked hierarchy,
largest at top, descending by size to a city list in small type at the base. A
small illustration — a winged creature, a mascot — sits above or behind the top
line, subordinate to the type rather than the hero. Rules and boxes separate
tiers. The composition is a poster, not a graphic.

**`font_styles`** — Every tier in a different face, deliberately: blackletter,
outlined display, italic script, condensed sans. Hand-drawn rather than set. Top
tier carries a keyline or drop outline. Base line is a clean small sans listing
cities separated by mid-dots.

### Prompts

1. Vertical billing block on pure white: a small winged serpent illustration at top drawn in fine line, then four descending tiers of empty type panels — largest at top, smallest at base — each panel a different shape, separated by thin horizontal rules. Panels empty, type set later. Black line art on pure white.

2. Poster-style stacked frame with a horned moth illustration at the head, three empty banner slots below in descending width, a boxed slot bottom-left and a boxed slot bottom-right, and a thin baseline rule. Black on pure white, no fill, no shading.

3. Small hand-drawn gargoyle perched above an empty arched header panel, two empty rectangular tiers beneath separated by double rules, empty baseline strip. All containment, no text. Black on pure white.

4. Ornate empty cartouche at top with scroll ends, below it three empty stacked panels of decreasing width with a small starburst between each, base strip left empty for a city list. Line art, black on pure white.

5. Skeletal hand gripping a lightning bolt at the head of a vertical stack, beneath it four empty type panels with alternating keyline weights, thin rules between. Black on pure white, maximum contrast.

6. Winged eye illustration at top in fine hatching, empty banner immediately below with pointed ends, then two empty boxed tiers side by side, then a full-width empty baseline strip. Black on pure white.

---

## `souvenir-roundel-1970s`

Read: "Survivor Road to Hana" Maui, Hawaii Turtle tee, Whidbey Island crewneck,
Albright College crewneck.

The closest register in the archive to a joke-led graphic: the illustration is
naive and hand-drawn, the caption inside the roundel carries the punchline, and
the place name anchors it.

**`color_palette`** — Single colour, always. Deep navy or bottle green printed on
a pale heather ground — powder blue, oatmeal, ash. One ink, no halftone, no
second pass. The ground shows through the linework where the print has worn.

**`design_elements`** — A hard circular boundary containing everything. A naive,
deliberately unpolished hand-drawn scene inside: an animal, a road, foliage,
drawn with visible line wobble and no perspective discipline. A small caption box
*inside* the circle carrying the joke. Foliage and texture rendered as dense
scribble hatching. The circle is the whole design — nothing sits outside it.

**`font_styles`** — Hand-lettered throughout, following the circle's curve, top
arc reading left-to-right and bottom arc reading left-to-right too. Letterforms
irregular in width and spacing, clearly drawn by hand rather than set. Caption
inside in a smaller hand-printed all-caps. A place name in the smallest size,
tucked against the inner edge.

### Prompts

1. Hard circular boundary, inside it a naive hand-drawn wombat sitting beside a dirt road with scribbled foliage behind, an empty caption box inside the circle to the left of the animal, and empty arcs at top and bottom of the ring for lettering. Single colour black line art on pure white, visible line wobble, no perspective.

2. Circular roundel containing a hand-drawn pelican standing on a jetty post, dense scribble-hatched water beneath, empty rectangular caption slot inside the circle, empty top and bottom arcs. Black on pure white, one ink, naive style.

3. Roundel with a hand-drawn goanna crossing a road, tyre tracks behind it, scribbled grass on both verges, small empty caption box lower-right inside the circle. Empty perimeter arcs. Single colour, deliberate line wobble, on pure white.

4. Circular badge, inside it a hand-drawn ute bogged to the axles with scribbled mud and reeds, an empty caption panel above the vehicle, empty arcs top and bottom. Black line art, naive, no shading, on pure white.

5. Roundel containing a hand-drawn cockatoo perched on a fence wire, scribble-hatched sky behind, small empty caption box beneath the bird, empty perimeter arcs. One colour on pure white, irregular hand-drawn line.

6. Circular boundary with a hand-drawn fishing boat at a wharf, scribbled pilings and water, empty caption slot inside the lower left, empty arcs for perimeter lettering. Black on pure white, naive hand style, no gradient.

---

## `local-promo-1970s`

Read: Bill's Liquors Del Paso Blvd Sacramento, 24K Au Gold Fields Mining 1986,
Grandma's Basketball Jerzees.

The smallest register in the archive and the least like the rest: one small
left-chest hit, no back print, no display type.

**`color_palette`** — One ink, mid-blue or red, on natural, oatmeal or ash. The
ground is undyed rather than chosen. The print is small enough that wear removes
sections of it entirely.

**`design_elements`** — Left-chest placement only, roughly 90mm wide, sitting
above a patch pocket. A simple cartoon mascot with thick uniform line weight and
no shading — anthropomorphised object or animal, three or four lines of detail
total. No containment shape; the artwork floats.

**`font_styles`** — Business name arced above the mascot in a bold rounded
script. Address and town beneath on two straight lines in a plain condensed sans,
much smaller. Nothing else.

### Prompts

1. Small left-chest lockup: an anthropomorphised beer keg with arms and legs mid-stride, thick uniform line weight, no shading, three or four details total. Empty arc above the figure for a business name and two empty straight baselines beneath for an address. Single colour black on pure white.

2. Cartoon fuel pump with a face and arms, waving, uniform heavy outline, no fill. Empty curved band above, two empty straight lines below. Black on pure white, small-print simplicity.

3. Cartoon meat pie with legs running, motion lines behind, thick even line, no interior shading. Empty arc above and two empty baselines beneath. Single colour on pure white.

4. Anthropomorphised esky with arms folded and a grin, four details maximum, uniform outline weight. Empty top arc, two empty lower baselines. Black on pure white.

5. Cartoon crayfish standing upright holding a spanner, heavy uniform line, no shading. Empty arced band above, two empty straight baselines below. On pure white.

6. Cartoon petrol can with a face, tipping to pour, thick uniform line, no gradient. Empty arc above for lettering, two empty baselines below. Single colour black on pure white.

## Cells not yet read

`skate-1988-93` and `surf-1970s` from the Wayback tree, `indie-label-1990s`, and
the 2000s decade (183 pieces). Go Media's 120 pieces are a distinct
mid-2000s band-merch register and would make a cell of their own.
