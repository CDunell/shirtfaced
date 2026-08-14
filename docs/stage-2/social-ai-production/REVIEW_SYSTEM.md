# shirtfaced — World Media Review System

**Status:** ACTIVE contract  
**Scope:** Automated review of still/video generation attempts and human decision handoff  
**Governing decision:** ADR-016

---

## 1. Decision

The world/media pipeline keeps its own `automated_reviews` table and its own rubric.

It does **not** merge with product `design_reviews`.

The two review domains share one structural idea:

- hard gates are data
- score categories are data
- rubric/version provenance is persisted
- the server evaluates the release/recommendation rules
- incomplete applicable evidence blocks release

A product design review and a world-media review answer different questions against different subjects. Sharing a table because both contain gates would make subject identity, lifecycle and rubric semantics unnecessarily polymorphic.

---

## 2. What changes from the current world judge

The current world judge persists physical columns for each rubric dimension, including:

- mood score
- Australian authenticity score
- product visibility score
- documentary credibility score
- story score
- branding compliant
- vehicle compliant
- structurally sound

That shape does not scale to video and continuity. Adding character, wardrobe, artwork, location, temporal, motion and frame-anchor gates as columns would make every future rubric change a schema migration.

`automated_reviews` therefore moves to rubric-shaped persisted data rather than column-per-gate storage.

---

## 3. Required persisted review shape

A world automated-review record should retain:

- review UUID
- generation-attempt FK
- rubric ID
- rubric version
- review schema version
- reviewer provider/model
- provider request ID where available
- `hard_gates` structured data
- `score_categories` structured data
- recommendation
- verdict
- strongest success
- material drift / summary
- recommended next action
- optional planning hints such as next product/camera only where still part of the workflow
- raw reviewer payload for audit/debugging
- relevant canon/document hashes
- created timestamp

The existing immutable-review behaviour remains: re-review creates another review; history is not overwritten.

---

## 4. Hard-gate contract

Each emitted hard gate carries at minimum:

- stable `id`
- human-readable `label`
- `result`
- `evidence`

Supported result vocabulary should be explicit and shared by the world review contract. At minimum:

- `pass`
- `fail`
- `not_tested`

If the world domain retains an `uncertain` state, it must be defined deliberately and its effect on recommendation/release must be explicit rather than inferred.

`not_tested` means an **applicable** gate lacked evidence and therefore blocks release/approval recommendation.

A gate that does not apply to the shot/media type is **not emitted merely to become `not_tested`**. Applicability is resolved before evaluation.

---

## 5. Score-category contract

Each score category carries at minimum:

- stable `id`
- label
- score
- maximum
- minimum required where applicable
- evidence / explanation where useful

Thresholds and weighting live in one rubric definition, not duplicated between prompt builder, parser, service and UI.

The server owns deterministic evaluation from returned gate/category data to recommendation/verdict. The reviewer model does not permanently approve its own output.

---

## 6. Rubric applicability

Rubric definitions declare which media/shot contexts each gate applies to.

Applicability selectors may include:

- still
- video
- either
- campaign-native only
- scene-bound only
- character-present only
- garment-present only
- first-frame anchor required
- last-frame anchor required
- vehicle-present only
- location-continuity required

Applicability is deterministic application logic derived from persisted shot/context state. The reviewer is not asked to decide whether a contractual requirement existed.

---

## 7. Core world/media gate families

The exact rubric can evolve as data. Initial families should cover the existing judge plus the new continuity/video requirements.

### Canon and brand

- world/canon fit
- mood/presentation fit
- Australian authenticity where applicable
- documentary credibility where required
- prohibited/foreign branding
- vehicle/prop compliance where relevant

### Structural quality

- physically/structurally plausible frame
- anatomy/object integrity
- duplicate/missing subject defects
- unreadable/corrupted required artwork

### Story and scene

- required story action present
- scene participation correct
- location/time state correct
- required prop/event state present
- no material story invention contradicting approved plan

### Character continuity

- character identity
- hair/facial-hair/body continuity
- current appearance/wardrobe
- accessory continuity
- dirt/wetness/damage state

### Garment fidelity

- correct garment/design
- correct colour
- correct front/back/placement
- artwork fidelity/orientation
- required visibility/legibility class
- acceptable occlusion

### Spatial and temporal continuity

- location geometry
- screen direction
- subject travel/facing direction
- prop/vehicle position
- time/lighting/weather continuity
- first-frame compatibility where required
- last-frame compatibility where required

### Motion/video quality

Only applicable to video or motion-derived assets:

- identity stability through motion
- garment/artwork stability through motion
- temporal object persistence
- interpolation/morphing defects
- impossible camera/subject motion
- frame-anchor adherence
- duration/action completion

---

## 8. Evidence source

The reviewer evaluates **stored media bytes plus persisted production state**.

It must not judge only the prompt.

Review context may include:

- shot specification
- scene continuity state
- character and appearance references
- location references
- garment/design references
- first/last-frame anchors
- relevant world canon excerpts
- exact production prompt for provenance/comparison
- prior adjacent approved media where continuity requires it

The existing principle in `review_service.py` survives: the generated media is the evidence; the prompt is context, not proof.

---

## 9. Measurement versus judgement

The world pipeline may have deterministic/vision measurement helpers that produce evidence before or alongside model review.

Examples:

- media dimensions/duration/FPS
- expected asset/reference availability
- exact hash/artwork comparisons where technically possible
- first/last-frame similarity metrics
- frame sampling
- detected duplicate/missing duration metadata

These helpers feed the world review contract. They do not reuse `design_extraction.py` wholesale, because print/design measurement and scene/video continuity are different evidence domains.

Generic low-level utilities should be shared only when an actual common primitive exists.

---

## 10. Recommendation and human decision

Automated review must never permanently approve or reject an attempt.

Its output ends in the existing handoff:

`GenerationAttempt -> AutomatedReview -> AWAITING_DECISION -> HumanDecision`

The human decision remains authoritative.

The review service must not:

- change canon directly
- alter approved story/scene facts
- approve/reject on the owner's behalf
- delete failed media
- silently rewrite shot requirements

Canon proposals remain proposals and follow the existing canon approval process.

---

## 11. Re-review

A re-review creates a new immutable `automated_reviews` row with its rubric version and reviewer provenance.

Changing the rubric does not rewrite historical reviews.

History must make it possible to answer:

- which rubric judged this attempt
- which model judged it
- what evidence it returned
- what human decision followed

---

## 12. UI contract

The world review UI should render from the returned/persisted rubric data rather than hard-code every gate label in the component.

It should clearly separate:

- applicable hard gates
- blockers
- score categories
- strongest success
- material drift
- reviewer recommendation
- human decision controls

Video-only gates do not clutter still reviews when they were not applicable.

---

## 13. Migration constraints

The eventual `automated_reviews` migration must preserve historical review meaning.

Before migration implementation, explicitly decide and test how existing physical columns map into the new structured gate/category representation. Historical rows cannot simply lose their scores/compliance results because the schema got cleaner.

The migration belongs to the world session. Product `design_reviews` remains untouched.
