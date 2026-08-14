# shirtfaced — Unified Shot Specification

**Status:** ACTIVE contract  
**Scope:** One production shot across still and video modalities  
**Governing decisions:** ADR-016, ADR-017

---

## 1. Definition

`shots` is the single directing unit for both still and video production.

A still is a shot with no temporal requirement. A video shot adds duration, motion and temporal continuity requirements; it does not become a different domain object.

The shot row is the production contract consumed by generation tooling. A generator may elaborate provider syntax but must not invent undocumented story, wardrobe, camera or continuity facts.

---

## 2. Identity and provenance

Every shot has:

- UUID identity
- non-null `world_id`
- stable `external_id`
- sequence
- priority
- status
- source provenance

Two source modes are required:

### Markdown-seeded

- source `markdown_import`
- `campaign_id = NULL`
- `scene_id = NULL`
- source line from `SHOTLIST.md`

### Campaign-native

- source `campaign_native`
- non-null campaign FK
- nullable scene FK
- `source_line = NULL`
- deterministic human-readable external ID

Campaign-native non-scene shots are legitimate for inserts, plates, title-card sources, transitions, CCTV cutaways, generic aftermath and similar editorial material.

---

## 3. Media intent

Required media intent:

- `still`
- `video`
- `either`

Temporal fields are required only when the selected production mode needs them.

For video-capable shots support:

- intended duration
- intended FPS / motion cadence intent where meaningful
- first-frame continuity requirement
- last-frame continuity requirement
- movement/action progression
- edit-in intent
- edit-out intent
- still-extraction potential

---

## 4. Camera contract

A campaign-native production shot should be able to resolve:

- shot size: ECU / CU / MCU / MS / MLS / WS / EWS or equivalent
- camera height
- horizontal camera position
- camera angle / pitch intent
- focal length or FOV intent
- camera movement
- movement speed / character where needed
- framing bias
- focus target
- depth-of-field intent
- foreground obstruction / texture intent
- safe-crop / alternate-aspect requirements

Camera terminology expresses intent rather than pretending AI providers reproduce physical optics perfectly.

---

## 5. Blocking and action

Persist structured blocking sufficient to reproduce spatial relationships:

- character positions
- facing directions
- direction of travel
- eyelines
- entrances/exits
- foreground action
- midground action
- background action
- prop interactions
- timing/order of action for video

JSONB is appropriate for the blocking map; character identity itself remains relational.

---

## 6. Character relationship

Use a relational `shot_characters` association.

It should support:

- shot FK
- character FK
- appearance/wardrobe FK where applicable
- prominence / framing class
- expected position
- action
- eyeline
- continuity notes

This makes character identity queryable and reviewable across shots.

---

## 7. Garment/product exposure

Each relevant shot declares garment treatment rather than leaving product visibility to chance.

Supported exposure classes:

- `hero_readable`
- `clearly_present`
- `partial`
- `atmospheric`
- `absent`

Where applicable also persist:

- wearer
- garment / approved-design reference
- visible side: front / back / left chest / sleeve / other
- approximate scale in frame
- artwork-legibility requirement
- acceptable occlusion
- layer state

Most shots should not require hero readability. Product naturalism is part of the directing contract.

---

## 8. Lighting and environment

Resolve:

- scene/location lighting state
- practical light sources
- dominant direction
- contrast/exposure intent
- colour-temperature intent where useful
- weather/environment state
- required continuity with adjacent shots

Existing `lighting_source` remains a valid compact field for legacy photography but campaign shots may require richer structured specification.

---

## 9. Continuity anchors

A shot may reference approved media assets as:

- character identity references
- wardrobe/garment references
- location references
- prop/vehicle references
- first-frame anchor
- last-frame anchor
- style/presentation references

Reference relationships must record their purpose. A flat list of asset IDs is insufficient once the same shot uses several reference classes.

---

## 10. Generation prompt contract

The shot's production prompt is derived from persisted state and should contain, where applicable:

- world/campaign context required for this shot
- scene fact summary
- character identity and current appearance
- location state
- exact action
- camera/framing/movement
- lighting/environment
- garment exposure requirement
- continuity anchors
- negative constraints / forbidden drift

Prompt provenance includes template/version and human edits.

The prompt is a projection of the shot contract, not the source of truth for facts already represented structurally.

---

## 11. Negative constraints

Shot-level forbidden conditions may include:

- character identity drift
- garment artwork mutation
- front/back artwork reversal
- added brand marks/logos
- wrong vehicle/prop
- altered room geometry
- camera acknowledgement when documentary behaviour is required
- duplicated/missing people
- impossible anatomy/structure
- changed weather/time state
- screen-direction reversal

Global/provider safety or technical negatives may be added separately by generation adapters.

---

## 12. Edit intent

Shot planning may declare editorial purpose:

- establishing
- action
- reaction
- insert
- transition
- hero garment
- evidence/found-footage
- aftermath
- title-card source
- cutaway

It may also declare candidate post roles from the canonical cycle.

This information helps editing and performance analysis but does not hard-bind one source shot to one post.

---

## 13. Acceptance before generation

A campaign-native shot is generation-ready only when:

- campaign exists
- world exists
- scene exists if the shot claims a scene
- scene and shot campaign IDs agree
- character references resolve
- applicable appearance/wardrobe resolves
- location/continuity state is sufficient
- media intent is known
- camera/action requirements are specified to the level needed
- garment exposure is explicit where product is relevant
- required reference assets exist
- prompt can be generated without inventing material facts

Generation-readiness is state, not inferred merely because a prompt string exists.
