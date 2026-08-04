# End-to-End Workflow

## Command

The UI action and API command are both called:

`Continue Shirtfaced World 1`

## Phase 1 — Load

1. Resolve the world slug.
2. Acquire a world generation lock.
3. Load `WORLD.md`, `CONTINUITY.md` and `SHOTLIST.md`.
4. Calculate SHA-256 hashes for all three documents.
5. Parse required structures.
6. Fail before spending money if validation fails.

## Phase 2 — Select

1. Query eligible planned shots.
2. Load the last five approved shots.
3. Load the last five rejected attempts.
4. Apply priority, product rotation and camera rotation.
5. Select one shot deterministically.
6. Record a selection explanation.

## Phase 3 — Plan

Build a structured request containing:

- relevant world canon;
- recent continuity;
- selected shot;
- rotation history;
- recent rejected drift;
- prompt construction protocol;
- required hero product;
- required camera perspective;
- model output schema.

The planning model returns:

- final production prompt;
- scene summary;
- emotional beat;
- hero product;
- product visibility instruction;
- camera position;
- lighting source;
- documentary imperfection;
- Australian authenticity anchors;
- negative constraints;
- selection rationale.

Reject output that does not satisfy the schema.

## Phase 4 — Generate

1. Persist the final prompt.
2. Persist generation settings.
3. Call the image adapter once.
4. Decode and save the original image.
5. Calculate its hash.
6. Create a thumbnail.
7. Store returned model and usage metadata.
8. Advance the attempt to `generated`.

## Phase 5 — Review

Build an image review request containing:

- generated image;
- selected prompt;
- relevant world rules;
- intended hero product;
- intended camera position;
- vehicle rules where applicable;
- branding rules;
- recent reference notes.

The review model returns:

- verdict;
- mood score;
- Australian authenticity score;
- product visibility score;
- documentary credibility score;
- story score;
- branding compliance;
- vehicle compliance;
- strongest success;
- material drift;
- proposed new permanent rule, if any;
- recommended next action.

The review must use structured output.

## Phase 6 — Present

Show:

- image;
- prompt;
- selection rationale;
- review verdict;
- scores;
- drift;
- proposed canon rule;
- approve;
- reject;
- variation.

No permanent document is changed yet.

## Phase 7 — Decide

### Approve

1. Persist human approval.
2. Mark shot approved.
3. Append continuity entry.
4. Update product and camera rotation.
5. Optionally promote to reference.
6. Apply validated Markdown changes atomically.
7. Git commit.
8. Release lock.

### Reject

1. Require or strongly encourage a reason.
2. Persist rejection.
3. Keep the shot planned by default.
4. Append rejected drift to continuity.
5. Do not alter canon.
6. Release lock.

### Variation

1. Persist variation instructions.
2. Mark current attempt `variation_requested`.
3. Keep shot active.
4. Start a child attempt only after explicit user action.
5. Include the prior prompt, review and user instruction.
6. Do not silently reuse the exact same seed or settings.

## Phase 8 — Canon proposal

When review identifies a reusable rule:

1. create a pending canon proposal;
2. show the exact proposed text and insertion location;
3. require explicit approval;
4. revalidate the complete `WORLD.md`;
5. apply atomically;
6. Git commit;
7. store commit hash.

## Failure handling

### Planning failure

- no image charge should occur;
- keep shot planned;
- store failure details;
- allow retry.

### Image failure

- store API error and request ID where available;
- do not create a phantom asset;
- allow retry.

### Review failure

- preserve generated image;
- mark review failed;
- allow review retry without regenerating the image.

### Markdown update failure

- preserve the database decision;
- flag reconciliation required;
- do not claim documents are updated.

### Git failure

- preserve valid files;
- flag uncommitted changes;
- surface the exact error.
