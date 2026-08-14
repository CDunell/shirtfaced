# shirtfaced — PostgreSQL-first AI social production model

**Status:** ACTIVE design authority  
**Scope:** Persistence from campaign kickoff through published social derivative  
**Database:** Existing Studio PostgreSQL database  
**Governing decisions:** ADR-016 and ADR-017 in `studio/docs/DECISIONS.md`

---

## 1. Governing rule

PostgreSQL is engaged at **campaign kickoff**, not after creative development and not only when a social package is ready to publish.

No campaign, story version, character, location, scene, campaign-native shot, generation attempt, review, approval, rejection, edit or platform derivative should exist only in prompt history, local files or an AI-model conversation.

The database is the operational system of record for the production lifecycle. Markdown remains authored creative canon where already established; PostgreSQL owns workflow state, relationships, provenance and decisions.

The campaign chain is:

`world -> campaign -> story version -> scene/shot planning -> shot -> generation attempt -> media asset -> automated review -> human decision -> edit version -> social post -> publication job -> performance`

The existing non-campaign photography path remains valid:

`world -> Markdown-seeded shot -> generation attempt -> media asset -> automated review -> human decision`

There is **one production spine**. AI social production does not create parallel `social_shots`, `social_generation_attempts`, `social_assets` or `social_continuity_checks` tables.

Existing `social_posts`, `social_derivatives`, `publication_jobs` and `cadence_policies` remain the downstream publishing layer and are linked to the campaign/edit lineage rather than replaced.

---

## 2. Kickoff transaction

Creating a campaign in Studio creates a persistent campaign row immediately.

Minimum campaign kickoff fields:

- `id` UUID
- `world_id` FK, non-null
- `name`
- `slug`
- `status`
- `campaign_type`
- `premise`
- `objective`
- `cycle_number`
- `cycle_start_at`
- `cycle_end_at`
- target platforms
- target primary-post count
- Instagram motion/photo target ratio
- TikTok motion/photo target ratio
- presentation-language target mix
- garments / approved designs initially in scope
- source creative brief
- created_by / origin metadata
- `created_at`
- `updated_at`

A campaign ID becomes the production root for all campaign-native records.

Nothing in the campaign workflow begins generation without a persisted campaign and a persisted shot specification.

---

## 3. New campaign-domain entities

These entities are genuinely new. They extend the existing world-production domain rather than duplicating it.

### `campaigns`

Canonical campaign / publishing-cycle root.

Responsibilities:

- world ownership
- kickoff state
- campaign premise and objective
- target schedule and channel mix
- lifecycle status
- campaign-level creative constraints
- presentation-language targets
- garments / approved designs in scope
- aggregate performance lineage

Suggested states:

- `draft`
- `developing`
- `preproduction`
- `generating`
- `editing`
- `review`
- `scheduled`
- `live`
- `complete`
- `abandoned`

### `story_versions`

Versioned narrative development belonging to one campaign.

Fields should include:

- campaign FK
- version number
- logline
- synopsis
- setup
- commitment
- escalation
- complication
- peak
- aftermath
- humour / tension mechanism
- ending / callback
- directing-language plan
- structured story JSONB
- source prompt/template version
- model/settings provenance where AI-assisted
- approval state
- rejection reason
- timestamps

Approved story versions are immutable. Revision creates a new version.

### `characters`

Persistent campaign cast identity.

Fields should include:

- campaign FK
- canonical name / internal handle
- role in story
- appearance specification
- age band
- build / height intent
- hair / facial-hair specification
- identity-lock descriptors
- reference media-asset IDs
- voice / dialogue notes where relevant
- allowed variation
- forbidden drift
- active state

This is the machine-readable replacement for leaving cast identity only in prose such as `CHARACTERS.md`.

### `character_appearances`

Versioned or scene-ranged character appearance and wardrobe state.

Fields should include:

- character FK
- campaign FK
- first applicable scene / sequence
- last applicable scene / sequence
- garment / approved-design / SKU references where available
- colour
- fit / size / silhouette intent
- layer state
- front/back artwork references
- placement requirements
- accessories / hair / dirt / wetness / damage state
- allowed continuity changes
- continuity notes

A character may have multiple appearances over one story. Wardrobe is therefore not a single mutable field on the character row.

### `locations`

Canonical campaign locations.

Fields should include:

- campaign FK
- location name / code
- description
- geography / environment intent
- reference media assets
- spatial / floorplan JSONB
- lighting defaults
- fixed props
- allowed state changes
- forbidden drift

### `scenes`

Story subdivision and continuity boundary.

Fields should include:

- campaign FK
- story-version FK
- sequence number
- scene code
- story purpose
- location FK
- time state
- lighting state
- action beats JSONB
- dialogue / audio intent
- props JSONB
- continuity-in JSONB
- continuity-out JSONB
- candidate post roles
- approval state
- timestamps

Characters participating in a scene should be relational through a join table rather than stored only as an ID array.

### `scene_characters`

Relates characters / appearances to scenes and can carry scene-specific blocking or state overrides.

### `edit_versions`

Versioned edits built from approved/selected media assets and source shots.

Fields should include:

- campaign FK
- role in the ten-post cycle
- version number
- edit decision list JSONB
- duration
- aspect ratio
- audio plan
- overlay / text plan
- source-shot relationships
- output media-asset FK
- state
- approval / rejection metadata
- timestamps

Source shots should be relational through an edit-to-shot association rather than hidden only inside JSONB.

### `performance_records`

Platform performance observations linked back to the creative lineage.

Fields should include where available:

- campaign FK
- social-post / derivative / publication reference
- platform
- observation timestamp / reporting window
- reach / impressions
- non-follower reach
- views / completions / watch metrics
- shares
- saves
- comments
- profile visits
- follows
- clicks
- attributed conversions / revenue when available
- raw provider payload JSONB
- ingestion provenance

Performance rows are observations over time, not mutable counters on the campaign row.

---

## 4. Existing production spine — extend, do not fork

### `shots`

`shots` remains the single deterministic directing unit for both still and video work.

Existing Markdown-seeded photography rows remain valid. Campaign-native rows extend the same table.

Required additions include:

- `source` / provenance, including at least `markdown_import` and `campaign_native`
- nullable `campaign_id` FK
- nullable `scene_id` FK
- media intent: still / video / either
- intended duration where temporal
- target aspect / safe-crop plan
- shot size
- camera height
- camera angle
- focal-length / FOV intent
- camera movement
- blocking JSONB
- eyeline
- foreground action
- midground action
- background action
- focus / depth intent
- richer lighting specification
- garment visibility class
- garment side visible
- garment scale in frame
- artwork-legibility requirement
- prop continuity requirements
- first-frame anchor reference where applicable
- last-frame anchor reference where applicable
- intended edit-in
- intended edit-out
- still-extraction potential
- negative constraints
- locked reference media-asset IDs / manifest

Existing fields such as sequence, priority, title, description, `hero_product`, `camera_position`, `lighting_source`, status and `source_line` remain valid thin-v1 fields.

#### ADR-017 provenance rules

Markdown-seeded shot:

- `world_id` non-null
- `campaign_id` NULL
- `scene_id` NULL
- `external_id` from `SHOTLIST.md`
- `source_line` populated
- `source = markdown_import`

Campaign-native shot:

- `world_id` non-null
- `campaign_id` non-null
- `scene_id` usually populated but legitimately nullable
- deterministic human-readable `external_id`, e.g. `CAMP01-S03-007`
- `source_line` NULL
- `source = campaign_native`

A campaign shot may legitimately have no scene: product insert, environmental plate, CCTV cutaway, transition, title-card source or generic aftermath material are valid examples.

If `scene_id` is present, application/database validation must ensure that the scene belongs to the same campaign as `shot.campaign_id`.

The world importer must continue to operate only on Markdown-origin rows. If pruning is ever introduced, it must be scoped to `source = markdown_import` so campaign-native rows cannot be removed by a shotlist re-import.

### `generation_attempts`

`generation_attempts` remains the single attempt/provenance record for still and video generation.

It already owns attempt numbering, parentage, state, exact production prompt, prompt-plan JSON, model fields, provider request ID, source-document hashes, failure state, assets, reviews and human decision.

Generalise image-specific columns rather than creating a second attempt table. Migration planning should cover:

- `image_model` -> media-neutral model field
- `image_size` -> output spec / dimensions field
- `image_quality` -> quality preset
- `image_format` -> output format
- provider
- modality: image / video / audio / imported where needed
- requested duration
- requested FPS
- provider/model version where available
- seed where available
- reference-input manifest
- first-frame input media asset
- last-frame input media asset
- generation source: manual paid UI / API / local / imported
- provider job / request identifiers
- provider-specific settings JSONB
- technical metadata JSONB
- started / completed timestamps where useful
- cost / credit metadata where observable

Existing image attempts remain valid records through the migration.

Rejected and failed attempts remain durable provenance. Do not delete the evidence that explains why a shot was regenerated.

### `image_assets` -> `media_assets`

This is a real domain and table rename, coordinated as one bounded change.

`media_assets` must support at least:

- generated still
- generated video
- extracted frame
- character reference still
- location reference still
- garment/design reference
- environmental plate
- first-frame anchor
- last-frame anchor
- edit master
- proxy / thumbnail
- audio where later required

The database stores stable object/path references, hashes, MIME type, dimensions, duration and technical/provenance metadata. Large image/video/audio bytes remain in file/object storage.

### `automated_reviews`

`automated_reviews` remains world/media-specific and separate from product `design_reviews`.

It adopts the same **structural contract**, not the same table or rubric:

- hard gates stored as data, carrying stable IDs, labels, result and evidence
- score categories stored as data, carrying stable IDs and scoring boundaries
- rubric/version provenance
- recommendation / verdict
- reviewer-model provenance
- applicability by media / shot type

The current physical gate/score columns must not be extended with another column per continuity rule. The migration should move the world judge away from column-per-gate storage.

World/media rubrics may include, as applicable:

- canon / mood fit
- Australian authenticity
- product visibility / garment behaviour
- documentary credibility
- story compliance
- branding / prohibited-brand compliance
- vehicle / prop compliance
- structural integrity
- character identity continuity
- wardrobe continuity
- garment artwork fidelity
- location continuity
- screen direction
- temporal continuity
- first/last-frame compatibility
- motion / interpolation defects

A gate that does not apply to a still is not recorded as `NOT_TESTED` merely because the rubric also supports video. Applicability is resolved before evaluation. A gate that **does apply** but is not evaluated remains blocking according to the review contract.

### `human_decisions`

One existing human-decision mechanism remains the approval authority for world media. Video does not create a second human-decision table.

---

## 5. Shot characters, continuity and references

Continuity is represented by relationships and review evidence, not by a parallel `social_continuity_checks` approval system.

Useful relational structures include:

- `scene_characters`
- `shot_characters`
- character appearance / wardrobe applicability
- shot-to-reference-media associations
- edit-to-source-shot associations

JSONB remains appropriate for evolving state snapshots such as:

- continuity-in / continuity-out
- blocking maps
- prop states
- provider-specific reference manifests

Automated review records the observed evidence and applicable gate results. Human decisions remain the final approval boundary.

---

## 6. Link to the publishing layer

The existing `social_posts.campaign_id` should become a real FK to `campaigns` once campaigns exist.

A social post should also be linkable to:

- approved `edit_version`
- cycle slot / narrative function
- source scene(s) where needed

Existing `social_derivatives`, publication jobs and cadence policies remain downstream.

Required reverse trace for a published item:

`publication job -> social derivative -> social post -> edit version -> source shots -> generation attempts -> media assets/reviews/decisions -> shot specs -> scene/story version -> campaign -> world`

---

## 7. Data ownership rules

### PostgreSQL owns

- campaign state
- story versions
- narrative structure
- cast and appearance / wardrobe metadata
- location identity
- scene and shot specifications
- prompts and model settings
- generation provenance
- review evidence and rejection reasons
- selected-vs-rejected decisions
- edit lineage
- publishing lineage
- performance observations

### Markdown owns where already established

- authored world canon
- `SHOTLIST.md` as the authored seed for the non-campaign photography queue

Markdown does not gain campaign scenes or screenplay structure.

### Object/file storage owns

- image bytes
- video bytes
- audio bytes
- large reference files
- rendered masters

PostgreSQL stores stable references, hashes, technical metadata and provenance for those assets.

Do not store large video binaries directly in PostgreSQL.

---

## 8. Prompt and model provenance

Prompts are production data.

Store at the relevant level:

- source brief
- template/system version
- AI-assisted creative proposal where used
- approved story prompt / provenance
- scene prompt / provenance
- shot production prompt
- negative constraints
- reference inputs
- provider / model / model version
- generation settings
- human edits
- timestamps
- generation and review outcome

A successful result must remain explainable even when the provider itself is nondeterministic.

---

## 9. JSONB vs relational columns

Use relational columns/FKs for identities and relationships that must be joined, constrained or indexed frequently.

Use JSONB for evolving structured creative payloads such as:

- beat arrays
- blocking maps
- provider-specific settings
- continuity snapshots
- reference-input manifests
- edit decision lists

Do not hide core relationships in a single campaign JSON document.

---

## 10. Approval boundaries

Approval and rejection are persistent state, never inferred from file existence.

Required review boundaries include at least:

- story version
- materially changed scene plan
- generated source selection through existing automated-review + human-decision flow
- final edit
- platform derivative where platform-specific review is required

Rejection reasons should use structured codes plus free-text evidence where practical so failure patterns can later be analysed.

---

## 11. Performance closes the loop

Performance must retain lineage back to creative decisions so later analysis can answer:

- Which directing languages produce non-follower reach?
- Which story roles drive shares?
- Which shot durations improve completion?
- Does readable garment exposure help or hurt watch time?
- Do polished / documentary / rough / weird presentation classes behave differently?
- Which characters or recurring narrative devices perform best?
- Which generation settings or continuity failures repeatedly cause rejection?

This is why the campaign row exists before story development rather than being added at publishing time.

---

## 12. Implementation sequence

Implementation order after ADR-016/017 redraw:

1. campaign / story / cast / location / scene contracts and ORM plan
2. extend `shots` for dual provenance and video-capable directing grammar
3. extend `generation_attempts` for media-neutral provenance
4. coordinated `image_assets` -> `media_assets` rename
5. migrate `automated_reviews` from physical gate columns to rubric-shaped gate/category data
6. add campaign/story/character/appearance/location/scene tables and associations
7. add edit versions and edit-source lineage
8. establish real campaign/edit linkage into existing social publishing rows
9. add campaign-chain smoke coverage that asserts persisted lineage and real asset metadata
10. campaign-development UI
11. generation-provider / manual-generation workflow extensions
12. performance ingestion and analysis

Before each Alembic migration, re-check current `main`. Revision numbers are claimed by pushing, not by planning. The first social/world revision is `0028` only while that remains the next free head.

---

## 13. Non-negotiable invariants

- No campaign-native generation without a persisted campaign.
- No generation attempt without a persisted shot specification.
- Every campaign-native shot has a campaign; a scene is required only where the shot belongs to a narrative scene.
- Markdown-seeded photography remains valid with `campaign_id` and `scene_id` NULL.
- No parallel shot, generation-attempt, asset, automated-review or human-decision systems.
- No published campaign derivative without lineage back to campaign kickoff.
- Rejected/failed generation attempts and review evidence remain durable provenance.
