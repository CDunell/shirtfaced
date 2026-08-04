# Test Plan

## Rules

- No live OpenAI API calls in automated tests.
- Use fixture images and fake adapters.
- Run integration tests against PostgreSQL, preferably with Testcontainers or a disposable CI service database.
- Do not treat SQLite as equivalent for advisory locks, JSONB, partial indexes or transaction behaviour.
- Every state transition requires tests.
- Every Markdown mutation requires round-trip validation.
- Tests must run on Windows, macOS and Linux where practical.

## Unit tests

### World loader

- loads valid files;
- rejects missing required headings;
- preserves unknown sections;
- detects hash changes;
- blocks path traversal.

### Shot selector

- selects lowest priority eligible shot;
- rotates hero product when alternatives exist;
- rotates camera when alternatives exist;
- skips disabled shots;
- skips active shots;
- records selection rationale;
- behaves deterministically.

### Prompt planner

- builds bounded context;
- validates structured output;
- rejects missing required fields;
- rejects hero-product mismatch;
- rejects empty production prompt.

### Generation orchestrator

- persists before paid call;
- saves image bytes;
- computes hash;
- resumes safely after review failure;
- blocks concurrent world generation;
- records provider errors.

### Review service

- sends actual image;
- validates scores;
- handles proposed rule;
- never applies canon.

### Decision service

- approval updates shot and continuity;
- rejection preserves planned shot;
- variation links child attempt;
- duplicate decision is rejected;
- reference promotion requires approval.

### Markdown store

- atomic write;
- conflict detection;
- malformed patch rejection;
- rollback or clear reconciliation state.

## Integration tests

- complete continue flow with fake OpenAI clients;
- complete approval flow;
- complete rejection flow;
- complete variation flow;
- failed image generation;
- failed review with successful retry;
- canon proposal approval;
- restart with preserved PostgreSQL state;
- advisory lock prevents concurrent Continue World operations;
- partial unique index prevents duplicate active attempts;
- transaction rollback leaves no partial decision state;
- Git commit adapter success and failure.

## Contract tests

Freeze representative structured outputs for:

- prompt plan;
- image review;
- canon proposal.

Ensure schema changes are deliberate.

## UI tests

At minimum:

- dashboard renders;
- continue button disabled while active;
- image and review display;
- approve;
- reject reason;
- variation instruction;
- error states;
- pending canon proposal.

## Manual acceptance test

1. Copy `.env.example` to `.env`.
2. Configure API models.
3. Start app.
4. Open World 1.
5. Click Continue.
6. Confirm one image is generated.
7. Confirm the image is reviewed.
8. Restart before deciding.
9. Confirm pending attempt remains.
10. Approve.
11. Confirm shotlist and continuity update.
12. Confirm Git history contains the update.
13. Generate a second shot.
14. Reject it.
15. Confirm the shot remains eligible.
16. Request a variation.
17. Confirm attempts are linked.
