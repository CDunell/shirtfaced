# shirtfaced — Character and Wardrobe Continuity

**Status:** ACTIVE contract  
**Scope:** Persistent cast identity and appearance state across AI-generated campaign media

---

## 1. Purpose

Characters are durable production entities, not repeated prompt descriptions.

The system must be able to answer, for any shot:

- who the person is
- what they look like
- what they are wearing at this point in the story
- what may change
- what must not drift
- which references the generator and reviewer should use

This closes the existing gap where cast identity exists only in prose.

---

## 2. Character identity

A character row belongs to one campaign and carries stable identity facts:

- UUID
- campaign FK
- internal handle / canonical name
- story role
- age band
- height/build intent
- face descriptors
- hair
- facial hair
- skin features / scars / tattoos / piercings where relevant and approved
- body-language / performance notes
- voice/dialogue notes where applicable
- stable reference media assets
- allowed variation
- forbidden drift
- active state

Do not encode sensitive real-person identity unless explicitly required and authorised; campaign characters are normally synthetic/persona entities.

---

## 3. Appearance versions

Wardrobe and mutable appearance live in `character_appearances`, not as one mutable block on `characters`.

Each appearance records:

- character FK
- campaign FK
- appearance code/version
- applicable story/scene range
- garment / approved-design references
- garment colour
- size / silhouette intent
- layer state
- front/back/left-chest/sleeve artwork references
- accessories
- footwear/headwear
- hair state if changed
- dirt/wetness/damage state
- allowed continuity changes
- forbidden changes
- reference media assets

This supports, for example, a hoodie added later in the night without rewriting what the character wore earlier.

---

## 4. Garment fidelity

Where a shirtfaced garment is present, continuity must distinguish:

- garment blank/silhouette
- colour
- artwork identity
- placement
- front vs rear graphic
- print scale
- layering/occlusion

The reviewer must not treat a roughly similar invented graphic as continuity success.

Approved design artwork/reference assets are the fidelity source where available.

---

## 5. Scene and shot resolution

A scene resolves which characters participate and which appearance applies.

A shot may inherit the scene appearance or explicitly select another valid appearance only when continuity permits it.

Resolution order:

1. character identity
2. story/scene applicability
3. character appearance/wardrobe state
4. shot-specific blocking/exposure
5. reference media assets

The generation prompt receives the resolved state. It does not choose wardrobe ad hoc.

---

## 6. Reference hierarchy

Reference media should be purpose-tagged.

Useful classes:

- canonical face/identity
- full-body proportions
- current wardrobe front
- current wardrobe back
- garment artwork
- accessory/prop relationship
- prior approved adjacent shot

When references conflict, canonical identity and current approved appearance outrank incidental prior-generation details unless continuity has explicitly promoted those details into state.

---

## 7. Continuity state changes

Changes must be deliberate and attributable to a story event or scene transition.

Examples:

- jacket removed
- sleeves rolled
- shirt becomes wet
- dirt appears after fall
- hat lost
- drink/prop changes hands
- injury/bandage appears

A state change records where it begins. Later shots inherit it until another declared change occurs.

Unexplained drift is a review failure, not a creative variation.

---

## 8. Character review dimensions

Applicable automated-review gates may include:

- identity match
- hair/facial-hair continuity
- body/build continuity
- wardrobe match
- garment colour
- garment artwork fidelity
- artwork placement/orientation
- accessory continuity
- dirt/wetness/damage continuity
- duplicate/missing character
- scene participation compliance

Applicability is determined before review. A gate irrelevant to the shot is not emitted merely to be marked `NOT_TESTED`.

---

## 9. Human decision

Automated continuity evidence feeds the existing world `HumanDecision` flow.

A human may:

- approve
- approve with note where supported by existing workflow
- reject
- request variation

The decision remains attached to the generation attempt; character continuity does not create a second approval system.

---

## 10. Persistence invariant

A recurring campaign character cannot exist only as a prompt paragraph.

A campaign shot involving a character cannot become generation-ready unless the required character identity and applicable appearance/wardrobe state resolve to persisted records and required references exist.
