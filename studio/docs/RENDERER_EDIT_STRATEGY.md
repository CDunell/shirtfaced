# Renderer Edit Strategy

Status: working production guidance derived from World 01 renderer validation.

## Core rule

Do not ask one image call to solve composition, identity, continuity, wardrobe, lighting, props and action simultaneously.

Treat the approved/master image as the owner of scene truth. Later image calls are controlled edits with explicit ownership.

**World 01 is scene-first, not hero-first.** A named character's action happens inside a fully realised event. Character fidelity must never cause the room, crowd, geography, secondary action or photographic accident to collapse into supporting scenery.

### Hard invariant: character work may not change scene hierarchy

Character development is required per scene, but it is a continuity layer inside the scene, never the organising principle of the scene. Identity work that improves a face while reducing room detail, crowd entropy, competing actions, occlusion, depth or incidental behaviour is a failed edit.

A scene must remain compelling if the named character is mentally removed from it. The world is already happening; the character incident is discovered inside that world.

## Two continuity layers

Every candidate must preserve and score two independent layers:

1. **Scene continuity** — environment, crowd density, distributed independent action, lighting, geography, props, occlusion, camera accident, foreground obstruction, secondary/tertiary events, depth and overall energy.
2. **Character continuity** — identity, build, wardrobe and the required action of named characters.

Character continuity is subordinate to scene continuity. A recognisable character performing the correct action is still a rejection if the surrounding world has become visually organised around them.

## Attention hierarchy

Do not confuse narrative importance with photographic dominance. Named characters may be narratively important while remaining only one event among many in the frame.

For crowd/event scenes, require:

- multiple simultaneous actions that do not involve the named character;
- people looking and moving in different directions;
- foreground bodies and occlusion that compete with the hero;
- no clean halo or protected negative space around the hero;
- no crowd semicircle, audience formation or supporting-cast arrangement around the hero;
- independent social clusters and reactions;
- scene energy that would still exist if the hero were removed from the frame;
- secondary people may be cropped, blurred, turned away, partially hidden or doing something unrelated;
- the named character must not become the implied source of everyone else's emotion unless explicitly required by the scene.

Add **attention distribution / scene richness** as a manual QC dimension alongside identity, action, geometry and lighting.

For `pub-1105`, the required hierarchy is:

`ROOM GOING OFF > ACCIDENTAL CROWD PHOTOGRAPH > MULTIPLE SIMULTANEOUS INTERACTIONS > DAMO POOL-TABLE INCIDENT > DAMO IDENTITY`

Damo is not the singer, leader, performer or gravitational centre of the room. He is a punter doing something ridiculous inside an already-chaotic Friday-night pub. The crowd must not appear to sing to him, cheer for him, watch him as a performance, or form an audience around him. Some people can notice him; many should remain occupied with their own Friday-night interactions.

## Ownership hierarchy

1. **Master image owns** camera position, framing, perspective, depth, lighting distribution, environment geometry, crowd/object placement, pose, physical contact, occlusion, accidental photographic character, attention distribution and overall realism.
2. **Head identity reference owns** face, hairline, hair, facial proportions, stubble and recognisable identity only.
3. **Expression-matched identity bridge owns identity in the target expression/head pose** when the neutral canonical headshot is too far from the scene performance.
4. **Full-body identity reference owns** build/body proportions only when a body correction is genuinely required. Do not include it during a head-only edit.
5. **Scene text owns** only facts missing from or demonstrably wrong in the current master.
6. **Approved output becomes the next master only if scene-richness QC still passes.** Identity improvement alone is not sufficient promotion.

## Staged pipeline

`SCENE_MASTER -> SCENE_RICHNESS_GATE -> IDENTITY_EDIT -> SCENE_RICHNESS_RECHECK -> FACT_CORRECTION -> LIGHTING_CAMERA_CORRECTION -> MANUAL STILL APPROVAL -> VEO I2V -> MANUAL FINAL APPROVAL -> CONTINUITY ASSET`

Each image stage must declare:

- `preserve`: properties that must not change;
- `change`: the smallest permitted edit class;
- reference roles, e.g. `locked-master-image`, `head-identity-only`, `body-build-only`, `expression-matched-identity`;
- exact input checksums;
- manual gate after the output;
- scene-richness/attention-distribution status before promotion.

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
3. If identity is still too weak, expand the permitted identity boundary deliberately while locking geometry below that boundary.
4. If the target expression is extreme and canonical identity is neutral, create an **expression bridge** from the canonical headshot.
5. Add full-body reference only if build is still wrong and a body edit is genuinely necessary.
6. Add additional cast one character at a time.
7. After every identity edit, compare against the pre-edit master for scene richness. If attention shifts toward the edited character or secondary detail falls away, reject the edit even if identity improved.

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

Expression bridges are surgical continuity tools, not scene masters and not a reason to increase the character's visual prominence.

### Bounded edit authority

When the model over-preserves the source identity, define a hard edit boundary instead of relaxing the entire image:

- outside the boundary: master image has full authority;
- inside the boundary: canonical/bridge identity reference has full authority;
- explicitly state that preserving the source face inside the boundary is a failure;
- preserve expression/head angle/performance separately from identity;
- never broaden authority to body, wardrobe, lighting or scene geometry unless that class is the next deliberate edit stage.

For especially difficult identity edits, a localized crop can be sent to the model and feather-composited back into the untouched master. This protects pixels outside the crop, but it does **not** by itself guarantee scene-level attention balance. The recomposited full frame must still pass scene-richness QC.

## Documentary realism rules

For SHIRTFACED World 01, photographic imperfections are scene truth, not defects. Preserve:

- foreground obstruction and clipped bodies;
- asymmetric/uncomfortable poses;
- crowd collisions and physical contact;
- uneven visibility and deep shadows;
- awkward framing and close-range distortion;
- motion blur / exposure imperfection when present;
- subjects not acknowledging the camera;
- lack of clean visual separation around the hero;
- competing focal events and independent human behaviour;
- details that make the room feel inhabited beyond the named cast.

Avoid instructions that encourage beautification, balanced composition, evenly readable faces, broad ambient fill, a protected hero silhouette or a crowd reacting uniformly to the hero.

## Social format

Generate/edit vertical-first for the World 01 social pipeline:

- master aspect ratio: 9:16;
- keep essential action within a central 4:5-safe region where practical;
- do not create landscape masters and crop later unless a scene specifically requires it.

Vertical reframing must not create empty headroom or isolate the hero by sacrificing crowd density. Fill the vertical frame with event information, foreground interference and layered depth.

## Veo handoff

There is no requirement that the still be generated by a Google image model. Veo receives an approved image as the first frame. The still generator is selected on accepted-seed quality and keeper cost.

Veo prompts should describe **change through time only**. Do not redescribe identities, location or style already locked in the approved first frame. Explicitly preserve role/geography when semantic ambiguity exists.

For event scenes, explicitly state that background people continue their **independent pre-existing actions**. They must not synchronise, turn toward, sing to, cheer for or otherwise become an audience for the named character unless the scene specifically requires that behaviour.

## Cost metric

Optimise for cost per accepted finished clip, not individual call price:

`(all still attempts + all video attempts) / accepted final clips`

Track model, resolution, attempts, rejection reason, provider operation ID, input/output checksums and manual acceptance for each stage.

## Pub 11:05 findings that generalise

- Fresh generation with many references tends to sanitise/recompose the event.
- A strong master image supplied as a locked edit source preserves realism far better.
- Composition reference + six identities in one call diluted both composition fidelity and identity.
- Master-only preservation worked strongly.
- Identity work can succeed locally while progressively shifting full-frame attention toward the edited character; this is a scene-level failure.
- The first identity-focused pub chain became too Damo-centric: room detail and independent crowd behaviour weakened even though Damo improved.
- Expression-matched bridges remain valuable, but only as surgical identity tools inside a scene master that continues to pass attention-distribution QC.
- Veo amplifies semantic hierarchy present in the still. A hero-centric seed caused the crowd to behave as if Damo were the performer. Fix the hierarchy in the still rather than trying to repair it only in the motion prompt.
- The target pub master must feel like a room already going off, with Damo's pool-table incident discovered inside it.

The exact pub pose, lighting and props are scene-specific. The scene-first ownership/edit strategy is pipeline-wide and should be applied to ute-0341, takeaway-0230, side-street-2126 and continuity-bridge.
