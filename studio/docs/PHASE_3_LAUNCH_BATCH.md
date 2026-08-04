# SHIRTFACED STUDIO — PHASE 3 LAUNCH BATCH

**Source of truth:** Claude worktree `confident-kapitsa-67af50`  
**Canon state reviewed:** 5 August 2026  
**Purpose:** Creative acceptance set for Phase 3 image generation and attempt history

## 1. What this batch tests

This is not a new shotlist. It is a controlled first run through the existing planned sequence.

The batch tests whether Phase 3:

- uses the shot selected by Phase 2 rather than inventing another;
- preserves exact hero-product and camera values;
- carries the planner-visible canon into the production prompt;
- makes every garment and consumable blank/generic;
- preserves Australian specificity and the tray-back vehicle rule;
- produces an image worth saving without the product;
- records multiple attempts without treating generation as approval;
- retains prompt, canon hashes, model settings and output provenance.

## 2. Run order

Use the application’s deterministic selector. Do not manually advance to the next shot until the current one has passed through the intended human decision flow.

Initial acceptance set:

1. `W01-011` — Car interior transition.
2. `W01-012` — Apartment lift.
3. `W01-013` — Apartment balcony.
4. `W01-014` — Kitchen kick-ons II.
5. `W01-015` — Sunrise balcony.

This sequence exercises five different camera strings and four hero-product roles while continuing the night from approximately 3:32am into sunrise.

## 3. Attempt strategy

For each shot:

- Generate Attempt A from the unmodified Phase 2 production prompt.
- Inspect provenance before judging the image.
- If a variation is needed, record one concise, shot-specific instruction and generate Attempt B under the same shot identity.
- Never change `WORLD.md` merely to rescue one weak output.
- Propose a canon change only if the same repeatable drift appears across attempts.

Two attempts are a ceiling for the launch batch unless the attempt machinery itself is being tested. The goal is to learn whether the pipeline works, not to brute-force a hero image.

## 4. W01-011 — Car interior transition

**Machine values:** `Tote bag` · `Rear seat`  
**Narrative position:** After the lookout; friends reorganise before the next stop.  
**Primary creative test:** Can a quiet car interior still feel full of renewed momentum?

Expected image evidence:

- photographer plausibly in the rear seat, looking through an open passenger door;
- ordinary friends reorganising seats, generic food and drinks;
- plain black tote bag naturally clear without being displayed;
- dome light, dashboard glow and streetlight spill;
- door frame obscuring part of the image and one person naturally cropped;
- no heroic vehicle composition;
- any visible ute remains an Australian open alloy tray-back;
- clothing and packaging completely blank, while subtle Shirtfaced environmental easter eggs remain permitted under the amended canon.

Reject if:

- the tote is held up or arranged for camera;
- the group reads tired, stranded or resigned;
- the viewpoint is outside the car or becomes automotive advertising;
- an American pickup body appears;
- visible third-party branding or garment graphics appear;
- everyone wears identical black outfits.

Phase 3 acceptance evidence:

- exact `Tote bag` and `Rear seat` snapshots persist;
- prompt and three canon hashes are inspectable;
- Attempt B, if made, links to the same shot without mutating Attempt A;
- successful storage does not mark the shot approved.

## 5. W01-012 — Apartment lift

**Machine values:** `Hoodie waist` · `Inside lift`  
**Narrative position:** The group moves vertically into the next stage of kick-ons.  
**Primary creative test:** Can a confined, ordinary location retain social momentum without looking staged?

Expected image evidence:

- crowded but believable Australian apartment lift;
- hoodie tied naturally around one waist and visible through movement;
- uneven attention: friends speaking to each other, nobody facing camera deliberately;
- practical lift lighting, reflective surfaces and imperfect crop;
- a clear sense that the doors have just closed or are about to open.

Reject if:

- the group becomes a fashion lineup or mirror selfie;
- the hoodie knot is unnaturally presented;
- lift signage introduces readable third-party/property branding;
- the image lacks a before-and-after story.

## 6. W01-013 — Apartment balcony

**Machine values:** `T-shirt` · `Inside lounge`  
**Narrative position:** Camera remains inside while activity continues at the balcony threshold.  
**Primary creative test:** Can the planner reveal the blank rear surface of the nominated T-shirt through a real balcony action?

Required interpretation:

The hero product is the T-shirt. “Back view” in the machine-visible scene title defines the composition opportunity; it is never a separate product and never permission to generate artwork.

Expected image evidence:

- camera physically inside the lounge looking outward;
- one blank garment back naturally clear as its wearer joins a balcony conversation;
- interior spill against early pre-dawn exterior light;
- friendships and conversation remain the reason for the frame.

Reject if any graphic, logo, text, label or embroidery appears on the garment.

This tests whether scene wording can carry placement intent while the hero-product column remains a real product.

## 7. W01-014 — Kitchen kick-ons II

**Machine values:** `Tote bag` · `Hallway`  
**Narrative position:** A second kitchen beat viewed from outside the room.  
**Primary creative test:** Does product rotation permit the tote to return after intervening products without repeating W01-011’s visual logic?

Expected image evidence:

- camera in the hallway with doorframe or wall obstruction;
- distinct social action from the earlier house-party kitchen;
- tote used for an ordinary purpose, not placed as a still life;
- renewed or sustained momentum, not people merely occupying a kitchen;
- warmer domestic light and different camera distance from W01-011.

Reject if it repeats the dining-room/island composition from W01-006 or turns the tote into the scene’s emotional subject.

## 8. W01-015 — Sunrise balcony

**Machine values:** `Hoodie` · `Balcony doorway`  
**Narrative position:** The night reaches morning without collapsing into regret.  
**Primary creative test:** Can sunrise remain optimistic, social and unresolved rather than becoming hangover content?

Expected image evidence:

- camera at the balcony doorway with a plausible physical position;
- blank black heavyweight hoodie clear through natural layering or morning cold;
- early window/sky light mixed with remaining apartment warmth;
- quiet connection, an emerging plan or emotional lift;
- restrained colour with accurate black fabric.

Reject if:

- subjects look miserable, incapacitated or ashamed;
- sunrise becomes glossy lifestyle advertising;
- the hoodie is posed or isolated;
- the scene reads as a definitive ending.

## 9. Human launch scorecard

Use this temporary scorecard until the formal review phase is available. It is a human worksheet, not an automated Phase 3 feature.

For every attempt answer yes/no:

1. Is the selected shot identity correct?
2. Are hero product and camera values preserved exactly?
3. Is the nominated product naturally visible?
4. Are every garment and consumable blank/generic?
5. Is the social action clear five seconds before and after?
6. Does the camera have a plausible physical position?
7. Does the image feel Australian without flags or cliché?
8. Does the emotional read retain optimism and possibility?
9. Is any vehicle secondary and canon-correct?
10. Would the image be worth saving with plain black clothing?
11. Does it add a new visual beat rather than repeat an approved reference?
12. Is attempt provenance complete?

Record only the strongest success, material drift, genuinely repeatable new rule if any, and whether another variation is justified.

## 10. Known issues to watch

### Back-view placement and blank garments

W01-013 now uses the real hero product `T-shirt`; `Apartment balcony back view` carries placement intent in the parsed scene title. Phase 3 must never generate artwork, text, labels or embroidery.

### Branding note now resolved

Commit `d8c04a1` resolves the prior conflict: third-party branding is banned; incidental Shirtfaced environmental easter eggs are permitted; garments remain blank. No unresolved-branding UI warning belongs in Phase 3.

### Current canon note wording — resolved

`CONTINUITY.md` now matches amended `WORLD.md`: readable third-party commercial branding fails, while incidental Shirtfaced environmental easter eggs remain permitted.

## 11. Batch completion

The launch batch is complete when all five shots have at least one durable attempt, the application proves attempt separation and provenance, human decisions remain explicit, no Markdown is changed by generation, and the findings clearly distinguish:

- a one-off model failure;
- a prompt-planning failure;
- a persistent canon gap;
- an application/provenance failure.

Only persistent canon gaps should return to the World Architect.
