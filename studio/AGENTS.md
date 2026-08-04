# AGENTS.md — Codex Start-Up Instructions

## Mission

Build **Shirtfaced Studio**, a local-first creative production application that runs the Shirtfaced World workflow end to end.

The primary user command is:

> Continue Shirtfaced World 1.

That command must cause the application to load current state, select the next valid shot, generate its production prompt, create one image, review the image, and present the result for explicit human approval.

The system must never silently approve an image or permanently alter creative canon without a recorded decision.

## Non-negotiable rules

1. Read all build documents before changing code.
2. Do not invent requirements that contradict the build documents.
3. Prefer the simplest implementation that fully satisfies the specification.
4. Keep OpenAI model names configurable through environment variables.
5. Isolate all OpenAI API calls behind adapter interfaces.
6. Keep image generation and image review as separate operations.
7. Never let generated model text directly overwrite canonical files.
8. Validate every proposed Markdown update before applying it.
9. Preserve all prior versions through Git and database audit records.
10. Require human approval for:
    - accepting a generated image;
    - rejecting a generated image;
    - promoting an image to reference status;
    - adding or changing permanent world canon.
11. Tests must not make live OpenAI API calls.
12. Do not commit API keys, generated secrets, local databases or paid API outputs.
13. Use Australian English in user-facing copy.
14. The application is for one owner initially. Do not build enterprise tenancy.
15. Build as a single deployable application for the existing Oracle Cloud environment.
16. Use the existing PostgreSQL database as production state storage.
17. Keep local development simple, but do not design production around SQLite.

## Product boundary

Version 1 must include:

- one local user;
- one world initially, while supporting additional worlds structurally;
- world, continuity and shotlist loading;
- deterministic next-shot selection;
- production prompt generation;
- OpenAI image generation;
- image review using an image-capable OpenAI model;
- explicit approval, rejection and variation controls;
- durable image and metadata storage;
- continuity and shotlist updates;
- proposed canon-rule updates requiring separate approval;
- cost and token usage capture where returned by the API;
- an audit trail;
- a practical web interface suitable for deployment on the existing Oracle Cloud host;
- PostgreSQL-backed durable operational state;
- environment-driven asset storage, initially local persistent storage with an adapter boundary for Oracle Object Storage.

Version 1 must not include:

- public accounts;
- payments;
- ecommerce;
- garment mockups;
- automatic publishing;
- social media integration;
- autonomous infinite generation;
- background generation without an explicit user action;
- arbitrary multi-agent frameworks;
- vector databases;
- Kubernetes;
- microservices.

## Technical direction

Use:

- Python 3.12+
- FastAPI
- PostgreSQL as the production database
- SQLAlchemy 2.x with psycopg 3
- Alembic
- Pydantic 2
- Jinja2 with HTMX, or another comparably simple server-rendered interface
- official OpenAI Python SDK
- pytest
- Ruff
- mypy
- Pillow only where local image metadata or thumbnails require it

Use a single deployable application.

Do not introduce React unless a requirement genuinely cannot be met cleanly with server-rendered HTML and HTMX.

## Required implementation behaviour

### Continue World

When the user invokes `Continue Shirtfaced World 1`:

1. Resolve World 1.
2. Refuse if another generation for that world is already active.
3. Load and validate the world files.
4. Read recent approved and rejected shots.
5. Determine the next eligible planned shot using deterministic rules.
6. Build a structured planning request.
7. Ask the text model for a production prompt and structured rationale.
8. Validate the response.
9. Persist a pending generation record.
10. Call the image generation adapter exactly once.
11. Save the original output locally.
12. Create a review request containing the image and relevant canon.
13. Ask the review model for a structured verdict.
14. Persist the review.
15. Present the image, prompt, rationale and review to the user.
16. Do not change shot status to approved or rejected until the user acts.

### Human decision

On approval:

- mark the generation approved;
- mark the shot approved;
- append a validated continuity entry;
- update rotation counters;
- optionally mark the image as a reference;
- create a Git commit only after all file changes succeed.

On rejection:

- mark the generation rejected;
- record the user's reason;
- keep the shot planned unless explicitly abandoned;
- update continuity with the rejected drift;
- do not alter permanent canon automatically.

On variation:

- retain the same shot identity;
- create a new generation attempt;
- carry forward user instructions;
- avoid treating the prior image as approved.

### Canon proposal

The review model may propose a new permanent rule.

It must be stored as a proposal.

The user must separately approve it before `WORLD.md` changes.

## Work method for Codex

Implement one vertical slice at a time.

For every slice:

1. inspect existing code;
2. state the intended change;
3. implement;
4. add or update tests;
5. run focused tests;
6. run the full suite;
7. report exact results;
8. update documentation where behaviour changed.

Do not claim completion with failing tests.

## Completion definition

The first release is complete only when a user can:

1. start the app;
2. open World 1;
3. click **Continue World**;
4. receive one generated image and structured review;
5. approve, reject or request a variation;
6. restart the app;
7. see all state preserved;
8. inspect the canon, continuity, shotlist and generation history;
9. run the full test suite without a live API key.
