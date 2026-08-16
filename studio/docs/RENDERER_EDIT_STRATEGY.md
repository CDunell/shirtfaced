# Renderer Edit Strategy

Status: working production guidance derived from World 01 renderer validation.

## Core rule

Do not ask one image call to solve composition, identity, continuity, wardrobe, lighting, props and action simultaneously.

Treat the approved/master image as the owner of scene truth. Later image calls are controlled edits with explicit ownership.

## Ownership hierarchy

1. **Master image owns** camera position, framing, perspective, depth, lighting distribution, environment geometry, crowd/object placement, pose, physical contact, occlusion, accidental photographic character and overall realism.
2. **Head identity reference owns** face, hairline, hair, facial proportions, stubble and recognisable identity only.
3. **Expression-matched identity bridge owns identity in the target expression/head pose** when the neutral canonical headshot is too far from the scene performance.
4. **Full-body identity reference owns** build/body proportions only when a body correction is genuinely required. Do not include it during a head-only edit.
5. **Scene text owns** only facts missing from or demonstrably wrong in the current master.
6. **Approved output becomes the next master.** Do not regenerate from scratch after a successful stage.

## Staged pipeline

`MASTER -> IDENTITY_EDIT -> FACT_CORRECTION -> LIGHTING_CAMERA_CORRECTION -> MANUAL STILL APPROVAL -> VEO I2V -> MANUAL FINAL APPROVAL -> CONTINUITY ASSET`

Each image stage must declare:

- `preserve`: properties that must not change.
- `change`: the smallest permitted edit class.
- reference roles, e.g. `locked-master-image`, `head-identity-only`, `body-build-only`, `expression-matched-identity`.
- exact input checksums.
- manual gate after the output.

## Editing discipline

Use edit language, not generation language:

- `IMAGE 1 IS THE LOCKED MASTER.`
- `Change only X.`
- `Keep everything else unchanged.`
- `Do not improve, clean up, rearrange or reinterpret the scene.`

Prefer one narrow edit per call. If identity transfer fails, narrow further before adding more references.

### Identity order

1. Master only: prove the model can preserve/reframe the source.
2. Master + head reference: replace face/head identity only.
3. If identity is still too weak, expand the permitted identity boundary deliberately (for example entire head + visible neck) while locking geometry below that boundary.
4. If the target expression is extreme and canonical identity is neutral, create an **expression bridge** from the canonical headshot: same person, target head pose/expression, neutral studio context. Use that bridge as the identity authority in the scene edit.
5. Add full-body reference only if build is still wrong and a body edit is genuinely necessary.
6. Add additional cast one character at a time.

Do not supply unrelated character references to a call that is editing only one person.

### Expression-matched identity bridges

A neutral canonical headshot can become weak identity evidence when the target scene has an extreme expression, severe head tilt, closed eyes, open mouth or partial occlusion. The model may preserve the source face because the pose mismatch is too large.

When that happens:

1. Derive a temporary identity bridge from the canonical headshot only.
2. Change only head pose/expression to match the target performance.
3. Preserve identity, age, hair, stubble, skin and wardrobe in the bridge.
4. Review the bridge itself before using it downstream.
5. Use the bridge as the authoritative identity reference in the bounded scene edit.
6. Keep the original canonical image untouched; the bridge is a cached derivative with provenance/checksum.

This pattern is reusable for shouting, laughing, sleeping, profile views, head-back poses, down-looking poses and other identity-hostile expressions.

### Bounded edit authority

When the model over-preserves the source identity, define a hard edit boundary instead of relaxing the entire image:

- outside the boundary: master image has full authority;
- inside the boundary: canonical/bridge identity reference has full authority;
- explicitly state that preserving the source face inside the boundary is a failure;
- preserve expression/head angle/performance separately from identity;
- never broaden authority to body, wardrobe, lighting or scene geometry unless that class is the next deliberate edit stage.

For especially difficult identity edits, a localized crop can be sent to the model and feather-composited back into the untouched master. This guarantees that the wider crowd, props, camera geometry and lighting cannot drift during the identity edit.

## Documentary realism rules

For SHIRTFACED World 01, photographic imperfections are scene truth, not defects. Preserve:

- foreground obstruction and clipped bodies;
- asymmetric/uncomfortable poses;
- crowd collisions and physical contact;
- uneven visibility and deep shadows;
- awkward framing and close-range distortion;
- motion blur / exposure imperfection when present;
- subjects not acknowledging the camera;
- lack of clean visual separation around the hero.

Avoid instructions that encourage beautification, balanced composition, evenly readable faces, broad ambient fill or a protected hero silhouette.

## Social format

Generate/edit vertical-first for the World 01 social pipeline:

- master aspect ratio: 9:16;
- keep essential action within a central 4:5-safe region where practical;
- do not create landscape masters and crop later unless a scene specifically requires it.

## Veo handoff

There is no requirement that the still be generated by a Google image model. Veo receives an approved image as the first frame. The still generator is selected on accepted-seed quality and keeper cost.

Veo prompts should describe **change through time only**. Do not redescribe identities, location or style already locked in the approved first frame. Explicitly preserve role/geography when semantic ambiguity exists (for example, audience member versus stage performer).

## Cost metric

Optimise for cost per accepted finished clip, not individual call price:

`(all still attempts + all video attempts) / accepted final clips`

Track model, resolution, attempts, rejection reason, provider operation ID, input/output checksums and manual acceptance for each stage.

## Pub 11:05 findings that generalise

- Fresh generation with many references tends to sanitise/recompose the event.
- A strong master image supplied as a locked edit source preserves realism far better.
- Composition reference + six identities in one call diluted both composition fidelity and identity.
- Master-only preservation worked strongly.
- Master + Damo full-body + head preserved the event but identity remained weak.
- Head-only and bounded head/neck edits preserved the event but the neutral reference still allowed too much source-identity retention.
- Local crop editing successfully froze the wider scene but did not materially improve identity by itself.
- A Damo expression bridge generated from the canonical headshot preserved Damo strongly while matching the target head-back / eyes-closed / mouth-open performance.
- Using that expression-matched bridge as the local identity authority produced the strongest scene-level Damo match so far without sacrificing scene realism.

The exact pub pose, lighting and props are scene-specific. The staged ownership/edit strategy is pipeline-wide and should be applied to ute-0341, takeaway-0230, side-street-2126 and continuity-bridge.
