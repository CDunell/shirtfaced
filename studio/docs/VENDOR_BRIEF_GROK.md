# Vector asset brief — Shirtfaced

Australian humour-led premium streetwear. The register is streetwear, not
Australiana: type-led wordmarks, small chest emblems, tattoo and occult flash,
brand-owned characters.

This is derived from 12,151 product images across 188 apparel brands that we
hold and have mined. Of 1,166 designs measured, 577 are a single element and the
median design carries four words. The graphic is usually the name, set well.

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
zone-cap_back
```

Include only the zones that garment has. A zone that exists per side takes a
`_left` / `_right` suffix.

`zone-cap_back` sits above the adjustment strap on a snapback or buckle. On a
fitted cap with no closure the whole back panel is available.

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

## 2. Five redraws

Single marks. Eight of the original thirteen are done and accepted — flame,
palm, crown, anchor, stubby bottle, heart, mountain range, breaking wave. These
five are still standing in:

wings · boomerang · can · spanner · thong

---

## 3. Illustration

Single marks, silhouette-led, readable across a room.

**Tattoo and flash** — skull, snake, eagle, wolf, panther, rose, dagger, dice,
cards, horseshoe, swallow, anchor, lightning, flame, wings, hourglass, hand of
fate, banner scroll, laurel, crescent moon, star field.

**Occult and horror** — reaper, cross, inverted arch, moon phases, candle, eye,
serpent, thorn, flame sigil.

**Character and mascot** — a drawn figure with a face and a posture, invented
rather than observed, with enough personality to carry twenty designs and be
recognised each time. This is the highest-value item on the whole brief.

**Panels and plates** — rectangular halftone or collage panels with borders,
torn edges, taped corners. Globe wireframes, grids, contour fields, star charts.

**Hands and figures** — pointing hand, thumbs up, fist, open palm, hand holding
a can, arms crossed. Figures standing, sitting, walking, running.

**Not this** — no wildlife, no native flora, no national food, no domestic
infrastructure. Depicting Australia literally is the souvenir register, and no
brand in our evidence works that way. What is Australian about Shirtfaced lives
in the words and the characters, not in a catalogue of fauna.

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

**Send the artwork. There are no structural rules.**

Earlier briefs asked for a single closed path with `id="mark"`, no detached
subpaths, counters wound against the outline, and a shape that survives at
25–30mm. Three of those were invented and the fourth is ours to handle:

- the converter already merges any number of paths, rects, circles, ellipses,
  polygons and lines into one — multi-path files have always ingested;
- nothing reads the `id`;
- detached subpaths are fine, and a constellation or a scatter needs them;
- ingested artwork is filled even-odd, so nesting decides what is a hole and
  winding direction no longer matters;
- there is no size test. Prints run 76mm to 400mm and the engine measures how
  involved a piece is and places it accordingly. Something intricate is a
  large-print asset, not a reject. Do not simplify defensively.

Colour is welcome and is recorded; the engine assigns its own inks per design.

Two things that help without being required: vector where it exists, because
prints span 76mm to 400mm and vector scales across that without resampling; and
higher resolution than seems necessary, because detail can be thrown away later
and cannot be added.

Anything the pipeline cannot read yet gets a converter written for it. That is
our side of the line, not a reason to send less.
