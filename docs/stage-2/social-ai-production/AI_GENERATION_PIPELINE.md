# shirtfaced — AI Media Generation Pipeline

**Status:** ACTIVE production contract  
**Scope:** Persisted shot specification through generated media, review and selection

---

## 1. Governing rule

Generation is an execution step inside the persisted production system.

The generator does not own story, character, wardrobe, location, camera or approval state. It consumes a resolved shot contract and returns media plus provenance.

No campaign-native generation attempt exists without:

- persisted campaign
- persisted shot
- resolved required references
- persisted production prompt / settings provenance

---

## 2. Generation modes

The system must support provenance for at least:

- manual paid UI generation
- API generation
- local generation
- imported externally generated media

The workflow may favour paid interfaces to avoid duplicate API spend, but provenance remains explicit whichever path produced the bytes.

Manual generation is not an untracked gap. Studio owns the brief, shot, prompt, handoff package, returned asset, review and decision even when another UI makes the pixels.

---

## 3. Generation-ready resolution

Before creating an attempt, resolve and freeze:

- world/campaign identity
- active approved story version where campaign-native
- scene facts where scene-bound
- shot specification
- character identities
- current character appearances/wardrobe
- location identity/state
- garment/design references
- prop/vehicle state
- camera/framing/motion requirements
- first/last-frame anchors where required
- negative constraints
- provider/model/settings

If required state cannot resolve, do not create a fake complete prompt. The shot remains not-ready with a concrete missing requirement.

---

## 4. Attempt creation

Each generation attempt records:

- shot FK
- world FK
- campaign/scene lineage derivable from the shot and optionally snapshotted where needed
- parent attempt FK for retry/variation chains
- attempt number
- state
- selection rationale
- exact production prompt
- prompt-plan JSON
- provider
- model/model version
- modality
- output specification
- quality preset
- format
- duration/FPS where applicable
- seed where available
- generation source
- provider request/job ID
- provider-specific settings JSONB
- reference-input manifest
- first-frame input asset FK where applicable
- last-frame input asset FK where applicable
- relevant document/story/continuity hashes or version IDs
- failure code/message
- timestamps
- cost/credit metadata where observable

The attempt snapshots what was asked for. Editing the shot later does not rewrite history.

---

## 5. Reference manifest

Reference inputs are purpose-tagged and frozen per attempt.

Reference classes may include:

- character identity
- full-body character
- current wardrobe front
- current wardrobe back
- garment/design artwork
- location exterior/interior
- location geometry
- prop/vehicle
- first-frame anchor
- last-frame anchor
- adjacent approved shot
- presentation/style reference

The manifest records asset ID, purpose and any weighting/priority supported by the provider.

Do not persist only provider-local temporary URLs as the sole reference provenance.

---

## 6. Prompt assembly

Prompt assembly projects persisted production state into provider-readable instructions.

The prompt should include only the context needed for this shot, while retaining exact requirements for:

- character identity/current appearance
- scene/location state
- action progression
- camera/framing/motion
- garment exposure
- continuity anchors
- forbidden drift

Prompt templates are versioned. Human edits after assembly are stored rather than replacing the generated source invisibly.

---

## 7. Still generation

A still attempt produces one or more media assets according to the explicit action and provider path.

The existing one-image-per-action principle remains unless separately changed by owner decision.

For each returned image record:

- stable media asset row
- object/path key
- hash
- MIME type
- dimensions
- byte size
- provider technical metadata where useful
- attempt lineage

---

## 8. Video generation

A video attempt additionally records and validates:

- requested duration
- actual duration
- requested/actual dimensions
- requested/actual FPS where supplied
- first-frame input
- last-frame input
- audio presence where applicable
- codec/container metadata where useful
- derived thumbnail/proxy/frame assets

Video is reviewed as media, not assumed valid because the provider job completed.

---

## 9. Continuity-aware batches

The orchestration layer may group work into batches for planning efficiency, but each attempt remains independently persisted.

Useful batch groupings:

- same character + same appearance + same location + same lighting
- same scene from multiple camera positions
- sequential actions sharing first/last-frame anchors
- companion stills after a video scene is stabilised

Batching must not erase attempt-level provenance or approvals.

---

## 10. First/last-frame continuity

For sequential video:

- the first-frame requirement is explicit
- the last-frame requirement is explicit
- approved anchor assets are stored and purpose-tagged
- the generated result's start/end compatibility is reviewed
- an extracted frame becomes an anchor only when deliberately selected/approved for that role

Do not chain generations by silently taking whatever last frame the model happened to emit.

---

## 11. Retry and variation

Retry/variation creates a child attempt rather than mutating the original.

Record the reason:

- technical failure
- character drift
- garment/artwork drift
- location drift
- structural defect
- motion defect
- anchor mismatch
- camera/framing miss
- owner-requested variation
- other structured reason + note

A retry may change prompt/settings/references, but the delta remains inspectable through parentage and attempt snapshots.

---

## 12. Asset lifecycle

Generated bytes live in file/object storage; `media_assets` owns metadata/provenance.

Asset lifecycle should distinguish where useful:

- generated/unreviewed
- reviewed
- selected
- rejected
- superseded
- approved reference/anchor
- edit master/derivative

Rejected media remains retained according to storage policy because it explains regeneration decisions and failure patterns.

---

## 13. Review handoff

After a valid media asset exists:

`attempt -> automated review -> awaiting decision -> human decision`

The generation orchestrator does not bypass review because a result appears visually good.

For manual-generation workflows, importing the returned asset triggers the same review/decision path as API-generated media.

---

## 14. Failure handling

Failures are classified and persisted.

Examples:

- provider unavailable
- provider rejected request
- timeout/job failure
- returned file unreadable
- invalid media metadata
- storage failure
- review failure
- generation completed but media structurally invalid

A review failure does not destroy valid returned media. A generation failure does not fabricate an asset row.

---

## 15. Cost and efficiency

Generation being cheaper or easier is not permission to produce undirected volume.

Track cost/credits when reliably observable so the system can later compare:

- attempts per approved shot
- rejection reason frequency
- provider/model efficiency
- cost per approved source asset
- continuity failure cost

Unknown cost is stored as unknown, not estimated as fact.

---

## 16. Audit invariant

Given any generated media asset, Studio must be able to identify:

- campaign/world/shot
- scene/story lineage where applicable
- exact attempt
- parent attempt if any
- exact prompt and human edits
- provider/model/settings
- exact references used
- first/last-frame inputs
- review result
- human decision

If that chain cannot be reconstructed, the generation workflow is incomplete.
