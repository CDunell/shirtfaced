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
