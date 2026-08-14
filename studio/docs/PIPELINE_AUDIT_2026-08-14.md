# Pipeline audit — 14 August 2026

**Scope:** the two product/design and world/marketing pipelines, end to end.
**Method:** routes enumerated from a running app instance, services and call
sites read, endpoints exercised against production, the product sequence
compared against `SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md`.

**Relationship to `docs/shirtfaced-audit.md`:** that audit is dated 10 August
and predates the vintage subsystem entirely. It is a guideline for direction.
Where it describes current state it is superseded here, and one of its factual
claims is now wrong — see *Corrections* below.

---

## The organising fact

There are **two pipelines**, and they belong in two places.

| | Pipeline | Home |
|---|---|---|
| **Product** | evidence → concept → design → approved version → print | `studio.shirtfaced.wtf` |
| **World** | canon → shot → photograph → decision → social → customer | `admin.shirtfaced.wtf` |

They meet exactly once: a finished product goes to the printer and the
customer, or into the world and reaches the customer through socials and the
site. One-directional, at the end.

**Four of Studio's ten top-level destinations are world-side.** Prompts, Social,
Email and a Dashboard built on world state are all in the product tool. That is
not a navigation preference; it is the two pipelines interleaved in one
interface, and it is the first thing a person hits.

---

## Product pipeline — the constitution is not implemented

The constitution defines a ten-step governing sequence. The built pipeline
answers six of the ten.

| Constitution | State |
|---|---|
| 1. define the product | **absent** |
| 2. define its role in the range | **absent** — Anchor / Core / Expression / Hero / Collaboration exist as prose |
| 3. select the garment architecture | **absent** |
| 4. select the graphic architecture | `design_advisor` answers this from 12,151 measured images, and **nothing calls it** |
| 5. construct the composition | `/api/compose/*`, built |
| 6. integrate typography | **absent** — no step, no service, no field |
| 7. validate recognition | measurement only |
| 8. validate production | measurement only |
| 9. review against the collection | **absent** |
| 10. approve, revise or reject | built |

Steps 1–4 decide *what a product is* before any artwork exists, and none of
them are represented in software. The research bench produces a graphic idea
and jumps straight to artwork, which is why output arrives as competent generic
work with no collection role and no declared archetype.

### The blocking gap

**No human judgement layer exists.** `design_extraction` measures one category
honestly and leaves nine `NOT_TESTED` — which correctly blocks release. There is
no form for a person to answer those nine, so `score_design()` can never receive
a complete input.

**No design can pass the scorecard. Not one, ever, by construction.**

That is the audit's Hot List #1, unmet since 7 August, and this is why.

### Nothing carries identity between steps

Three separate defects with one cause:

- `POST /api/concepts/attempts/{id}/assets` exists and **no screen calls it** —
  artwork cannot be attached to an attempt.
- `/api/design/score` takes an uploaded file and **references no attempt** — a
  measurement attaches to nothing and persists nowhere.
- `printing.py` and `print_service.py` contain **no reference to
  `approved_designs`** — the approved version is not Print's input.

Each step works alone. None of them hands anything to the next.

### The backlog cannot be reached from research

`Send to design pipeline` binds a research concept to a design concept picked
from a dropdown. The only way a concept *enters* that backlog is
`concept_importer` reading `TSHIRT_CONCEPT_LIBRARY.md`. Ten researched concepts
cannot become ten backlog concepts.

---

## World pipeline — more complete, and in the wrong building

Twenty-two steps, twenty-one built. It has the thing product lacks:

`review_service.py` is a real AI judge with ten canon-derived gates that
**never approves or rejects itself** and always lands on `AWAITING_DECISION`.
Canon proposals feed learning back into `WORLD.md`. There is a publish queue
with hold, cancel, schedule and run-due.

That asymmetry is the clearest finding in this audit: **the world pipeline was
built to a standard the product pipeline never received.**

### Gaps

- **No code reads `CHARACTERS.md`.** The cast is prose; `CONTINUITY.md` tracks
  hero products and camera positions, not people, so the planner cannot know
  who is in a shot.
- **No video path.** `print_design()` takes one image and one hand-dragged quad
  and cannot extend to frames.
- **No line to the customer.** Storefront and studio share a repository and
  nothing else.

---

## Corrections to the 10 August audit

**§2.1 and Area 2 describe `design_scoring.py` as tested code behind a live
endpoint.** That file and `app/domain/design_review.py` were deleted per §8 of
`DESIGN_ENGINE_ADAPTATION.md`, which found they reimplemented
`admin/src/design-system/workflow.ts` in Python, in the wrong app, without the
workflow. `POST /api/design/score` still exists and now measures only, deferring
judgement to `workflow.ts`.

The consequence matters for the two-pipeline split: **the product judgement
engine lives in admin, and by this audit's own division admin is the world
tool.** Either the scorecard moves to studio or the division needs restating.

**The vintage subsystem does not appear in that audit at all.** It postdates it:
five collectors, 3,639 pieces, 11,544 images, a research bench, and a manual
path that keeps generation off metered APIs.

---

## What has changed since 10 August

- Vintage evidence corpus and collectors, from nothing to 3,639 pieces.
- A research loop that produces ten concepts per run without API spend.
- The Python review reimplementation deleted; one engine, in admin.
- Evidence and Research ported into the React shell; two embedded HTML pages
  retired.
- An end-to-end smoke check that runs on every deploy and fails it.

Hot List #5 — *build a design generator* — is **partially met and unrecognised**.
The research bench is a concept generator. The audit says System B only ever
evaluates work that already exists; that is no longer true.

---

## The constraint that reframes everything

Paid subscriptions to OpenAI, Gemini and Anthropic already exist. An API key
bills separately. Generation must therefore happen in a paid interface and the
result be brought back.

This is not a limitation to route around — it decides the shape. The app owns
the brief, the record, the measurement, the judgement and the decision. It does
not own the pixels. Every gap above should be read with that settled.

It also means Hot List #1's wording — a design *"generated by this app"* —
cannot be met literally and needs restating as: carried through this app's
pipeline and persisted with a decision.

---

## Verdict

| Pipeline | Verdict |
|---|---|
| **Product** | Ends cannot meet. Evidence collection is strong and printing works; between concept and approved version, six of the constitution's ten steps are absent or unwired, and no design can pass the scorecard because nothing can answer its nine human questions. |
| **World** | Nearly complete and correctly built, with a genuine judgement layer. Missing a cast the code can read, any video path, and any line to the customer. Living in the wrong tool. |

**The single highest-value item** is the nine-category judgement form. It is
small, it unblocks Hot List #1, and without it every other product improvement
compounds into a pipeline that still cannot finish a design.

**The single largest structural item** is separating the two pipelines into
their two homes, because every navigation and ownership question downstream
depends on it.
