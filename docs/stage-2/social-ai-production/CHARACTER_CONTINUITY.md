# shirtfaced — Character and Wardrobe Continuity

**Status:** ACTIVE contract  
**Scope:** Persistent cast identity and appearance state across AI-generated campaign media  
**Reviewed:** 16 August 2026

---

## 1. Purpose

Characters are durable production entities, not repeated prompt descriptions.

The system must be able to answer, for any shot:

- who the person is
- which global canon character they resolve to
- which approved visual identity version is authoritative
- what they look like
- what they are wearing at this point in the story
- what may change
- what must not drift
- which references the generator and reviewer should use

This closes the gap where cast identity exists only in prose or only in an AI conversation.

---

## 2. Global canon vs campaign materialisation

`docs/foundations/CHARACTERS.md` is the global narrative authority for the recurring cast across worlds/campaigns.

The campaign-domain `characters` records described in the production data model are **operational materialisations of that canon for a campaign**, not a licence to create a different Damo, Emma or Brock for every campaign.

A recurring-character campaign row should therefore carry or resolve a stable global canonical slug/identity key where the implementation supports it.

If campaign data conflicts with owner-approved global character canon or the current approved visual reference, the campaign data is stale/wrong and must be corrected. The campaign row does not outrank canon.

Anonymous one-scene background people may remain campaign-local and need no global character entry.

---

## 3. Character identity

A campaign character record should carry stable identity facts such as:

- UUID
- campaign FK
- global canonical slug/key where recurring
- internal handle / canonical name
- story role
- age band
- height/build intent
- face descriptors where useful for review/search
- hair
- facial hair
- approved skin features / scars / tattoos / piercings where relevant
- body-language / performance notes
- voice/dialogue notes where applicable
- stable reference media assets or reference-version IDs
- allowed variation
- forbidden drift
- active state

The reference image remains the visual identity authority where one exists. Text descriptors do not override the approved file.

Do not encode sensitive real-person identity unless explicitly required and authorised; campaign characters are normally synthetic/persona entities.

---

## 4. Appearance versions

Wardrobe and mutable appearance live in `character_appearances`, not as one mutable block on the character identity.

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
- hair state if deliberately changed
- facial-hair state if deliberately changed
- dirt/wetness/damage state
- allowed continuity changes
- forbidden changes
- reference media assets

This supports, for example, a hoodie added later in the night without rewriting what the character wore earlier.

A change is mutable only because canon says it can change. The generator does not get to create an appearance version by accident.

---

## 5. Garment fidelity

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

## 6. Scene and shot resolution

A scene resolves which characters participate and which appearance applies.

A shot may inherit the scene appearance or explicitly select another valid appearance only when continuity permits it.

Resolution order:

1. global canonical character identity
2. approved visual identity/reference version
3. story/scene applicability
4. character appearance/wardrobe state
5. shot-specific blocking/exposure/action
6. provider reference manifest

The generation prompt consumes this resolved state. It does not choose identity or wardrobe ad hoc.

Literal provider-facing prose may remain anonymous (`the man from reference 1`, `one bloke`, etc.) while the production manifest resolves that role to the canonical slug. Anonymous provider wording must never mean anonymous production identity.

---

## 7. Reference hierarchy

Reference media should be purpose-tagged.

Useful classes:

- canonical face/identity
- full-body proportions
- current wardrobe front
- current wardrobe back
- garment artwork
- accessory/prop relationship
- prior approved adjacent shot
- provider-native reusable character derived from canonical references

When references conflict:

1. owner-set narrative canon wins on story facts;
2. current approved canonical identity reference wins on identity;
3. current approved appearance wins on mutable wardrobe/state;
4. an adjacent prior shot wins only for details deliberately promoted into continuity state.

Incidental model inventions never outrank those sources.

---

## 8. Canon integrity / forbidden invention

For an established recurring character, omission is not permission to invent a permanent or distinguishing feature.

Unless approved canon or appearance state says otherwise, generation must not add or remove identity-changing traits such as:

- tattoos
- scars
- piercings
- jewellery
- glasses
- facial-hair changes
- hair colour/style changes
- body/build changes
- distinctive accessories

A result that does so fails continuity even if the rest of the scene is strong.

Natural story-driven effects such as sweat, flushed skin, rumpled clothing, dirt, wetness or fatigue are allowed when appropriate and must themselves persist if continuity requires it.

---

## 9. Continuity state changes

Changes must be deliberate and attributable to a story event or scene transition.

Examples:

- jacket removed
- sleeves rolled
- shirt becomes wet
- dirt appears after fall
- hat lost
- drink/prop changes hands
- injury/bandage appears
- deliberate shave/stubble progression where the story spans enough time for it

A state change records where it begins. Later shots inherit it until another declared change occurs.

Unexplained drift is a review failure, not a creative variation.

---

## 10. Character review dimensions

Applicable automated-review gates may include:

- identity match
- hair/facial-hair continuity
- body/build continuity
- approved distinguishing-feature continuity
- absence of unauthorised distinguishing features
- wardrobe match
- garment colour
- garment artwork fidelity
- artwork placement/orientation
- accessory continuity
- dirt/wetness/damage continuity
- duplicate/missing character
- scene participation compliance

Applicability is determined before review. A gate irrelevant to the shot is not emitted merely to be marked `NOT_TESTED`.

A known identity failure should block the asset before owner presentation where the workflow can determine it reliably.

---

## 11. Human decision

Automated continuity evidence feeds the existing world `HumanDecision` flow.

A human may:

- approve
- approve with note where supported by existing workflow
- reject
- request variation

The decision remains attached to the generation attempt; character continuity does not create a second approval system.

Human approval can deliberately promote a new reference/appearance state. Merely approving a scene does not automatically make every accidental model detail permanent canon.

---

## 12. Provider-native characters

A reusable provider-native Character (for example, a Flow character object where supported) is an execution artifact derived from approved references.

It must record or be traceable to:

- provider
- provider object ID where available
- canonical character slug
- source reference version(s)
- voice source where applicable
- creation date

It does not replace `CHARACTERS.md` or the approved reference files. If it drifts, replace/rebuild the provider object rather than changing canon to match the provider.

---

## 13. Persistence invariant

A recurring campaign character cannot exist only as a prompt paragraph.

A campaign shot involving an identity-critical recurring character cannot become generation-ready unless:

- canonical identity resolves
- the applicable approved visual reference/version resolves
- appearance/wardrobe state resolves
- required reference assets are available to the selected generation path
- forbidden drift is known to the review path

If a required identity reference is unavailable to the active tool/session, do not generate a substitute person and call it continuity.
