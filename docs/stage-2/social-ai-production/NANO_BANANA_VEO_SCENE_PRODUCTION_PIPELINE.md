# SHIRTFACED --- Nano Banana → Veo Scene Production Pipeline

## Purpose

This is the production method for turning an approved SHIRTFACED World
scene into coherent multi-shot video coverage without rebuilding the
world for every shot.

The governing principle is:

> **The scene exists independently of the camera.**

Continuity is achieved by establishing character identity first,
establishing the world once, then observing different parts of that same
world.

The pipeline has two separate Nano Banana processes, followed by Veo
motion generation:

**Character identity expansion → Scene coverage expansion →
Selected-shot extraction → Veo motion → Editorial assembly**

------------------------------------------------------------------------

## 1. Production hierarchy

The order matters. Each stage depends on the approved output of the
stage before it.

``` text
CANONICAL CHARACTER REFERENCES
        ↓
NANO CHARACTER CONTACT SHEETS
        ↓
APPROVED CHARACTER IDENTITY COVERAGE
        ↓
APPROVED 16:9 SCENE MASTER
        ↓
NANO SCENE COVERAGE CONTACT SHEET
(master + relevant character contact sheets)
        ↓
APPROVED SCENE COVERAGE SHEET
        ↓
NANO PANEL EXTRACTION
        ↓
APPROVED STANDALONE SHOT FRAME
        ↓
VEO IMAGE-TO-VIDEO
        ↓
RAW 6–8 SECOND TAKE
        ↓
KEEPER FRAGMENT
        ↓
FINAL EDIT
```

A later stage must not silently repair or reinterpret a failed earlier
stage. If a contact-sheet panel is wrong, reject or regenerate the
contact sheet. Do not attempt to fix it during extraction.

------------------------------------------------------------------------

# PROCESS A --- CHARACTER IDENTITY EXPANSION

## 2. Input

For each recurring character, start with the approved canonical visual
reference set.

Where available, provide:

-   approved full-body reference;
-   approved head-and-shoulders reference.

The full-body image establishes body proportions, build, wardrobe and
footwear. The closer reference strengthens facial identity.

## 3. Generate the character contact sheet

Nano Banana receives the canonical character reference(s) and the
generic **Character Contact Sheet Master Prompt**.

The output is a coherent 3×3 identity sheet of the **same person**,
deliberately varying camera distance and useful viewing angle.

Target coverage:

  Panel   Coverage
  ------- -----------------------------------------
  1       Full body / long shot
  2       Three-quarter full view
  3       Medium long / knees up
  4       Medium / waist up
  5       Medium close-up / chest up
  6       Close-up / head and shoulders
  7       Profile
  8       Rear three-quarter / over-shoulder
  9       Alternate useful high/low spatial angle

The contact sheet is not a mood board. It is an **identity expansion
asset**.

It teaches the later scene process what the approved character looks
like from views that were not present in the original reference
photographs.

## 4. Approve the character sheet

Review for:

-   facial identity;
-   body proportions;
-   hair and facial hair;
-   wardrobe;
-   permanent physical features;
-   believable alternate angles;
-   no unexplained identity drift.

Once approved, the complete contact sheet becomes part of the
character's visual authority.

Do **not** manually crop every panel into a reference library as a
prerequisite. Nano can consume the complete approved sheet later.

------------------------------------------------------------------------

# PROCESS B --- SCENE COVERAGE EXPANSION

## 5. Establish the scene master

The approved 16:9 scene master is the spatial authority.

It owns:

-   room/location geography;
-   furniture and prop placement;
-   crowd density;
-   lighting;
-   environmental texture;
-   character blocking;
-   scale;
-   the event state at that moment.

The scene master is **not regenerated independently for each shot**.

For W01-P28 / PUB-1105, this means the approved packed pub, full-size
pool table, stool, pint, band, bar, crowd and existing character
placement remain one continuous world.

## 6. Resolve character references for the scene

Supply the scene master plus the approved contact sheets for the
recurring characters whose identity matters to the requested coverage.

There is no one-character-per-shot restriction.

Examples:

``` text
Damo coverage:
scene master + Damo contact sheet

Emma coverage:
scene master + Emma contact sheet

Emma + Brock coverage:
scene master + Emma contact sheet + Brock contact sheet

Band/environment coverage:
scene master only, unless a recurring character is identity-critical
```

Use the minimum useful identity set. Do not burden a tight Damo
operation with unrelated character references.

## 7. Generate the scene contact sheet

Nano receives:

1.  approved 16:9 scene master;
2.  relevant approved character contact sheets;
3.  scene-specific coverage prompt.

Its job is to create **different camera observations of the same
established event**, not nine new versions of the scene.

For PUB-1105 the tested coverage architecture is:

  Panel   Observation
  ------- ----------------------------------------------
  1       Room wide / discovery
  2       Damo long/wide in context
  3       Damo three-quarter / alternate crowd angle
  4       Damo medium
  5       Emma + Brock inside their own crowd activity
  6       Band / actual performance source
  7       Pool-table / stool / pint / physical detail
  8       Alternate obstructed crowd-level observation
  9       Wide return to the uninterrupted room

Different panels deliberately vary:

-   camera position;
-   camera distance;
-   angle;
-   observation target;
-   foreground obstruction;
-   depth relationships.

They do **not** deliberately vary the world.

## 8. Distributed attention rule

The crowd is not required to ignore a character doing something
conspicuous.

Some nearby people may naturally:

-   glance at Damo;
-   laugh with him;
-   gesture toward him;
-   briefly react to him.

That is normal human behaviour.

The failure condition is **collective convergence**.

Damo must not become the dominant performance source. The room must
retain distributed attention: people watch the band, sing with mates,
talk, drink, move, look elsewhere and conduct simultaneous independent
interactions.

Reject:

-   organised audience behaviour around Damo;
-   a semicircle around the table;
-   cleared hero space;
-   majority attention directed toward him;
-   stage-like isolation;
-   the room visually reorganising around him.

The band remains the actual performance source.

------------------------------------------------------------------------

# PROCESS C --- PANEL SELECTION AND NANO EXTRACTION

## 9. Select the useful panel

Review the complete scene contact sheet as an editorial coverage map.

Select panels by structural position:

``` text
row 1 / column 2
top-centre
panel 2
```

Selection should not require Nano to reinterpret what the panel means.

## 10. Feed the complete contact sheet back to Nano

The tested extraction method is deliberately simple.

Example:

``` text
Crop out the top-center image from this 3x3 contact sheet.

Return ONLY that single image as a standalone image.

Remove the surrounding 8 panels and all grid borders.

Expand the selected top-center image to fill the entire output canvas while preserving its exact content, composition, subjects, camera angle, perspective and lighting.

Do not generate a new shot.
Do not return the contact sheet.
Do not include a grid.
```

This step is treated as **structural extraction**, not creative
development.

The complete contact sheet is fed back to Nano. Nano resolves the
selected panel into a standalone production image.

## 11. Extraction law

> **Never repair the selected shot during extraction.**

Do not ask extraction to:

-   change a character;
-   move a prop;
-   redirect the crowd;
-   improve composition;
-   change camera angle;
-   repair scene geography;
-   invent missing information.

If the selected panel is wrong, go back to the scene-contact-sheet
stage.

This protects lineage:

``` text
scene master
    ↓
coverage sheet
    ↓
selected panel
    ↓
standalone extraction
```

------------------------------------------------------------------------

# PROCESS D --- VEO MOTION

## 12. Approve the standalone source frame

Before paying for Veo, inspect the extracted standalone frame.

It must pass the shot-specific visual gate.

For PUB-1105 Shot A this includes:

-   correctly scaled full-size pool table;
-   Damo already on the table;
-   pool cue horizontal overhead;
-   adult-size wooden stool and pint present;
-   packed room;
-   plausible crowd distribution;
-   band still reads as performance source;
-   Damo is part of the event rather than staged as its performer.

Only an approved standalone image becomes a Veo seed.

## 13. Persist the source

The approved extracted frame must be stored in the production asset
system / Studio server.

Record:

-   scene ID;
-   shot ID;
-   source/master lineage;
-   character reference lineage;
-   scene contact-sheet asset;
-   selected row/column/panel;
-   extracted standalone asset;
-   SHA-256 checksum;
-   prompt/version metadata.

The checksum ensures the exact approved image---not a similarly named
replacement---is sent to Veo.

## 14. Veo prompt responsibility

At this stage appearance and composition already exist.

The Veo prompt should therefore primarily describe **what changes
through time**.

For PUB-1105 Shot A:

-   Damo rocks with the chorus;
-   weight shifts naturally;
-   knees remain loose;
-   torso moves with the music;
-   cue remains securely horizontal overhead;
-   stool and pint remain stable;
-   surrounding crowd members continue independent actions;
-   foreground bodies occasionally cross or interfere;
-   a few nearby people may naturally react to Damo;
-   attention remains distributed;
-   handheld phone instability is small and physical;
-   minor bumps and imperfect reframing are desirable.

Avoid asking Veo to redesign the room or establish character appearance
from scratch.

## 15. Camera motion

The camera behaves like a phone physically held by somebody inside the
crowd.

Preferred:

-   small handheld instability;
-   subtle operator sway;
-   minor crowd bumps;
-   momentary occlusion;
-   tiny corrective reframes;
-   imperfect sight lines.

Avoid:

-   crane moves;
-   sweeping cinematic dollies;
-   impossible overhead motion;
-   hero push-ins;
-   stabilised commercial-camera movement;
-   camera choreography that makes Damo a performer.

## 16. Veo generation

Generate approximately **6--8 seconds** of source motion per planned
take.

The complete generated duration is raw material, not an editing
obligation.

For the current PUB-1105 architecture:

``` text
A — Damo wide/discovery
B — Damo close
C — Emma/Brock crowd coverage
D — band/room insert
E — wide return if A cannot supply it
```

Do not automatically generate E if later footage from A provides the
required return.

## 17. Existing automated execution path

The repository already contains a GitHub Actions route for PUB coverage
Veo validation.

A trigger written under:

``` text
studio/veo-coverage-triggers/*.json
```

causes the workflow to:

1.  resolve the exact Studio-server seed path;
2.  verify its SHA-256;
3.  invoke `run_pub_coverage_veo.py`;
4.  run one Veo Lite generation;
5.  retrieve the generated result;
6.  strip generated audio;
7.  probe the resulting video;
8.  checksum the final video;
9.  upload the result as a workflow artifact.

The source image therefore has to exist on the Studio server before the
trigger can execute.

------------------------------------------------------------------------

# PROCESS E --- REVIEW AND EDIT

## 18. Review the raw take

Judge the generated take as footage, not as a six-second finished scene.

Identify the strongest usable fragment.

A six-second generation may yield only:

-   1.2 seconds;
-   2.5 seconds;
-   3 seconds;

of excellent footage.

That is acceptable.

Reject or trim around:

-   identity drift;
-   prop mutation;
-   cue orientation failure;
-   furniture scale changes;
-   crowd synchronisation;
-   unwanted hero behaviour;
-   impossible camera motion;
-   obvious temporal artefacts.

## 19. PUB-1105 target edit

Current editorial grammar:

``` text
0:00–0:03.0   Damo wide / discovery
0:03–0:04.5   Damo close
0:04.5–0:06.5 Emma + Brock
0:06.5–0:08.0 Band / room source
0:08–0:10.0   Physical detail
0:10–0:13.0   Wide return
```

These are targets, not compulsory durations.

The strongest generated fragments determine the final cut.

Expected finished social length: approximately **10--13 seconds**.

## 20. Sound

Generated Veo audio is not required for World 01.

Audio is stripped from the raw generation and the scene soundtrack is
authored in post.

This prevents generated audio from controlling timing, musical
continuity or editorial decisions.

------------------------------------------------------------------------

# Production laws

1.  **Character identity is established before scene coverage.**
2.  **The scene master owns spatial truth.**
3.  **Character contact sheets own expanded visual identity.**
4.  **Scene contact sheets explore camera observations, not alternate
    worlds.**
5.  **Multiple character contact sheets may be supplied when a shot
    genuinely contains multiple identity-critical characters.**
6.  **The complete contact sheet is fed back to Nano for selected-panel
    extraction.**
7.  **Extraction is structural, not corrective.**
8.  **Failed panels are fixed upstream.**
9.  **Veo animates an approved shot; it does not design the shot.**
10. **The Veo prompt primarily describes temporal change.**
11. **Generated duration is raw footage; only keeper fragments need to
    reach the edit.**
12. **Crowd attention is distributed, not artificially blind to
    recurring characters.**
13. **Continuity is never solved by independently regenerating the
    world.**

------------------------------------------------------------------------

# Canonical flow

``` text
CHARACTER
Approved full-body/headshot
        ↓
Nano character contact sheet
        ↓
Character sheet approval

WORLD
Approved 16:9 scene master
        +
Relevant approved character contact sheets
        ↓
Nano scene contact sheet
        ↓
Scene coverage approval

SHOT
Choose panel structurally
        ↓
Feed complete sheet back to Nano
        ↓
Standalone extraction
        ↓
Shot approval
        ↓
Persist + checksum

MOTION
Approved standalone image
        ↓
Veo motion prompt
        ↓
6–8 second raw take
        ↓
Strip generated audio
        ↓
Review
        ↓
Keeper fragment

EDIT
Keeper fragments from coverage
        ↓
10–13 second World 01 scene
        ↓
Authored soundtrack in post
```

## Core principle

> **World/event → distributed human activity → camera observation →
> character incident → character identity.**

The camera does not create the event.

It finds it.
