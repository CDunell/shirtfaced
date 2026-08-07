# Stage 2 creative documents

## Status: four stored and inactive, one promoted

Four of these five documents are **reference only**. Nothing in them reaches the
planning model, and no code reads them.

`PRODUCT_PHOTOGRAPHY.md` is the exception: promoted 7 August 2026 (Hot List item 2).
Its operative rules now live in `worlds/world-01/WORLD.md` under **Product
Photography Extraction**, on the planner's allowlist. The file stays here as the
fuller production reference.

They arrived in a pack drafted through ChatGPT on 5 August 2026 and are kept here
verbatim so the thinking is versioned rather than lost in a downloads folder.

| Document | Covers | Status |
|---|---|---|
| `PRODUCT_PHOTOGRAPHY.md` | Product photography canon: shot families, prominence, styling, review gates | **Promoted** — see `WORLD.md` |
| `WEBSITE_IMAGE_SYSTEM.md` | Website image roles, page sequencing, responsive and accessibility rules | Inactive |
| `CHANNEL_TRANSLATION.md` | Translating one event into Instagram, Reels, TikTok, paid social and email | Inactive |
| `CAMPAIGN_AND_DROP_SYSTEM.md` | Campaign units, phase architecture, release clock, launch asset matrix | Inactive |
| `SEASONAL_CAMPAIGN_SYSTEM.md` | Australian seasonal continuity, weather truth, annual rhythm | Inactive |

## Why the other four are inactive

Version 1 of Shirtfaced Studio deliberately excludes ecommerce, garment mockups,
automatic publishing and social media integration — see the product boundary in
`../../AGENTS.md`. These four sit squarely in that excluded territory, and the pack
that supplied them agrees: website placement and channel sequencing "belong to later
implementation increments".

## Why `PRODUCT_PHOTOGRAPHY.md` was promoted rather than left inactive

It used to be flagged here as pushing against a core Version 1 principle: the product
specification says *product is incidental*, and a product photography discipline
looked close to the opposite. The document's own text already resolved that tension
— "There is no documentary brand on social and separate ecommerce brand on the
website. Product photographs are quieter, clearer fragments of the same world" — and
its P0–P3 prominence scale keeps P0/P1 (incidental) as the default, with P2/P3
(clearer) as an extraction from the same continuity, not a parallel practice. The
promoted heading also makes the enclosed-space rule *stricter* for product frames
than the general World 01 rule: no exception for an outside-looking-in shot, not
even the one the general rule allows elsewhere.

## How a rule in here becomes real

A rule has no effect on generation until it lives in `WORLD.md` under a heading the
planner reads. To promote one:

1. decide which canon file and heading owns it;
2. resolve any rule it contradicts — do not leave the model to guess;
3. edit `WORLD.md`;
4. if it needs a new heading, add it to `PLANNING_CANON_HEADINGS` in
   `app/services/prompt_planner.py`, with a test asserting the section is sent;
5. `python -m app.cli validate-world world-01` then `import-world`;
6. inspect the plan preview before generating anything.

Step 4 matters. A section of `WORLD.md` that is not on the allowlist is invisible to
the planner. See `../HANDOVER_PHASE_2.md` §2.

## Two Phase 3 documents from the same pack were not stored

The pack also contained `STUDIO_PHASE_3_CREATIVE_WORKFLOW.md` and
`PHASE_3_CODEX_BUILD_PACK.md`. They were reviewed and not adopted, because they
conflict with decisions already recorded in this repository:

- they specify **asynchronous** generation with a queue and background worker;
  ADR-010 keeps Version 1 synchronous, and that was reaffirmed on 5 August 2026;
- they propose the states `QUEUED → PLANNING → GENERATING → SUCCEEDED | FAILED |
  CANCELLED`, which drop `awaiting_decision` — the state that makes human approval
  visible in the data. `ARCHITECTURE.md` holds the agreed state machine;
- they omit the partial unique index limiting a world to one active attempt, and the
  advisory lock around the critical section. Both are required by `DATA_MODEL.md`;
- they instruct the interface to warn about an unresolved branding conflict. That
  conflict was resolved in `WORLD.md` on 5 August 2026: the ban is third-party only.

Worth carrying forward from them when Phase 3 is built: the attempt provenance list
(canon document hashes, hero product and camera snapshots, model parameters, provider
request ID, classified failure category), an idempotency key on attempt creation,
retry as a new linked attempt, and the principle that a stored image is not an
approved image.
