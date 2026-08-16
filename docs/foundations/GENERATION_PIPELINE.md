# Generation pipeline — how a scene actually gets made

**Status:** SUPERSEDED as active doctrine on 16 August 2026.  
**Historical date:** 15 August 2026.  
**Active production contracts:**

- `docs/stage-2/social-ai-production/AI_GENERATION_PIPELINE.md`
- `docs/stage-2/social-ai-production/FLOW_SCENE_PRODUCTION_SPEC.md`
- `docs/stage-2/social-ai-production/SEED_IMAGE_REQUEST_RECIPE.md`
- `docs/stage-2/social-ai-production/CHARACTER_CONTINUITY.md`
- `docs/foundations/CAST_REFERENCE_USE.md`

This file is retained because it records useful empirical lessons from earlier Grok-based testing. **Do not treat its model limits, reference counts, resolution claims, prompt formulas or Grok workflow as current universal production rules.**

---

## 1. Why it was superseded

The original document hard-coded a two-tool pipeline:

`multi-reference still generator -> Grok Imagine motion`

That is no longer the production assumption. Current work is centred on Google Flow with Nano Banana / Veo where appropriate, and Flow exposes multiple generation modes whose prompting requirements differ.

The old file also elevated observations from one provider/tier into permanent universe-wide constraints. Examples included:

- exactly three named character references
- a permanent 720p reference-video ceiling
- a universal four-line motion prompt
- the claim that models cannot initiate a physics event from an upright/stable source
- the claim that text-to-video can never hold characters
- Grok-specific negative-prompt behaviour

Those may have described particular tests at the time. They are **not provider-independent facts** and must not constrain current production without current evidence.

---

## 2. Historical lessons that remain useful

The following principles survived the provider change and are now expressed more carefully in the active contracts.

### 2.1 Build visible state in the source image when using image-to-video

When a source image drives video, it already carries identity, composition, scene geography, lighting, wardrobe and visual treatment. Current image-to-video prompting should focus mainly on **what changes through time** rather than redundantly redescribing the source.

See `FLOW_SCENE_PRODUCTION_SPEC.md`.

### 2.2 A defective source image is expensive downstream

If identity, anatomy, blocking, props or scene geometry are already wrong in the first still, do not waste video generations trying to rescue it.

See `SEED_IMAGE_REQUEST_RECIPE.md` acceptance/rejection gates.

### 2.3 Character identity is an asset, not a prose paragraph

The strongest durable lesson from the old tests remains binding:

**a recurring character must resolve to approved identity references and persisted production identity before generation.**

See `CHARACTERS.md`, `CAST_REFERENCE_USE.md` and `CHARACTER_CONTINUITY.md`.

### 2.4 Motion prompts should be economical

Short clips work best when they have one primary narrative event. Add ordered physical beats only where order/trajectory genuinely needs control. Do not bury the motion signal under repeated static description.

### 2.5 Sequential continuity should be deliberate

Extracted/generated frames may become next-shot anchors, but only after deliberate review/approval. Never silently chain whatever final frame happened to be emitted.

See `AI_GENERATION_PIPELINE.md` and `FLOW_SCENE_PRODUCTION_SPEC.md`.

---

## 3. Historical Grok observations — NON-BINDING

The statements below are preserved as experiment notes only.

### 3.1 Source-image look dominated Grok motion attempts

Earlier tests found that dark/exposure/camera characteristics held more reliably when present in the source image than when re-described in Grok motion prose.

Useful observation; not a universal model law.

### 3.2 Saved character names did not bind reliably in one text-to-video test

One Grok test returned strangers when asked to use saved character references without a source still. That result justified reference-driven continuity in that workflow. It does **not** prove that current Flow/Veo text/reference modes can never maintain identity.

### 3.3 Three-character limit was tier/provider-specific

The earlier subscription tier exposed a three-character-reference ceiling. The old wording called this a permanent production constraint. That was inaccurate.

Current rule: check the selected provider/model/tier's present documented limits and design the shot accordingly.

### 3.4 Resolution statements were tier/provider-specific

The earlier 720p/1080p comparison was tied to the then-current Grok workflow. Do not reuse it as current Flow documentation.

### 3.5 `Use all references exactly` was provider-specific wording

It may have helped that tested provider. It is not a universal binding phrase and should not be inserted automatically into every model prompt.

### 3.6 Negative-prompt behaviour was provider-specific

The claim `negative prompts do not work` came from Grok tests. Current provider handling varies by model/interface. Active Flow guidance defaults to positive desired-state wording, but this is not the same as claiming that all negative mechanisms are ineffective.

### 3.7 Physics-event claim was too absolute

The old rule said models animate what is already in frame and `do not invent events`, with tipping/spilling cited as examples. The practical lesson is narrower:

**complex contact/physics events are higher risk and often become more reliable when the source frame already contains a physically plausible trajectory.**

Do not turn one failed test into a universal impossibility claim.

---

## 4. Current order of operations

Active workflow:

`scene canon -> canonical cast resolution -> current appearance state -> capture premise -> reference architecture -> still purpose -> seed still -> still QC -> choose Flow/video mode -> mode-specific motion prompt -> video QC -> approved continuity asset`

Detailed procedure lives in `FLOW_SCENE_PRODUCTION_SPEC.md`.

For the first still, use `SEED_IMAGE_REQUEST_RECIPE.md`.

For attempt/reference provenance, use `AI_GENERATION_PIPELINE.md`.

---

## 5. Provider capability rule

No reference-count, duration, resolution, model availability, audio capability, credit cost or generation-mode statement becomes permanent doctrine merely because it is true today.

When a production decision depends on a provider capability:

1. verify the current provider/model/tier capability;
2. record the selected mode/settings with the attempt;
3. do not back-port that temporary product limit into universe canon.

---

## 6. Historical value

Keep this document because failed generations are evidence. It explains why the system moved toward:

- canonical character assets
- source-still QC
- motion-focused I2V prompts
- explicit continuity anchors
- provider/version provenance
- failure classification instead of blind retries

Those lessons remain useful. The obsolete provider-specific absolutes do not.
