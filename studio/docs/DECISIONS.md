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
