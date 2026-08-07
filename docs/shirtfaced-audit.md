# SHIRTFACED — SYSTEM AUDIT

**Date:** 7 August 2026
**Scope:** `Cdunell/shirtfaced` @ HEAD — 89 markdown documents, studio pipeline, storefront, admin.
**Method:** full read of foundations, research, studio docs, world-01 canon, stage-2 pack, compositing and planning code.

---

## SCORES

| Area | Score | One-line verdict |
|---|---|---|
| 1. World & series | **7 / 10** | World 01 is excellent. The *series* it belongs to does not exist. |
| 2. Product & design | **5 / 10** | World-class framework, zero instances, formally disconnected from the world. |
| 3. Marketing & channel | **4 / 10** | Good documents, all switched off, and the key creative conflict is unresolved. |
| 4. Brand voice | **2 / 10** | No document exists. Three competing registers in active use. |
| 5. Pipeline & tech | **7 / 10** | Stills pipeline is strong and real. Video is a 295-word proposal. |

**Overall: 5 / 10.** The thinking is far ahead of the instantiation. You have a constitution and no citizens.

---

## THE ONE-PARAGRAPH SUMMARY

You have built two excellent systems that do not touch each other, and documented a third that is turned off.

**System A (the world)** is deep, hard-won and running. **System B (product design)** is a rigorous constitution with not a single design ever passed through it. **System C (marketing)** is written and explicitly inactive. Nothing connects a design to a world, or a world image to a product page. Brand voice — the thing that is supposed to hold consistency while design content changes — has no owner at all.

Every gap below is downstream of that.

---

# AREA 1 — WORLD & SERIES — 7/10

## What is genuinely strong

- `UNIVERSE_PREMISE.md` establishes the correct hierarchy: Attitude → Worlds → Characters → Stories → Products. Products last. This is the right architecture and most brands never get here.
- `world-01/WORLD.md` (4,238 words) is the best document in the repo. The observer rule, the enclosure rule and the two-question branding rule are hard-won and precisely written.
- `CARRY_FORWARD_CANON.md` is the mechanism that makes a *series* possible — it separates rules that are World-01-specific from rules that are portable. This is unusually smart and it already exists.
- `CONTINUITY.md` + `SHOTLIST.md` give you rotation discipline: hero product rotation, camera position rotation, reject-if-repeats-an-emotional-beat.
- The machinery is real: `PLANNING_CANON_HEADINGS` allowlist, `validate-world`, `import-world`, planner sees only allowlisted sections. A rule is not real until it is imported. Excellent discipline.

## Gaps — ranked

**1.1 — There are no characters. This is the biggest hole in the repo.**
The premise names characters as level 3 of the hierarchy: "recurring ordinary Australians whose lives continue across worlds." No character bible exists. `CONTINUITY.md` tracks hero products and camera positions — not people. Without a recurring cast, worlds are *settings*, not *episodes*, and "ongoing series" is not achievable. Nothing carries across a world boundary except style rules.

**1.2 — Only one world exists, and there is no map of the others.**
The premise says "WORLD 01 is only one world, not the brand," but no candidate worlds are listed, no series arc is defined, and there is no `WORLD_TEMPLATE.md`. Creating World 02 currently means hand-copying World 01 and hoping.

**1.3 — The episode structure is already there and unnamed.**
`SHOTLIST.md` "Future Buckets" are: Night Out → Transition → Kick-ons → Morning After. That is a four-act structure for one night. It is the episode grammar, sitting in a backlog section, undeclared.

**1.4 — The Scene Specification is proposed, not built.**
`SHIRTFACED_VIDEO_PIPELINE_ARCHITECTURE.md` (295 words, "Proposed Canon") contains the correct idea — a scene is the canonical source, renderers consume it. It is not implemented. Photography prompts are currently the source of truth, which is the thing that document says is wrong.

**1.5 — Live contradiction between two documents that both claim canon status.**
`PROMPT_CONSTRUCTION_PRINCIPLES.md` Level 4 states the camera is "another friend," "**never** an invisible observer," and lists valid positions including *inside the back seat* and *through the passenger window*.
`WORLD.md` and `CARRY_FORWARD_CANON.md` state the exact opposite: "We are observers… the camera is never in the box with the subjects… a lift photographed from inside the lift is a passenger."
`PROMPT_CONSTRUCTION_PRINCIPLES.md` declares itself "permanent creative canon… read before any prompt generation." One of these is wrong and the newer, harder-won rule is the one *not* marked permanent.

---

# AREA 2 — PRODUCT & DESIGN — 5/10

## What is genuinely strong

- `SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md` — 10-step governing sequence, explicit permanent vs seasonal layers. No concept exempt for being funny. Correct principle, correctly stated.
- `DESIGN_REVIEW_SCORECARD.md` — 12 hard-fail gates plus a weighted 100-point rubric with approval bands. **This is the kill filter, and it already exists.** HF-09 "Weak Without the Logo" and HF-11 "Mock-Up Only Success" are exactly the right gates.
- `GRAPHIC_ARCHETYPE_TAXONOMY.md` — construction archetypes (G1 Isolated Emblem, etc.) derived from an evidence corpus, with findings classified as observed / inferred / derived. Genuinely rigorous.
- Supporting depth: composition mechanics, brand recognition systems, production visual language, collection architecture, brief and review-record templates.

## Gaps — ranked

**2.1 — Zero designs exist. The entire system has never been run once.**
`print_service.py` says it outright: "There is no artwork in this repository yet." The scorecard has scored nothing. The archetypes have produced nothing. Every field in the product definition — collection role, commercial tier, scale role — is a required field with no populated value anywhere.

**2.2 — The constitution formally refuses to connect to the world.**
Its own scope statement: "It does not govern the Brand Universe, photography, campaigns, characters, lore, social content or community activity." So System A and System B are disconnected *by design*. No document owns the question "which design belongs to which world," and therefore nothing owns the link from a post to a cart item.

**2.3 — The two-line product split is not in the documents.**
The distinction between brand-mark product and standalone-design product exists in your head and in conversation, not in the repo. `COLLECTION_ARCHITECTURE.md` has persistent product families and collection roles, which is the nearest structure, but the split is unnamed. HF-09 is effectively the Line 2 test without saying so.

**2.4 — Rules are post-hoc, not generative.**
Everything in System B evaluates a design that already exists. There is no design *generator* analogous to `prompt_planner.py`. The deterministic mechanics you asked about are review mechanics.

**2.5 — No hero / staple / hook taxonomy instantiated.**
Scale-role taxonomy is named as constitutional and never enumerated.

---

# AREA 3 — MARKETING & CHANNEL — 4/10

## What is genuinely strong

- `CHANNEL_TRANSLATION.md` is a serious document. Source event → five layers → per-channel jobs. Instagram mix percentages, Reel durations, TikTok social roles, prominence scale P0–P3, reuse scale R0–R3, six campaign phases (Trace → Recognition → Reveal → Release → Proof → Continuation), stable `CHANNEL_*` reject codes.
- `CAMPAIGN_AND_DROP_SYSTEM`, `SEASONAL_CAMPAIGN_SYSTEM`, `WEBSITE_IMAGE_SYSTEM`, `PRODUCT_PHOTOGRAPHY` all exist with real content.
- `launch-decision-register.md` and the launch-research pack show the operational thinking is done.

## Gaps — ranked

**3.1 — The entire marketing system is switched off.**
`stage-2/README.md`: "reference only. Nothing in them reaches the planning model, and no code reads them." Five documents, ~4,500 words, zero effect.

**3.2 — The most important unresolved creative decision in the repo is flagged and parked.**
Also from `stage-2/README.md`: `PRODUCT_PHOTOGRAPHY.md` "pushes against a core Version 1 principle. The product specification says *product is incidental*… A product photography discipline is close to the opposite, and reconciling the two is a creative decision, not an implementation one."

That decision is still unmade. It is the same decision as: does a clip end on a hero product frame? Everything about product reveals, hero last frames, and the post→cart link is blocked behind it.

**3.3 — No video system exists.**
295-word proposal. Seedance 2.0 Fast named with settings. No motion prompts anywhere in the repo. No hook taxonomy. No resolve/end-state grammar. The stills pipeline has no motion sibling.

**3.4 — Hooks are actively discouraged.**
`CHANNEL_TRANSLATION.md` §5 bans trend transitions, speed ramps, beat-synced reveals and autoplay noise, and specifies "straight cuts, held shots and ambient sound." That is a coherent aesthetic position and it is in direct tension with stopping a scroll. The document never addresses attention capture.

**3.5 — No line from post to cart.**
No asset lineage from a world image to a product detail page. The storefront (`src/`) and the studio (`studio/`) share a repo and nothing else. `products-data.generated.ts` has no products.

---

# AREA 4 — BRAND VOICE — 2/10

**There is no brand voice document in this repository.** 89 markdown files, none of them a voice or tone guide.

Voice currently lives in three places, in three different registers:

| Source | Register |
|---|---|
| `src/lib/taglines.ts` | `GOOD TIMES. / <rotating> / ZERO REGRETS.` — "BAD INFLUENCES", "COMPLETE CHAOS", "FUCK YES", "NO PLAN", "WENT SIDEWAYS" |
| `world-01/WORLD.md` emotional tone | "Fuck yeah." / "One more." / "We'll work it out." / "Who's driving?" |
| Working conversation | "Good mates, great times, shirtfaced." |

Three structures, three tones, no owner, no reconciliation. The taglines file is the only one with a fixed grammar — and it lives in a TypeScript file in the storefront, invisible to the studio and to canon.

**Additionally: the word is undefined.** Nowhere in the repo does any document state what *shirtfaced* means, that it functions as a verb and a state, that it is a thing you *get* and something you get *together*, or that it does not require intoxication. The linguistic core of the brand is undocumented, which is why the tagline registers drift.

`CHANNEL_TRANSLATION.md` §4 gives good caption *rules* ("never explain the joke or force slang") but rules are not a voice.

**This is the single cheapest high-value fix in the audit.** It is also the direct answer to "brand consistency while design content changes" — the answer is voice, and voice is the one thing not written down.

---

# AREA 5 — PIPELINE & TECH — 7/10

## Strong

- `compositing.py` is well-built: perspective quad, displacement by blurred-luminance gradient, luminance multiply for shading, colour-distance occluder cut-out. Deterministic, free re-runs, guaranteed text fidelity. Correct architecture for stills.
- Planner architecture with canon-heading allowlist, synchronous generation (ADR-010), `awaiting_decision` state, one-active-attempt index, advisory lock. Disciplined.
- Test coverage present (25 unit, 16 integration).

## Gaps

- **No video path.** `print_design()` takes one image and one hand-dragged quad. Cannot extend to frames.
- **`_garment_mask` deletes print in shadow.** Fabric colour is a single RGB median; tolerance is Euclidean RGB distance, so shading reads as "not garment." Black tee, lit 0.20 vs fold 0.03 → distance ≈0.29 against 0.22 tolerance → ~⅓ ink loss. White shirt under flash, 0.95 vs 0.45 → ≈0.87 → print vanishes in folds. Direct flash on light garments is a core World 01 scenario. Fix: normalise per-pixel luminance before distance (chroma-only comparison); shading is already handled separately by the luminance multiply.
- **`_displaced` takes the gradient over the whole photo,** including the garment silhouette. Any placement near a collar or armhole gets yanked. Fix: mask the gradient to the covered region.
- **Manual placement is the throughput ceiling** and the reason a video path cannot exist.

---

# HOT LIST

Ranked by how much each unblocks.

| # | Action | Area | Why it is here |
|---|---|---|---|
| **1** | **Write `BRAND_VOICE.md` and define the word.** What *shirtfaced* means, verb form, group form, no-intoxication-required, the tagline grammar, the three registers reconciled into one. Make `taglines.ts` derive from it. | 4 | Nothing else holds consistency while designs change. Cheapest, highest value. |
| **2** | **Resolve the product-incidental vs product-photography conflict.** Written decision, in the decision register. Recommended shape: found register = product incidental; reverence register = product hero; one clip resolves from one to the other. | 3 | Blocks video, product reveals, hero frames and the post→cart line. Everything downstream. |
| **3** | **Build the character bible.** 6–10 recurring people, named, with relationships and roles. Add a cast column to `CONTINUITY.md`. | 1 | Without it there is no series, only a mood board with rotation rules. |
| **4** | **Fix the camera contradiction.** Delete or rewrite Level 4 of `PROMPT_CONSTRUCTION_PRINCIPLES.md`. Demote it from "permanent canon" or promote the observer rule into it. | 1 | Two canon documents currently instruct opposite things. |
| **5** | **Run one design through the scorecard end to end.** Any design. Populate every required field. | 2 | The system has never executed. Until it does, its quality is unknown. |
| **6** | **Implement the Scene Specification** as the source of truth, with photography as one renderer. | 1/3 | Already designed. It is the only path to a video sibling. |
| **7** | **Add `resolve` / `end_state` to the scene schema.** End state constrained: one subject, chest to camera, unoccluded, stationary, half a second of intent. | 3 | Makes hero-last-frame generation deterministic and collapses the video compositing problem. |
| **8** | **Patch `_garment_mask` to chroma-only distance** and mask `_displaced` to the covered region. | 5 | Two small fixes, both bite hardest on core scenarios. |
| **9** | **Name the two product lines in `COLLECTION_ARCHITECTURE.md`.** Brand-mark line and standalone-design line, with their different jobs and different review weightings. | 2 | HF-09 already tests for it. Make it explicit. |
| **10** | **Write `WORLD_TEMPLATE.md`** and list candidate World 02–05. Promote the Night Out → Transition → Kick-ons → Morning After arc into named episode structure. | 1 | Turns one world into a series. |
| **11** | **Define asset lineage** from world image → product page, so a post and a PDP share provenance. | 3 | The post→cart line does not exist today. |
| **12** | **Add a hook taxonomy** and reconcile it with the anti-trend rules in `CHANNEL_TRANSLATION.md` §5. | 3 | Currently the docs forbid attention capture without addressing it. |

---

# THE PLAN

Three phases. Do not parallelise them.

## Phase 1 — Settle the canon (nothing generates)
Items 1, 2, 3, 4. All writing, no code, no generation.
**Exit test:** a new person can read `BRAND_VOICE.md`, `UNIVERSE_PREMISE.md` and the character bible and correctly predict whether a given caption, design or scene belongs.

## Phase 2 — Prove the systems on one instance each
Items 5, 7, 8.
One design through the full scorecard. One scene with an end state through generation to composite. Compositor patched.
**Exit test:** one design and one 6-second clip that both survive their own review gates.

## Phase 3 — Make it a series and connect it to commerce
Items 6, 9, 10, 11, 12.
Scene spec as source of truth, two named lines, world template, asset lineage, hooks.
**Exit test:** World 02 can be created from the template by someone who did not build World 01, and any image on the site can be traced back to the scene that made it.

---

# CLOSING NOTE

The recurring failure mode in this repository is not sloppiness. It is the opposite: each system has been built to a very high standard *in isolation*, with explicit scope statements that prevent it touching the others. The constitution says it does not govern the universe. Stage 2 says no code reads it. The carry-forward canon says it changes nothing on its own.

Every one of those boundaries is individually defensible. Together they are why you are losing context: there is no document that stands above all of them and says how they connect.

Item 1 and Item 2 are that document, in two halves. Start there.
