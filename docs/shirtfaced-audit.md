# SHIRTFACED — SYSTEM AUDIT

**Date:** 7 August 2026
**Amended:** 10 August 2026 — see amendment notes inline. Scores, gap statuses and the
hot list are updated to verified current state (routes actually registered, tests
actually run, files actually read); original text is kept rather than deleted so the
delta is visible. Nothing below was updated on the strength of a document's claim
about itself — each amendment cites a file read, a test run, or a command executed
this session.
**Scope:** `Cdunell/shirtfaced` @ HEAD — 89 markdown documents, studio pipeline, storefront, admin.
**Method:** full read of foundations, research, studio docs, world-01 canon, stage-2 pack, compositing and planning code.

---

## SCORES

| Area | Score (7 Aug) | Score (10 Aug) | One-line verdict |
|---|---|---|---|
| 1. World & series | 7 / 10 | **8 / 10** | Characters now exist. Only one world still exists. |
| 2. Product & design | 5 / 10 | **7 / 10** | The kill filter is now code, tested, and has actually scored a design. Zero designs still come from this app's own generator. |
| 3. Marketing & channel | 4 / 10 | **4 / 10** | Unchanged. Still switched off. |
| 4. Brand voice | 2 / 10 | **8 / 10** | `BRAND_VOICE.md` exists, the word is defined, three registers reconciled to one. `taglines.ts` migration still pending, by its own admission. |
| 5. Pipeline & tech | 7 / 10 | **8 / 10** | Both flagged compositor bugs fixed. A real AI-judged review pipeline exists and is more built than this audit credited. Still no video path. |

**Overall (10 Aug): 7 / 10**, up from 5/10. The gap that's closed is canon-vs-code: the
foundational documents that were missing on 7 August now exist. The gap that hasn't
closed: this app has still never generated and fully reviewed one design of its own.

---

## THE ONE-PARAGRAPH SUMMARY

*(7 August, kept for record.)* You have built two excellent systems that do not touch each other, and documented a third that is turned off.

**System A (the world)** is deep, hard-won and running. **System B (product design)** is a rigorous constitution with not a single design ever passed through it. **System C (marketing)** is written and explicitly inactive. Nothing connects a design to a world, or a world image to a product page. Brand voice — the thing that is supposed to hold consistency while design content changes — has no owner at all.

Every gap below is downstream of that.

**Amendment, 10 August:** brand voice now has an owner (`BRAND_VOICE.md`) and System A
has a cast (`CHARACTERS.md`). System B's kill filter is real, tested code with a live
endpoint, verified by actually running it against a real image this session — not a
document anymore, an app. What's still true: System B has scored zero designs that
came from this repository's own generator, and Systems A and B still don't touch.

---

# AREA 1 — WORLD & SERIES — 7/10

## What is genuinely strong

- `UNIVERSE_PREMISE.md` establishes the correct hierarchy: Attitude → Worlds → Characters → Stories → Products. Products last. This is the right architecture and most brands never get here.
- `world-01/WORLD.md` (4,238 words) is the best document in the repo. The observer rule, the enclosure rule and the two-question branding rule are hard-won and precisely written.
- `CARRY_FORWARD_CANON.md` is the mechanism that makes a *series* possible — it separates rules that are World-01-specific from rules that are portable. This is unusually smart and it already exists.
- `CONTINUITY.md` + `SHOTLIST.md` give you rotation discipline: hero product rotation, camera position rotation, reject-if-repeats-an-emotional-beat.
- The machinery is real: `PLANNING_CANON_HEADINGS` allowlist, `validate-world`, `import-world`, planner sees only allowlisted sections. A rule is not real until it is imported. Excellent discipline.

## Gaps — ranked

**1.1 — RESOLVED, 10 August 2026.** `docs/foundations/CHARACTERS.md` now exists: a
family-and-friends web of 15 people, ages/occupations/relationships/personalities
supplied by the owner rather than invented, centred on the owner's own family. Two
names (Lucas, Tommy) are still open. `CONTINUITY.md` has not yet been given a cast
column — that part of the original action is still outstanding.

*(Original text, 7 August, kept for record:)* There are no characters. This is the biggest hole in the repo.
The premise names characters as level 3 of the hierarchy: "recurring ordinary Australians whose lives continue across worlds." No character bible exists. `CONTINUITY.md` tracks hero products and camera positions — not people. Without a recurring cast, worlds are *settings*, not *episodes*, and "ongoing series" is not achievable. Nothing carries across a world boundary except style rules.

**1.2 — Only one world exists, and there is no map of the others.**
The premise says "WORLD 01 is only one world, not the brand," but no candidate worlds are listed, no series arc is defined, and there is no `WORLD_TEMPLATE.md`. Creating World 02 currently means hand-copying World 01 and hoping.

**1.3 — The episode structure is already there and unnamed.**
`SHOTLIST.md` "Future Buckets" are: Night Out → Transition → Kick-ons → Morning After. That is a four-act structure for one night. It is the episode grammar, sitting in a backlog section, undeclared.

**1.4 — The Scene Specification is proposed, not built.**
`SHIRTFACED_VIDEO_PIPELINE_ARCHITECTURE.md` (295 words, "Proposed Canon") contains the correct idea — a scene is the canonical source, renderers consume it. It is not implemented. Photography prompts are currently the source of truth, which is the thing that document says is wrong.

**1.5 — APPEARS MOOT, checked 10 August 2026.** `docs/research/PROMPT_CONSTRUCTION_PRINCIPLES.md`
no longer exists anywhere in the working tree, and `git log --all --diff-filter=D`
finds no record of it ever being tracked and deleted — so either it was removed
before ever being committed, or it lived somewhere this search didn't reach. Either
way, the contradictory "camera as another friend" text is not currently present to
contradict anything. Flagged rather than closed, because I can't point to the commit
or decision that resolved it.

*(Original text, 7 August, kept for record:)* Live contradiction between two documents that both claim canon status.
`PROMPT_CONSTRUCTION_PRINCIPLES.md` Level 4 states the camera is "another friend," "**never** an invisible observer," and lists valid positions including *inside the back seat* and *through the passenger window*.
`WORLD.md` and `CARRY_FORWARD_CANON.md` state the exact opposite: "We are observers… the camera is never in the box with the subjects… a lift photographed from inside the lift is a passenger."
`PROMPT_CONSTRUCTION_PRINCIPLES.md` declares itself "permanent creative canon… read before any prompt generation." One of these is wrong and the newer, harder-won rule is the one *not* marked permanent.

---

# AREA 2 — PRODUCT & DESIGN — 5/10 → 7/10

## What is genuinely strong

- `SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md` — 10-step governing sequence, explicit permanent vs seasonal layers. No concept exempt for being funny. Correct principle, correctly stated.
- `DESIGN_REVIEW_SCORECARD.md` — 12 hard-fail gates plus a weighted 100-point rubric with approval bands. **This is the kill filter, and it already exists.** HF-09 "Weak Without the Logo" and HF-11 "Mock-Up Only Success" are exactly the right gates.
- `GRAPHIC_ARCHETYPE_TAXONOMY.md` — construction archetypes (G1 Isolated Emblem, etc.) derived from an evidence corpus, with findings classified as observed / inferred / derived. Genuinely rigorous.
- Supporting depth: composition mechanics, brand recognition systems, production visual language, collection architecture, brief and review-record templates.
- **New, 10 August:** the kill filter is no longer just a document. `design_scoring.py`
  (pure deterministic scorer) and `design_extraction.py` (real PIL-based measurement —
  genuine thumbnail/blur/greyscale/coverage tests against actual pixels) are real,
  tested code behind a live endpoint, `POST /api/design/score`. Verified this session
  by running it directly against a real image: it correctly scored the one measurable
  category and correctly refused to guess at the other eight, blocking release rather
  than fabricating a judgement. `design_advisor.py` also exists — corpus-derived
  presentation recommendations (scale role, coverage, ink count, placement, polarity)
  from 12,151 measured images across 188 brands in `studio/var/design_corpus/`, none
  of which existed at the 7 August audit.

## Gaps — ranked

**2.1 — UPDATED, 10 August 2026. The kill filter now runs. Nothing has been fed to it.**
`print_service.py`'s "no artwork in this repository yet" is still literally true: this
app's own `design_generator.py` has never produced a design, and the scorecard has
never scored one that came from it. What's changed: the scoring *machinery* is proven,
not theoretical — I ran it this session and it behaved exactly as documented, correctly
leaving nine of ten categories `NOT_TESTED` rather than guessing. Nobody has ever
constructed a full `DesignReviewInput` for a real candidate and persisted a decision.
That's the actual remaining gap, and it's narrower than "the entire system has never
run once."

*(Original text, 7 August, kept for record:)* Zero designs exist. The entire system has never been run once.
`print_service.py` says it outright: "There is no artwork in this repository yet." The scorecard has scored nothing. The archetypes have produced nothing. Every field in the product definition — collection role, commercial tier, scale role — is a required field with no populated value anywhere.

**2.2 — UNCHANGED. The constitution still formally refuses to connect to the world.**
Its own scope statement: "It does not govern the Brand Universe, photography, campaigns, characters, lore, social content or community activity." So System A and System B are disconnected *by design*. No document owns the question "which design belongs to which world," and therefore nothing owns the link from a post to a cart item. This is now arguably the single biggest remaining conceptual gap in the repo, since almost everything around it has moved.

**2.3 — RESOLVED.** `COLLECTION_ARCHITECTURE.md` now names "Line 1 — Brand mark" and
"Line 2 — Standalone design" explicitly, ties HF-09 to Line 1 and HF-11-style
independent value to Line 2, and cross-references Layer (Permanent Core, etc.). Verified
by reading the current file.

*(Original text, 7 August, kept for record:)* The two-line product split is not in the documents.
The distinction between brand-mark product and standalone-design product exists in your head and in conversation, not in the repo. `COLLECTION_ARCHITECTURE.md` has persistent product families and collection roles, which is the nearest structure, but the split is unnamed. HF-09 is effectively the Line 2 test without saying so.

**2.4 — UNCHANGED. Rules are still post-hoc, not generative.**
Everything in System B evaluates a design that already exists. There is no design *generator* analogous to `prompt_planner.py`. `design_advisor.py` (new since 7 August) prescribes *presentation* — archetype, scale, coverage, ink count — from corpus evidence, which is real progress, but its own docstring is explicit: "It will not write the joke, invent the artwork, or decide whether an idea is any good." The concept-generation gap stands.

**2.5 — RESOLVED.** Scale-role taxonomy (S1–S4) is now enumerated with measured
coverage bands in `design_advisor.py`'s `SCALE_BANDS`, derived from the corpus rather
than declared by fiat. Verified by reading the current file.

*(Original text, 7 August, kept for record:)* No hero / staple / hook taxonomy instantiated.
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

# AREA 4 — BRAND VOICE — 2/10 → 8/10

**RESOLVED, 7–8 August 2026 (before this amendment, confirmed still current on 10
August).** `docs/foundations/BRAND_VOICE.md` exists: the word defined as a verb and a
state ("that level of good time, not that many drinks"), the always-lowercase rule,
two named voices (Identity vs Storefront) mapped to which surface uses which, tagline
grammar with a 30-line starting bank, "good times bad decisions" formally retired.
`POSITIONING.md` (8 August) closes an adjacent gap this audit didn't originally name —
where the Australian part of the brand is allowed to live (words and characters, never
depicted subject matter), backed by evidence from the same 12,151-image corpus.

**One thing from the original action item is explicitly still open, by the document's
own admission:** `BRAND_VOICE.md` §9 flags that `taglines.ts` has not been migrated to
derive from canon — it still hand-authors its own line list, independently, which is
exactly how it drifted out of sync the first time.

---

*(Original text, 7 August, kept for record.)*

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

# AREA 5 — PIPELINE & TECH — 7/10 → 8/10

## Strong

- `compositing.py` is well-built: perspective quad, displacement by blurred-luminance gradient, luminance multiply for shading, colour-distance occluder cut-out. Deterministic, free re-runs, guaranteed text fidelity. Correct architecture for stills.
- Planner architecture with canon-heading allowlist, synchronous generation (ADR-010), `awaiting_decision` state, one-active-attempt index, advisory lock. Disciplined.
- Test coverage present. **10 August: verified directly — 829 unit tests, all passing,
  this session.** Integration tests (234) are skipped rather than failing in this
  environment; they need a live Postgres container per `LOCAL_RUNBOOK.md` that wasn't
  running here, so that layer is untested-here, not confirmed-broken.
- **New, 10 August: the photography review pipeline is more built than this audit
  credited.** `review_service.py` + `adapters/review.py`'s `OpenAIImageReviewClient` is
  a real, working AI judge — structured JSON-schema output, ten canon-derived gates,
  mood/authenticity/story/structural-plausibility scoring — that never approves or
  rejects itself and always lands on `AWAITING_DECISION` for the owner. This is the
  correct shape for "automated pipeline with a human final call," and it already
  exists; Area 2's design-scoring pipeline (§2.1 amendment) does not yet have its
  equivalent judgement layer, only the measurable half.

## Gaps

- **No video path.** `print_design()` takes one image and one hand-dragged quad. Cannot extend to frames. Still unchanged.
- ~~`_garment_mask` deletes print in shadow.~~ **FIXED.** Commit `58dfc56`, "fix: two
  compositor bugs from the audit (Hot List item 8)." Verified by reading the current
  code: distance is now taken on chroma (`photo / luminance`), not raw RGB, so shading
  no longer reads as "not garment."
- ~~`_displaced` takes the gradient over the whole photo.~~ **FIXED**, same commit —
  the gradient is now masked to the covered region before use.
- **Manual placement is the throughput ceiling** and the reason a video path cannot exist. Still unchanged.

*(Original gap text, 7 August, kept for record: "`_garment_mask` deletes print in
shadow. Fabric colour is a single RGB median; tolerance is Euclidean RGB distance, so
shading reads as 'not garment.' Black tee, lit 0.20 vs fold 0.03 → distance ≈0.29
against 0.22 tolerance → ~⅓ ink loss... `_displaced` takes the gradient over the whole
photo, including the garment silhouette. Any placement near a collar or armhole gets
yanked.")*

---

# HOT LIST — 7 August 2026 (STATUS AS OF 10 AUGUST)

Ranked by how much each unblocks. Kept for record, with status added per item.

| # | Action | Area | Status, 10 August |
|---|---|---|---|
| **1** | Write `BRAND_VOICE.md` and define the word. | 4 | **DONE.** Taglines.ts migration still open (see new list, #3). |
| **2** | Resolve the product-incidental vs product-photography conflict. | 3 | **OPEN.** Carried to new list, #4. |
| **3** | Build the character bible. | 1 | **DONE.** `CHARACTERS.md`. `CONTINUITY.md` cast column still open. |
| **4** | Fix the camera contradiction. | 1 | **APPEARS MOOT.** Offending file no longer exists; no commit found that explains why. |
| **5** | Run one design through the scorecard end to end. | 2 | **PARTIAL.** Scoring machinery built, tested, and proven this session. No real design has gone through it with a persisted decision. Carried to new list, #1. |
| **6** | Implement the Scene Specification as source of truth. | 1/3 | **OPEN.** Carried to new list, #6. |
| **7** | Add `resolve` / `end_state` to the scene schema. | 3 | **OPEN.** Carried to new list, #6 (merged — same underlying work). |
| **8** | Patch `_garment_mask` and `_displaced`. | 5 | **DONE.** Commit `58dfc56`. |
| **9** | Name the two product lines in `COLLECTION_ARCHITECTURE.md`. | 2 | **DONE.** |
| **10** | Write `WORLD_TEMPLATE.md` and list candidate worlds. | 1 | **OPEN.** Carried to new list, #7. |
| **11** | Define asset lineage from world image → product page. | 3 | **OPEN.** Carried to new list, #8. |
| **12** | Add a hook taxonomy. | 3 | **OPEN.** Carried to new list, #9. |

---

# HOT LIST — 10 AUGUST 2026

Ranked by how much each unblocks, given everything above. Six of the original twelve
items are done or moot; this is what's actually left, plus what this session's own
work surfaced.

| # | Action | Why it is here |
|---|---|---|
| **1** | **Generate and fully review one real design, end to end, through this app's own pipeline** — `design_generator.py` → compositing → `design_extraction.py` → a human populates the nine judgement categories `extract()` correctly leaves blank → `score_design()` → a persisted decision. Not a Codex export scored by hand in a chat. | The scoring *machinery* is proven; the *system* — generation through to a stored decision — has still never run once. This is the direct completion of old #5. |
| **2** | **Connect System B to System A.** Name which design belongs to which world. The constitution still formally refuses this by its own scope statement. | With brand voice, characters and the scoring engine all now real, this is the single largest remaining structural disconnect in the repo. |
| **3** | **Migrate `taglines.ts` to derive from `BRAND_VOICE.md`.** Flagged as not-done in the canon document's own §9. | The exact failure mode that produced the 7 August gap — voice living in an invisible TypeScript file — is still live for this one file. |
| **4** | **Resolve the product-incidental vs product-photography-hero conflict.** Written decision, in the decision register. | Unchanged from 7 August. Still blocks video, product reveals, hero frames, post→cart. |
| **5** | **Build a design generator.** Everything in System B still only evaluates work that already exists — `design_advisor.py` prescribes presentation, not concept. There is still nothing analogous to `prompt_planner.py` for System B. | Without this, item #1 above means a human designs by hand forever. |
| **6** | **Implement the Scene Specification as source of truth**, with `resolve`/`end_state` in the schema. | Unchanged from 7 August. Still the only path to a video sibling. |
| **7** | **Write `WORLD_TEMPLATE.md`** and list candidate World 02–05. | More valuable now than on 7 August — there's an actual cast to carry across a world boundary. |
| **8** | **Define asset lineage** from world image → product page. | Unchanged. Storefront and studio still share nothing but a repo. |
| **9** | **Add a hook taxonomy**, reconciled with `CHANNEL_TRANSLATION.md` §5's anti-trend rules. | Unchanged, and still lowest urgency — the marketing system it belongs to is still switched off entirely. |

---

# THE PLAN

*(7 August original, kept for record — see amendment below for current status against these exact exit tests.)*

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

## AMENDMENT, 10 August — Phase 1 exit test now passes.

`BRAND_VOICE.md`, `UNIVERSE_PREMISE.md` and `CHARACTERS.md` all exist and are mutually
consistent. Camera contradiction (old item 4) appears moot. Product-photography
conflict (old item 2) is the one Phase 1 item still genuinely open — see new Hot List
#4.

Phase 2's exit test does not pass yet, and won't from documents alone: the compositor
is patched (old item 8, done), but "one design through the full scorecard" still means
a real design, generated by this app, fully judged and persisted — not a hand-scored
Codex export in a chat transcript. New Hot List #1 is that exact exit test, unmet.

---

# CLOSING NOTE

The recurring failure mode in this repository is not sloppiness. It is the opposite: each system has been built to a very high standard *in isolation*, with explicit scope statements that prevent it touching the others. The constitution says it does not govern the universe. Stage 2 says no code reads it. The carry-forward canon says it changes nothing on its own.

Every one of those boundaries is individually defensible. Together they are why you are losing context: there is no document that stands above all of them and says how they connect.

Item 1 and Item 2 are that document, in two halves. Start there.
