# shirtfaced — Nano Banana Contact-Sheet Pipeline

**Status:** ACTIVE production contract  
**Scope:** Character identity expansion, scene coverage expansion and Nano Banana panel extraction before motion generation.

## Governing sequence

The two contact-sheet operations are separate, ordered and dependent:

`canonical character reference(s) → character contact sheet → approved character contact-sheet asset`

then

`approved scene master + relevant approved character reference/contact-sheet asset(s) → scene coverage contact sheet → approved scene contact-sheet asset`

then

`approved contact sheet + requested panel → Nano Banana standalone extraction → approved still/source frame → motion generation`

The character contact-sheet stage establishes reusable visual coverage of identity. The scene contact-sheet stage establishes useful camera coverage of one already-approved world. They are not interchangeable.

## 1. Character contact sheet

Use `NANO_BANANA_CHARACTER_CONTACT_SHEET_PROMPT.md`.

Input:

- canonical/approved character identity image(s)
- resolved appearance state where required

Output:

- one 3x3 character contact-sheet asset containing the same exact character across useful scales and angles

The contact sheet is a first-class reference asset. Preserve its attempt, prompt, model/settings, input manifest and hash.

Do not automatically split/crop its nine cells into final references. When a standalone view is needed, feed the approved contact sheet back to Nano Banana and run the extraction operation.

## 2. Character panel extraction

Use `NANO_BANANA_CONTACT_SHEET_EXTRACTION_PROMPT.md` with the approved character contact sheet as the primary input.

Optional additional inputs:

- original canonical identity reference(s)
- current approved appearance reference(s)

The requested contact-sheet panel determines the view. Nano Banana returns one standalone full-resolution image reproducing that selected view. The extraction attempt records the contact-sheet asset as its parent/reference input.

An extracted character view becomes an approved reusable reference only after normal review/approval.

## 3. Scene coverage contact sheet

Use `NANO_BANANA_SCENE_COVERAGE_PROMPT.md` as the generic master. Each production scene may persist its own resolved scene-specific copy with scene facts and failure constraints injected without changing the master architecture.

Inputs:

- approved scene/world master image — spatial, compositional and environmental authority
- relevant approved character reference/contact-sheet assets — identity authority
- scene-specific prompt instance

Reference selection is shot/coverage dependent. Do not force one character per generation and do not send every recurring character merely because they exist in the scene.

Examples:

- Damo-focused coverage: scene master + Damo reference/contact sheet
- Emma + Brock coverage: scene master + Emma reference/contact sheet + Brock reference/contact sheet
- band/environment coverage with no identity-critical recurring cast: scene master may be sufficient

When multiple recurring characters are identity-critical in one panel, supply multiple approved character references/contact sheets where supported by the active Nano Banana model/path.

The scene master remains spatial authority. Character references do not grant permission to relocate a person or rebuild the world around a cleaner identity view.

## 4. Scene panel extraction

Feed the approved scene coverage contact sheet back to Nano Banana using `NANO_BANANA_CONTACT_SHEET_EXTRACTION_PROMPT.md`.

Inputs:

- approved scene coverage contact sheet
- requested panel number/description
- requested delivery aspect ratio
- relevant character references/contact sheets when identity reinforcement is needed
- approved scene master when spatial/detail reinforcement is needed

Output:

- one standalone full-resolution still representing the selected contact-sheet observation

This is not a literal pixel crop requirement. Nano Banana uses the approved contact sheet as visual authority and reproduces the chosen view as a standalone production image, resolving missing fine detail conservatively from the same approved reference set.

The extraction must not invent a new camera angle, restage the scene, move characters, alter props or create a different version of the world.

## 5. Motion handoff

Only after a standalone scene panel has been reviewed/approved does it become the first-frame/source still for motion generation.

`approved standalone scene shot → shot-specific motion prompt → Veo/raw motion generation → keeper-range review → edit`

The motion generator does not choose scene coverage. That decision has already been embodied visually in the approved standalone shot.

## 6. Provenance / data requirements

Persist every stage as a distinct generation attempt/asset with lineage:

- canonical character reference asset(s)
- character contact-sheet attempt + output asset
- character extraction attempt + standalone character asset where used
- approved scene master asset
- scene coverage contact-sheet attempt + output asset
- scene extraction attempt + standalone scene-shot asset
- motion attempt + video asset
- keeper selection/edit lineage

For every attempt retain:

- exact prompt/template version
- resolved scene-specific prompt where applicable
- model/provider/settings
- exact input/reference manifest
- parent attempt/asset lineage
- asset hashes
- dimensions/aspect ratio
- review and human decision

A contact sheet is not a disposable UI preview. It is a persisted visual planning/reference artifact.

## 7. Authority hierarchy

For scene coverage and extraction:

1. owner-approved narrative/scene canon controls facts and action
2. approved scene master controls geography, composition, crowd placement, props and lighting
3. approved character references/contact sheets control recurring-character identity and appearance
4. approved scene contact sheet controls the selected camera observation
5. extraction reproduces that observation as a standalone still
6. motion generation animates the approved still without re-solving coverage

## 8. Superseded crop assumption

Where older PUB-1105 notes describe the route as:

`approved 16:9 master + focus → deterministic 9:16 crop/reframe → Veo`

that is superseded for the Nano Banana contact-sheet path by:

`approved scene master + relevant approved character refs → Nano scene coverage contact sheet → Nano selected-panel extraction at target aspect ratio → review/approval → Veo`

A deterministic pixel crop may still be used as an explicit fallback/tooling operation when intentionally selected, but it is no longer the governing continuity/coverage method for this workflow.