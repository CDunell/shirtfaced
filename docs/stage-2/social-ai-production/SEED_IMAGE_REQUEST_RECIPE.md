# SHIRTFACED — Seed Image Request Recipe

**Status:** ACTIVE production contract  
**Scope:** Initial scene stills / seed images  
**Companions:** `FLOW_SCENE_PRODUCTION_SPEC.md`, `CHARACTERS.md`, `CAST_REFERENCE_USE.md`, `CHARACTER_CONTINUITY.md`

Use this recipe whenever requesting an initial SHIRTFACED scene image. It separates locked canon, reference authority and permitted environmental invention.

## 0. Mandatory authority resolution

Before writing or generating the image, resolve these sources in order:

1. `docs/foundations/CHARACTERS.md` — canonical identity/story facts.
2. `docs/foundations/CAST_REFERENCE_USE.md` + current approved `studio/var/cast/<slug>/` files — canonical visual identity.
3. `docs/stage-2/social-ai-production/CHARACTER_CONTINUITY.md` — current scene appearance/wardrobe state.
4. Scene/story/shot canon — exact event, blocking, props, geography and camera.
5. This recipe — generation procedure.

**Authority order:** owner-set canon > approved visual reference > approved scene appearance > shot instruction > generator interpretation.

Do not use an old prompt paragraph as a substitute for an approved current character image. If the required visual asset is not actually available to the generation tool/session, stop and request/resolve it rather than recasting the character.

## 1. Scene

- **Scene name:**
- **Location:**
- **Date/time:**
- **What is happening:**

Describe the situation plainly. This is canon.

## 2. Exact instant

**The image captures:**

Describe the exact frozen instant, not what happens before or afterwards.

**The hero action/state is locked. Do not reinterpret it into a different moment.**

## 3. Characters

### Hero

- **Canonical slug/name:**
- **Canonical identity reference:** attach/resolve
- **Face reference if needed:** attach/resolve
- **Wardrobe/appearance state for this scene:**
- **Exact position/action:**

Use supplied approved references as authority for identity, face, hair, apparent age, build/body proportions and distinguishing physical characteristics.

The provider-facing prompt may refer to the person anonymously (`the man from reference 1`, etc.); the production record must still resolve the canonical slug.

### Other established characters

For each:

- **Canonical slug/name:**
- **Reference image(s):** attach/resolve
- **Wardrobe/appearance state:**
- **Position/action:**

### Background people

Describe generally: density, type and behaviour. They do not require established identities unless specifically promoted into canon.

## 4. Character integrity — LOCKED

For every referenced character, do not invent identity-changing features absent from approved canon/reference/scene state, including:

- tattoos
- scars
- piercings
- jewellery
- facial-hair changes
- different hairstyle/hair colour
- glasses
- hats/headwear not in scene state
- body-shape changes
- distinctive accessories

unless explicitly authorised for the scene.

Natural scene-dependent changes such as sweat, wet hair, flushed skin, rumpled clothing, dirt or fatigue are permitted only where appropriate.

**Omission is not permission.** If the canonical reference has no tattoo, the generator does not get one because the prompt forgot to say `no tattoos`.

## 5. Hero geometry

- **Position in scene:**
- **Body orientation:**
- **Feet/support:**
- **Hands/grip:**
- **Head:**
- **Eyes:**
- **Expression:**
- **Object being held/touched:**
- **Relationship to camera:**

These are hard scene constraints, not suggestions.

## 6. Important props

For each important prop:

- **Object:**
- **Location:**
- **State/orientation:**
- **Who interacts with it:**

Ordinary incidental objects may be invented where appropriate to make the environment believable.

## 7. Camera

- **Who is taking the picture:**
- **Camera/device:**
- **Camera position:**
- **Camera height:**
- **Distance:**
- **View/shot size:**
- **Orientation/aspect ratio:**

The camera must behave as though the stated photographer physically occupies that position.

## 8. Composition

- **Hero placement:**
- **Foreground:**
- **Midground:**
- **Background:**
- **Required visible elements:**
- **Allowed partial obstruction:**

Composition should feel naturally captured rather than arranged unless specifically stated otherwise.

## 9. Location / environment

The location must contain enough ordinary incidental detail to feel genuinely inhabited.

### Required environment features

- 
- 
- 

### Environmental freedom

Plausible incidental environmental detail that belongs naturally in the location may be invented.

For a pub this can include beer signage, brewery advertising, chalkboards, posters, taps, glasses, furniture, worn surfaces, miscellaneous bar clutter and ordinary patrons.

Realistic incidental branding is acceptable when contextually appropriate. It must remain background texture and must not become a dominant graphic element, headline, focal point or visual competitor to SHIRTFACED branding/campaign imagery.

Do not sanitise a real environment into an empty generic set merely to avoid incidental detail.

## 10. Lighting

- **Actual light sources:**
- **Exposure:**
- **Colour/temperature behaviour:**

Lighting must originate plausibly from the stated environment/capture method.

## 11. Behaviour

- **Hero:**
- **Established characters:**
- **Background people:**

Unless specifically stated otherwise, nobody acknowledges the photographer, nobody poses, nobody performs the joke for the camera, and people remain occupied with events around them.

## 12. Visual language

- **Capture style:** e.g. accidental phone photograph / direct-flash snapshot / 35mm documentary photograph
- **Desired imperfections:** only physically plausible imperfections
- **Overall feeling:**

## 13. Creative freedom

### LOCKED — DO NOT CHANGE

- canonical recurring-character identity
- established physical characteristics
- current approved character-reference version
- specified scene wardrobe/appearance state
- exact hero action/state
- specified character positions
- important props and their state
- established story facts
- camera premise

### FREE TO INTERPRET

- anonymous background people
- incidental environmental clutter
- minor furniture
- plausible signage/advertising
- small background objects
- naturally occurring imperfections
- details necessary to make the location convincing

**Freedom exists to make the world believable, not to rewrite the scene or characters.**

## 14. Pre-generation gate

Before generation:

1. Resolve every recurring character to canonical slug.
2. Identify the exact approved visual reference/version for each identity-critical character.
3. Verify those images are actually available to the generation tool/session.
4. Resolve current appearance/wardrobe state.
5. Resolve the exact frozen instant from scene canon.
6. Identify every attached reference and its role.
7. Preserve all LOCKED information.
8. Do not substitute a visually similar but different action.
9. Do not invent distinguishing features on established characters.
10. Allow realistic incidental environmental detail where permitted.
11. Compose from the specified physical camera position.
12. Generate only when these requirements are internally consistent.

If a required identity reference is missing from the active generation context, **do not generate a substitute person**.

## 15. Post-generation rejection gate

Reject the result before presenting it as acceptable if any of these occur:

- wrong established character
- material identity drift
- invented distinguishing character feature
- missing approved distinguishing feature
- unexplained build/hair/facial-hair change
- wrong scene wardrobe/appearance state
- wrong hero action
- wrong hero position
- wrong important prop
- wrong camera premise
- major continuity violation

A strong pub/location/composition does not rescue a wrong hero.

## Shorthand invocation

The user does not need to reproduce this document every time. They may say:

> **Use SHIRTFACED Seed Image Recipe.**  
> Scene: [scene / canonical scene ID].  
> Exact instant: [locked instant].  
> Characters: [canonical slugs + attached/resolved references]. Preserve identities exactly.  
> Camera: [capture premise].  
> Environment: [required environment plus permitted incidental freedom].  
> Generate the seed still.

If the scene, character identities, current references and wardrobe state already exist in the repo/current conversation, resolve them instead of asking the user to restate them. Ask only for genuinely unavailable required assets or an unresolved owner decision.
