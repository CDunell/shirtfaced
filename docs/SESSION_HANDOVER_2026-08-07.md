# SESSION HANDOVER — 7 August 2026

Decisions, working conclusions and open items from a strategy session. Nothing here
is canon yet. Canon lives in `WORLD.md`, the constitution and the decision register.
This file exists so the thinking is not lost, and so each item below can be promoted,
rejected or rewritten deliberately.

Companion document: `SYSTEM_AUDIT_2026-08-07.md` — the gap analysis this session produced.

---

## 1. THE WORD — settled, needs promoting to canon

**Shirtfaced is a verb and a state, not an identity.**

- "I got shirtfaced." "I want to get shirtfaced." "We all get shirtfaced together."
- Sits in the Australian lexicon alongside shitfaced, munted, written off, off your
  chops, maggoted, cooked, legless, blind.
- **There is no tribe noun and none is needed.** A noun is an identity claim the wearer
  has to defend. A verb is just Saturday. Lower social risk, wider entry.
- **The unit is the group.** Nobody gets shirtfaced alone. This is why group custom
  orders are a core commercial mechanic, not a side channel.
- **The boundary is the occasion, not the demographic.** The swappable token is the
  night — the trip, the wedding, the buck's, the grand final — not a suburb or an age
  bracket.

### The critical widening

**Shirtfaced means *that level of good time*, not *that many drinks*.**

Consequences:
- Addressable occasions expand from piss-ups to every big night.
- The sober mate, the pregnant mate, the driver are all still in the photo and still
  shirtfaced. Nobody is excluded from their own night.
- Wearability rises sharply. A garment reading *drunk* gets worn twice a year. One
  reading *we had the best night* gets worn on a Wednesday. Worn garments are the
  distribution channel.
- The pun survives intact — the audience supplies the original meaning for free. The
  edge is obtained without being owned. This is the deniability layer working.

**Protection clause:** this only holds if imagery does not drag it back. Schooners and
staggering collapse the word to *drunk* and the range is lost. Visual language sits on
**aftermath and affection** — the group shot at the end, the bad chips, shoes off,
sunrise, the mate asleep in a plastic chair. Everyone laughing at something that
happened, not at the drinking that may or may not have caused it.

**Action:** this section is the seed of `BRAND_VOICE.md` (Hot List item 1).

---

## 2. TAGLINE GRAMMAR — working, needs reconciling

Three-beat structure, third beat fixed:

> `<beat one>, <beat two>, shirtfaced`

Reference form: **Good mates, great times, shirtfaced.**

The escalation does the moral positioning — the mates come first, shirtfaced is the
consequence, not the goal. Nothing sells intoxication; it sells the night, after the fact.

Because the third beat is always the brand, every shirt and every caption signs itself.
This is frame-and-token expressed in copy, before artwork exists.

### Variants generated

Good mates, great times, shirtfaced · Long lunch, no dinner · Two carloads, one esky ·
Nan's 80th · Someone's cousin's boat · Everyone said early night · Ferry there, taxi home ·
Grand final, either way · Wedding, wake, whatever · Sunrise, servo pie · Best mate's
wedding, worst speech · Shoes in hand · Group chat's still going · Bali, day three ·
Nobody knows whose ute this is · Christmas with the outlaws · Meant to be there for one ·
Someone's turning 30 again · Melbourne Cup, Tuesday · Backyard, borrowed chairs ·
Camping, technically · Six mates, one tent · Fishing trip, no fish · Bucks in a bus ·
Wrong pub, right crowd · Twenty year reunion · Golf day, front nine only · Missed the
last train · Uncle's on the karaoke · Barefoot by nine · Whole street's here now ·
Nobody's got a charger

### CONFLICT — must be resolved

`src/lib/taglines.ts` runs a different fixed grammar:
`GOOD TIMES. / <rotating> / ZERO REGRETS.` with middle lines BAD INFLUENCES, COMPLETE
CHAOS, FUCK YES, NO PLAN, WENT SIDEWAYS.

`WORLD.md` emotional tone runs a third: "Fuck yeah." / "One more." / "We'll work it out."

Three grammars, no owner. `BRAND_VOICE.md` must pick one and the others must derive
from it or be retired. **Taglines should not live in a TypeScript file** — they should
be generated from canon.

---

## 3. TWO PRODUCT LINES — hypothesis, unproven

Not currently in any repo document. Named here so it can be argued with.

| | Line 1 — Brand mark | Line 2 — Standalone design |
|---|---|---|
| Bought because | It's Shirtfaced | The design is good |
| Buyer | Already knows the word | Has never heard of us |
| Job | Monetise believers | Recruit strangers |
| Branding | Headline | Signature — back neck, hem, sleeve |
| Economics | High margin, infinite reorder | Variance, failure rate, drops |
| Contains | Wordmark, crest, all drinkware, group custom | The five design mechanics |
| Review weighting | Recognition-heavy | Must survive HF-09 (weak without the logo) |

**Honest status:** this is a hypothesis about how acquisition and margin separate. It is
supported by the sequencing at Black Milk (designs sold first, community-branded product
followed) and contradicted by Budgy Smuggler (the wordmark on the garment *was* both
lines at once, and it worked). It is **not** an observed industry failure mode and was
initially overstated as one.

Cheapest test: post both to a cold organic surface and read tag-and-send rate. Paid
testing is the wrong instrument for an organic-first brand.

`DESIGN_REVIEW_SCORECARD.md` HF-09 already tests for the Line 2 property without naming it.

---

## 4. VISUAL DIRECTION — two registers

Rejected: Michael Bay (aspirational gloss makes the wearer a spectator and kills the
badge) and music-video (performance; this world is documentation).

### Register A — Found
Every group scenario. Handheld, wrong white balance, blown highlights, thumb in the
corner. The camera is a mate.
Highest-leverage single instruction: **one person aware of the camera, everyone else
mid-something-else.** That is what makes an image read as taken rather than made.
Kill list: symmetrical framing, everyone facing camera, even exposure, clean bokeh,
sunset backlight on all subjects, conventionally attractive casting, matching outfits.

### Register B — Reverence
Every product shot. Locked off, dead centre, hard key, slow push, absurd gravity. A
stubby cooler shot like a Fabergé egg.
Then vandalised: hero-lit cooler in wet grass with a bent cigarette; folded shirt on
black velvet with one sauce stain; thongs under museum lighting, one broken.

**The clash is the joke.** Register B grants a $28 item the seriousness Register A
refuses to grant anyone's actual life.

**Note:** Register A is compatible with existing canon. Register B is the thing
`stage-2/README.md` flags as conflicting with *product is incidental*. See item 6.

---

## 5. HOOKS — missing from the system

Animating a finished still produces slow drift, and drift is scroll-death. The fix is at
generation, not animation.

**Rule: the first frame must already be wrong.** Not establishing — mid-event. Prompt the
still as frame 40, not frame 1.

Six hook types:

1. **Mid-action entry** — already falling, already yelling, already spilling.
2. **Camera whip** — subject enters from off-frame at speed; camera overshoots, corrects.
3. **Reveal in-frame** — a hand enters from the bottom and places something down; camera static.
4. **The look** — one person turns and clocks the camera, deadpan, half a second. Cheapest and strongest.
5. **Register cut** — 0.8s Register A chaos, hard cut to Register B product, hard cut back.
6. **Physical impact** — camera jolts as someone knocks the operator, refocuses.

Global motion additions: `camera already moving at frame one`, `no slow zoom`,
`subject exits frame before clip ends`.

**Conflict:** `stage-2/CHANNEL_TRANSLATION.md` §5 bans trend transitions, speed ramps and
beat-synced reveals and specifies held shots and straight cuts. That is a coherent position
that never addresses attention capture. Reconcile before adopting either.

---

## 6. THE HERO LAST FRAME — proposed resolution to the central conflict

**Proposal: a 6-second clip resolves, in its final ~1.5 seconds, to the product in full view.**

This is the single highest-value idea from the session because it resolves several problems at once.

**It collapses the video compositing problem.** The final frames are effectively a still —
camera settled, subject squared to lens, chest unoccluded. So:
- composite on the **final** frame, not the first, then generate motion toward it;
- the print exists in exactly one controlled frame;
- everything before it can be blurred, cropped, half-turned and dark — the register we want;
- no SAM2, no per-frame tracking, no drift. The existing compositor works unmodified;
- motion blur does the work we would otherwise be fighting.

**It is also the better edit.** Chaos resolving to stillness, product landing on the last
beat. The register clash compressed into one clip instead of two cut together. It reads as
one idea. And it is maximally loopable — the first frame after the last is chaos again.

**It resolves the parked conflict.** *Product incidental* holds for Register A, which is
most of the frames. *Product hero* holds for the resolve. Both principles survive.

**Two demands:**
1. The resolve must be **earned, not merely stopped** — a beat of intent: the look to
   camera, the deadpan, the can raised into frame. Half a second. Without it, it reads as
   the clip ending.
2. The scene schema needs a **`resolve` / `end_state`** field alongside the hook. End state
   is constrained: chest to camera, arms clear, subject stationary, light on the torso.

**Explicit note:** do NOT audit the existing scenario bank against this constraint. All
generated output to date is dev work and disposable. Build the bank from the resolve
outward — the end state is the fixed point, and each scenario is then just *what chaos was
happening six seconds earlier, and what caused it to settle*.

---

## 7. COMPOSITOR — two defects and a scope decision

`studio/app/services/compositing.py` is well built and architecturally correct for stills:
deterministic, free re-runs, guaranteed text fidelity.

**Defect 1 — `_garment_mask` deletes print in shadow.**
Fabric colour is a single RGB median over the covered region; tolerance is Euclidean RGB
distance. Shading therefore reads as "not garment."
- Black tee: lit 0.20 vs fold 0.03 → distance ≈0.29 against 0.22 tolerance → ~⅓ ink loss.
- White shirt under flash: 0.95 vs 0.45 → ≈0.87 → print vanishes in folds entirely.
Direct flash on light garments is a core World 01 scenario, so this bites where it hurts most.
**Fix:** normalise each pixel by its own luminance before taking the distance — compare
chroma only. Shading is already handled separately by the luminance multiply, so the mask
should only answer "is this a different material."

**Defect 2 — `_displaced` takes the gradient over the whole photo,** including the garment
silhouette, which is the strongest gradient in frame. Placements near a collar or armhole
get yanked.
**Fix:** mask the gradient to the covered region before sampling.

**Scope decision:** do not extend the compositor to video. Item 6 removes the need. Manual
quad placement remains the throughput ceiling — worth benchmarking a reference-conditioned
image editor (Flux Kontext / Nano Banana class) on ~20 photos to see whether automatic
placement is viable. Expect text fidelity to be the deciding factor.

---

## 8. STANDING NOTE

All Shirtfaced photography and video generated to date is **dev work and disposable**.
Nothing is locked until the format is settled. Do not treat existing generated assets or
scenario banks as constraints on new work.

---

## 9. STRATEGIC BACKGROUND

Four brands dissected: **Old Row** and **Shinesty** (US), **Budgy Smuggler** and
**Black Milk Clothing** (AU). Patterns holding four-for-four:

- Audience existed before product, every time. None launched into silence.
- The customer is both the design department and the media department.
- Anti-aspirational casting is non-negotiable in humour apparel.
- Local short-run manufacture is a strategic capability — it is what makes customisation
  and fast reactive drops possible — not a cost problem.
- Roughly a decade to profitability is the base rate. Budgy lost money for eight-plus years.
  The break, when it came, was never bought.
- Every one engineered an escape from one-and-done: subscription, drop scarcity, group
  custom orders, or a boring repeat-purchase category behind the joke.

**Group custom is the recommended escape mechanism for Shirtfaced** and is likely
under-weighted. Australian drinking rituals are group rituals with a named occasion. Every
custom order is a paid design experiment plus a dozen billboards plus a group photo, and it
solves manufacturing minimums and cash cycle at the same time.

**What is formulable:** tribe definition, audience engine, frame/token/joke architecture,
cost per at-bat, the kill filter, casting rules, designing for the photograph someone else
takes, the one-and-done escape, portfolio math.
**What is not:** taste, timing, and the break. The system does not produce hits. It produces
a machine cheap enough to keep swinging, honest enough to know when it connected, and alive
long enough for the culture to hand it one.

**Selection metric:** track **tag-and-send rate**, not likes. Likes measure amusement; tags
and DMs measure *"this is literally you"*, which is the badge test and therefore the purchase
test. This matters more as generation capacity rises — volume without proportional rejection
discipline produces slop, and slop dilutes the tribal signal the whole brand rests on.

---

## OPEN ITEMS — nothing below is decided

1. Which tagline grammar wins, and does `taglines.ts` become generated output.
2. Whether the two-line product split is adopted, and how review weighting differs.
3. Whether hooks are adopted, and how §5 of `CHANNEL_TRANSLATION.md` is amended.
4. Whether the hero-last-frame resolution is accepted as the answer to the product-incidental
   conflict, and recorded in the decision register.
5. Trademark position on "shirtfaced" — IP Australia, class 25 and class 21. Unresolved and
   worth more than any individual design.
