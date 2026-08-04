# Implementation Plan

## Phase 0 — Repository foundation

- initialise Python project;
- configure Ruff, mypy and pytest;
- add FastAPI app;
- add settings;
- connect to PostgreSQL with psycopg 3;
- add SQLAlchemy pooling and Alembic;
- add `.env.example`;
- add baseline CI;
- add health endpoint.

Exit:

- app starts against PostgreSQL;
- initial migration applies cleanly;
- lint passes;
- type check passes;
- tests pass.

## Phase 1 — World ingestion

- copy World 1 documents;
- implement Markdown loaders;
- implement validators;
- import shots into SQLite;
- calculate hashes;
- create read-only world page.

Exit:

- current world files load;
- invalid fixtures fail clearly;
- shotlist visible in UI.

## Phase 2 — Selection and planning

- implement deterministic selector;
- implement rotation state;
- define PromptPlan schema;
- add fake planning adapter;
- add OpenAI planning adapter;
- render planned prompt before generation in development mode.

Exit:

- next shot selection is deterministic and tested;
- structured prompt plan validates.

## Phase 3 — Image generation

- define generation adapter;
- persist attempt state;
- call image API;
- save original and thumbnail;
- show generated image;
- implement bounded retry and failures.

Exit:

- one click creates exactly one durable image.

## Phase 4 — Automated review

- define ImageReview schema;
- review actual stored image;
- display verdict and scores;
- create pending canon proposal where applicable.

Exit:

- generated image receives a validated review.

## Phase 5 — Human decisions

- approval;
- rejection;
- variation;
- reference promotion;
- duplicate-decision protection;
- continuity and shotlist updates;
- audit events.

Exit:

- full loop persists through restart.

## Phase 6 — Canon proposals

- proposal queue;
- exact diff preview;
- approval and rejection;
- safe Markdown update;
- Git commit;
- conflict handling.

Exit:

- canon changes cannot occur without explicit approval.

## Phase 7 — Cost, history and polish

- usage records;
- estimated cost display;
- history filters;
- retry review;
- export state;
- accessibility;
- error polish.

Exit:

- practical daily-use local application.

## Phase 8 — Optional Custom GPT interface

Only after the app is stable:

- expose authenticated HTTPS API;
- publish OpenAPI schema;
- define Custom GPT Action;
- keep application as source of truth.

This phase is optional and must not delay Version 1.
