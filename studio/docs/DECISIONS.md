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
