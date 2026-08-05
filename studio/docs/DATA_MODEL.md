# Data Model

## Database

PostgreSQL is the production database.

Use native PostgreSQL UUID columns.

Use `timestamptz` for all timestamps and store UTC.

Use JSONB for structured model payloads and audit metadata.

Use database constraints for state integrity rather than relying only on application validation.

SQLite may be used only for isolated unit tests where PostgreSQL behaviour is irrelevant. Integration tests must run against PostgreSQL.

## World

- `id`
- `slug`
- `name`
- `directory_path`
- `status`
- `world_document_hash`
- `continuity_document_hash`
- `shotlist_document_hash`
- `created_at`
- `updated_at`

## Shot

- `id`
- `world_id`
- `external_id` — e.g. `W01-011`
- `sequence`
- `priority`
- `title`
- `description`
- `hero_product`
- `camera_position`
- `lighting_source`
- `status`
- `disabled`
- `blocked_reason`
- `source_line`
- `created_at`
- `updated_at`

Allowed status:

- `planned`
- `in_progress`
- `approved`
- `rejected`
- `abandoned`

## GenerationAttempt

- `id`
- `world_id`
- `shot_id`
- `parent_attempt_id`
- `attempt_number`
- `state`
- `selection_reason`
- `production_prompt`
- `prompt_plan_json` — JSONB
- `image_model`
- `image_size`
- `image_quality`
- `image_format`
- `failure_code`
- `failure_message`
- `created_at`
- `updated_at`

## ImageAsset

- `id`
- `attempt_id`
- `kind` — original, thumbnail, reference
- `relative_path`
- `sha256`
- `mime_type`
- `width`
- `height`
- `byte_size`
- `created_at`

## AutomatedReview

- `id`
- `attempt_id`
- `review_model`
- `verdict`
- `mood_score`
- `australian_authenticity_score`
- `product_visibility_score`
- `documentary_credibility_score`
- `story_score`
- `branding_compliant`
- `vehicle_compliant`
- `structurally_sound` — whether what is shown could physically exist
- `strongest_success`
- `material_drift`
- `recommended_action`
- `raw_json` — JSONB
- `created_at`

Scores use integers from 1 to 5.

## HumanDecision

- `id`
- `attempt_id`
- `decision`
- `reason`
- `promote_to_reference`
- `created_at`

Allowed decision:

- `approved`
- `rejected`
- `variation_requested`

## CanonProposal

- `id`
- `world_id`
- `attempt_id`
- `status`
- `proposed_heading`
- `proposed_text`
- `insertion_anchor`
- `reason`
- `human_note`
- `git_commit`
- `created_at`
- `decided_at`

Allowed status:

- `pending`
- `approved`
- `rejected`
- `applied`
- `failed`

## UsageRecord

- `id`
- `attempt_id`
- `operation`
- `model`
- `input_tokens`
- `output_tokens`
- `cached_tokens`
- `image_count`
- `estimated_cost_usd`
- `provider_request_id`
- `created_at`

The application may estimate cost using configurable price metadata. Estimated cost must be labelled as an estimate.

## AuditEvent

- `id`
- `world_id`
- `attempt_id`
- `event_type`
- `actor`
- `payload_json` — JSONB
- `created_at`

Audit events are append-only.

## PostgreSQL indexes and locking

Required indexes:

- unique world slug;
- unique `(world_id, external_id)` for shots;
- index shots by `(world_id, status, priority, sequence)`;
- index attempts by `(world_id, created_at desc)`;
- index attempts by `(shot_id, attempt_number)`;
- index reviews by `attempt_id`;
- index audit events by `(world_id, created_at desc)`;
- partial unique index allowing only one active attempt per world.

Active attempt states:

- `planned`
- `prompt_ready`
- `generating`
- `generated`
- `reviewing`
- `awaiting_decision`

Use advisory locks for the Continue World critical section.

## Integrity rules

- One human final decision per attempt.
- One original image asset per successful attempt.
- Approved shots must reference at least one approved attempt.
- Reference images must derive from approved attempts.
- Canon proposals cannot be applied unless approved.
- A world cannot have more than one active generation attempt.
