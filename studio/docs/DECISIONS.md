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
