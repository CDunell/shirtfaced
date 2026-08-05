# Internal API Contract

The Base Web interface calls these endpoints. Since ADR-011 the interface is a
separate build rather than server-rendered templates, so this contract is the only
interface between the two halves: changing an endpoint shape breaks the UI.

## Worlds

### `GET /api/worlds`

Returns available worlds and summary status.

### `GET /api/worlds/{world_slug}`

Returns world summary, next eligible shot, rotation state and pending decisions.

### `POST /api/worlds/{world_slug}/continue`

Runs planning and image generation synchronously for Version 1, per ADR-010. Review
is attached by Phase 4.

Returns `201` with the attempt. `live` is `false` when the deterministic fakes
produced the result, which is the case whenever `OPENAI_API_KEY` and the relevant
model are not both set; nothing is billed then.

The world's reference library is sent with every generation, `REFERENCE_IMAGE_LIMIT`
images of it, locked first. A world with no references generates from text alone.

**Query parameters**

| Name | Type | Default | Meaning |
|---|---|---|---|
| `draft` | bool | `false` | Generate on `OPENAI_IMAGE_DRAFT_MODEL` instead of `OPENAI_IMAGE_MODEL`. |

A draft is for checking framing and geometry cheaply. It is flagged `is_draft` on the
attempt, cannot be promoted to a reference, and its review scores are not comparable
with a full frame's.

`draft=true` returns `422` when a key is configured and `OPENAI_IMAGE_DRAFT_MODEL` is
not. It never falls back to the full model, because falling back is how a draft
quietly costs full price.

`image_model` on the response is the model that was **actually called**, not the one
requested. These can differ: the client fixes its model at construction.

The attempt is left in `generated`, which is an active state: it occupies the world
until a human decides. `approved` is always `false` here — generating an image is not
approving it.

Response:

```json
{
  "attempt": {
    "id": "uuid",
    "attempt_number": 1,
    "state": "generated",
    "shot": { "external_id": "W01-011", "title": "Car interior transition" },
    "selection_reason": "W01-011 chosen from 10 eligible planned shots…",
    "production_prompt": "…",
    "prompt_plan": {},
    "image_model": "…",
    "image_size": "1536x1024",
    "hero_product": "Tote bag",
    "camera_position": "Rear seat",
    "world_document_hash": "…",
    "image_url": "/assets/<uuid>",
    "thumbnail_url": "/assets/<uuid>",
    "failure_code": null,
    "approved": false
  },
  "live": false
}
```

Error responses:

- `409` — an attempt is already active for this world.
- `422` — no shot is eligible, or the world has not been imported.

Provider and storage failures do not raise. The attempt is recorded as `failed` with a
classified `failure_code` — `planning_failed`, `provider_error`, `provider_timeout`,
`provider_refused`, `invalid_image`, `storage_failed`, `configuration` or `internal` —
so the failure is inspectable rather than lost in a status code. A failed attempt is
terminal and releases the world.

### `GET /api/worlds/{world_slug}/next-shot`

Runs the deterministic selector and returns the chosen shot, the explanation, the
rotation state used and the shots that were set aside with the reason for each.

Calls no model and changes no state, so it is safe to poll.

Response:

```json
{
  "selected": { "external_id": "W01-011", "title": "Car interior transition" },
  "reason": "W01-011 chosen from 10 eligible planned shots. Lowest priority (100)…",
  "eligible_count": 10,
  "set_aside": [{ "external_id": "W01-016", "reason": "repeats the previous hero product 'Cap'" }],
  "last_hero_product": "Cap",
  "last_camera_position": "Beside parked car"
}
```

`selected` is `null` when nothing is eligible; `reason` says why.

### `POST /api/worlds/{world_slug}/plan-preview`

Builds the production prompt for the next shot without generating an image and
without persisting anything. Development mode only: returns `404` when `DEBUG` is
false.

`live` is `false` when the deterministic planner produced the plan, which is the case
whenever `OPENAI_API_KEY` and `OPENAI_TEXT_MODEL` are not both set. Nothing is billed
in that case.

Error responses:

- `404` — not in development mode, or the world has not been imported.
- `409` — no shot is eligible.
- `422` — the world files could not be read.
- `502` — the planning model failed or returned an unusable plan.

### `GET /api/worlds/{world_slug}/attempts`

Returns attempts for a world, newest first. `limit` defaults to 20, capped at 100.

## Attempts

### `GET /api/attempts/{attempt_id}`

Returns the prompt, plan, image URLs, model settings and provenance. Review, decision
and audit events are attached by later phases.

Provenance on every attempt: the shot's hero product and camera position as they stood,
and the three canonical document hashes. The documents can be edited afterwards, so a
generated image stays traceable to the world version that produced it.

## Assets

### `GET /assets/{asset_id}`

Returns one stored image by its identifier. Only assets recorded in the database are
served, and the path comes from the row rather than the request.

- `404` — no such asset.
- `503` — the asset is recorded but its file could not be read, which means the volume
  is missing or was cleared. Deliberately not a `404`: the record exists.

Built interface bundles are served from `/static`, not `/assets`, so the two never
collide.

### `POST /api/attempts/{attempt_id}/approve`

Body:

```json
{
  "promote_to_reference": false,
  "note": "",
  "idempotency_key": null
}
```

Marks the attempt and the shot approved, updates the shotlist marker, adds an approved
entry and rotation rows to `CONTINUITY.md`, and commits when Git is enabled.

Reference promotion is an option on approval, not a fourth decision. It reuses the
approved original's path and hash, so a reference can never drift from the image that
was approved.

### `POST /api/attempts/{attempt_id}/reject`

Body:

```json
{
  "reason": "The group reads as resigned rather than optimistic.",
  "idempotency_key": null
}
```

A reason is required and is recorded verbatim. The shot stays `planned`; only the
attempt is rejected.

The drift entry is inserted at the **top** of `# Rejected Drift`, because the planner
reads the first three subsections. Older entries stay below as history and are never
deleted. Owner text is sanitised before it reaches the document, so a reason cannot
create a heading or break a table.

### `POST /api/attempts/{attempt_id}/variation`

Body:

```json
{
  "instruction": "Use a front perspective and make the black cap panel visible."
}
```

Records the request and nothing else. It calls no model, generates no image and
changes no document. The attempt becomes `variation_requested` — terminal, and
deliberately not `rejected` (ADR-013) — which releases the world so an explicit
Continue World can create the child attempt.

### `POST /api/attempts/{attempt_id}/retry-review`

Reviews the stored image again. No image is regenerated, so this costs one review.

Reviews are immutable: this adds another rather than replacing the last, and the most
recent one is the one shown.

- `404` — no such attempt.
- `409` — the attempt has no stored image to review.
- `422` — the world files could not be read.
- `502` — the review failed. The attempt records `failure_code: review_failed`, keeps
  its image, and can be retried.

### Decision responses

All three decision endpoints return the same shape. The four downstream outcomes are
reported separately because they cannot succeed or fail together:

```json
{
  "attempt_id": "uuid",
  "attempt_state": "approved",
  "decision": "approved",
  "shot_external_id": "W01-011",
  "shot_status": "approved",
  "markdown_sync": "succeeded",
  "git_sync": "succeeded",
  "reference_sync": "succeeded",
  "git_commit": "…",
  "document_hashes": { "SHOTLIST.md": "…", "CONTINUITY.md": "…" },
  "reconciliation_required": false,
  "reconciliation": []
}
```

- `404` — no such attempt.
- `409` — the attempt is not awaiting a decision, or a different decision already
  exists. A repeated *identical* request returns `200` with the existing decision.
- `422` — a missing reason or instruction, or the world documents failed validation.

A decision is final the moment it is recorded. If a downstream step fails, the response
still reports the decision as made, sets `reconciliation_required` and names the stage.
It never implies a rollback, because there is none.

## Canon proposals

### `GET /api/worlds/{world_slug}/canon-proposals`

Rules the reviewer has proposed, newest first. Every one is `pending` until the owner
decides. Nothing here has changed `WORLD.md`.

### `POST /api/canon-proposals/{proposal_id}/approve`

### `POST /api/canon-proposals/{proposal_id}/reject`

## Shots

### `POST /api/worlds/{world_slug}/shots`

Creates a planned shot.

### `PATCH /api/shots/{shot_id}`

Allows controlled metadata edits.

### `POST /api/shots/{shot_id}/disable`

## Health

### `GET /health`

Confirms only that the application process is alive. It performs no database or
filesystem work, so a slow dependency cannot make a healthy process look dead.

### `GET /ready`

Validates the dependencies: PostgreSQL is reachable, required migrations are applied,
the world directory exists and is readable, and asset storage is writable.

## Structured model contracts

Use Pydantic models and JSON Schema for planning and review outputs.

Model output must never be parsed from informal Markdown.

### PromptPlan

Required fields:

- `scene_summary`
- `emotional_beat`
- `hero_product`
- `product_visibility_instruction`
- `camera_position`
- `lighting_source`
- `documentary_imperfection`
- `australian_authenticity_anchors`
- `negative_constraints`
- `selection_rationale`
- `production_prompt`

### ImageReview

Carries both vocabularies, per ADR-012: the nine evidence gates from the Phase 4
review contract, and the scores and compliance flags the data model requires.

Required fields:

- `recommendation` — `APPROVE_RECOMMENDED`, `APPROVE_WITH_NOTE_RECOMMENDED`,
  `REJECT_RECOMMENDED` or `REVIEW_UNCERTAIN`
- `gates` — all nine of `mood`, `australian_authenticity`, `product_visibility`,
  `third_party_branding`, `vehicle_continuity`, `wardrobe_balance`, `composition`,
  `documentary_credibility`, `story`. Each has `status` (`PASS`, `FAIL`, `UNCERTAIN`,
  `NOT_APPLICABLE`), `evidence`, `codes`, `confidence` and `material`.
- `mood_score`, `australian_authenticity_score`, `product_visibility_score`,
  `documentary_credibility_score`, `story_score` — integers 1 to 5
- `branding_compliant`, `vehicle_compliant`
- `strongest_success`
- `material_drift` — or null
- `new_rule_proposal` — or null. Becomes a pending canon proposal.
- `next_hero_product`, `next_camera` — or null

`verdict` is derived from `recommendation` and is not supplied by the model.

A gate only blocks when it is both `FAIL` and `material`. Uncertainty never blocks on
its own; it asks for human inspection.
