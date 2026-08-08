# Vendor brief — vector asset generation

*Paste this whole document as the brief. It answers the questions you asked and
tells you what already exists so nothing gets built twice.*

---

## What this feeds

Shirtfaced is an Australian humour-led apparel brand. The design engine takes
supplied content — a phrase, a mark — and assembles it into a composition using
a library of parts, then places that composition inside a real print zone at
real millimetre dimensions. Output is print-ready vector.

Register: Australian vernacular. Pubs, utes, the coast, the trades, backyards.
Funny rather than jokey.

---

## Do not build these — they exist

| Your category | Status |
|---|---|
| **2. Composition / layout patterns** | Done. Eight arrangements: crest, banner over mark, stamp, stencil, flanked word, tower, lone mark, ticket. Each names roles rather than shapes, so one arrangement produces many designs. |
| **3. Modular containers** | Done. Eighteen, and parametric — rectangle, capsule, shield, circle, arch, ticket, plaque, ribbon, diamond, hexagon, octagon, cog, rope roundel, three badges. A 6-tooth cog and a 24-tooth cog are one parameter apart, so more variants are free. |
| **4. Combination rules** | Done. A density budget that scales with print size, family constraints per role, and gates that refuse a crest on a 63mm pocket. |

Your category **1 is the real gap** and nothing in the repo covers it.

---

## Priority 1 — Garment silhouettes with print zones

This is the whole ask to start with. We have the print zones as *numbers*
already, in millimetres, but no garment geometry to place them against.

### Garments wanted

- T-shirt — crew, v-neck, oversized
- Long sleeve tee
- Hoodie — pullover, zip
- Crew sweatshirt
- Tank / muscle
- Crop top
- Cap — dad hat, trucker, snapback
- Bucket hat
- Beanie

Front and back view for each where the back differs.

### Print zones — use these IDs exactly

The engine looks these up by name. Spelling and underscores matter.

```
zone-centre_chest        zone-full_front         zone-left_chest
zone-full_back           zone-upper_back_yoke    zone-short_sleeve
zone-long_sleeve         zone-inner_neck_label   zone-outer_back_neck
zone-pocket
```

Only include the zones that garment actually has. A beanie has none of them; a
cap needs a front-panel zone, so add `zone-cap_front` and `zone-cap_side`.

### File structure

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     width="520mm" height="740mm" viewBox="0 0 520 740">
  <path id="garment-outline" d="..."/>
  <path id="garment-collar"  d="..."/>
  <path id="garment-seams"   d="..."/>
  <path id="zone-centre_chest" d="..."/>
  <path id="zone-left_chest"   d="..."/>
</svg>
```

Zones as separate named `<path>` elements, not groups. One path per zone.

### Units — real millimetres, not a normalised box

`viewBox` units are millimetres. A 520-unit-wide viewBox is a 520mm garment.
Print is metric here and the pipeline is metric end to end, so a 1000×1000
normalised box would just have to be converted back.

**State the flat measurements you drew to** in a comment at the top of each
file — chest width, body length, whatever you used. Adult M as the base. Do not
guess a house standard and leave it unstated; if the numbers are wrong we can
correct them, but only if we know what they were.

---

## Priority 2 — Thirteen redraws

We have crude in-house versions of these and want them drawn properly. Each is
a single mark, not a composition.

**Wrong and known to be wrong:** wings (reads as a bat), flame (reads as a
pear), breaking wave, thong (reads as a rugby ball), palm (fronds are radial
spokes), mountain range (three even spikes).

**Adequate but characterless:** anchor, crown, boomerang, stubby bottle, can,
spanner, heart.

---

## Priority 3 — Illustration

Volume work, in batches. Single marks, silhouette-led, built to read across a
room.

**Australian vernacular** — magpie, kookaburra, cockatoo, galah, kangaroo,
wombat, blue heeler, goanna, redback, cane toad, esky, hills hoist, ute, roo
bar, servo bowser, milk crate, camp chair, water tank, windmill, corrugated
iron, jetty, snag on bread, meat pie, lamington, Chiko roll, zinc stripe,
bucket hat, boardies, work boot, high-vis, stubby holder, gum leaf, wattle,
banksia, bottlebrush, Southern Cross variants.

**Trade** — hammer, shifter, angle grinder, tape measure, level, trowel,
welding mask, hard hat, gloves, drill, chalk line, sawhorse.

**Pub** — schooner, pot, pint, keg, tap, bottle opener, coaster, dart, pool
cue, jukebox, meat tray, raffle ticket, chook.

**Coast** — board (short, mal, fish), fin, leg rope, wax block, tinnie,
outboard, crab, prawn, snapper, bream, tackle box, rod, sinker, life ring.

**Hands and figures** — pointing hand, thumbs up, shaka, fist, open palm, hand
holding a can, arms crossed, figures standing, sitting, walking, running.

**Standard apparel marks** — skull, snake, eagle, wolf, bear, lion, rose,
laurel, oak leaf, lightning bolt, flames, wings, dice, cards, horseshoe, star
field, moon phases, rocket, radio tower.

---

## Naming

Matches the archive's existing convention so files drop straight in.

```
garment_tee_crew_front.svg        garment_hoodie_pullover_back.svg
garment_cap_trucker_front.svg     garment_tank_muscle_front.svg

symbol_flame_0001.svg             symbol_magpie_0001.svg
frame_ribbon_0001.svg             ornament_divider_0001.svg
```

`family_subject_NNNN` for marks. Families are `symbol`, `frame`, `ornament`,
`illustration_part`, `pattern`. Number from 0001 and increment for variants of
the same subject — three different flames are `symbol_flame_0001` through
`0003`, not `flame_a`, `flame_b`.

---

## Technical

**Send SVG.** The pipeline reads paths, rectangles, circles, ellipses, polygons
and lines, so primitives are fine — it converts them. Anything it does not read
yet gets a converter written for it, so send it regardless.

**Strokes expanded to filled outlines** where you can. An unexpanded stroke
scales wrongly between a 76mm yoke print and a 400mm back print, and separates
wrongly at the press.

**Colour is kept, not discarded.** The engine assigns its own inks per design,
but the palette a piece arrived in is recorded. Use colour freely; it just is
not the final word.

**Holes as counters**, wound against the outer path, so they hold under the
default fill rule rather than filling solid.

**No detail ceiling.** Prints run 76mm to 400mm and the engine measures how
involved a piece of artwork is, then places it accordingly. Something intricate
is a large-print asset, not a reject. Do not simplify defensively.

---

## Two things worth knowing

**Everything gets rendered and looked at.** Not a threat — a warning from
experience. We generated 25 shapes here and a third came out wrong: the flame
was a pear on three separate attempts, and the reviewing tool was itself lying
about two others. Confident SVG output and correct SVG output are different
things, and only looking tells them apart.

**Start with priority 1, one garment.** A single T-shirt front with its zones,
so we can check the units, the IDs and the zone geometry against the engine
before you produce a set. Faster to correct one file than nine.
