# Architecture

## Shape

A modular monolith.

```text
Browser
  |
FastAPI + server-rendered UI
  |
Application services
  |--- World service
  |--- Shot selector
  |--- Prompt planner
  |--- Generation orchestrator
  |--- Continuity reviewer
  |--- Decision service
  |--- Canon proposal service
  |
Adapters
  |--- OpenAI text
  |--- OpenAI image generation
  |--- OpenAI image review
  |--- Markdown repository
  |--- Asset store
  |--- Git repository
  |
PostgreSQL
```

## Repository layout

```text
shirtfaced-studio/
├── AGENTS.md
├── START_CODEX.md
├── README.md
├── pyproject.toml
├── .env.example
├── alembic.ini
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db/
│   │   ├── base.py
│   │   ├── models.py
│   │   ├── session.py
│   │   └── migrations/
│   ├── domain/
│   │   ├── enums.py
│   │   ├── schemas.py
│   │   └── errors.py
│   ├── services/
│   │   ├── world_loader.py
│   │   ├── shot_selector.py
│   │   ├── prompt_planner.py
│   │   ├── generation_orchestrator.py
│   │   ├── review_service.py
│   │   ├── decision_service.py
│   │   ├── continuity_service.py
│   │   └── canon_service.py
│   ├── adapters/
│   │   ├── openai_text.py
│   │   ├── openai_image.py
│   │   ├── openai_review.py
│   │   ├── markdown_store.py
│   │   ├── asset_store.py
│   │   └── git_store.py
│   ├── routes/
│   │   ├── pages.py
│   │   └── api.py
│   ├── templates/
│   └── static/
├── worlds/
│   └── world-01/
│       ├── WORLD.md
│       ├── CONTINUITY.md
│       ├── SHOTLIST.md
│       ├── references/
│       └── generations/
├── prompts/
│   ├── plan_prompt.md
│   ├── review_prompt.md
│   └── canon_proposal_prompt.md
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── contract/
└── docs/
```

## Boundaries

### Markdown store

Responsible for:

- loading canonical files;
- validating required headings and tables;
- applying controlled patches;
- atomic writes;
- content hashing;
- retaining backups until Git commit succeeds.

It must not call OpenAI.

### PostgreSQL database

The existing PostgreSQL database hosted in the Oracle environment is the production operational source of truth.

It is responsible for:

- shots;
- attempts;
- assets;
- reviews;
- decisions;
- proposals;
- audit events;
- model usage.

Markdown remains the human-readable creative record.

### OpenAI adapters

Each adapter exposes a narrow interface.

```python
class PromptPlanningClient(Protocol):
    def create_plan(self, request: PromptPlanRequest) -> PromptPlan: ...

class ImageGenerationClient(Protocol):
    def generate(self, request: ImageGenerationRequest) -> GeneratedImage: ...

class ImageReviewClient(Protocol):
    def review(self, request: ImageReviewRequest) -> ImageReview: ...
```

Services depend on protocols, not the SDK.

### Orchestrator

The orchestrator coordinates one generation attempt.

It must be restart-safe.

Every state transition is persisted:

```text
planned
prompt_ready
generating
generated
reviewing
awaiting_decision
approved
rejected
failed
```

## Concurrency

Only one active generation per world in Version 1.

Enforce with PostgreSQL:

- a transaction-scoped advisory lock keyed by world ID during selection and generation-state creation;
- a partial unique index preventing more than one active attempt per world;
- row-level locking when finalising decisions;
- clear `409 Conflict` responses.

Do not rely on an in-memory process lock because production may restart or later run more than one worker.

## File safety

Canonical files use:

1. validate proposed new content;
2. write temporary file;
3. fsync;
4. atomic rename;
5. Git commit;
6. record commit hash.

If Git commit fails, retain the valid file and report the failure. Do not pretend the change is versioned.

## PostgreSQL connectivity

- Use psycopg 3.
- Use SQLAlchemy connection pooling.
- Enable `pool_pre_ping`.
- Configure pool size and overflow through environment variables.
- Require TLS in production when supported by the existing PostgreSQL endpoint.
- Keep transactions short.
- Use Alembic for every schema change.
- Never run destructive schema changes automatically on application startup.

## Asset storage

Version 1 may store generated files on a persistent mounted volume on the Oracle host.

All asset access must go through an `AssetStore` interface so Oracle Object Storage can be introduced without changing domain services.

The database stores asset metadata and stable object keys, not image binary payloads.

## Security

- API key only through environment variables or Oracle-managed secrets.
- Bind to localhost by default.
- No key in browser JavaScript.
- Validate uploads and file paths.
- Prevent directory traversal.
- Escape all rendered model output.
- Restrict generated file writes to the active world directory.
- Never execute model-generated code or shell commands.
