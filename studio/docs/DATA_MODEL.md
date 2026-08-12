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

## Design concept pipeline (migration 0026)

This document describes the photography pipeline and had fallen behind the
schema; the element archive, composed designs, observations, social and email
tables (migrations 0014–0025) live in their model modules under `app/db/` and
are not repeated here. The design concept pipeline is recorded because it is
the second full production line, not a satellite table.

### DesignConcept

- `id`
- `library` — `tshirt | headwear | brand_garment`; numbering is only unique within a library
- `external_number` — permanent identity; #1 stays #1, retired entries keep their numbers
- `slug` — `001-she-ll-be-right`; carries the number because titles repeat
- `title`, `concept_text` — authored, verbatim, updated on re-import
- `retirement` — `'' | hard | unconditional | conditional`, how the source wrote it
- `garments`, `round`, `round_label`, `source_path`, `source_line`, `source_document_hash`, `parsed_json`
- `status`, `concept_kind`, `priority`, `tags`, `treatment_lanes`, `preferred_execution`, `integral_text`, `constraints`, `notes` — workflow-owned; the importer never touches them
- `created_at`, `updated_at`

Allowed status:

- `backlog`
- `ready`
- `exploring`
- `approved`
- `rejected`
- `held` — a conditional retirement or a deliberate pause; a decision not yet made
- `retired`
- `superseded`

### DesignAttempt

- `id`, `concept_id`, `parent_attempt_id`, `attempt_number` (unique per concept)
- `method` — `image_generation | deterministic_composition | manual_import | hybrid`
- `state` — `planned → generating → generated → awaiting_decision → approved | rejected | variation_requested | failed`; its own PostgreSQL type, deliberately not photography's `attempt_state`
- `brief_snapshot` — the concept as it stood when the attempt started
- `production_prompt`, `model`, `model_settings`, `reference_inputs`, `execution_rules`, `source_concept_hash`
- `failure_code`, `failure_message`, `notes`, timestamps

### DesignAsset

- `id`, `design_attempt_id`, `kind` (`artwork | preview | print_master | separation | source | mockup`)
- `relative_path` (under `ASSETS_ROOT`, key shape `designs/{library}/{number}/attempts/{attempt_id}/{name}`), `sha256`, `mime_type`, `width`, `height`, `byte_size`, `created_at`
- Immutable; unique on `(design_attempt_id, relative_path)`.

### DesignDecision

- `id`, `design_attempt_id` (unique — exactly one), `decision`, `reason`, `note`, `instruction`, `actor`, `idempotency_key`, `created_at`
- Immutable, and `actor` must be non-empty: an approval nobody signed is not an approval.

Allowed decision:

- `approved`
- `rejected`
- `variation_requested`

### ApprovedDesign

- `id`, `concept_id`, `design_attempt_id` (unique), `master_asset_id` (RESTRICT — the milestone keeps its bytes), `version` (unique per concept), `approved_by`, `approved_at`, `superseded_at`, `production_spec`
- The frozen production milestone. Only these rows may reach anything downstream.

### DesignAttemptElement

- `id`, `design_attempt_id`, `element_id` (RESTRICT), `role` (unique per attempt), `render_id`, `settings`, `created_at`
- Normalises `composed_designs.parts` so element provenance is a join, not a JSON scan.

### ProductLink

- `id`, `approved_design_id`, `external_system` (default `shirtfaced_shop`), `external_product_id`, `external_slug`, `sync_state`, `last_synced_at`, `metadata_json`, timestamps
- A soft reference. Studio and the shop are separate databases by decision, so this is an identifier and a sync state, never a foreign key.

### Additional integrity rules

- `composed_designs.design_attempt_id` (nullable, partial unique) links a deterministic composition to at most one attempt; the attempt's decision settles both rows.
- Import never deletes or renumbers a concept; a number missing from the source is reported and kept.
- The importer only writes `backlog`, `held` and `retired`; every other status belongs to the workflow and wins on conflict, with the conflict reported.
