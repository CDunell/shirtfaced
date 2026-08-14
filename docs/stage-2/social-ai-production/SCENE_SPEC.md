# shirtfaced — Campaign Scene Specification

**Status:** ACTIVE contract  
**Scope:** Approved story version to scene-level production plan

---

## 1. Scene purpose

A scene is a continuity boundary inside a campaign story. It groups action that shares a coherent place/time/state and supplies the context required for one or more shots.

A scene is not a social post and not every campaign shot requires a scene. ADR-017 explicitly permits campaign-native inserts, plates, transitions and similar shots with `scene_id = NULL`.

---

## 2. Required scene identity

Each scene has:

- UUID primary key
- campaign FK
- approved story-version FK
- stable scene code, e.g. `CAMP01-S03`
- sequence number
- title
- story purpose
- status / approval state

Scene codes are human-facing stable references; UUID remains database identity.

---

## 3. Required production state

Each scene records or resolves:

- location FK
- time-of-day / time-state
- lighting state
- weather/environment state where relevant
- participating characters
- applicable character appearances / wardrobe states
- action beats
- dialogue intent
- ambient sound / music intent
- key props
- vehicles where relevant
- continuity-in state
- continuity-out state
- candidate post roles
- presentation/directing language

Core relationships must be relational where identity matters. JSONB may carry evolving snapshots and action maps.

---

## 4. Scene-character relationship

Use a relational `scene_characters` association.

It should support:

- scene FK
- character FK
- appearance/wardrobe FK where applicable
- role in scene
- entrance state
- exit state
- blocking notes
- dialogue/performance notes

Do not store participating characters only as an unvalidated JSON array.

---

## 5. Continuity-in / continuity-out

A scene explicitly declares what must be true on entry and what changes by exit.

Typical continuity state:

- character presence
- character appearance / wardrobe
- garment layer state
- dirt / wetness / damage
- carried objects
- drink/food/prop state
- vehicle presence / position
- location state
- lighting/time progression
- emotional / behavioural state

The next scene may derive expected continuity from the prior scene's output but still persists its own required input snapshot. This makes mismatches inspectable rather than implicit.

---

## 6. Spatial contract

For locations where multiple angles need continuity, the scene should resolve:

- canonical location reference assets
- floorplan/spatial description where useful
- entrances/exits
- important fixed objects
- screen-direction axis where relevant
- light-source positions
- vehicle/prop positions

The goal is not architectural CAD. It is enough stable spatial truth to stop independent generations from silently rearranging the room or reversing action.

---

## 7. Shot derivation

Scene planning produces candidate shots with explicit purpose.

Each derived shot must answer:

- what story information this shot adds
- whether motion is required
- which characters are visible
- expected character/wardrobe state
- which garment exposure class applies
- camera intent
- entry/exit continuity anchors where needed
- likely edit role

A scene should not accumulate coverage because generation is cheap. Every planned shot needs a plausible editorial role.

---

## 8. Approval rule

A scene may be approved only when:

- it belongs to the active approved story version
- location and participating characters resolve to persisted records
- wardrobe/appearance state is resolvable
- continuity-in/out is coherent
- its action does not invent a material story event absent from the approved story
- candidate shots can be specified without guessing core facts

Material scene changes after approval create a new/revised scene plan or return the story version for revision where the story itself changed.

---

## 9. Scene-level audit fields

Persist:

- created/updated timestamps
- source/origin
- approval state
- approver
- review/revision reason
- structured provenance for AI-assisted planning where used

Rejected or superseded scene plans remain traceable rather than disappearing.
