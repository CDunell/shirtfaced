# SHIRTFACED — Seed Image Request Recipe

**Status:** ACTIVE production contract  
**Scope:** Initial scene stills / seed images  
**Companion:** `FLOW_SCENE_PRODUCTION_SPEC.md`

Use this recipe whenever requesting an initial SHIRTFACED scene image. It separates locked canon, reference authority and permitted environmental invention.

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

- **Name:**
- **Reference image(s):** attach
- **Wardrobe for this scene:**
- **Exact position/action:**

Use supplied references as authority for identity, face, hair, apparent age, build/body proportions and distinguishing physical characteristics.

### Other established characters

For each:

- **Name:**
- **Reference image(s):** attach
- **Wardrobe:**
- **Position/action:**

### Background people

Describe generally: density, type and behaviour. They do not require established identities unless specifically named.

## 4. Character integrity — LOCKED

For every referenced character, do not invent identity-changing features absent from both supplied references and scene canon, including:

- tattoos
- scars
- piercings
- jewellery
- facial-hair changes
- different hairstyle/hair colour
- glasses
- hats
- body-shape changes
- distinctive accessories

unless explicitly requested for the scene.

Natural scene-dependent changes such as sweat, wet hair, flushed skin, rumpled clothing or dirt are permitted where appropriate.

**Authority order:** canon > supplied visual references > scene-specific instructions > generator interpretation.

## 5. Hero geometry

- **Position in scene:**
- **Body orientation:**
- **Feet:**
- **Hands:**
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

- referenced character identities
- established physical characteristics
- specified wardrobe
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

## 14. Generation instruction

Before generating:

1. Identify every attached reference and its role.
2. Preserve all LOCKED information.
3. Check the requested frozen instant against scene canon.
4. Do not substitute a visually similar but different action.
5. Do not invent distinguishing features on established characters.
6. Allow realistic incidental environmental detail where permitted.
7. Compose from the specified physical camera position.
8. Generate only when the requirements are internally consistent.

After generation, reject the result if any of these occur:

- wrong established character
- invented distinguishing character feature
- wrong hero action
- wrong hero position
- wrong important prop
- wrong camera premise
- major continuity violation

Do not present a failed image as an acceptable result.

## Shorthand invocation

The user does not need to reproduce this document every time. They may say:

> **Use SHIRTFACED Seed Image Recipe.**  
> Scene: [scene].  
> Exact instant: [locked instant].  
> Characters: [attached reference assignments]. Preserve identities exactly.  
> Camera: [capture premise].  
> Environment: [required environment plus permitted incidental freedom].  
> Generate the seed still.

Established canon and this recipe supply the remaining constraints.