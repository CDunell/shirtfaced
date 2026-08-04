# Shirtfaced Studio

A local-first creative production application for building coherent Shirtfaced photographic worlds.

The application turns a simple command:

> Continue Shirtfaced World 1.

into a controlled production workflow that:

1. loads the active world canon;
2. reads continuity and shot history;
3. selects the next eligible scene;
4. constructs a production-ready prompt;
5. generates an image through the OpenAI API;
6. reviews the result against canon;
7. presents the image and verdict for human approval;
8. persists the decision;
9. updates continuity and shot status;
10. changes world canon only when a reusable permanent rule is discovered.

## Source of truth

- `worlds/world-01/WORLD.md` — creative canon.
- `worlds/world-01/CONTINUITY.md` — human-readable continuity record.
- `worlds/world-01/SHOTLIST.md` — human-readable production backlog.
- PostgreSQL — operational state, generated assets, evaluations, approvals and audit history.
- Git — version history for canon and deliberate state changes.

## Development

Full instructions are in `docs/LOCAL_RUNBOOK.md`. In short:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env               # then set DATABASE_URL and DB_SSLMODE=disable
alembic upgrade head
uvicorn app.main:app --reload
```

The interface is a separate Base Web build in `web/`:

```bash
cd web
npm install
npm run build          # FastAPI then serves it at http://127.0.0.1:8000
npm run dev            # or: Vite on :5173, proxying the API to :8000
```

Quality gates — Python:

```bash
ruff check .
ruff format --check .
mypy app
pytest
```

Quality gates — interface, from `web/`:

```bash
npm run lint
npm run format:check
npm run typecheck
npm test
```

Integration tests need a real PostgreSQL database and are skipped without one. Point
`TEST_DATABASE_URL` at a throwaway container, never at a database that holds anything
you care about — the fixtures drop and recreate the `public` schema.

Three things catch people out:

- The interface is pinned to **React 18**. Base Web 18.2.0 still relies on
  `defaultProps` for function components, which React 19 removed, so `Card` and others
  throw at render on 19. `web/` has its own `node_modules`, so this is independent of
  the React 19 storefront at the repository root.

- An exported `DATABASE_URL` from another project overrides `.env`, because the process
  environment takes precedence. `DATABASE_URL` must use the `postgresql+psycopg://`
  prefix, so a connection string for a different stack is rejected rather than used.
- If PostgreSQL is already installed locally, publish the container on a spare port
  (for example `-p 55432:5432`) instead of 5432, so there is no ambiguity about which
  server you reach.

## Required reading order

Codex must read:

1. `AGENTS.md`
2. `docs/PRODUCT_SPEC.md`
3. `docs/ARCHITECTURE.md`
4. `docs/WORKFLOW.md`
5. `docs/DATA_MODEL.md`
6. `docs/API_CONTRACT.md`
7. `docs/TEST_PLAN.md`
8. `docs/IMPLEMENTATION_PLAN.md`
9. `docs/ORACLE_CLOUD_DEPLOYMENT.md`

Do not begin implementation before reading all nine documents.
