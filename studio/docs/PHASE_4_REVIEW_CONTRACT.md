# SHIRTFACED STUDIO — PHASE 4 REVIEW CONTRACT

**Status:** Creative and structured-output specification  
**Depends on:** Stable Phase 3 generation-attempt IDs and image provenance  
**Authority:** `WORLD.md` Operating System → Continuity Director

## 1. Purpose

Phase 4 reviews each successful image attempt against the World 01 canon. It provides structured evidence to the owner; it never makes the final human decision, changes shot status, appends continuity or edits permanent canon.

Review is a separate model operation from generation. A technically stored image is not an approved image.

## 2. Inputs

Every review request contains:

- generation attempt ID and image;
- shot ID, scene, exact hero product and camera values;
- production prompt and rationale;
- canon document hashes used for generation;
- the relevant planner-visible canon excerpts;
- the stable Continuity Director review headings from `WORLD.md`;
- recent approved/rejected context needed for rotation and repetition;
- verified vehicle/product constraints;
- prior attempts for the same shot only where comparison is requested.

The model must not infer missing product specifications or treat unverified image text as fact.

## 3. Overall verdict

The model returns one of:

- `APPROVE_RECOMMENDED`
- `APPROVE_WITH_NOTE_RECOMMENDED`
- `REJECT_RECOMMENDED`
- `REVIEW_UNCERTAIN`

These are recommendations. Phase 5 records the owner’s decision using the canon’s human-facing outcomes `APPROVED`, `APPROVED WITH NOTE` or `REJECTED`.

`REVIEW_UNCERTAIN` is required when image evidence is insufficient, ambiguous or below the model’s reliable visual resolution.

## 4. Gate result structure

Each gate returns:

- `status`: `PASS`, `FAIL`, `UNCERTAIN`, or `NOT_APPLICABLE`;
- `evidence`: one concise, visible observation;
- `codes`: zero or more stable rejection/finding codes;
- `confidence`: 0.0–1.0;
- `material`: whether the finding can change the recommendation.

Evidence describes what is visible. It does not produce generic aesthetic commentary.

## 5. Gates

### Mood

Tests optimism, momentum and possibility. Quiet is allowed; resignation, exhaustion, humiliation, violence and intoxication-as-joke are not.

Codes: `MOOD_NO_OPTIMISM`, `MOOD_RESIGNATION`, `MOOD_DRUNKEN_COMEDY`, `MOOD_UNSAFE`, `MOOD_GENERIC_CAMPAIGN`.

### Australian authenticity

Tests plausible Australian architecture, vehicles, streets, venues, objects and behaviour without reliance on flags or cliché.

Codes: `AU_GENERIC`, `AU_NORTH_AMERICAN_DRIFT`, `AU_WRONG_ARCHITECTURE`, `AU_WRONG_VEHICLE`, `AU_CLICHE`.

### Product visibility and truth

Tests whether the nominated hero is present, naturally visible and exact enough for the shot’s purpose. Every garment remains blank. A back-view scene means a visible blank rear surface of the nominated real garment product, never artwork.

Codes: `PRODUCT_MISSING`, `PRODUCT_NOT_CLEAR`, `PRODUCT_FORCED`, `PRODUCT_WRONG_ITEM`, `PRODUCT_WRONG_COLOUR`, `PRODUCT_INACCURATE`, `PRODUCT_INVENTED_GRAPHIC`, `PRODUCT_INVENTED_LABEL`, `PRODUCT_CAP_PANEL_HIDDEN`.

### Third-party branding

Tests garments, consumables, vehicles and environmental objects for **readable** third-party branding. Incidental Shirtfaced environmental easter eggs are permitted; garments and packaging remain blank/generic.

**Branding turns on what the brand sells, not on whether a mark is visible.** These are two rules, not one:

- **Apparel** — worn, carried, folded, or on a poster behind — is blank always. No background exemption, no allowance for distance or blur.
- **Everything else** may carry real branding and is *wanted*: servo boards, shopfronts, buses, signage, packaging, cans. It fails only when it stops being background — centred, held up, presented, or large and legible enough to take the eye first.

An unbranded object is never a branding failure. Where a mark is present but illegible, return `UNCERTAIN` rather than `FAIL`.

This gate was the least reliable of the nine in live use — across three consecutive frames it failed a permitted esky sticker, failed an explicitly unbranded drink can, and failed paper bags that "could potentially carry" a mark. That looked like a model defect and was at least partly a canon defect: `CONTINUITY.md` carried a stale note reading "readable third-party commercial branding anywhere in frame is a failure", which contradicts Rule Two above and reached the reviewer on every request. The reviewer was enforcing two incompatible rules at once. Resolved 5 August 2026 in favour of Rule Two; the note is gone and a test now fails if it returns.

Codes: `BRAND_THIRD_PARTY_VISIBLE`, `BRAND_GARMENT_MARK`, `BRAND_PACKAGING_MARK`, `BRAND_SHIRTFACED_TOO_PROMINENT`.

### Vehicle continuity

Where a vehicle appears, tests Australian form, secondary narrative role, **where the camera is**, and **what people are doing with the vehicle**. If no relevant vehicle appears, return `NOT_APPLICABLE`.

Colour, cab configuration and age are open — a black dual cab is an ordinary Australian work vehicle. What fails is the wrong body shape, the camera inside the cabin, or anyone getting into or out of the vehicle.

A correct body shape does not pass this gate on its own. A live review returned `vehicle_compliant: true` for a photograph taken from the passenger seat, which the oldest rule in the vehicle canon forbids.

Codes: `VEHICLE_AMERICAN_PICKUP`, `VEHICLE_ENCLOSED_TUB`, `VEHICLE_LIFESTYLE_HERO`, `VEHICLE_TOO_PROMINENT`, `VEHICLE_CAB_OVER`, `VEHICLE_CAMERA_INSIDE`, `VEHICLE_ENTERING_OR_EXITING`, `VEHICLE_OCCUPANT_MISORIENTED`.

### Wardrobe balance

Tests natural distribution of black product-ready garments, varied non-product clothing and absence of coordinated uniforms.

Codes: `WARDROBE_ALL_BLACK`, `WARDROBE_TOO_COORDINATED`, `WARDROBE_LOGO`, `WARDROBE_PRODUCT_DOMINANCE`, `WARDROBE_IMPLAUSIBLE`.

### Composition

Tests believable photographer position, accidental framing, useful imperfection, readable faces where needed and product visibility arising from action.

Codes: `COMPOSITION_POSED`, `COMPOSITION_TOO_CLEAN`, `COMPOSITION_CAMERA_IMPLAUSIBLE`, `COMPOSITION_PRODUCT_DISPLAY`, `COMPOSITION_NO_DOCUMENTARY_DEPTH`, `COMPOSITION_FACE_UNREADABLE`.

### Documentary credibility

Tests whether the photograph feels taken rather than designed and whether people interact with one another instead of performing for camera.

Codes: `DOCUMENTARY_PERFORMANCE`, `DOCUMENTARY_FASHION`, `DOCUMENTARY_STOCK`, `DOCUMENTARY_STAGED_IMPERFECTION`, `DOCUMENTARY_MODEL_ARTEFACT`.

### Story

Tests a clear social action, a plausible five seconds before/after and a reason the night continues.

Codes: `STORY_NO_ACTION`, `STORY_NO_BEFORE_AFTER`, `STORY_REPEATED_BEAT`, `STORY_NO_CONTINUATION`, `STORY_PRODUCT_IS_PLOT`.

### Structural plausibility

Tests whether the thing photographed could physically exist. This is a fact check, not a taste judgement, and it is the only gate that asks the question.

- Is anything missing that must be there — seats, a vehicle's rear body, a floor?
- Is every person supported by a surface that is visible or clearly implied?
- Does the furniture match the people: a row built for two cannot seat three, and a seat faces the way it is bolted down?
- Counts and joins: limbs, fingers, chair legs, wheels, doors, and reflections that disagree with the scene.

Set `structurally_sound` false whenever this gate fails.

The other nine gates all judge taste and intent. A frame can be beautiful, documentary and unmistakably Australian while showing something impossible, and in live use it repeatedly was: a car with no front seats scored documentary credibility 4/5, and a van whose entire rear body was absent — the road visible straight through the opening — scored 5/5 and passed vehicle continuity. Neither score was wrong. Nothing in the rubric named physical structure, so nothing looked at it.

Codes: `STRUCTURE_MISSING_ELEMENT`, `STRUCTURE_UNSUPPORTED_BODY`, `STRUCTURE_IMPOSSIBLE_SEATING`, `STRUCTURE_GEOMETRY_CONFLICT`, `STRUCTURE_ANATOMY`, `STRUCTURE_REFLECTION_CONFLICT`.

#### This gate does not work yet, and physical correctness is human-checked

Measured, not assumed. A draft of W01-011 contained an orphaned car door — a red door panel and a window frame with no vehicle behind them, at the wrong scale, sitting at footpath level with a woman inside it. Both configured review models were asked to judge that frame against this gate:

| Model | `structurally_sound` | Evidence |
|---|---|---|
| `gpt-4o-mini` | `true` | "All elements in the photograph appear to exist as part of the scene" |
| `gpt-5.5` | `true` (confidence 0.83) | "the vehicle and parking meter read as physically coherent" |

The stronger model was not better. It asserted the vehicle was coherent, in a frame containing no vehicle. So the earlier hypothesis — that the rubric was the constraint and a more capable reviewer would apply it — is wrong. Neither tier performs the check.

**Therefore: physical correctness is a human responsibility.** The owner checks structure; the reviewer does not. A `structural_plausibility: PASS` is not evidence that anything was verified, and must never be read as clearance.

The gate is kept anyway, for three reasons: it occasionally fires on gross cases, it gives structural findings somewhere to be recorded when a human does spot one, and its presence makes the omission visible rather than silent — which is what went wrong when there was no such gate at all.

Revisit if a materially better vision model becomes available. The test is cheap: re-review a stored attempt, generate nothing.

## 6. Material failure rules

Recommend rejection when any clearly evidenced foundational failure occurs:

- wrong or materially inaccurate nominated product;
- any garment graphic, logo, text, embroidery or visible label;
- readable third-party branding;
- posed/fashion-campaign behaviour;
- American pickup or prohibited ute body where visible;
- emotional resignation or unsafe/drunken-comedy drift;
- image has no independent documentary value;
- severe generation artefact compromising people, product or scene;
- anything that could not physically exist — missing structure, an unsupported body, seating that does not fit;
- a camera inside a vehicle, or anyone entering or leaving one.

A structural failure is material whatever the gate's `material` flag says, because the photograph shows something that cannot be. The recommended-action summary reports it separately for that reason: an unmarked gate must not be able to bury it.

Recommend approval with note only when the image belongs to World 01 and the note records a non-blocking continuity fact or genuinely repeatable rule. Do not use it to excuse a foundational failure.

## 7. Concise review output

In addition to gate objects, return only:

- `recommendation`;
- `strongest_success`: one sentence;
- `material_drift`: one sentence or `null`;
- `new_rule_proposal`: one concise repeatable rule or `null`;
- `next_hero_product`: exact normalized value or `null`;
- `next_camera`: exact normalized value or `null`.

No long generic critique. A new rule proposal must describe a repeatable failure not already covered by canon.

## 8. Proposed JSON shape

```json
{
  "attempt_id": "string",
  "recommendation": "APPROVE_RECOMMENDED | APPROVE_WITH_NOTE_RECOMMENDED | REJECT_RECOMMENDED | REVIEW_UNCERTAIN",
  "gates": {
    "mood": {"status": "PASS", "evidence": "string", "codes": [], "confidence": 0.0, "material": false},
    "australian_authenticity": {},
    "product_visibility": {},
    "third_party_branding": {},
    "vehicle_continuity": {},
    "wardrobe_balance": {},
    "composition": {},
    "documentary_credibility": {},
    "story": {},
    "structural_plausibility": {}
  },
  "structurally_sound": true,
  "strongest_success": "string",
  "material_drift": null,
  "new_rule_proposal": null,
  "next_hero_product": "Hoodie waist",
  "next_camera": "Inside lift"
}
```

The implementation must replace empty objects with the complete gate schema and validate exact enum values through Pydantic.

## 9. Confidence and uncertainty

Confidence is evidentiary, not decorative. The reviewer returns `UNCERTAIN` instead of guessing about tiny labels, exact fabric construction, obscured vehicle bodies or ambiguous environmental marks.

Low confidence cannot support a material failure by itself. It can request human inspection.

## 10. Model and persistence requirements

- Keep the review model configurable.
- Validate structured output before persistence.
- Store model ID, prompt/review schema version, token/cost usage where returned, canon hashes and raw safe provider ID.
- Reviews are immutable; a re-review creates another linked result.
- Tests use fixtures/mocks and never call a live model.
- A review cannot update Markdown, shot status or attempt decision.

## 11. Human review presentation

Show image, prompt, rationale, recommendation, ten gate summaries, strongest success, material drift and any proposed rule. Failed/uncertain gates are expanded first. The owner can approve, reject or request variation independently of the recommendation.

Any proposed permanent rule enters the Phase 6 proposal path; it never changes `WORLD.md` during review.

## 12. Acceptance fixtures

The Phase 4 test set should include:

1. correct W01-011 car interior with natural tote visibility;
2. same scene with a branded chip packet;
3. same scene with an American pickup body;
4. correct apartment lift with hoodie at waist;
5. posed lift fashion lineup;
6. W01-013 blank back surface;
7. W01-013 with an invented back graphic;
8. quiet optimistic sunrise balcony;
9. miserable hangover interpretation;
10. ambiguous tiny environmental mark requiring `UNCERTAIN`.

Added after live use, each one a frame the original nine gates passed:

11. car with no front seats — every creative gate passes, `structural_plausibility` fails;
12. van with no rear end — scored documentary credibility 5/5 and `vehicle_compliant` true in the live review;
13. camera inside the cabin — correct vehicle body, forbidden camera position;
14. plain unbranded can in the foreground — `third_party_branding` must pass.

Each fixture has expected material gate outcomes, not pixel-perfect prose.

## 13. Gate reliability, measured

Seven frames were generated on 5 August 2026 and every gate verdict was checked
against the image by hand, zooming in. This is what that found. It is recorded because
the recommendation reads with the same authority whether it is right or wrong, and
nothing else in the repository says which parts to believe.

| Gate | Verdict |
|---|---|
| `australian_authenticity` | Reliable. Scored 4–5 throughout and never disagreed with the image. |
| `documentary_credibility` | Reliable on staging. Says nothing about whether the scene is possible. |
| `structural_plausibility` | Unreliable. Passed an orphaned car door at two model tiers. See above. |
| `vehicle_continuity` | Unreliable in both directions. Passed a van with no rear end and a camera inside a cabin; failed three frames that obeyed the canon, twice describing a seated passenger at an open window as the camera being inside the car. |
| `third_party_branding` | Unreliable. Four verified wrong calls in seven frames, before and after the instructions were rewritten: a permitted esky sticker, an explicitly unbranded drink can, bags that "could potentially carry" a mark, and illegible packaging that should have returned `UNCERTAIN`. |
| `mood`, `story` | Unresponsive. Scored 2–3 on every frame regardless of prompt, including after the mood block and closing line were added specifically to address them. |

Two consequences.

The recommendation is not a filter. It has rejected every frame produced this session,
including the structurally soundest one, and its stated reasons have frequently been
wrong about what is in the image. Read the gate **evidence**, which is often sharper
than the verdict it supports, and decide from the photograph.

Do not tune prompts against these scores. A day was spent doing that. The prompt was
measurably improved by comparison against the seeded reference set — a fixed, human
artefact — and not at all by chasing gate numbers that do not move.

## 14. Gate count

Ten. Tests assert `len(GateName)` rather than a literal, so adding the eleventh does not require finding every hardcoded `9` — which, when the tenth was added, appeared in six places across three files.
