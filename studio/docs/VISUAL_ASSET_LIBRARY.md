# SHIRTFACED Studio — Visual Asset Library

Status: architecture/product specification

Owner: SHIRTFACED Studio

Scope: cast, locations/scouting, scene masters, coverage frames, props/other production references

## 0. What is built, as of 17 August 2026

Phases 1 and 2 of §14, and Phase A of §15. Everything below them is still
specification.

| Section | State |
|---|---|
| §9 `visual_assets`, §9.1 `asset_lineage`, §9.2 tags | Built, migration 0031 |
| §5 cast library, §11 cast and asset endpoints, §15 Phase A UI | Built — `/api/cast`, the Cast bench |
| §14 Phase 2 ingest | Built — `python -m app.cli ingest-cast`, idempotent |
| §14 Phase 5 cutover, cast half | Built — nothing resolves a cast reference by path any more |
| §7 scene masters | Built in part, migration 0032 — `scene_masters`, one approved per scene |
| §8 coverage frames | **Not built as rows.** Crops still land in `var/…/coverage/<shot>/` with a manifest, now carrying the master's asset ID |
| §6 locations | **Not built.** No tables exist |

The cutover is what §2.1's audit describes as missing, so specifically: the
six-slot installer at `/api/renderer/cast-upload` is **retired** and returns
410; `run_renderer_seed.py`, `run_renderer_scene_rich_pub.py` and
`run_damo_expression_bridge.py` resolve through
`app/services/reference_resolution.py` by member and role, and record the asset
ID and SHA in their manifests; and `composition_path()`'s newest-mtime
selection is gone — a scene master must be a registered, approved asset, and
two approved candidates are a refusal rather than a tie-break.

Scene masters are resolved **per scene** by `scene_key`, which is what the
coverage tool, the derivation script and the Veo manifests already agree on.
Every path that used to pick a master by filename now asks the library:

- `app/routes/coverage.py` tried `composition-gpt.png`, then `.jpg`, then
  `.jpeg`, and took the first that existed;
- `scripts/derive_scene_coverage.py` took a path and a hash from a workflow
  trigger, which could not distinguish the approved master from a neighbour;
- `run_renderer_scene_rich_pub.py` took whichever matching file had the newest
  modification time;
- the three Veo scripts took a seed path and the hash of that same path, which
  is self-consistent and says nothing about which master the frame came from.
  They now refuse a seed whose parent is not the scene's approved master.

The evidence that this mattered is on the box: the four coverage frames cut for
pub-1105 on 16 August cite parent SHA `81290e2f…`, and no file on the host
hashes to it. The master at that path was replaced. Under the old rules the next
derivation would have silently cut different pixels for the same shot names.

Two departures from what is specified below, both recorded as **ADR-020** in
`DECISIONS.md` — the cast table is `cast_members`, because 0029's `characters`
already exists and is campaign-scoped; and cast asset roles are free text with
`CAST_ASSET_ROLES` as the offered vocabulary, because a closed list would refuse
photographs nobody anticipated.

## 1. Purpose

SHIRTFACED needs one professional visual asset system for all reusable production imagery. The current production approach has outgrown fixed folders and ad-hoc manifests. Cast references, location plates, approved scene masters and deterministic coverage frames must become first-class database-backed production assets with explicit provenance and lineage.

The Visual Asset Library is the authoritative catalogue for visual production inputs. Binary files continue to live in persistent asset storage, but PostgreSQL becomes the source of truth for identity, metadata, relationships, approval state, lineage, rights and discovery.

The system must support this production model:

`World/Event reality -> approved widescreen spatial master -> camera observations/coverage -> Veo motion -> selected usable fragments -> post-production`

The scene does not change when the camera changes. Named characters live inside the world. Different shots are observations of one event, not independently invented replacements.

## 2. Existing state audit

### 2.1 What already exists

Studio already has several useful building blocks:

- PostgreSQL is the mandated production state store, with SQLAlchemy/Alembic and persistent asset storage separated from database metadata.
- `ImageAsset` already records a stable asset row with path, SHA256, MIME type, dimensions and byte size. Its current scope is generated outputs belonging to a `GenerationAttempt`, so it cannot represent arbitrary cast/location/master library assets without extension or a new generalised asset table.
- `/api/renderer/cast-upload` exists with a primitive HTML upload form. It installs exactly six PNG files into fixed `var/cast/...` slots: Damo full/head, Brock full/head and Emma full/head. It validates files and records hashes in the response, but does not persist cast records or asset metadata in PostgreSQL.
- `/api/renderer/scene-reference-upload` exists for `pub-1105`, but it writes one fixed `composition-gpt.*` file into `var/scene-references/pub-1105/`. It is scene-specific and folder-backed rather than a reusable library.
- The virtual-camera coverage route already implements a valuable constitutional behaviour: exact SHA-locked master resolution, original-pixels-only 9:16 cropping, crop-coordinate manifests and no provider call. This should be retained and moved onto database-backed master/coverage records.
- `Shot.locked_reference_manifest` already provides a place to persist exact locked references for a shot, but today this is JSONB and not a replacement for proper relational library records.

### 2.2 What does not exist yet

There is no professional cast-library UI or DB-backed cast asset model. The current form is a six-slot installer, not a library. It cannot add Damo's third/expression reference, arbitrary new characters, multiple reference roles, ordering, approval, deprecation, tags, provenance, rights or history.

There is no reusable DB-backed location/scouting library. Scene references are tied to a fixed filesystem naming convention rather than a location/sub-location model.

There is no first-class DB record for approved scene masters with location/cast relationships and parent/source lineage. Coverage exists as files plus JSON manifests, not as durable production records linked to an immutable master row.

Therefore the new system should extend existing storage/database patterns rather than create a parallel stack.

## 3. Constitutional production rules

### 3.1 World master = reality

For any World/Event, the approved scene master represents the spatial truth of that event. Once approved, downstream shots must not silently redesign established geography, cast identity, wardrobe, props, practical lighting or event facts.

Hierarchy remains:

`WORLD / EVENT -> DISTRIBUTED HUMAN ACTIVITY -> CAMERA OBSERVATION -> CHARACTER INCIDENT -> CHARACTER IDENTITY`

Never:

`CHARACTER -> ACTION -> BACKGROUND`

### 3.2 Widescreen spatial-master rule

Scouting/base masters and scene masters should preferentially be captured/generated in a wide or ultrawide format with useful lateral geography. Target approximately 2.39:1 when the location and scene benefit from lateral coverage.

The purpose of the wide master is not to make the venue larger. It is to expose more of the same physically coherent location so multiple 9:16 observations can be extracted later.

A wide master must:

- preserve correct physical scale;
- contain enough resolution for meaningful vertical crops;
- distribute useful world activity across the frame rather than centre one hero;
- preserve left/right geography and practical anchors;
- avoid artificial empty zones around named characters;
- include enough environmental context to support deterministic camera moves/reframes.

### 3.3 Coverage = observation, not regeneration

A coverage frame is a reproducible viewport into an approved spatial master. The default operation is original-pixels-only crop/reframe. Store exact source master asset ID, source SHA256, viewport coordinates, crop dimensions and resulting SHA256.

Veo receives camera-ready observations. It is asked to animate established reality, not discover what is supposedly outside the crop.

### 3.4 Masters must already be production-correct

Nothing knowingly wrong is promoted to `approved_master`.

Approval requires scene richness, character identity, wardrobe, action, props, geography, lighting, camera, physical scale and factual details to be correct.

Nano/image editing is optional bounded repair. It is not a mandatory continuity stage and must not be used merely to regenerate an already-approved frame.

## 4. Product information architecture

Primary Studio navigation:

1. **Cast**
2. **Locations**
3. **Scene Masters**
4. **Coverage**
5. **Props / Other**

A single global **Visual Library** search can span all categories.

### 4.1 Shared asset browser

Desktop-first professional contact-sheet/grid view with:

- thumbnail;
- asset role/type;
- approval badge;
- character/location/scene association;
- dimensions/aspect ratio;
- rights state;
- provenance icon;
- version/active state;
- warnings for duplicate SHA, deprecated asset or missing rights.

Controls:

- search;
- filters;
- sort;
- bulk tag;
- bulk deprecate where safe;
- compare selected assets;
- attach to scene;
- set reference role;
- open lineage;
- upload/import.

### 4.2 Detail inspector

Every visual asset gets a right-side or full-page inspector with:

- full preview;
- stable asset ID;
- SHA256;
- dimensions/MIME/size;
- storage key/path;
- provenance and source;
- parent/child lineage graph;
- approval history;
- rights/licence metadata;
- tags;
- notes;
- associations;
- audit trail;
- replace/new-version action;
- deprecate action.

No production action should depend on a human-readable filename alone.

## 5. Cast library

### 5.1 Character records

`characters`

Suggested fields:

- `id UUID PK`
- `slug unique`
- `display_name`
- `world_id nullable` — null permits reusable/global cast
- `description`
- `canonical_metadata JSONB` — age/build/hair/marks/other continuity facts
- `status` — active/deprecated
- `created_at`, `updated_at`

Character identity and descriptive canon belong to the character record. Individual photos are separate visual assets.

### 5.2 Cast asset roles

Support unlimited assets per character. Recommended roles:

- `full_body_neutral`
- `head_shoulders_neutral`
- `expression_bridge`
- `profile_left`
- `profile_right`
- `three_quarter`
- `shouting`
- `laughing`
- `sleeping`
- `severe_head_angle`
- `wardrobe_reference`
- `body_reference`
- `historical/deprecated`
- `other`

This immediately solves Damo's third photo: it becomes another linked asset rather than forcing the system to invent a third hard-coded file slot.

### 5.3 Cast UI workflow

Character page:

- large identity header;
- canonical metadata;
- ordered reference strip;
- primary full-body and primary neutral-head badges;
- expression/reference gallery;
- upload dropzone;
- add role/tag;
- reorder references;
- approve/deprecate;
- compare against another reference;
- show scenes currently using each asset.

Uploading a new cast photo should:

1. validate image;
2. calculate SHA256 and dimensions;
3. reject or flag exact duplicate SHA;
4. persist bytes through the asset-storage adapter;
5. create `visual_assets` row;
6. create `character_asset_links` row;
7. persist provenance/rights metadata;
8. optionally mark as approved reference after explicit human approval;
9. append an audit event;
10. regenerate compatibility exports if legacy renderer code still needs them.

No user should need to hand-edit JSON.

## 6. Location and scouting library

### 6.1 Professional scouting model

A `location` is a reusable real or constructed place. It may have nested sub-locations.

Examples:

- Railway Hotel
  - front bar
  - back room
  - side street
  - rear car park
- late-night takeaway
  - exterior kerb
  - serving counter

Suggested `locations` fields:

- `id UUID PK`
- `parent_location_id nullable FK`
- `slug`
- `display_name`
- `location_type`
- `country/region/city` where relevant
- `description`
- `layout_notes`
- `scale_anchor_notes`
- `lighting_notes`
- `time_of_day_tags`
- `weather_tags`
- `practical_fixtures JSONB`
- `restrictions JSONB`
- `continuity_notes`
- `rights_status`
- `status`
- timestamps

### 6.2 Scouting asset classes

Location images can be:

- `scout_photo`
- `survey_wide`
- `survey_detail`
- `empty_plate`
- `participant_neutral_base`
- `generated_location_plate`
- `approved_base_master`
- `lighting_reference`
- `scale_reference`

Provenance must distinguish real photography, commissioned photography, licensed stock, generated imagery and edited derivatives.

### 6.3 Capture standard

Preferred scouting/base-master imagery:

- high resolution;
- landscape/widescreen, preferably 2.39:1 where appropriate;
- useful lateral geography;
- correct perspective and physical scale;
- participant-neutral/empty where possible;
- multiple camera positions for important locations;
- practical lights retained;
- scale anchors visible or measured;
- exposure notes stored;
- no HDR/tone-mapped look unless explicitly canonical;
- natural shadow/highlight behaviour;
- no heavy irreversible grade;
- enough width/resolution to extract multiple 9:16 observations.

A useful scout asset is not merely attractive. It is spatially legible and reusable.

### 6.4 Acquisition channels and rights

The library may ingest:

1. SHIRTFACED's own photography.
2. Commissioned location photographers/scouts.
3. Licensed stock where the licence explicitly permits commercial modification/derivative use.
4. Generated location plates.
5. Public-domain/appropriately licensed material where rights are clear.

Store for each asset:

- rights owner;
- licence source;
- licence type;
- commercial-use permission;
- modification permission;
- territory/term limits;
- release requirements;
- evidence/document reference;
- expiry date if any.

An asset with unknown rights can be used for internal inspiration but must not be promoted to production-safe base master.

## 7. Scene Masters library

A Scene Master is the approved immutable spatial truth for one World/Event/Scene version.

Suggested `scene_masters` fields:

- `id UUID PK`
- `scene_id FK`
- `visual_asset_id FK UNIQUE`
- `location_id FK`
- `status` — candidate/approved/superseded/rejected/deprecated
- `prompt_version`
- `canon_hash`
- `parent_master_id nullable FK`
- `base_location_asset_id nullable FK`
- `approved_at`
- `approved_by`
- `production_ready boolean`
- `notes`

`scene_master_cast`:

- `scene_master_id`
- `character_id`
- `role_in_scene`
- `reference_asset_ids JSONB or normalised join`
- `wardrobe_spec`
- `placement/blocking metadata`

Production inputs resolve by explicit scene master ID and its immutable SHA. Never `latest`, newest timestamp or loosely matching filename.

### 7.1 Scene construction workflow

1. Select World/Event/Scene.
2. Select an approved location/base master from Locations.
3. Select participating canonical cast and exact cast references.
4. Build the scene prompt/package from those explicit IDs.
5. Compose/generate participants into the existing location while preserving spatial geography.
6. Review physical scale, scene activity, identity, wardrobe, props, geography, light and photographic treatment.
7. Approve exactly one candidate as a new Scene Master version.
8. Lock asset ID + SHA256 + parent/base lineage.
9. Derive named coverage observations.
10. Send only approved coverage frames to Veo.

Generation is allowed while constructing a candidate master. Once a master is approved, generation must not silently redefine its location. A material geography change creates a new candidate/master version and requires approval.

## 8. Coverage library

Existing original-pixel crop behaviour is correct and should be retained.

Suggested `coverage_frames`:

- `id UUID PK`
- `scene_master_id FK`
- `visual_asset_id FK UNIQUE`
- `shot_id nullable FK`
- `name`
- `aspect_ratio`
- `x`, `y`, `width`, `height`
- `source_master_sha256`
- `frame_sha256`
- `operation` — crop_only/reframe/derived_other
- `approved_for_veo boolean`
- timestamps

The coverage UI should evolve from the current draggable 9:16 tool into a library-aware virtual camera:

- choose master from DB;
- drag 9:16 viewport;
- zoom only when explicitly permitted and recorded;
- save named frame;
- show safe regions and existing saved observations;
- compare coverage frames;
- attach frame to Shot;
- display exact lineage;
- optionally define deterministic A->B camera moves across the same master.

## 9. General visual asset schema

Introduce a general-purpose `visual_assets` table rather than stretching `image_assets`, because existing `image_assets.attempt_id` is non-null and semantically represents provider outputs.

Suggested fields:

- `id UUID PK`
- `kind` — cast/location/scene_master/coverage/prop/reference/other
- `role`
- `storage_key`
- `sha256 CHAR(64)`
- `mime_type`
- `width`
- `height`
- `byte_size`
- `aspect_ratio`
- `source_type` — upload/generated/edited/imported/commissioned/licensed_stock
- `provider/model nullable`
- `provider_request_id nullable`
- `prompt_hash nullable`
- `status` — pending/approved/deprecated/rejected
- `rights_status`
- `rights_metadata JSONB`
- `metadata JSONB`
- `created_at`, `updated_at`

Constraints/indexes:

- unique SHA256 for exact-byte dedupe unless there is a compelling alias requirement;
- index on kind/status;
- index on source_type;
- index on rights_status;
- trigram/full-text indexes for names/tags at the associated entity level;
- immutable `sha256`, `byte_size`, dimensions and storage key after asset creation;
- changing bytes creates a new asset row/version, never mutation-in-place.

### 9.1 Lineage

`asset_lineage`:

- `parent_asset_id`
- `child_asset_id`
- `relationship` — crop/edit/generated_from/composited_into/upscaled/colour_corrected/etc.
- `operation_metadata JSONB`
- `created_at`

This replaces fragile inference from filenames.

### 9.2 Tags

`tags` and `visual_asset_tags` support searchable reusable taxonomy:

- pub
- night
- red-bar
- 2.39
- expression-shout
- profile
- exterior
- rain
- car-park
- participant-neutral
- production-safe

## 10. Compatibility JSON and filesystem layout

Legacy JSON/manifests may remain during migration, but they are generated compatibility views of DB state, not competing truth.

Recommended rule:

- DB owns identity and relationships.
- Asset store owns bytes.
- JSON export is disposable/rebuildable.
- Git stores schema/code/canon, not production binaries.

Existing `studio/var/cast/...` and `studio/var/scene-references/...` paths may remain as compatibility mirrors initially. New code must resolve asset IDs through the DB rather than scan directories.

## 11. API surface

Suggested endpoints:

### Assets

- `POST /api/visual-assets` — upload/import asset
- `GET /api/visual-assets` — search/filter
- `GET /api/visual-assets/{id}`
- `PATCH /api/visual-assets/{id}` — mutable metadata only
- `POST /api/visual-assets/{id}/approve`
- `POST /api/visual-assets/{id}/deprecate`
- `GET /api/visual-assets/{id}/lineage`

### Cast

- `POST /api/characters`
- `GET /api/characters`
- `GET /api/characters/{id}`
- `PATCH /api/characters/{id}`
- `POST /api/characters/{id}/assets`
- `PATCH /api/characters/{id}/assets/{asset_id}` — role/order/state
- `DELETE` should normally mean detach/deprecate, not destroy bytes/history.

### Locations

- `POST /api/locations`
- `GET /api/locations`
- `GET /api/locations/{id}`
- `PATCH /api/locations/{id}`
- `POST /api/locations/{id}/assets`

### Scene masters

- `POST /api/scenes/{scene_id}/masters`
- `GET /api/scenes/{scene_id}/masters`
- `POST /api/scene-masters/{id}/approve`
- `POST /api/scene-masters/{id}/supersede`
- `POST /api/scene-masters/{id}/cast`

### Coverage

- `POST /api/scene-masters/{id}/coverage`
- `GET /api/scene-masters/{id}/coverage`
- `POST /api/coverage/{id}/approve-for-veo`
- `POST /api/coverage/{id}/attach-shot`

### Compatibility

- `POST /api/visual-library/export-legacy-manifests`

All create/update flows that touch bytes and DB metadata must be transactional from the caller's perspective. If byte persistence succeeds and DB insert fails, clean up the orphan or mark it for reconciliation. If DB insert succeeds but compatibility export fails, the DB remains authoritative and export can be retried.

## 12. Approval lifecycle

Suggested states:

`pending -> approved -> deprecated`

Alternative terminal state:

`pending -> rejected`

Scene master lifecycle:

`candidate -> approved -> superseded/deprecated`

No asset becomes canonical because it is newest.

Approval must be explicit and create an audit event containing:

- user;
- timestamp;
- asset ID;
- prior/new state;
- note/reason;
- relevant scene/character/location context.

Deletion of approved production assets should be strongly discouraged. Prefer deprecation. Bytes referenced by approved masters, coverage frames or completed production clips must not be hard-deleted.

## 13. Production-readiness gates

### Cast reference

- readable image;
- correct character;
- appropriate role assigned;
- explicit approval;
- rights/provenance known;
- SHA/dimensions persisted;
- not deprecated.

### Location base master

- rights permit production/derivative use;
- physical geography useful and believable;
- sufficient resolution;
- useful wide aspect/lateral coverage where applicable;
- no disqualifying HDR/irreversible treatment;
- provenance stored;
- explicit approval.

### Scene master

- location continuity correct;
- all named cast use approved canonical references;
- scene details/canon correct;
- physical scale believable;
- wardrobe/props/action correct;
- photographic treatment correct;
- parent/base lineage complete;
- explicit master ID + SHA lock;
- production-ready approval recorded.

### Coverage frame

- parent master approved;
- exact parent SHA matches;
- crop coordinates persisted;
- output SHA persisted;
- no unrecorded regeneration;
- approved for Veo where required.

## 14. Migration plan

### Phase 0 — inventory

Inventory all existing assets under:

- `studio/var/cast/*`
- `studio/var/cast-backups/*`
- `studio/var/scene-references/*`
- renderer-validation outputs that have explicit approved status/manifests
- existing generated `ImageAsset` rows where relevant

For every binary calculate/verify SHA256, dimensions, MIME and size.

Do not infer approval from timestamp.

### Phase 1 — schema

Add migrations for:

- `visual_assets`
- `asset_lineage`
- `characters`
- `character_asset_links`
- `locations`
- `location_asset_links`
- `scene_masters`
- `scene_master_cast`
- `coverage_frames`
- tags and rights/audit extensions as required.

Reuse the existing PostgreSQL, UUID, SQLAlchemy, audit and asset-storage patterns.

### Phase 2 — ingest current cast

Create Damo, Brock and Emma character rows.

Ingest existing full/head images as approved references with exact hashes.

Ingest Damo's third/expression image as an `expression_bridge` (or more specific role after human confirmation). Do not overwrite either existing Damo primary reference.

Generate legacy `var/cast/...` compatibility files from DB records until renderer code is migrated.

### Phase 3 — ingest current scene masters

Create scene/master records for approved assets only. Current `composition-gpt.*` names are not enough; the migration requires explicit human mapping of which file is approved where ambiguity exists.

Persist parent SHA/lineage from existing manifests where trustworthy.

### Phase 4 — coverage migration

Import existing coverage `frame.png + manifest.json` records, verify the stored source SHA against the corresponding imported master and preserve exact crop coordinates.

### Phase 5 — cutover

Update renderer/prompt/Veo code to resolve explicit DB asset IDs.

After cutover:

- no directory scanning for `latest`;
- no fixed six-slot cast contract;
- no scene master resolved only by filename;
- JSON manifests are compatibility/export artefacts.

## 15. UI implementation phases

### Phase A — Cast library first

Reason: immediate pain is visible and bounded.

Deliver:

- Cast navigation;
- Damo/Brock/Emma DB records;
- unlimited reference uploads;
- role/order/approval/deprecation;
- third Damo image ingestion;
- compatibility export;
- duplicate SHA warnings.

Acceptance: user can add a fourth Damo image without code changes, mark it `shouting`, approve it, and the renderer can lock that exact asset by ID/SHA.

### Phase B — Locations / scouting

Deliver:

- location/sub-location CRUD;
- location asset gallery;
- rights/provenance fields;
- wide/base-master approval;
- filters/tags;
- location compare/contact sheet.

Acceptance: user can select one approved participant-neutral widescreen pub back-room plate as a reusable base master for multiple scenes.

### Phase C — Scene Masters

Deliver:

- build scene from location + cast references;
- explicit candidate/master promotion;
- cast/location relationships;
- lineage panel;
- production-readiness gate.

Acceptance: every production master resolves by DB master ID and immutable SHA, never newest filename.

### Phase D — Coverage integration

Move the existing virtual-camera tool onto Scene Master IDs.

Acceptance: save multiple named 9:16 crops from one 2.39 master; each DB row reproduces the exact output byte-for-byte from the parent master and coordinates.

### Phase E — production integration

Veo job creation requires an approved Coverage ID or explicitly approved Scene Master ID. Prompt/job manifests embed all relevant IDs/SHAs and parent lineage.

Acceptance: a Veo run cannot resolve a deprecated/replaced/newest-lookalike asset by accident.

## 16. Tests

Minimum automated tests:

- duplicate SHA ingestion;
- immutable binary metadata;
- cast asset role ordering;
- deprecation without destructive deletion;
- rights-state gate for production base masters;
- master approval requires valid linked asset;
- coverage refuses parent SHA mismatch;
- coverage coordinates reproduce expected SHA;
- production resolver accepts explicit asset/master IDs only;
- no `latest file` selection path;
- compatibility export deterministic from DB;
- migration preserves existing hashes;
- audit event emitted for approval/deprecation;
- API transaction rollback on storage/DB failures.

Visual/manual acceptance:

- contact-sheet browsing remains practical with hundreds/thousands of assets;
- lineage from Veo seed back to coverage -> scene master -> location base/cast references is visible in one inspector;
- user can identify whether an asset is real photograph, generated, commissioned or licensed without opening filesystem manifests.

## 17. Scouting collection strategy

Build the library deliberately rather than scraping random pretty photographs.

For each recurring World type, create a shot list of reusable locations and collect a small set of genuinely useful spatial plates:

- pub back room;
- front bar;
- side street;
- takeaway exterior;
- residential car park;
- ute/tray environment;
- suburban house/party spaces;
- beach/coastal locations;
- festival/footy/BBQ environments as future Worlds require.

For important interiors, aim for at least:

- one primary ultrawide lateral plate;
- one reverse or alternate lateral plate;
- one neutral lighting/detail survey;
- scale/reference measurements.

The goal is not a stock-photo folder. It is a reusable virtual location department.

## 18. Major architectural decision

Do **not** build a separate cast database, location database and scene-master database with separate file stores.

Use one `visual_assets` substrate plus relational domain entities/links. This keeps SHA/provenance/rights/lineage consistent across every class of production image and reuses the existing Studio PostgreSQL + asset-storage architecture.

The existing renderer upload forms and coverage tool become transitional utilities. Their strongest behaviours — validation, SHA locking, persistent storage and original-pixel coverage — should be preserved. Their fixed filesystem identity model should be retired.

## 19. Definition of done

The Visual Asset Library is complete when:

1. every canonical cast photo is represented in PostgreSQL;
2. Damo can have three, four or twenty reference images with explicit roles;
3. a user can upload/manage these from Studio without editing JSON or folders;
4. locations and scouting plates are searchable reusable assets;
5. approved base/scouting masters carry rights/provenance;
6. every approved scene master is a DB object linked to its location and cast;
7. masters are preferentially wide enough for multiple 9:16 observations;
8. coverage frames store exact coordinates and parent SHA lineage;
9. Veo consumes explicit approved asset IDs, never `latest`;
10. every production clip can be traced backwards through coverage, scene master, location/base plate and cast references;
11. deprecated assets remain historically resolvable;
12. the filesystem is storage, not the creative source of truth.
