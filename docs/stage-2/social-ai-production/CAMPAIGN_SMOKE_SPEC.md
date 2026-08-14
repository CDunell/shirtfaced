# shirtfaced — Campaign Production Smoke Contract

**Status:** ACTIVE implementation gate  
**Scope:** Concrete production verification for campaign/story/video world pipeline

---

## 1. Purpose

The campaign pipeline is not considered implemented because routes return success, ORM classes import, or a React page renders.

The smoke chain must prove concrete persisted facts against the deployed system.

It follows the standard established by `smoke_design_chain.py`: assert counts, lineage, stored metadata and real bytes/relationships where applicable.

---

## 2. Required smoke chain

A deployment-level campaign smoke must exercise or inspect the following chain:

`campaign -> story version -> character/appearance -> location -> scene -> campaign-native shot -> generation attempt -> media asset -> automated review -> human decision -> edit version -> social linkage`

Performance ingestion may be separately smoke-tested once a real platform source exists.

---

## 3. Campaign assertion

Create or use an isolated smoke campaign and assert:

- campaign row exists
- `world_id` resolves to a real world
- campaign slug/code is unique
- target platform/cycle metadata is persisted
- campaign status is expected

Do not assert only that POST returned 201.

---

## 4. Story assertion

Persist a story version and assert:

- campaign FK is correct
- version number is correct
- structured story/beat payload is non-empty
- approval state is persisted
- parent/version lineage behaves correctly when a second version is created

If approved versions are immutable, the smoke must attempt the forbidden mutation or otherwise exercise the invariant through a focused integration test.

---

## 5. Character and wardrobe assertion

Persist one synthetic character and one appearance and assert:

- character belongs to campaign
- appearance belongs to character/campaign
- garment/design reference resolves where the smoke uses one
- reference media association is purpose-tagged where required
- scene/shot resolution returns the expected appearance

Do not merely count one character row.

---

## 6. Location/scene assertion

Persist one location and one scene and assert:

- location belongs to campaign
- scene belongs to campaign and approved story version
- scene location FK is correct
- scene character relationship resolves
- continuity-in/out payload survives round-trip

---

## 7. Dual-provenance shot assertion

The smoke must prove ADR-017 rather than only campaign creation.

Assert a campaign-native shot has:

- non-null world ID
- non-null campaign ID
- expected scene ID for a scene-bound smoke shot
- `source = campaign_native`
- `source_line = NULL`
- deterministic external ID
- video media intent
- non-empty camera/action specification

Also inspect an existing Markdown-seeded shot and assert:

- campaign ID is NULL
- scene ID is NULL
- source is Markdown provenance after migration/backfill
- source line remains intact

This catches migrations that accidentally force campaigns/scenes onto legacy photography.

---

## 8. Generation-attempt assertion

Create or inspect a smoke generation attempt and assert:

- shot FK is correct
- modality is video for the campaign smoke
- provider/model/settings are persisted
- duration/FPS/output spec survive round-trip
- exact prompt is persisted
- reference manifest is persisted
- parent attempt linkage works for a variation/retry

The smoke does not need to spend money on a live provider call if the workflow supports imported/manual generation. It must still exercise the same persisted attempt path.

---

## 9. Media-asset assertion

Attach a deterministic small fixture asset through the real asset-store path and assert:

- `media_assets` row exists
- stable relative/object path resolves
- bytes actually exist and are readable
- SHA-256 matches the stored row
- MIME type is correct
- dimensions and/or duration metadata are concrete
- asset points to the expected attempt

A path string without readable bytes is failure.

---

## 10. Review assertion

Persist/execute a deterministic test review and assert:

- review points to the expected attempt
- rubric ID/version are present
- applicable hard gates are structured data
- applicable `not_tested` blocks recommendation/release
- video-only gate appears for video smoke
- a non-applicable gate is not fabricated as `not_tested`
- category data round-trips
- review leaves attempt awaiting human decision rather than approving it

Historical-review migration behaviour belongs in migration/integration tests, not only this end-to-end smoke.

---

## 11. Human-decision assertion

Record a deterministic human decision and assert:

- it belongs to the reviewed attempt
- only one decision exists where the existing invariant requires one
- attempt reaches the expected terminal/next state
- variation retains parentage semantics where tested

---

## 12. Edit assertion

Create one edit version from approved/selected source media and assert:

- campaign FK correct
- source-shot association exists relationally
- output asset resolves if an edit fixture is used
- duration/aspect/role persisted
- version lineage works
- approval state persisted

---

## 13. Social lineage assertion

Create or inspect a social package linked to the smoke campaign/edit and assert backward traceability:

`social post -> edit -> source shot -> attempt -> campaign`

Where publication is exercised, extend to:

`publication job -> derivative -> social post -> edit -> shot -> attempt -> campaign`

The smoke should print IDs/short codes in its success output so failures can be investigated directly.

---

## 14. Cleanup/isolation

The smoke must not pollute normal production queues.

Use a stable smoke/test marker and either:

- transaction/fixture cleanup where safe, or
- clearly isolated records excluded from selectors/publish queues

Never create a publishable live social job as a side effect of deployment smoke.

---

## 15. Failure output

Each check reports:

- what concrete fact was expected
- what was actually found
- the relevant campaign/shot/attempt ID where available

Avoid checks such as `response == response`, generic truthiness, or only HTTP status assertions.

---

## 16. Minimum deployment success output

A successful campaign smoke should be able to report facts of this form:

```text
ok  campaign persisted                 CAMP-SMOKE, world <slug>, 1 active story
ok  character continuity resolves      1 character, 1 appearance, garment <ref>
ok  scene continuity resolves          S01, location <code>, 1 participant
ok  dual shot provenance holds         campaign shot + markdown shot verified
ok  video attempt provenance holds     provider/model, duration/FPS, N references
ok  media bytes are real               <sha-prefix>, <mime>, <dimensions/duration>
ok  rubric is applicable               N gates, M categories, video gates present
ok  human gate remains human           awaiting decision -> <decision>
ok  edit lineage resolves              edit v1 -> N source shot(s)
ok  social lineage resolves            post -> edit -> shot -> attempt -> campaign
```

Counts are examples; the implemented smoke prints the real values it proves.
