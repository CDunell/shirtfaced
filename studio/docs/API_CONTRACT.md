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

Runs planning, image generation and review synchronously for Version 1.

Response:

```json
{
  "attempt_id": "uuid",
  "state": "awaiting_decision",
  "shot": {
    "external_id": "W01-011",
    "title": "Car interior transition"
  },
  "prompt_plan": {},
  "production_prompt": "...",
  "image_url": "/assets/...",
  "review": {
    "verdict": "approved_with_note",
    "scores": {
      "mood": 5,
      "australian_authenticity": 4,
      "product_visibility": 5,
      "documentary_credibility": 4,
      "story": 5
    }
  }
}
```

Error responses:

- `409` — active generation already exists.
- `422` — world files or model output failed validation.
- `502` — OpenAI request failed.
- `500` — persistence or local filesystem failure.

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

### `GET /api/worlds/{world_slug}/history`

Returns paginated attempts.

## Attempts

### `GET /api/attempts/{attempt_id}`

Returns prompt, image, review, decision and audit events.

### `POST /api/attempts/{attempt_id}/approve`

Body:

```json
{
  "promote_to_reference": false,
  "note": ""
}
```

### `POST /api/attempts/{attempt_id}/reject`

Body:

```json
{
  "reason": "The group reads as resigned rather than optimistic."
}
```

### `POST /api/attempts/{attempt_id}/variation`

Body:

```json
{
  "instruction": "Use a front perspective and make the black cap panel visible."
}
```

This records the request. The UI may then explicitly start the variation attempt.

### `POST /api/attempts/{attempt_id}/retry-review`

Retries review without regenerating the image.

## Canon proposals

### `GET /api/worlds/{world_slug}/canon-proposals`

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

Required fields:

- `verdict`
- `mood_score`
- `australian_authenticity_score`
- `product_visibility_score`
- `documentary_credibility_score`
- `story_score`
- `branding_compliant`
- `vehicle_compliant`
- `strongest_success`
- `material_drift`
- `recommended_action`
- `proposed_permanent_rule`
