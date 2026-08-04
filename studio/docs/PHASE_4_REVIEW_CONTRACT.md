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

Tests whether the nominated hero is present, naturally visible and exact enough for the shot’s purpose. Every garment remains blank. `Back surface` means a visible blank rear garment surface, never artwork.

Codes: `PRODUCT_MISSING`, `PRODUCT_NOT_CLEAR`, `PRODUCT_FORCED`, `PRODUCT_WRONG_ITEM`, `PRODUCT_WRONG_COLOUR`, `PRODUCT_INACCURATE`, `PRODUCT_INVENTED_GRAPHIC`, `PRODUCT_INVENTED_LABEL`, `PRODUCT_CAP_PANEL_HIDDEN`.

### Third-party branding

Tests garments, consumables, vehicles and environmental objects for readable third-party branding. Incidental Shirtfaced environmental easter eggs are permitted; garments and packaging remain blank/generic.

Codes: `BRAND_THIRD_PARTY_VISIBLE`, `BRAND_GARMENT_MARK`, `BRAND_PACKAGING_MARK`, `BRAND_SHIRTFACED_TOO_PROMINENT`.

### Vehicle continuity

Where a ute appears, tests Australian tray-back form, open aluminium alloy tray and secondary narrative role. If no relevant vehicle appears, return `NOT_APPLICABLE`.

Codes: `VEHICLE_AMERICAN_PICKUP`, `VEHICLE_ENCLOSED_TUB`, `VEHICLE_LIFESTYLE_HERO`, `VEHICLE_TOO_PROMINENT`.

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

## 6. Material failure rules

Recommend rejection when any clearly evidenced foundational failure occurs:

- wrong or materially inaccurate nominated product;
- any garment graphic, logo, text, embroidery or visible label;
- readable third-party branding;
- posed/fashion-campaign behaviour;
- American pickup or prohibited ute body where visible;
- emotional resignation or unsafe/drunken-comedy drift;
- image has no independent documentary value;
- severe generation artefact compromising people, product or scene.

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
    "story": {}
  },
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

Show image, prompt, rationale, recommendation, nine gate summaries, strongest success, material drift and any proposed rule. Failed/uncertain gates are expanded first. The owner can approve, reject or request variation independently of the recommendation.

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

Each fixture has expected material gate outcomes, not pixel-perfect prose.
