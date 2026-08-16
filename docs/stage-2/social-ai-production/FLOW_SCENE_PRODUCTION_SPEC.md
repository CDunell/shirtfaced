# SHIRTFACED — Flow Scene Production Spec v2.0

**Status:** ACTIVE production guidance  
**Scope:** Google Flow / Nano Banana / Veo scene decomposition, still generation, video handoff, review and continuity  
**Companion contract:** `AI_GENERATION_PIPELINE.md`

---

## 0. Governing principle

Do not begin by writing a prompt.

Begin by determining:

- What information must be created?
- What information already exists visually?
- What must change through time?
- Which Flow generation mode gives the strongest control over those variables?

Write the prompt only after those questions are answered.

This spec distinguishes three rule classes:

- **[G] Google-supported** — documented Google / DeepMind prompting or product guidance.
- **[P] Production inference** — filmmaking, continuity or generative-media reasoning; useful but not claimed as Google documentation.
- **[S] SHIRTFACED rule** — campaign-specific visual language and production discipline.

Do not silently promote [P] or [S] rules into provider facts.

---

## 1. Phase zero — scene decomposition

Before selecting references or writing prompts, resolve five layers.

### 1.1 Narrative event

State the single event the scene exists to communicate.

Example: `The bloke at the pool table gets completely carried away by the chorus while everyone around him treats it as normal.`

A location description is not an event.

### 1.2 Immutable canon

Record facts that may not drift:

- character identities and relationships
- age/build where relevant
- wardrobe continuity
- recurring props
- date/time
- established location
- scene geography
- story chronology
- preceding condition
- following condition

These are continuity constraints, not necessarily prompt text.

### 1.3 Hero information

Identify:

- hero character
- hero action
- hero prop
- hero relationship to environment
- hero emotional/behavioural state

Only one action is primary.

### 1.4 Supporting information

Classify everything else as:

- **Necessary** — required to understand the event.
- **Useful** — improves authenticity or continuity.
- **Decorative** — can disappear without harming the scene.

Decorative information receives the lowest prompting priority.

### 1.5 Capture premise

State who or what supposedly captured the image/footage and where they physically are.

Examples: mate inside crowd with phone; person seated on kerb; friend across road; direct-flash compact camera; observer beside ute tray.

For SHIRTFACED, the camera normally belongs to a real person occupying physical space in the scene. [S]

---

## 2. Define the shot before the still

### 2.1 Shot objective

Write: `This shot succeeds if ____________.`

Bar example: `This shot succeeds if the man's commitment to the chorus is immediately funny without anybody visibly performing the joke for the camera.`

Judge all later decisions against this.

### 2.2 Deliverable and aspect ratio

Choose the intended delivery format before composing the image. [G]

Do not automatically make a 16:9 master when the real deliverable is vertical. Where both formats matter, independent compositions may outperform a single crop-first master. [P]

---

## 3. Reference architecture

Every visual input gets one defined role:

- identity
- body/build
- wardrobe
- pose
- prop
- location
- composition
- style

Do not attach a reference merely because it is relevant. [P]

When ambiguity exists, explicitly state what each reference contributes. [G]

### 3.1 Recurring characters

Assess reusable Flow Characters first when the current Flow product supports them and the character recurs frequently. [G]

Prefer a reusable character when stable identity, clothing and/or voice continuity are useful.

Prefer loose references when:

- wardrobe must change substantially
- a specific body reference is required
- a particular pose must be borrowed
- the scene needs a materially different appearance
- the reusable character proves less faithful than the source references

Where useful, maintain campaign/world appearance variants such as `DAMO — WORLD01 NIGHT`. [P]

### 3.2 Reference quality

Prefer clean, sharp, high-resolution and visually compatible references. Subject references should use simple/segmented backgrounds where practical. Avoid unwanted people/objects in references unless they are intentionally part of the desired composition. [G]

### 3.3 Reference quantity

Use the **minimum sufficient reference set that removes ambiguity without introducing conflicting visual information**. [P]

Do not impose an arbitrary one-reference rule. Additional references are justified when they perform distinct necessary roles.

Example: head reference = identity; full-body reference = build; stool reference = recurring prop.

---

## 4. First-still strategy

Determine the still's job before generating it.

### Type A — Establishing master

Defines scene geography, lighting and composition. May later become a location reference, ingredient, continuity guide or start frame.

### Type B — Animation start frame

Becomes the literal opening frame of image-to-video. Exact composition, identity, lighting and scene state therefore matter strongly. [G]

### Type C — Character/prop integration frame

Establishes a difficult identity/object combination before animation.

### Type D — Terminal frame

Represents the intended end state for first+last-frame interpolation.

### Type E — Continuity bridge

Connects shots and may be harvested from an already successful video. [G]

There is no universal requirement that an animation start frame be pre-action or "loaded." Choose the state according to the shot. [P]

---

## 5. First-still components

Resolve each component explicitly before writing the image prompt.

### 5.1 Style

Define the image/capture type: photorealistic documentary photograph, phone photograph, direct-flash snapshot, etc. [G]

### 5.2 Subject

Define who appears, which reference controls identity, clothing where not already locked, and only physically important appearance traits. [G]

Do not exhaustively redescribe a face when a strong visual reference already carries identity. [P]

### 5.3 Setting

Define actual location, time and environmental cues necessary to establish place. Prefer observable physical cues over vague atmosphere words. [G/P]

### 5.4 Action / pose

Describe the exact frozen moment. [G]

For an animation start frame, choose a narratively useful and physically coherent pose compatible with intended movement. [P]

Do not automatically preserve future action. If the video is about raising the cue, start before/during the raise. If it is about singing and crowd behaviour, the cue may already be overhead. If using first+last frames, establish both states deliberately.

### 5.5 Composition

Resolve only meaningful variables:

- shot size
- camera height
- viewpoint
- field-of-view/lens character
- subject placement
- foreground/midground/background
- meaningful occlusion
- aspect ratio

[G]

Do not add technical numbers merely to make the prompt sound photographic. A phrase such as `wide phone-camera field of view from chest height inside the crowd` may communicate the desired result better than an arbitrary focal length. [P]

### 5.6 Lighting

Describe motivated sources: pool-table lamp, ceiling practicals, stage spill, direct flash, sodium streetlight, etc. [G]

For SHIRTFACED documentary scenes, describe real sources rather than generic `cinematic lighting`. [S]

### 5.7 Spatial relationships

For complex scenes, resolve only topology that affects narrative or generation ambiguity: hero beside stool; stool on pool table; band behind hero; waiting player clear of cue; crowd between camera and stage. [P]

Do not convert every person into coordinates.

---

## 6. First-still prompt construction

Use coherent descriptive prose rather than a keyword dump. [G]

The internal checklist is reasoning scaffolding; it is not the final model prompt.

Recommended information order:

1. image/capture type
2. composition
3. referenced subject assignment
4. frozen action
5. setting
6. important spatial relationships
7. lighting
8. photographic behaviour
9. essential continuity constraints

### 6.1 Negative instructions

Default to describing the desired state positively. Keep explicit exclusions for recurring high-cost failures only. [P]

Prefer `everybody remains engaged with events inside the room, unaware of the camera` over a long `no posing / no looking / no...` appendix.

---

## 7. First-still acceptance gate

Evaluate separately for visual quality and video readiness.

### 7.1 Visual quality

Check:

- identity fidelity
- location credibility
- composition
- lighting
- photographic realism
- wardrobe
- prop fidelity

### 7.2 Video readiness

When the image will drive video, check:

- sufficient source quality/sharpness
- no serious anatomy defect
- plausible object contacts
- coherent scene geometry
- intended movement physically possible from the state
- critical moving elements not already malformed
- framing compatible with intended movement

[G/P]

### Fatal defects

Reject before video for:

- wrong identity
- wrong hero prop
- impossible pose affecting intended motion
- incorrect core geography
- major continuity error
- fundamentally wrong camera perspective

Do not spend video credits trying to rescue a defective source frame. [P]

---

## 8. Video-mode decision

Select mode only after the source state is approved. Check current Flow capability before recommending a provider/model/mode combination. [G]

### Mode 1 — First-frame image-to-video

Use when exact opening composition matters, the still already establishes identity/location/style, and the task is primarily movement.

**Prompt rule: prompt motion, not appearance.** [G]

Do not redundantly redescribe face, clothing, location, lighting or photographic style unless it genuinely needs to change.

### Mode 2 — First + last frame

Use when the final state matters strongly, a trajectory has a defined endpoint, and the selected model supports it. [G]

Prompt primarily what happens between the two states.

### Mode 3 — Ingredients / references to video

Use when identity/object/location continuity matters more than preserving one exact opening composition and the selected model supports Ingredients. [G]

State how each ingredient is used.

### Mode 4 — Text-to-video

Use when no canonical source frame is needed, identity requirements are weak, or an exploratory/establishing shot can tolerate variation.

### Mode 5 — Video-to-video

Use when motion/performance already works and supported visual changes are required. Do not regenerate successful motion from scratch merely to change a correctable visual detail. [G/P]

---

## 9. Image-to-video prompting

For first-frame I2V, prompt **only what changes**. [G]

Useful categories:

### Subject motion

`The man plants his second boot against the rail and raises the cue above his head.`

### Camera motion

`The handheld camera gets nudged slightly right by someone passing close to the operator.`

### Environmental motion

`The crowd continues shifting around the pool table and the band moves naturally onstage.`

### Audio

`Audio: loud live band, crowd singing, overlapping pub chatter and glasses.`

Refer to visible characters simply as `the man`, `the woman`, `the person beside him`, etc. rather than redescribing identity. [G]

---

## 10. Action complexity

A short clip gets one primary narrative event. [G]

One event may contain ordered physical beats. Detailed play-by-play is appropriate when action order/trajectory needs tighter control. [G]

Example primary event: hero commits to chorus.

Possible beats:

1. shifts weight
2. raises cue
3. straightens
4. tilts head back
5. shuts eyes
6. begins roaring chorus

Do not combine unrelated story events into one short clip.

Start with the minimum action description capable of producing the shot. Increase beat specificity when ordering is wrong, motion is omitted, trajectory matters, or fast action becomes chaotic. [P]

---

## 11. Secondary behaviour

Background characters should not appear frozen, but do not assign elaborate independent stories to everyone. [S/P]

Prioritise:

1. hero action
2. one directly interacting secondary action
3. one environmental/crowd behaviour if necessary

If background behaviour already works in the source media, leave it alone.

---

## 12. Camera behaviour

Use explicit camera direction when it matters. [G]

SHIRTFACED additionally requires camera movement to fit the capture premise. [S]

Preferred documentary behaviours include tiny handheld drift, late reframe, brief obstruction, reaction to being bumped, operator shift, or subject partially leaving ideal framing.

Avoid perfect orbit, floating movement, glossy gimbal tracking or dramatic automated push-ins unless deliberately required.

Documentary imperfection should have a physical cause. [S/P]

---

## 13. Audio

When generated audio is desired, define meaningful sound and perspective. [G]

For SHIRTFACED consider:

- primary sound caused by hero event
- environmental sound
- capture-device perception

Bar example: `Audio: loud four-piece band, crowd singing along, overlapping nearby conversation, glasses and pool-room noise; the phone microphone compresses slightly under the volume.`

Do not request pristine cinematic mixing for an accidental phone recording. [S]

---

## 14. Video acceptance gate

Evaluate in this order:

1. **Event** — did the intended event happen?
2. **Identity** — are recurring characters stable?
3. **Physical coherence** — hands, limbs, feet, contacts, momentum, collisions.
4. **Prop continuity** — are important recurring objects stable?
5. **Environment** — are architecture, furniture and lighting stable enough?
6. **Performance** — natural, unaware of camera, humour incidental rather than performed.
7. **Camera** — does it behave like the claimed device/operator?
8. **Audio** — does it match source, environment and action?

---

## 15. Failure classification

Never reduce a failed generation to `try again`.

Classify it:

- **SOURCE** — source still defective; fix image first.
- **IDENTITY** — character drift; strengthen/change reference strategy.
- **ACTION** — movement missing/incorrect; simplify or clarify motion.
- **ORDER** — correct movements in wrong sequence; add ordered beats.
- **PHYSICS** — movement/contact impossible; change source state or trajectory.
- **PROP** — important object mutates/disappears; strengthen reference or reduce simultaneous action.
- **CAMERA** — camera behaviour wrong; rewrite camera instruction only.
- **CROWD** — freezes/clones/overreacts; reduce/modify secondary behaviour.
- **STYLE** — capture language changes; for I2V inspect source before restating style.
- **AUDIO** — wrong/missing sound; modify Audio instruction.
- **CONTINUITY** — conflict with adjacent shot; return to canon/reference assets.

Preserve successful variables. If composition, identity and lighting work and motion fails, change motion rather than rewriting everything. [P]

Retry/variation lineage and exact prompt/reference deltas must remain persisted under `AI_GENERATION_PIPELINE.md`.

---

## 16. Frame harvesting

Successful generated frames are production assets. [G]

Deliberately save approved frames as appropriate:

- start frame
- end frame
- ingredient
- character-reference candidate
- location continuity reference
- next-shot bridge

Do not automatically return to the original studio reference after a character is successfully established in-world. The strongest continuation reference may be an approved in-world frame. [P]

An extracted frame becomes an anchor only when deliberately selected/approved, consistent with `AI_GENERATION_PIPELINE.md`.

---

## 17. Required ChatGPT response contract

For every new SHIRTFACED scene, respond in this order.

### A. Scene Event

The one event the scene is about.

### B. Canon

Immutable facts.

### C. Capture Premise

Who has the camera and where they physically are.

### D. Shot Objective

What makes the shot successful.

### E. Deliverable

Aspect ratio and intended channel/use.

### F. Reference Plan

Table: `Asset | Role | Required/optional | Why`.

Also classify each relevant asset as reusable Flow Character, loose ingredient, previous-scene frame, or unnecessary.

### G. First-Still Type

Choose establishing master, animation start, integration frame, terminal frame or continuity bridge, and explain why.

### H. First-Still Decisions

Resolve style, subject, exact frozen action, composition, setting, spatial relationships, lighting and relevant photographic behaviour.

### I. Still Risk Register

List only likely high-impact failure modes.

### J. First-Still Prompt

One coherent production-ready prompt. Do not expose the internal checklist as a keyword stack.

### K. Still Acceptance Gate

Separate **Fatal requirements** and **Preferred qualities**.

### L. Video Mode Decision

Choose the correct mode and include model, duration, aspect ratio, input assets and reason. Verify current capability before specifying it.

### M. Motion Plan

Only what changes during the shot, separated into hero motion, secondary motion, environmental motion, camera motion and audio.

### N. Video Prompt

Prompt according to mode:

- first-frame I2V = motion-focused
- first+last = transition-focused
- Ingredients = reference-role + action-focused
- text-to-video = full cinematography + subject + action + context + style

Never use one universal formula for every mode.

### O. Video Acceptance Gate

Scene-specific pass/fail criteria.

### P. Failure Map

For each likely failure: `symptom -> probable cause -> smallest corrective action`.

### Q. Continuity Output

State what should be saved for the next shot.

---

## 18. Bar scene — first-still constituents

For the Friday 11:05pm pub scene, resolve before first image generation:

### Narrative

- exact part of the chorus event captured

### Identity

- hero identity source
- recurring secondary cast required in this shot

### Character state

- hero body orientation
- feet/support
- cue position
- head state
- expression
- orientation relative to stage

### Story objects

- wooden pub stool
- beer
- pool cue

### Geography

- camera
- pool table
- hero
- waiting player
- crowd
- stage/band

### Composition

- orientation
- shot size
- camera height
- field of view
- subject position
- whether foreground obstruction helps

### Environment

- credible Australian pub back room
- crowd density
- live band
- pool-table lighting
- humidity/condensation only where visually useful

### Capture language

- phone footage from a friend inside the crowd

### Lighting

- practical pub sources
- pool-table light
- stage spill

### Motion compatibility

- subsequent clip action must be physically achievable from the selected still

Everything else must justify its inclusion.

---

## 19. Core rules

1. Decide before prompting.
2. Use references for information they can carry visually.
3. Assign each reference a role.
4. Use coherent image prompts rather than keyword dumps.
5. A source still must be good enough to deserve animation.
6. There is no universal ideal first-frame action state.
7. Select video mode before writing the video prompt.
8. Image-to-video prompts describe change, not the image again.
9. One short clip = one narrative event.
10. Use detailed play-by-play only when the event requires it.
11. Do not over-direct background extras.
12. Camera direction must serve the capture premise.
13. SHIRTFACED imperfection must have a physical cause.
14. Audio belongs to the same documentary perspective as the image.
15. Fix the failed variable, not everything around it.
16. Harvest successful generated frames for continuity.
17. Current product capability beats remembered capability: verify model/mode before specifying it.
18. The final criterion is not `looks AI-impressive`; it is `looks like this really happened and somebody happened to capture it`.

---

## 20. Workflow summary

`scene -> event -> canon -> capture premise -> reference architecture -> still purpose -> still decisions -> still generation -> still QC -> choose video mode -> mode-specific motion instructions -> video QC -> continuity asset harvest`

Not:

`scene -> giant prompt -> image -> even bigger prompt -> video`
