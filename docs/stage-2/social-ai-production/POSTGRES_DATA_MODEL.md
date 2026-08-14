# shirtfaced — PostgreSQL-first AI social production model

**Status:** ACTIVE design authority
**Scope:** Persistence from campaign kickoff through published social derivative
**Database:** Existing Studio PostgreSQL database

---

## 1. Governing rule

PostgreSQL is engaged at **campaign kickoff**, not after creative development and not only when a social package is ready to publish.

No campaign, story, scene, shot, generation attempt, continuity decision, approval, rejection or platform derivative should exist only in prompt history, markdown, local files or an AI model conversation.

The database is the system of record for the production lifecycle.

The production chain is:

`campaign -> story version -> scene -> shot -> generation attempt -> selected asset -> edit/derivative -> social post -> publication job -> performance`

Existing `social_posts`, `social_derivatives`, `publication_jobs` and `cadence_policies` remain the downstream publishing layer. The AI production schema sits upstream and links into those records rather than replacing them.

---

## 2. Kickoff transaction

Creating a campaign in Studio must create a persistent campaign row immediately.

Minimum campaign kickoff fields:

- `id` UUID
- `name`
- `slug`
- `status`
- `campaign_type`
- `premise`
- `objective`
- `world_id` / creative-world reference where applicable
- `cycle_number`
- `cycle_start_at`
- `cycle_end_at`
- target platforms
- target primary-post count
- Instagram motion/photo target ratio
- TikTok motion/photo target ratio
- presentation-language target mix
- garments / designs initially in scope
- source creative brief
- created_by / origin metadata
- `created_at`
- `updated_at`

A campaign ID becomes the root foreign key used by all subsequent production records.

Nothing should begin generation without a campaign ID.

---

## 3. Required production entities

### `social_campaigns`

Canonical campaign / cycle root.

Responsibilities:

- kickoff state
- campaign premise and goal
- target schedule and channel mix
- lifecycle status
- campaign-level creative constraints
- aggregate performance reference

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

### `social_story_versions`

Versioned narrative development.

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
- character notes
- humour / tension mechanism
- ending / callback
- directing-language plan
- full structured story JSONB
- prompt provenance
- model/settings provenance
- approval state
- rejection reason
- timestamps

Story versions are immutable once approved. A revision creates a new version.

### `social_characters`

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
- reference asset IDs
- voice / dialogue notes where relevant
- allowed variation
- forbidden drift
- active state

### `social_character_wardrobe`

Character-to-garment allocation and continuity state.

Fields should include:

- character FK
- garment/design/SKU references where available
- colour
- fit / size / silhouette intent
- layer state
- front/back artwork references
- placement requirements
- first scene / last scene
- allowed continuity changes
- continuity notes

### `social_locations`

Canonical generated locations.

Fields should include:

- campaign FK
- location name
- description
- geography / environment intent
- reference assets
- spatial / floorplan JSONB
- lighting defaults
- fixed props
- forbidden drift

### `social_scenes`

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
- participating character IDs
- action beats JSONB
- dialogue / audio intent
- props JSONB
- continuity-in JSONB
- continuity-out JSONB
- candidate post roles
- approval state
- timestamps

### `social_shots`

The deterministic directing unit.

Fields should include:

- campaign FK
- scene FK
- sequence number
- shot code
- intended duration
- target aspect / safe-crop plan
- shot size
- camera height
- camera position
- camera angle
- focal-length / FOV intent
- camera movement
- blocking JSONB
- eyeline
- foreground action
- midground action
- background action
- focus/depth intent
- lighting specification
- garment visibility class
- garment side visible
- garment scale in frame
- artwork-legibility requirement
- prop continuity requirements
- first-frame anchor
- last-frame anchor
- intended edit-in
- intended edit-out
- still-extraction potential
- generation prompt
- negative constraints
- locked reference asset IDs
- state
- timestamps

The shot record is the production contract. Generation tooling consumes it; generation tooling does not invent an undocumented shot specification on the fly.

### `social_generation_attempts`

Every AI generation attempt, successful or rejected.

Fields should include:

- campaign FK
- scene FK
- shot FK
- attempt number
- provider
- model
- model version where available
- generation mode
- prompt sent
- negative prompt / constraints
- settings JSONB
- seed where available
- reference inputs JSONB
- requested duration / dimensions / FPS
- provider job ID
- started_at
- completed_at
- cost metadata where available
- result asset ID / URI
- technical metadata JSONB
- QC state
- rejection reason
- continuity-failure codes
- selected flag

Rejected generations remain stored as provenance. Do not delete the evidence that explains why a shot was regenerated.

### `social_assets`

Canonical source assets generated or imported for production.

Examples:

- character reference still
- location reference still
- garment reference
- video shot
- still shot
- audio
- plate
- first/last-frame anchor
- edit master

Fields should capture stable path/object-storage key, hash, MIME type, dimensions/duration, provenance and lifecycle state.

### `social_continuity_checks`

Structured QC against locked continuity.

Fields should include:

- campaign / scene / shot / generation-attempt references
- check type
- expected state JSONB
- observed state JSONB
- pass/fail
- severity
- reviewer / model
- notes
- timestamps

Example check types:

- character identity
- garment artwork
- garment placement
- location geometry
- prop state
- screen direction
- time / lighting
- weather
- vehicle identity
- body/tattoo/accessory continuity

### `social_edit_versions`

Versioned edits built from selected source shots.

Fields should include:

- campaign FK
- role in ten-post cycle
- version
- edit decision list JSONB
- duration
- aspect ratio
- audio plan
- overlay/text plan
- source-shot IDs
- output asset ID
- state
- approval/rejection metadata

### Link to existing `social_posts`

The existing `social_posts.campaign_id` must become a real FK to the campaign root once the production campaign table exists.

A social post should also be linkable to:

- the approved edit version that created it
- its cycle slot / narrative function
- its source scene(s)

Existing downstream derivative review and publication jobs remain intact.

---

## 4. Data ownership rules

### PostgreSQL owns

- campaign state
- story versions
- narrative structure
- cast and continuity metadata
- scene and shot specifications
- prompts and model settings
- generation provenance
- QC and rejection reasons
- selected-vs-rejected decisions
- edit lineage
- publishing lineage
- performance metadata / imported metrics

### Object/file storage owns

- image bytes
- video bytes
- audio bytes
- large reference files
- rendered masters

PostgreSQL stores stable references, hashes, technical metadata and provenance for those assets.

Do not store large video binaries directly in PostgreSQL.

---

## 5. Auditability rule

Given any published TikTok or Instagram post, Studio must eventually be able to trace backwards:

`publication job -> social derivative -> social post -> edit version -> selected source shots -> generation attempts -> shot specs -> scenes -> approved story version -> campaign kickoff`

And given any campaign kickoff, Studio must be able to trace forwards to every generated attempt, rejected asset, approved edit, scheduled derivative, published post and performance record.

This bidirectional lineage is required.

---

## 6. Prompt provenance

Prompts are production data.

Store, at the relevant level:

- system/template version
- source brief
- generated creative proposal
- approved story prompt
- scene prompt
- shot prompt
- negative constraints
- reference inputs
- provider/model
- generation settings
- timestamps
- human edits
- approval/rejection outcome

A later successful result must be reproducible enough to understand how it was produced even if the exact provider is nondeterministic.

---

## 7. JSONB vs relational columns

Use relational columns/FKs for identities and relationships that must be queried, joined, constrained or indexed frequently.

Use JSONB for evolving structured creative payloads such as:

- beat arrays
- blocking maps
- provider-specific generation settings
- continuity snapshots
- reference-input manifests
- edit decision lists

Do not hide core relational structure in one giant campaign JSON document.

---

## 8. Approval is persistent state

Approval and rejection must be stored, not inferred from file existence.

Required review boundaries include at least:

- story version
- scene plan where material changes occur
- shot/source selection
- final edit
- platform derivative

Rejection reasons should use both structured codes and free-text notes where practical so the system can later analyse failure patterns.

---

## 9. Performance closes the loop

The database should retain performance against the creative lineage so later analysis can answer questions such as:

- Which directing languages produce non-follower reach?
- Which story roles drive shares?
- Which shot durations improve completion?
- Does readable garment exposure help or hurt watch time?
- Do polished/documentary/rough/weird presentation classes behave differently?
- Which characters or recurring narrative devices perform best?
- Which generated assets are repeatedly rejected and why?

This is why the campaign record must exist before story development: performance needs to connect all the way back to the creative decision tree.

---

## 10. Implementation sequence

Recommended implementation order inside Studio:

1. `social_campaigns`
2. `social_story_versions`
3. characters / wardrobe / locations
4. `social_scenes`
5. `social_shots`
6. asset registry
7. `social_generation_attempts`
8. continuity checks
9. edit versions
10. real FK/linkage into existing `social_posts`
11. SocialBench campaign-development UI
12. generation-provider adapters
13. performance ingestion and analysis

The schema should be introduced through normal Alembic migrations in the existing PostgreSQL stack.

---

## 11. Non-negotiable kickoff invariant

**No generation without a persisted campaign. No shot without a persisted scene. No generation attempt without a persisted shot specification. No published derivative without lineage back to kickoff.**
