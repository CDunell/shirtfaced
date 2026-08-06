# SHIRTFACED — Image-to-Video Pilot

Status: Ready to run  
Created: 5 August 2026  
Scope: Subtle animation of approved documentary stills for Instagram Reels and TikTok

## Decision

Do not select an image-to-video platform from demo reels, feature lists or generic model rankings.

Run a controlled SHIRTFACED pilot using the same approved source stills, the same motion intent and the same review criteria across:

1. Runway Gen-4.5
2. Google Veo image-to-video
3. Adobe Firefly Video

Kling, Luma and other systems remain secondary candidates until the first three establish a usable baseline.

## Why these three go first

### Runway Gen-4.5

Runway currently supports image-to-video clips from 2–10 seconds, including native 9:16 output at 720 × 1280, fixed aspect-ratio options and API access. Its own guidance says the source image establishes composition, subject, lighting and style, while the prompt should describe motion.

This directly suits the SHIRTFACED requirement: preserve an approved still and request restrained movement rather than regenerate the scene from scratch.

### Google Veo

Veo supports image-to-video through Vertex AI, including 9:16 output, 720p or 1080p output and 4, 6 or 8 second clips on supported models. It also provides an API path, making it relevant to future batch production and orchestration.

Veo enters the pilot because output quality may justify a more infrastructure-heavy workflow.

### Adobe Firefly Video

Firefly supports image-to-video from first and last keyframes, 24 fps generation, vertical aspect ratios, camera-motion controls and direct handoff into Firefly's video editor and Premiere. Adobe positions Firefly Video as commercially safe, but SHIRTFACED must still verify the applicable account terms and generated-asset conditions before release.

Firefly enters the pilot because it may offer the cleanest generation-to-finishing workflow even if its raw motion is not the strongest.

## What the pilot is testing

The pilot is not testing whether each system can create impressive video.

It is testing whether each system can preserve the SHIRTFACED documentary still while adding motion that feels incidental, believable and restrained.

## Source asset set

Use six approved stills covering different failure risks.

1. Two-person scene with minimal interaction
2. Mixed group walking between venues
3. Servo or street scene with practical lighting
4. Pub interior with several people and glassware
5. Product-incidental scene with a blank shirt, hoodie or cap
6. Empty or near-empty environmental plate

Each source must already be approved as a still. Do not use rejected or borderline images to evaluate video models.

## Motion briefs

Every platform receives the same four motion classes for each source.

### A — Locked observational

- camera remains almost static
- minor handheld breathing only
- natural blinking and breathing
- practical lights remain stable
- no subject approaches camera

### B — Environmental motion

- subjects remain largely still
- subtle traffic, steam, rain, smoke, neon or background crowd movement
- no new people enter the foreground
- no object changes identity

### C — Documentary drift

- slow handheld lateral drift or slight push-in
- no cinematic orbit
- no crash zoom
- no dramatic rack focus
- movement should resemble an unnoticed camera operator

### D — One simple human action

- one subject turns slightly, laughs, takes one step or shifts their weight
- no complex hand-to-object interaction
- no drinking action
- no dialogue
- no multi-person choreography

## Base prompt rule

Describe motion only. Do not redescribe the entire source image unless the model requires it.

Base wording:

> Preserve the exact people, clothing, objects, lighting, framing and documentary realism of the source image. Add only subtle natural motion. The camera movement is restrained and observational, not cinematic. No new people or objects. No changes to faces, garments, hands, text, logos or scene layout.

Append the selected motion class after this block.

Where a model responds poorly to negative wording, convert the restrictions into positive motion instructions rather than stacking exclusions.

## Output settings

Generate:

- vertical 9:16 where natively supported
- 5–8 seconds for first-pass comparisons
- 24 or 25 fps
- no generated dialogue
- no generated music
- no captions or text inside generation
- no automatic prompt enhancement unless separately recorded

Keep the original generation before any upscale, interpolation, grade or edit.

## Required sample count

Per platform:

- 6 source stills
- 4 motion classes per still
- 2 generations per motion class

Total per platform: 48 clips  
Total initial pilot: 144 clips

This is large enough to expose repeatability problems without pretending that one lucky clip proves a platform is reliable.

## Review criteria

Score every clip from 0–5.

### 1. Source preservation

- faces remain the same
- body shape remains stable
- clothing remains the same
- product-incidental garments do not mutate
- props do not change

### 2. Motion realism

- motion has believable weight
- people do not slide or float
- background movement follows plausible physics
- camera motion feels physically possible

### 3. Documentary restraint

- motion does not become glossy advertising
- no unnecessary cinematic flourish
- no exaggerated facial performance
- no artificial slow-motion feeling unless requested

### 4. Frame stability

- hands remain usable
- glassware and small objects remain coherent
- faces do not drift between frames
- scene geometry does not breathe or warp

### 5. Vertical usability

- important subjects remain inside 9:16 crop
- no destructive auto-crop
- no edge hallucination
- room remains for platform interface overlays where required

### 6. Finishing burden

Estimate the work needed before release:

- none
- trim only
- grade and sound only
- minor repair
- major repair
- unusable

## Automatic rejection conditions

Reject a clip immediately when any of these occur:

- face identity changes materially
- a garment or product changes design
- fingers, glasses, bottles or limbs visibly mutate
- commercial text or logos appear
- a person materialises or disappears
- the clip becomes visibly stylised or cinematic
- camera movement contradicts the documentary world
- a loop requires hiding a major continuity break

## Decision metrics

For each platform calculate:

- percentage passing automatic rejection
- percentage reaching release-ready after light finishing
- median source-preservation score
- median documentary-restraint score
- average generations required per usable clip
- average credits or dollars per usable clip
- average finishing minutes per usable clip
- vertical-output pass rate

The winning platform is not the platform with the best single clip.

It is the platform with the lowest total cost per release-ready, on-brand clip.

## Pilot pass threshold

A platform may enter the working production stack when:

- at least 50% of tested source stills produce one usable restrained-motion clip
- at least 25% of all generated clips survive automatic rejection
- product-incidental garments remain stable in the selected outputs
- a usable vertical export can be finished without rebuilding the shot
- total cost per release-ready clip is known

These are SHIRTFACED test thresholds, not industry standards. Revise them only after the first complete pilot, not halfway through testing.

## Initial operating recommendation

Start with Runway Gen-4.5 as the fastest controlled baseline because it offers native image-to-video, vertical output, variable short durations and API access in one system.

Run Veo against the same assets before locking the stack. Its higher-resolution and API options may outweigh workflow friction if it preserves people and scenes more reliably.

Run Firefly Video as the workflow-control candidate, particularly for first/last-frame control and direct finishing integration.

Do not buy a broad annual stack before the pilot identifies where usable clips actually come from.

## Finishing path

Every shortlisted clip moves through:

1. trim start and end instability
2. repair or discard visible mutations
3. stabilise only where required
4. upscale only after selection
5. match the approved still's grade
6. add real or licensed environmental sound
7. export platform master
8. create Instagram and TikTok versions
9. preserve source, prompt, settings, generation and final export lineage

## Evidence sources

Official product documentation reviewed 5 August 2026:

- Runway Gen-4.5: https://help.runwayml.com/hc/en-us/articles/46974685288467-Creating-with-Gen-4-5
- Runway image-to-video prompting: https://help.runwayml.com/hc/en-us/articles/48324313115155-Image-to-Video-Prompting-Guide
- Runway API: https://docs.dev.runwayml.com/api/
- Google Veo model documentation: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/veo/3-0-generate-001
- Google Veo image-to-video sample: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/samples/googlegenaisdk-videogen-with-img
- Adobe Firefly image-to-video: https://helpx.adobe.com/firefly/web/work-with-audio-and-video/work-with-video/generate-videos-using-images.html
- Adobe Firefly video editor: https://helpx.adobe.com/firefly/web/firefly-video-editor/generate-videos/generate-video-using-firefly-models.html

## Next action

Select the six approved source stills and record them in a pilot manifest before opening any generation platform.
