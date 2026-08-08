# SHIRTFACED

Orientation for anyone — human or agent — opening this repository.

## What this is

Shirtfaced is Australian humour-led **high-end streetwear**, plus drinkware. **Shirtfaced** is a
verb and a state: something you *get*, and something you get *together*. It means *that
level of good time*, not *that many drinks* — the sober mate is still shirtfaced.

The premise is not a clothing brand. It is a persistent Australian social universe, and
the clothing is the visible sign that someone belongs in it. See
`docs/foundations/UNIVERSE_PREMISE.md`.

## Three systems, and how they relate

This is the part that is easy to get wrong. Each system is documented to a high standard
with an explicit scope statement that prevents it touching the others.

| | System | Governs | Lives in |
|---|---|---|---|
| **A** | The Universe | Worlds, characters, photography, canon | `docs/foundations/`, `studio/worlds/` |
| **B** | Product Design | Garments, graphics, review, approval | `docs/research/` |
| **C** | Channel & Campaign | Social, web, email, drops | `studio/docs/stage-2/` — **currently inactive** |

**System B explicitly does not govern System A.** Read its scope statement in
`SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md` before assuming a design rule applies to a
photograph, or vice versa.

**System C is reference-only, with one exception.** `studio/docs/stage-2/README.md`:
the channel/campaign documents there reach nothing and no code reads them.
`PRODUCT_PHOTOGRAPHY.md` — filed alongside them but actually part of System A's
photography, not channel distribution — was promoted on 7 August 2026; its rules now
live in `worlds/world-01/WORLD.md` under Product Photography Extraction.

## The rule that catches everyone

**A rule has no effect on generation until it lives in a world's `WORLD.md` under a
heading listed in `PLANNING_CANON_HEADINGS`, and the world has been validated and
imported.** A section not on the allowlist is invisible to the planner.

Promotion steps are in `studio/docs/stage-2/README.md`. Do not add a rule to a research
document and assume it is live.

## Where things actually are

- **World canon:** `studio/worlds/world-01/WORLD.md` — the deepest document here. Read it first.
- **Portable rules:** `studio/docs/CARRY_FORWARD_CANON.md` — what survives into new worlds.
- **Positioning:** `docs/foundations/POSITIONING.md` — high-end streetwear, and the
  rule that the Australian part lives in the words and characters, never in depicted
  subject matter. Read before writing any brief about what artwork should show.
- **Brand voice:** `docs/foundations/BRAND_VOICE.md` — the word, the tagline grammar,
  Identity vs Storefront voice. Holds consistency while design content changes.
- **Characters:** `docs/foundations/CHARACTERS.md` — a name list, nothing formed yet.
  Never named in a generation prompt regardless.
- **Production backlog:** `studio/worlds/world-01/SHOTLIST.md` and `CONTINUITY.md`.
- **Design constitution:** `docs/research/SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md`.
- **The kill filter:** `docs/research/DESIGN_REVIEW_SCORECARD.md` — 12 hard-fails plus a
  weighted 100-point rubric. Nothing has been scored through it yet.
- **Compositing:** `studio/app/services/compositing.py` — designs are printed onto blank
  garments locally after generation. Deterministic, free to re-run, text stays accurate.
- **Storefront:** `src/` (Next.js) and `admin/`. Shares a repo with the studio and
  nothing else.

## Current state — read these two first

- `docs/shirtfaced-audit.md` — gap analysis, scores, prioritised hot list, phased plan.
- `docs/SESSION_HANDOVER_2026-08-07.md` — decisions and open items not yet promoted to canon.

The headline finding: the thinking is far ahead of the instantiation. There is no brand
voice document, no character bible, no design has ever been run through the scorecard,
and two canon documents contradict each other on camera position.

## Working notes

- All generated photography and video to date is **dev work and disposable**. Do not
  treat existing assets or scenario banks as constraints.
- Version 1 of Shirtfaced Studio deliberately excludes ecommerce, garment mockups,
  automatic publishing and social integration. See `studio/AGENTS.md`.
- Generation is synchronous by decision (ADR-010). The `awaiting_decision` state exists
  so human approval is visible in the data. A stored image is not an approved image.
- Australian English throughout.
