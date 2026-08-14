# Session handover — 14 August 2026

> **Closed 15 August 2026. The world session is finished.** What it landed, what
> it did not, and what reverts to unowned is recorded at the end under
> *Handback*. The ownership split below is kept because it is the record of how
> the two sessions ran, not because it is still live.

Two implementation sessions are working this repository at once: this one on the
**product design pipeline**, and a concurrent one on **AI social/world
production**. `WORKING_AGREEMENT.md` divides creative direction from
implementation; it does not divide two implementers. This does.

Written from the product side. Where it proposes rather than records, it says so.

---

## 1. What is live, verified

`main` is at `d570116`. The deploy is green and migration **0027** is applied to
production.

Phase 1 of `studio/docs/DESIGN_FLOW_PLAN.md` shipped: a research concept becomes
a numbered design concept, an attempt takes artwork through a drop zone,
measures it, carries thirteen hard gates and nine weighted categories, and
`score_design()` gates the approval before it is recorded. Print renders the
approved version into a defined garment zone.

Both smoke chains pass against production:

```
  ok  the scorecard is reachable and complete   13 gates and 9 categories in 3 groups
  ok  the backlog lists every library           260 concepts across ['tshirt'] libraries
  ok  garments declare printable zones          22 garments, 89 zones
  ok  an attempt's review evaluates             0/100, 2 blockers, next action stated
  ok  an approved version renders into its zone no approved version exists yet to print
```

**Three defects were found by running rather than reasoning**, and one of them
was not ours: garments resolved to a path that does not exist on the box, so
`design_composition` and `design_range` had been finding **zero garments in
production** for as long as they have been deployed. `22 garments, 89 zones` was
`0, 0` this morning. Nothing said so until a check asked.

Take that as the standard rather than as a war story: a green deploy, a passing
type check and a rendering screen are all compatible with a feature that does
nothing.

## 2. What is decided

**ADR-016** — one production spine, still and video, and the judge stops being
columns. `social_shots`, `social_generation_attempts`, `social_assets` and
`social_continuity_checks` do not become tables; `shots`, `generation_attempts`,
`image_assets` and `automated_reviews` are extended instead. Built in Studio.

**ADR-017** — two provenances share one `shots` table. `SHOTLIST.md` is not
mutated into a screenplay database. Markdown shots keep `campaign_id` and
`scene_id` NULL; campaign shots are database-native.

Both are in `studio/docs/DECISIONS.md` on `main`. They are the owner's
decisions, not this session's proposals.

## 3. Ownership — proposed, and needing agreement

### The product pipeline (this session)

| | |
|---|---|
| tables | `design_concepts`, `design_attempts`, `design_assets`, `design_decisions`, `design_reviews`, `approved_designs`, `design_attempt_elements`, `product_links` |
| services | `design_scoring.py`, `design_extraction.py`, `approved_print.py`, `design_pipeline.py`, `next_action.py`, `concept_importer.py` |
| domain | `domain/design_review.py` |
| routes | `routes/concepts.py`, `routes/design.py` |
| web | `AttemptPanel.tsx`, `DesignsBench.tsx` |
| migrations | `0027` (done) |
| smoke | `scripts/smoke_design_chain.py` |

### The world / campaign pipeline (concurrent session)

| | |
|---|---|
| new tables | campaigns, story versions, characters, wardrobe/appearances, locations, scenes, edit versions, performance |
| extended tables | `shots`, `generation_attempts`, `image_assets` → `media_assets`, `automated_reviews` |
| services | `review_service.py`, `canon_service.py`, `generation_orchestrator.py`, `prompt_planner.py`, `world_importer.py`, `social_delivery.py`, `decision_service.py` |
| routes | `routes/social.py`, `routes/api.py` (world parts), `routes/printing.py` |
| web | `SocialBench.tsx`, `PromptWorkbench.tsx`, `WorldPage.tsx`, `PrintBench.tsx` |
| migrations | `0028` onward |
| smoke | `scripts/smoke_vintage.py`, plus equivalent coverage for the campaign chain |

## 4. Where the boundary is not clean — five things, now allocated

**Allocated by the world session, 14 August 2026, and accepted.** The table
below records the outcome; the discussion that follows it is kept because the
reasoning is the useful part.

| Surface | Decision | Owner |
|---|---|---|
| 4.1 judge rewrite | **Two review tables, one structural contract.** `design_reviews` stays product-specific, `automated_reviews` stays world-specific. Same `hard_gates[]` / `score_categories[]` / rubric-provenance / verdict / evidence shape; independently versioned rubrics. Do not merge. | World |
| 4.2 `media_assets` rename | Real rename including ORM, domain and call sites, one coordinated commit, warning before touching product-touched files | World |
| 4.3 navigation separation | Correct, but waits until the campaign UI shape is known. World will not restructure `App.tsx` | Product |
| 4.4 `next_action.py` | One shared mechanism, pipeline-specific rules. No competing sentence engine | Product |
| 4.5 measurement | **Do not reuse `design_extraction` wholesale.** World media evidence gets its own evaluator feeding the same review contract shape. Extract shared primitives only when a real duplicate appears | World |

The distinction that carries 4.1 and 4.5: **shared contract, not shared
implementation.** A design review asks whether a printable product design is
acceptable; a world review asks whether generated media satisfies canon,
continuity and production. Character identity drift, first/last-frame
compatibility, motion defects and screen direction are not extensions of
measuring graphic recognition. Combining either pair because both contain gates
would produce a polymorphic junk drawer.

**Consequence for the product session:** Phase 2 of `DESIGN_FLOW_PLAN.md` *is*
the navigation separation, so it is blocked by 4.3. It is split: **Phase 2a**
groups the existing destinations by pipeline inside `App.tsx`, which depends on
nothing the world session is building; **Phase 2b** relocates world screens and
waits on their UI shape.

### The original five, as raised

These are the collisions. None is settled, and each needs an owner before code
is written against it.

**4.1 The judge rewrite.** ADR-016 says `automated_reviews` adopts the shape
`design_reviews` was given: gates as data carrying their own ids and
applicability, not as columns. That is the product session's pattern applied to
the world session's table. Whoever writes it, the open question underneath is
sharper: **one review table for both pipelines, or two tables sharing one
shape?** A product design review and a photograph review answer different
rubrics against different subjects; they currently share only an idea. Merging
them is tempting and probably wrong. Two tables and one contract module is the
proposal, and it is only a proposal.

**4.2 The `media_assets` rename.** Fifteen Python files, four of them
migrations, including `print_service.py` — which the product side changed today
for the zone-print path. Whoever does it should do it in one commit, and the
other session should have nothing in flight in those files when it lands.

**4.3 Phase 2's navigation separation.** The plan separates product and world
destinations inside Studio. That edits `App.tsx` and touches `SocialBench` and
`PromptWorkbench`, which are world-side files. It cannot be done unilaterally
while the campaign UI is being built in them.

**4.4 `next_action.py`.** The product side computes one sentence per state, from
rows that already exist, with one copy of each phrasing. If the world pipeline
wants the same — and Phase 3's `ProductionItem` assumes something like it — that
is either a shared module or a second implementation. It should be decided
before the second one exists.

**4.5 Measurement reuse.** `design_extraction` measures an image into gate
results and category scores. Continuity, garment-artwork fidelity and
first/last-frame compatibility are measurement problems of the same family.
Whether the world judge reuses that service or grows its own is unanswered.

## 5. Protocol while both sessions run

**Alembic slots are claimed by pushing.** `deploy-studio.sh` runs `alembic
upgrade head`, so two heads fail the deploy outright rather than subtly. Before
writing a migration, `ls studio/app/db/migrations/versions/` against current
`main`. `0027` is `design_reviews`, applied to production. The next free slot is
`0028`.

**The full gate before every commit**, both sides:

```
cd studio && ruff check . && ruff format --check . && mypy --platform linux app && pytest
cd web && npx eslint . && npx prettier --check . && npx tsc --noEmit && npx vitest run && npm run build
```

`mypy` needs `--platform linux` because `os.killpg` does not exist on win32.

**`pytest`, not `pytest tests/unit`** — corrected 14 August, the hard way. The
working agreement said `tests/unit`, and `studio-ci.yml` runs bare `pytest`
against a real PostgreSQL container. Phase 4's brief gate broke eleven
integration tests that the documented gate does not run, and CI caught it one
step after it should have been caught.

Integration tests skip themselves without `TEST_DATABASE_URL`, so running the
whole suite locally is free when there is no database and correct when there
is. Point it at one:

```
TEST_DATABASE_URL=postgresql+psycopg://user@127.0.0.1:5432/shirtfaced_test pytest
```

The database must be on **UTC** — `test_timestamps_are_populated_and_utc`
asserts it, and a throwaway instance inherits the host's timezone.

**Exercise it before claiming it works.** Server checks have passed while a
React screen was throwing, and a type check has passed while a path resolved to
a directory that does not exist on the box.

**Add smoke coverage for anything new.** Both smoke scripts run as the last
deploy steps and fail the deploy. Assert concrete facts — counts, real bytes,
named zones — not that a response was received. A check that compares a response
to itself passes while the endpoint is unreachable.

**Do not edit the other session's files without saying so first.**

## 6. What this session needs from the other

1. Confirmation of the ownership split in §3, or a counter-proposal.
2. An owner for each of the five items in §4 — particularly 4.1, because the
   judge rewrite is the largest shared surface and both pipelines regress if it
   is done twice.
3. Warning before `media_assets` lands, so nothing is in flight in
   `print_service.py`.

## 7. What the other session should know it is not blocked on

- Migration slot `0028` is free and uncontested.
- ADR-016 and ADR-017 are committed; the data-model redraw can proceed against
  them without waiting on the product side.
- Phase 2 is not started and will not start without agreement on 4.3.
- Nothing in the product pipeline reads or writes any world table.


---

## Handback — 15 August 2026

The world session is done. `origin/main` carries its work and the two pipelines
coexist: single alembic head, 1,242 tests against a real PostgreSQL, all six
live design-chain smoke links intact with `0029` deployed.

### What it landed

**`0029_campaign_production_foundation`**, merged as PR #3, taking the slot the
protocol reserved for it. `campaigns`, `story_versions`, `characters` and the
rest, with **`shots` extended rather than a parallel `social_shots`** — ADR-016
and ADR-017 honoured exactly. `campaign_models.py` holds the ORM.

That is the hard part of the redraw, and it is right.

### What it did not

Three of the five allocated surfaces are untouched, and one promise is unkept.
None of this is a criticism of a session that shipped the foundation; it is what
the next person needs to know rather than discover.

| | State |
|---|---|
| **4.1 judge rewrite** | **Not done.** `automated_reviews` is still column-per-gate — `mood_score`, `vehicle_compliant`, `structurally_sound`. ADR-016 has it adopting `design_reviews`' data shape, and it has not. Every video dimension is still a schema migration away. |
| **4.2 `media_assets` rename** | **Not done.** `image_assets` / `ImageAsset` throughout; no file mentions `media_assets`. |
| **4.5 world measurement** | **Not started.** No evaluator, which follows from 4.1 not having a contract to feed. |
| **campaign chain smoke** | **Not written.** Promised explicitly — *"'endpoint returned 200' is officially about as reassuring as a dashboard warning light painted green"* — and the two smoke scripts are still `smoke_vintage` and `smoke_design_chain`. |

### The finding that matters

**The campaign foundation is deployed and unreachable.** Migration `0029` is
applied to production and `campaign_models.py` defines the tables, but **no
route and no service reads any of them**, and nothing in the web client mentions
a campaign.

That is the audit's own oldest finding, repeated in a new place: `design_advisor`
answered constitution steps 3 and 4 from a corpus and *nothing called it* for
weeks. A table nobody can reach is in exactly that condition — correct, tested,
migrated, and doing nothing.

It also cannot be smoke-tested yet, which is why the promised campaign chain
check does not exist: there is no chain to walk. The check becomes possible the
moment the first route does.

### What this means for ownership

Everything in §3's world column reverts to **unowned**. Nothing in the product
pipeline reads or writes a campaign table, so nothing is blocked by leaving them
alone — but nothing else will pick them up either.

If the world pipeline is resumed, the order that costs least is: routes over the
new tables first (so there is something to smoke), then 4.1, then 4.2, then 4.5.
4.1 before 4.2 because the judge's shape decides what a media asset has to carry.

### Phase 2b

Closed as superseded rather than done — see `studio/docs/DESIGN_FLOW_PLAN.md`.
It was *relocate the world screens*, and the Phase 2 correction removed the place
to relocate them to: Admin is the storefront, and world data lives in Studio.
Phase 2a delivered Phase 2's actual exit test. No campaign UI was built, so the
collision §4.3 was protecting against never arrived.
