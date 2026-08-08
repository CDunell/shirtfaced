# Vector asset brief — Shirtfaced

Australian humour-led apparel brand. Register is Australian vernacular: pubs,
utes, the coast, the trades, backyards.

Assets feed an engine that composes designs from parts and places them in real
print zones at real millimetre dimensions.

---

## Already built — do not make these

- **Composition / layout patterns.** Eight arrangements exist.
- **Modular containers.** Eighteen exist, parametric.
- **Combination rules.** Density budgets and placement constraints exist.

---

## 1. Garment silhouettes with print zones

The only category we need. Start here.

**Garments:** T-shirt (crew, v-neck, oversized) · long sleeve tee · hoodie
(pullover, zip) · crew sweatshirt · tank / muscle · crop top · cap (dad,
trucker, snapback) · bucket hat · beanie.

Front and back view where the back differs.

**Zone IDs — exact, including underscores:**

```
zone-centre_chest    zone-full_front       zone-left_chest
zone-full_back       zone-upper_back_yoke  zone-short_sleeve
zone-long_sleeve     zone-inner_neck_label zone-outer_back_neck
zone-pocket          zone-cap_front        zone-cap_side
```

Include only the zones that garment has.

**File:**

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     width="520mm" height="740mm" viewBox="0 0 520 740">
  <!-- adult M: chest 520mm flat, body 740mm -->
  <path id="garment-outline" d="..."/>
  <path id="garment-collar"  d="..."/>
  <path id="garment-seams"   d="..."/>
  <path id="zone-centre_chest" d="..."/>
  <path id="zone-left_chest"   d="..."/>
</svg>
```

- viewBox units are millimetres
- one `<path>` per zone, no groups
- adult M as base; state the flat measurements you drew to in a comment

**Deliver one T-shirt front first** for checking against the engine, then the
set.

---

## 2. Thirteen redraws

Single marks. Crude versions exist.

wings · flame · breaking wave · thong · palm · mountain range · anchor · crown ·
boomerang · stubby bottle · can · spanner · heart

---

## 3. Illustration

Single marks, silhouette-led, readable across a room.

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

```
garment_tee_crew_front.svg      garment_hoodie_pullover_back.svg
garment_cap_trucker_front.svg   garment_tank_muscle_front.svg
symbol_flame_0001.svg           frame_ribbon_0001.svg
```

`family_subject_NNNN` for marks. Families: `symbol`, `frame`, `ornament`,
`illustration_part`, `pattern`. Variants increment the number.

---

## Format

- SVG. Primitives fine — rect, circle, ellipse, polygon, line all convert.
- Strokes expanded to filled outlines.
- Holes as counters, wound against the outer path.
- Colour welcome; the engine reassigns inks per design.
- No detail ceiling. Prints run 76mm to 400mm. Do not simplify defensively.
