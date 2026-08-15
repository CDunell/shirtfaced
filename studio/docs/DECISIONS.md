# Architecture Decisions

## ADR-001 — API app before Custom GPT

The application is the source of truth.

A Custom GPT may later act as an interface, but it must not own durable workflow state.

## ADR-002 — Modular monolith

A single FastAPI application is sufficient.

Microservices add cost and failure modes without benefit for one local user.

## ADR-003 — PostgreSQL production database

The application will use the existing PostgreSQL database in the Oracle Cloud environment.

PostgreSQL supports the required locking, JSONB, constraints, concurrent safety and durable deployment.

SQLite is not the production target and may only be used for narrow unit tests where PostgreSQL-specific behaviour is irrelevant.

## ADR-004 — Markdown plus database

Markdown holds creative canon and remains editable and versionable.

The database holds operational state, audit history and relationships.

Neither alone is sufficient.

## ADR-005 — Human approval gates

No model can approve its own output permanently.

Human approval controls images and canon.

## ADR-006 — No generic agent framework

The workflow is explicit and finite.

Plain application services are easier to test, understand and control than an agent framework.

## ADR-007 — Server-rendered interface

**Superseded by ADR-011.**

Jinja2 and HTMX are preferred for Version 1.

The product needs a clear workflow, not a front-end platform.

## ADR-008 — Model adapters

OpenAI models and API details change.

Adapters protect domain logic and make tests deterministic.

## ADR-009 — One image per action

This limits cost and preserves deliberate creative review.

Variations require another explicit action.

## ADR-010 — Synchronous Version 1 workflow

For one user, synchronous orchestration is simpler.

Persist every state transition so a background worker can be added later without redesigning the domain.

**Reaffirmed 5 August 2026.** An externally drafted Phase 3 pack proposed asynchronous
generation: a queued attempt state, a background worker and an immediate HTTP
response. It was declined for Version 1. One user clicking one button does not need a
job runner, and adding one to a single-process deployment buys polling in the
interface and a larger set of failure modes to test in exchange for latency the user
is already waiting on deliberately.

The escape hatch in this ADR still applies: every state transition is persisted, so a
worker remains a later service change rather than a redesign. The agreed attempt state
machine is the one in `ARCHITECTURE.md`, which keeps `awaiting_decision` — the state
that makes ADR-005's human approval gate visible in the data.

## ADR-011 — Base Web interface

**Supersedes ADR-007.**

The interface uses Uber's Base design system (`baseui` with React and Styletron)
rather than Jinja2 with HTMX.

The owner's decision. The application is a daily-use creative production tool, and the
review screen in particular carries dense state: an image, a prompt, a rationale, five
scores, drift notes and three decision actions. A mature component library gives that
screen a better result than hand-rolled server-rendered markup.

Accepted consequences:

- React, Styletron and a Node build step join a Python application, so the repository
  has two toolchains and CI has two pipelines.
- FastAPI serves a JSON API and static build output rather than Jinja2 templates. The
  endpoints in `API_CONTRACT.md` become the sole interface between the two halves,
  which makes that contract load-bearing rather than advisory.
- The UI test layer becomes a JavaScript test runner, not server-rendered assertions.
- The interface is pinned to **React 18**. Base Web 18.2.0 relies on `defaultProps` for
  function components, which React 19 removed; `Card` and others throw at render on 19.
  Ninety-five Base modules use that pattern, so patching around it is not viable. This
  is revisited when Base ships React 19 support.
- A single `@types/react` version is forced through npm `overrides`, because a
  transitive Base dependency pulls `@types/react` 16 and two copies make every Base
  component fail to typecheck as a JSX element.

Unchanged by this decision:

- The application remains a single deployable service behind one reverse proxy.
- No API key ever reaches browser JavaScript. All OpenAI calls stay server-side.
- All rendered model output is still escaped.
- Human approval gates (ADR-005) and one image per action (ADR-009) are untouched.

## ADR-012 — Review output carries both vocabularies

`PHASE_4_REVIEW_CONTRACT.md` specifies nine evidence-based gates, each with a status,
one visible observation, stable finding codes, a confidence and whether the finding is
material. It does not include the five 1-to-5 scores or the two compliance booleans
that `DATA_MODEL.md`, `API_CONTRACT.md` and `WORKFLOW.md` all require.

Both are kept. The review model returns the gates *and* the scores.

The alternative was to derive the scores from gate statuses, which would have invented
precision: a five-point score cannot honestly be computed from PASS, FAIL, UNCERTAIN
and NOT_APPLICABLE. Asking for both costs a little more output and keeps every number
attributable to the model that produced it.

The three-value verdict the product specification uses is the one thing that *is*
derived, because it is a pure renaming of the recommendation:

- `APPROVE_RECOMMENDED` → `approved`
- `APPROVE_WITH_NOTE_RECOMMENDED` → `approved_with_note`
- `REJECT_RECOMMENDED` → `rejected`
- `REVIEW_UNCERTAIN` → `uncertain`

`uncertain` is new. The product specification lists three automated outcomes, but the
review contract requires the reviewer to say when the evidence is insufficient rather
than guess, and collapsing that into one of the other three would be a lie about what
the model saw.

## ADR-013 — `variation_requested` is a terminal attempt state

`WORKFLOW.md` says a variation marks the attempt `variation_requested`, and
`DATA_MODEL.md` lists it among the allowed human decisions. But `ARCHITECTURE.md`, the
Python `AttemptState` enum and the PostgreSQL type ended an attempt only at `approved`,
`rejected` or `failed`. The state existed in the decision vocabulary and nowhere else.

`variation_requested` is now a terminal attempt state, added through migration 0005.
It sits **outside** the active-attempt partial index, so asking for a variation
releases the world for the next explicit action.

The alternative — recording a variation as `rejected` — was rejected. The owner asking
for another take is not the owner saying the image was wrong. Conflating them would put
a false entry into `# Rejected Drift`, and the first three entries there go into every
planning prompt. The cheapest way to corrupt the planner is to teach it a lesson that
was never learned.

A variation therefore changes no document: no shotlist marker, no continuity entry, no
canon. It records the instruction, frees the world, and waits for an explicit Continue
World to create the child attempt.

Adding an enum member in Python does not change the PostgreSQL type. Both migration
0004 and migration 0005 needed an explicit `ALTER TYPE ... ADD VALUE`, and in both
cases an integration test caught the omission rather than a reviewer.

## ADR-014 — `gpt-image-1-mini` is not used, and drafting stays unused with it

Drafting was wired up so framing and geometry could be checked cheaply, on the theory
that a fifth of the cost buys most of the information. The first genuine mini draft —
the first one where the draft model was actually called rather than merely recorded —
settled it the other way.

The prompt for that frame explicitly asked for: nobody posing, nobody acknowledging
the camera, two strangers arguing beside a scooter rack, a blurred bus with unreadable
markings, motion blur, imperfect framing, a cropped shoulder at the left edge, and a
blurred parking sign pole in front of the lens.

`gpt-image-1-mini` returned six cast members in an evenly spaced arc, every face lit,
readable and turned toward the lens, with none of the occlusion, cropping, background
life or foreground obstruction that had been asked for. A group portrait. The same
canon and the same instructions produce documentary frames on `gpt-image-2`, so this
is not a prompt or canon failure — the model does not follow the documentary
instructions that matter most to this world.

It also contained an orphaned car door: a panel and a window frame with no vehicle
behind them, at the wrong scale, at footpath level.

**Decision.** Mini is out. It is not used for production or for drafts. A cheap model
earns its place only by producing frames of the standard of the seeded reference set;
until one does, iteration happens on the full model and costs what it costs.

The draft path is kept rather than reverted. It is correct now — the model is chosen
at client construction, a draft that cannot run refuses instead of silently costing
full price, and the attempt records the model actually called. The mechanism is sound
and the only cheap model available fails on quality. When a better one exists, setting
`OPENAI_IMAGE_DRAFT_MODEL` is the whole change.

The practical consequence: there is no cheap iteration loop. Every experiment costs a
full frame, which raises the value of the checks that cost nothing — previewing the
production prompt, confirming a rule reaches the planner, and confirming no canon
section is truncated — before spending anything.

## ADR-015 — Markdown is the seed, PostgreSQL is the queue

The concept libraries under `docs/design/` are the authored creative source, and
they stay that way. But a Markdown file cannot remember that #4 has three
attempts and a rejection, "next" meant whatever the last conversation
remembered, and a retired entry either lingered ambiguously or was deleted and
renumbered everything after it. Migration 0026 makes the library the seed of a
durable backlog — `design_concepts` through `approved_designs` — exactly as
ADR-004 split `SHOTLIST.md` from `shots`.

The decisions that shaped it:

**`external_number` is permanent identity.** #1 stays #1 forever. A retired
concept remains a row; a number missing from the source is reported and kept;
the importer refuses a non-contiguous file rather than guessing. Renumbering is
how the queue drifted before this existed.

**Conditional retirements become `held`, never `retired`.** The tee library
retires in three distinct forms: in the title (`RETIRED — TITLE (lane)`), in the
body (`Retired.`), and conditionally (`Retire … if …` with a salvage clause).
The first two are decisions the owner made. The third is one the owner has not
made, and mapping it to `retired` would fabricate a ruling the source does not
contain. Anchoring is by prefix, never substring — entry 54 describes "three
retired blokes" and is a live concept.

**`design_attempt_state` is a fresh PostgreSQL type.** Migration 0017 taught
`composed_designs` to share photography's `attempt_state`, so widening that type
for designs would silently widen the photography pipeline's vocabulary too.
`design_decision_kind` is separate from `human_decision_kind` for the same
reason, even though the values are identical today.

**The importer only writes what the source expresses.** It derives `backlog`,
`held` and `retired`; every other status belongs to the workflow. On conflict —
the source changes its mind about a concept the workflow has moved — the
database wins and the conflict is reported with both sides named, the same rule
the world importer holds for shots.

**Approval is a versioned milestone, not a state.** A concept can hold
seventeen attempts; only an `approved_designs` row, pinned by RESTRICT to its
master asset, lets anything downstream. That is what stops "we made an image"
being read as "that design is finished".

**Events ride the audit trail.** `design_decision_recorded` and
`design_approved` are `audit_events` rows. A dedicated outbox table with no
consumer is speculative; when shop sync is built, `product_links.sync_state` is
the hook, and Studio never holds a foreign key into the shop's database.

Only the tee library is imported today. The schema carries a `library`
discriminator and namespaced asset keys (`designs/{library}/{number}/…`) so the
headwear and brand-garment libraries arrive as a data change, not a schema
change.

## ADR-016 — One production spine, still and video, and the judge stops being columns

**Decided by the owner, 14 August 2026**, reconciling this branch's Phase 1 work
with the concurrent AI social production model
(`docs/stage-2/social-ai-production/POSTGRES_DATA_MODEL.md`, on main at
`8c0c9b44`). That document proposed `social_shots`, `social_generation_attempts`,
`social_assets` and `social_continuity_checks` beside the existing `shots`,
`generation_attempts`, `image_assets` and `automated_reviews`.

**The existing world production model is upgraded into a unified still + video
media-production model. AI social production must not create parallel shot,
generation, asset, automated-review or human-decision systems.** Campaign,
narrative, cast, scene, edit and performance entities extend that spine.

### Why the proposal looked reasonable and still had to change

It was not simple duplication. `shots` holds eleven columns built for
stills — sequence, title, description, `hero_product`, `camera_position`,
`lighting_source`, status — and the proposed `social_shots` held roughly
thirty-five built for video: duration, aspect and safe-crop, shot size, camera
height and angle, focal length, movement, blocking, eyeline, fore/mid/background
action, garment visibility and scale, artwork legibility, first- and last-frame
anchors, edit-in and edit-out, still-extraction potential.

That is the audit's own named gap — *"no video path"* — answered properly. The
error was answering it beside the existing spine rather than in it.
`GenerationAttempt` already carries attempt numbering, parentage, the exact
prompt, model settings, provider request id, three source-document hashes,
failure state, its assets, its automated review and its human decision. A second
copy of that would be the largest piece of duplicated machinery in the
repository.

**A still is a shot with no temporal requirement.** `shots` gains `scene_id`, a
media intent, and the video grammar above; the eleven existing columns are the
thin v1 of the larger specification, not obsolete. `generation_attempts`
generalises rather than forks: `image_model` / `image_size` / `image_quality` /
`image_format` are real columns on that table today and become model, output
spec, quality preset and format, joined by provider, modality, duration, FPS,
seed, reference asset ids, first/last-frame inputs and generation source
(manual paid UI / API / local / imported). Existing image attempts stay valid
records.

### `image_assets` becomes `media_assets`, as a real rename

Still, generated video, extracted frame, reference image, frame anchors, edit
master, audio, proxy. Fifteen Python files reference `ImageAsset` or
`image_assets`, four of them migrations. Renaming the domain abstraction while
leaving the table named for one of the media types it holds is how a database
acquires an archaeology department; the rename is a migration, done once the
call sites are known.

### The judge is reused — and its gates have to stop being columns

`AutomatedReview` separates automated judgement from human decision, and that
separation survives. But **every gate it applies is physically a column**:
`mood_score`, `australian_authenticity_score`, `product_visibility_score`,
`documentary_credibility_score`, `story_score`, `branding_compliant`,
`vehicle_compliant`, `structurally_sound`. A gate about utes is in the schema.

So "the judge reviews different dimensions according to shot type" is not a
small change in this shape. The nine new dimensions — character continuity,
wardrobe continuity, garment artwork fidelity, location continuity,
screen-direction, temporal continuity, first/last-frame compatibility, motion
defects, story compliance — would be nine more columns, video-only ones NULL on
every still, and each future gate another migration.

**The world judge adopts the shape the product judge was just given.**
`design_reviews` (migration 0027) stores `hard_gates` and `score_categories` as
arrays of `{id, label, result, evidence}` and `{id, score, maximum,
minimumRequired}`, with the rubric served from one place and rendered rather
than restated. Adding a gate is data. Gates carry the shot type they apply to,
so a still is not marked NOT_TESTED against a motion-defect gate it could never
fail — and `NOT_TESTED` keeps blocking, exactly as it does on the product side.

`HumanDecision` stays one human decision. Not one for photography and another
because the pixels move.

### What is genuinely new, and protected

Campaigns as the production root. Story versions, because story development
needs revision history rather than a mutated blob. Characters — converting the
cast from prose into something the planner can read, which is the audit's
*"no code reads `CHARACTERS.md`"*. Wardrobe and appearances. Locations. Scenes,
the missing level between a world and a shot. Edit versions, because a generated
shot and a finished cut are different things. Performance, so directing choices
eventually learn from outcomes.

### Placement follows from supersede

**The work is built in Studio**, because the spine being extended is already
there: `worlds`, `shots`, `generation_attempts`, `image_assets`,
`automated_reviews`, `human_decisions`, `canon_proposals`, `reference_frames`,
and the social publication stack. Studio is also the most database-dependent
application in the repository — thirty-two tables, twenty-seven migrations, and
ten of twenty route modules taking a live session per request.

This is not a ruling that world work lives in Studio forever. It is a refusal to
split one transactional domain across two databases for the sake of a division
that has not been executed. Admin today is the storefront: twelve tables of
products, colours, stock and page copy on its own `shirtfaced_shop` database,
with no world code in it. Moving six new tables there while nineteen dependencies
stayed behind — including `social_posts`, which the model needs a real foreign
key into — would be worse architecture than tolerating the present placement.

**If the Studio/Admin split is executed later, the whole world-production domain
moves as one bounded migration**, old tables and new together, not nineteen
tables later because six moved early.

### Consequences

- `POSTGRES_DATA_MODEL.md` is requirements, not placement, until its shot,
  attempt, asset and continuity-check layer is redrawn onto the existing spine.
  **No migration is written before that redraw.**
- Alembic revision `0027` is `design_reviews` on this branch; the first
  migration of this work is `0028`. `deploy-studio.sh` runs `alembic upgrade
  head`, so two heads fail the deploy outright rather than subtly.
- Phase 2 of `DESIGN_FLOW_PLAN.md` is already corrected to a separation inside
  Studio rather than a move of data; this ADR is the reason it stays that way.

## ADR-017 — Two provenances, one `shots` table; Markdown never learns about scenes

**Decided by the owner, 14 August 2026**, completing ADR-016's redraw. The
question it answers: once campaign and scene sit above `shots`, does
`SHOTLIST.md` have to express them?

**No. `SHOTLIST.md` is not mutated into a screenplay database.** It was built for
an authored photography queue and expresses a handful of fields; scene
hierarchy, character state, temporal continuity, edit anchors and
forty-angle campaign coverage are not among them and should not be forced into
it.

Two provenances share one table and one production spine:

| | Markdown-seeded shot | Campaign-native shot |
|---|---|---|
| origin | `SHOTLIST.md`, via `world_importer` | the campaign/story workflow |
| `campaign_id` | NULL | always set |
| `scene_id` | NULL | usually set, legitimately NULL |
| `external_id` | from the source | deterministic, e.g. `CAMP01-S03-007` |
| `source_line` | the line it was parsed from | NULL |

`World → Shot` stays valid for the authored queue.
`World → Campaign → StoryVersion → Scene → Shot` is the campaign path.

### Why this composes safely, and it is not obvious

**The world importer never prunes.** It iterates the parsed shots and upserts on
`(world_id, external_id)`; nothing in it deletes or disables a row that the
Markdown no longer mentions. So a re-import of `SHOTLIST.md` cannot remove,
disable or overwrite a campaign-native shot sitting in the same table. Without
that property this design would be a data-loss bug waiting for the first
re-import, so it is recorded here as load-bearing rather than incidental — if
pruning is ever added, it must be scoped to `source = 'markdown_import'`.

The importer already refuses to overwrite operational state the workflow owns
and reports disagreement instead of resolving it silently. Campaign-native rows
extend that same rule to their whole existence.

### `campaign_id` sits directly on `shots`, and that redundancy is deliberate

Not every campaign shot needs a narrative scene: a product insert, an
environmental plate, a CCTV cutaway, a title-card source, a transition, a
generic aftermath still. Inventing a scene to satisfy a hierarchy is database
theatre. So `campaign_id` is directly present and `scene_id` is nullable
alongside it.

The agreement rule — *if a shot has a scene, that scene's campaign is the shot's
campaign* — should be **declarative rather than a trigger or application code**:

- `scenes` carries `UNIQUE (id, campaign_id)` (redundant, legal, and the price
  of the constraint);
- `shots` carries `FOREIGN KEY (scene_id, campaign_id) REFERENCES scenes (id, campaign_id)`.

A composite foreign key defaults to `MATCH SIMPLE`, which **skips the check
entirely when any column is NULL** — exactly right for `scene_id IS NULL`, and
exactly wrong for the reverse. So it needs one guard beside it:
`CHECK (scene_id IS NULL OR campaign_id IS NOT NULL)`. Without that, a shot can
carry a scene and no campaign and nothing complains.

### `external_id` stays non-nullable

Stable human-readable identifiers earn their place in prompts, review, logs and
regeneration; `CAMP01-S03-007` is worth more in a failure report than a UUID.
The database UUID remains identity.

One consequence to design to rather than discover: `shots` already carries
`UniqueConstraint("world_id", "external_id")`. Campaign-native ids share that
namespace with Markdown ids inside a world, and a world can hold several
campaigns — so the campaign discriminator has to be *in* the identifier. The
`CAMP01-` prefix is not a naming preference, it is what satisfies an existing
constraint.

### `source` is provenance, and it is not nullable

`markdown_import` / `campaign_native` / `manual`, with every existing row
backfilled to `markdown_import` — which is what they all are. A nullable
provenance column would make "we do not know where this came from" a
representable state on the one axis this ADR exists to keep clear.

### Consequence

The model to redraw is:

`World → Campaign → StoryVersion → Scene → Shot → GenerationAttempt →
MediaAsset → Review → HumanDecision → EditVersion → Social publication →
Performance`

with `World → Shot` deliberately retained. No migration until that redraw is
complete and reconciled with ADR-016.


## ADR-018 - The constitution's five collection roles, not `domain.ts`'s six

Phase 4 needed a `collection_role` enum and found two lists.

`SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md` section 4 names five: **Anchor,
Core, Expression, Hero, Collaboration**. The deleted
`admin/src/design-system/domain.ts` carried six: `core`, `staple`, `expression`,
`hero`, `capsule`, `collaboration` -- no `anchor`, plus `staple` and `capsule`
which section 4 does not define.

**The constitution wins.** It is the governing document, its five each carry a
definition a review can be held against, and `staple` and `capsule` carry none.
A role nobody can point to in the constitution is a role nobody can defend in a
review, which is the only place these are used.

Recorded rather than silently reconciled, because the same divergence produced
ADR-016's larger finding: `workflow.ts`'s thirteen hard gates are the
constitution's section 16 twelve plus rights, and are *not*
`DESIGN_REVIEW_SCORECARD.md`'s HF-01..HF-12 -- that document's *HF-10 Collection
Redundancy* still has no gate id. Two documents disagreeing about a vocabulary
is a pattern here rather than an accident, and each instance gets written down
when it is met.

Nothing is migrated: no row ever held a collection role before migration 0028.

## ADR-019 — City Beach is a corpus of images, not yet a corpus of numbers

**15 August 2026.** The owner named City Beach as a source of modern design at
volume, to sit beside the vintage evidence rather than merge into it.

**It is collected as its own tradition, `current-retail`.** Not folded into
`au-streetwear` with the other Australian shops. `advise()` filters on tradition
before it takes a median, and the whole reason that parameter exists is that
averaging two registers produces a design belonging to neither — current retail
and 1990s archive stock are exactly that distance apart.

**It needed its own collector.** `collect_design_corpus.py` reads Shopify's
`/products.json`. City Beach runs Salesforce Commerce Cloud and has no such
endpoint, so adding a row to `BRANDS` would have produced a skip, not a corpus.
`collect_current_retail.py` reads the SFCC storefront grid, whose product tiles
carry the same data as structured JSON attributes.

**It is a retailer, and `corpus_tiers.py` excludes retailers.** Deliberately not
excluded here, and the file says so at the exclusion list so nobody reverses it.
Tier 3's objection is that a retailer's stock gets filed under the shop's name
and poisons brand-level numbers. Both halves are answered by construction: every
product records the label that actually made it in `retail_brand`, and the
tradition is one nothing else writes, so no label's medians can move. What a
shop can hold evidence about is what is on the shelf now, which is the question
being asked.

**The measurement does not work on these photographs, and this is the finding
that matters.** `mine_design_patterns.py`'s `_analyse` was written for flat-lays
and torso crops. City Beach shoots every product worn and full-body. Painting
the print mask back over the image shows three failures: fold shadows measure as
ink (a plain tee scored 31% coverage), the fixed torso box lands under chest
prints and over arms, hair and background, and a light print on a dark garment
trips the off-garment cut-off and measures as no print at all (a full-front
Formula 1 graphic scored 0.3%).

Only the first is a threshold problem. Rescaling each pixel to the garment's own
luminance before measuring collapses drape to nothing — verified — because a
fold is the garment colour times a scalar while ink has its own hue. The other
two need the garment located in the frame and the print located within it,
rather than both assumed by a fixed crop. That is a piece of work, not an edit,
and it is not done.

**So the engine was left alone.** Changing a shared measurement to suit one
source, when two of its three failures would remain, would buy a number that
looks better and is still wrong. `_analyse` has no test coverage at all, which
is why none of this surfaced earlier and is the first thing to fix if anyone
picks this up.

Until then the corpus is real reference imagery to look at — 58 designs across
26 labels on the first pass — and not a source of medians. Nothing is wired in:
`var/` is gitignored, and `joined.json` exists only when somebody runs the
joiner.

### ADR-019 addendum — the USA half, and what flat-lays proved

**15 August 2026, same day.** The owner asked for City Beach's USA equivalents.

**Eleven shops, one tradition.** CCS, NJ Skateshop, KCDC, Black Sheep and 35th
North on the skate side; Jack's Surfboards, Huntington Surf & Sport, Val Surf,
Cleanline Surf and Hansen Surf on the surf side; DTLR on the street side. All
tagged `current-retail`, the same tradition as City Beach, because it is the same
question and very nearly the same shelf — Vans, Thrasher, Champion, adidas,
Billabong and Quiksilver appear in both markets. No second tradition was
invented: the shop is the directory name, so an Australian-only or American-only
cut stays one filter away, and a tradition that splits on nationality would
imply a design difference not in evidence.

All eleven are Shopify, so they need no new collector — they are rows in
`BRANDS`. Shopify's `vendor` field carries the label that actually made each
design, and `collect_design_corpus.py` now writes it as `retail_brand`, which is
what makes the tier 3 exemption honest for these the way it already was for City
Beach. CCS lists 36 vendors on a single page; NJ Skateshop, 45.

**Tillys and PacSun are absent, and they are the two closest equivalents by
size.** Tillys answers 403; PacSun serves a PerimeterX captcha. Both are
refusing automated access and the refusal is respected rather than worked
around. A known gap, recorded, not a silent one — the same treatment this file
already gives the majors that run custom platforms.

**A bug that made the documented default unusable.** `collect_brand`'s
round-robin had two conditions disagreeing about what "no cap" meant: the outer
read `PRODUCTS_PER_BRAND = 0` as unlimited, the inner as `len(wanted) < 0`,
which is never true. At the default the loop drained no bucket and spun forever
collecting nothing. Reproduced before changing — cap 3 terminates with 3, cap 0
spins — which also explains how the comment in that file can say the cap was
lifted while 165 of 187 brands still sit at exactly 18 products on disk. The
lift was never runnable.

**And the finding that sharpens ADR-019.** These shops photograph flat-lay on
white, not worn. Running `_analyse` over them removes the first failure
completely: no drape, and a plain hoodie correctly reads as no print. What
remains is the second failure, and it is now confirmed on photography as
different from City Beach's as it gets — **the fixed torso box sits below a
chest print**. A CCS tee with a blue skateboard graphic across the chest and a
Polar raglan with a small chest mark both measured zero, because the box starts
35% down the frame and the print sits at 28%.

So the box is not wrong for City Beach's framing in particular. It is wrong.
Moving it cannot fix both, because a flat-laid garment fills the frame and a
worn one does not — which is the argument for finding the garment and then the
print, rather than assuming where both are, and the reason the engine is still
left alone.

### ADR-019 resolved — the garment is found, not assumed

**15 August 2026.** The measurement is fixed. `_analyse` no longer crops a fixed
rectangle and calls it the torso; it locates the garment and measures what the
garment encloses.

**How.** The backdrop comes from the four corners, not the border ring, which on
a worn shot runs through the model. The subject is what differs from the
backdrop — raw distance, because levelling a black tee to a white ground's
brightness makes the two look alike, which cost one attempt an 8% garment. The
fabric colour is read from a ring just inside the silhouette rather than from
the middle, because a print covering a quarter of the garment *is* the median of
a middle band, after which the fabric measures as ink and the ink as fabric. The
garment is what matches that colour once brightness is divided out, so a fold
stays fabric. And the print is what the garment encloses: filling holes finds
it, a white print inside a black tee is a hole like any other, and an arm across
the chest runs out to the frame edge and is never filled.

All three original failures now have a test named for them, in
`tests/unit/test_design_mining.py`. There were none before, which is why they
lived so long.

**What it refuses, and why that is the feature.** 245 of 643 frames are refused,
233 of them because most of what stands out from the backdrop is not the
garment — a body wearing it. Sampled and looked at: seven of eight were models,
the eighth a white tee on a white backdrop, which is a real limit and has its
own test. City Beach's 58 are skipped at source. What is left is 398 measured,
388 with a detectable print, and a report that states every refusal by reason
rather than averaging them in.

**Two things learned the hard way, recorded so they are not re-tried.**

A brightness test for prints with no hue of their own — black on grey — was
abandoned once because without segmentation it caught the backdrop and the model
and scored a plain worn tee at 15%. Inside a located garment it is safe and
necessary, because chroma levelling otherwise rescales a black print into a grey
tee and loses it entirely.

Filtering print regions by size is the obvious way to stop seams, buttons and a
straw hat's weave inflating coverage. It also removes 39% of a lettering print:
"KCDC BROOKLYN" is twelve separate letter-shaped regions, each individually
small. For a brand whose graphics are mostly words that is the wrong trade, so
the seam noise stays.

**And a correction to this ADR's own addendum.** It said the American shops
photograph flat-lay. That is only mostly true — the surf and street shops put
about a third of their range on models, which is why the worn/flat decision
moved from a per-source declaration to a per-image check. `brand.json` still
records `photography`, now as `mixed` for the retailers, but only `worn` skips a
source outright; everything else is decided per frame.
