# SHIRTFACED — Nano Banana Scene Coverage Prompt

**Purpose:** Reusable Nano Banana prompt for deriving documentary coverage ideas from one approved scene master without regenerating or rearranging the world.

```text
<instruction>
Analyze the entire established scene in the input master image.

Identify ALL key subjects, groups, interactions, props, environmental features and areas of activity already present in the scene, and understand their spatial relationships to one another.

The input image is the approved spatial truth. The scene already exists independently of the camera.

Generate a cohesive 3x3 "Documentary Scene Coverage Sheet" featuring 9 distinct camera observations of exactly this same uninterrupted event in exactly the same environment.

Do NOT create nine different versions of the scene. Show nine plausible observations of different parts, scales, interactions and details within the ONE established world.

You must adapt the camera observations to what actually exists in the input scene. Do not mechanically apply generic cinematic shot types. Select the most useful observations available from the scene itself.

**Row 1 — World / Event:**

1. **Environmental Discovery:** A wider observation establishing the physical environment, crowd density and primary event. Named characters are inhabitants of the scene rather than the reason the scene exists.

2. **Primary Incident in Context:** Observe the strongest character incident or action while retaining enough surrounding people and environment to show that it is happening inside a larger independent event. Do not isolate the character or arrange the world around them.

3. **Independent Social Activity:** Observe another active region of the same scene where other people are having their own interactions. This must not become a reaction shot to the primary character.

**Row 2 — Human Coverage:**

4. **Incident Medium:** A closer documentary observation of the primary incident, preserving neighbouring bodies, occlusion and environmental context. The subject must remain unaware of the camera and actively engaged in the event.

5. **Secondary Character / Group Observation:** Find a meaningful secondary person, pair or social cluster already present and observe their ongoing behaviour. Preserve their established position and relationship to the rest of the scene.

6. **Event Source / Cause:** Observe the person, group, activity or environmental source actually driving the larger event. Frame it through the existing world rather than as a clean staged performance shot.

**Row 3 — Physical Texture / Alternate Observation:**

7. **Physical Detail:** A close observation of an important existing physical relationship: hands, feet, drink, clothing, prop, furniture, contact, movement or another detail that communicates the event without inventing anything new.

8. **Crowd-Level Alternate View:** A different physically plausible observation from inside the established environment. Existing foreground bodies or objects may partially obstruct the view. The camera should feel embedded in the event rather than granted a perfect cinematic position.

9. **World Return:** Return to a broader observation showing that the same event continues independently across the environment. Nothing has reset, concluded or reorganised around the recurring characters.

**Critical continuity rules:**

Maintain strict consistency across all 9 panels:

- exactly the same people
- exactly the same faces and identities
- exactly the same clothing and appearance
- exactly the same body proportions
- exactly the same props
- exactly the same furniture and realistic object scale
- exactly the same environment and spatial geography
- exactly the same lighting sources and atmosphere
- exactly the same crowd density
- exactly the same time and event state
- exactly the same relationships between established people, objects and areas of the environment

Different panels change only the camera's observation of the established world.

Do not add, remove, duplicate, relocate or redesign people, furniture, props or major environmental elements.

Do not clean up, simplify or empty a crowded environment to improve composition.

Do not manufacture clear space around a named character.

Do not create a hero halo, spotlight, protected negative space or audience formation around a named character.

Do not make background people collectively look toward, react to, imitate or perform for a named character unless that behaviour is clearly established in the input image.

Do not synchronise independent people into one collective action.

Do not invent reactions for editorial convenience.

Do not pose anybody for the camera.

Do not turn an incidental character into a performer, celebrity or centre of the world.

Preserve natural collisions, overlapping bodies, partial visibility and occlusion.

Camera positions must be physically plausible for a person present in the established environment.

Prefer observational documentary framing, imperfect sight lines, foreground interference and believable human camera positions.

Avoid impossible overhead views, artificial worm's-eye hero shots, crane perspectives, perfect symmetry, dramatic staged compositions and camera positions that could not physically exist in the scene.

The purpose of the sheet is to discover useful coverage already latent inside the approved world.

World/event → distributed human activity → camera observation → character incident → character identity.

Continuity must be achieved by observing another part of the same world, never by regenerating or rearranging the world.
</instruction>

A professional 3x3 photorealistic documentary contact sheet containing 9 panels derived from one approved master scene.

The contact sheet explores the exact same uninterrupted event through varied but physically plausible camera observations.

**Top Row:** Environmental discovery, primary incident in context, independent social activity.

**Middle Row:** Incident medium, secondary character/group observation, event source/cause.

**Bottom Row:** Physical detail, crowd-level alternate observation, world return.

All 9 panels contain the same established people, identities, clothing, props, environment, geography, crowd density, lighting and event state as the input master image.

Every panel feels like another camera observation made within the same real event rather than a newly staged version of it.

Photorealistic natural textures. Realistic depth of field appropriate to each framing distance. Documentary rather than cinematic-hero composition. Natural foreground obstruction and environmental depth where appropriate. No repeated compositions.
```

## Pipeline use

This prompt is intended for Nano Banana after an approved world master exists. Scene-resolved production data may inject named incidents, cast/group targets, event source, prop anchors and scene-specific forbidden drift without changing the prompt architecture.

Production path:

`approved world master → Nano Banana coverage sheet → coverage selection/extraction → deterministic target-aspect source → checksum → motion generation → keeper extraction → edit`

The coverage stage discovers useful observations. It does not grant the model permission to redesign the scene or choose continuity.