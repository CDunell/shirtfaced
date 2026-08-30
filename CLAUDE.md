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

## Read this before writing code

Name the document that governs what you are about to build. If you cannot name
one, search for it — do not start. Every expensive mistake in this repository so
far has been caught by that one question, asked too late.

| Building | Read first |
|---|---|
| The design engine | `studio/docs/DESIGN_ENGINE_ADAPTATION.md` — the architecture, agreed before the build |
| Anything about the corpus | `studio/docs/DESIGN_CORPUS_SCHEMA.md`, and `studio/var/design_corpus/` itself |
| Market / competitor demand evidence | `studio/docs/MARKET_INTELLIGENCE_LAYER.md` — external commercial signals may rank structural treatment only; source copy and subject matter never become creative direction |
| A brief for supplied assets | `studio/docs/ASSET_SPECIFICATION.md` — and audit `assets/` before asking for anything |
| What the brand is | `docs/foundations/POSITIONING.md`, `BRAND_VOICE.md` |
| Product design rules | `docs/research/SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md` |
| Migrations or deploys | `studio/docs/LOCAL_RUNBOOK.md`, `ORACLE_CLOUD_DEPLOYMENT.md`, `.github/workflows/deploy.yml` |

`DESIGN_ENGINE_ADAPTATION.md` opens by recording that the first attempt went
straight to code and produced a duplicate of something that already existed. It
happened again afterwards. Reading it costs one turn; not reading it has cost
several days.

## Standing rules, and why they exist

These were each learned by breaking them. The reason matters more than the rule,
because a rule with no reason gets re-derived away.

**A constraint exists only if it is a property of the machine, or a decision the
owner made. Never one you derived.** Invented constraints so far: a licence gate
at intake, a single-colour mandate, a 25mm legibility test, a single-path rule,
an `id="mark"` requirement, a no-detached-subpaths rule, a 20mm minimum print,
and watermarks refused at the door. Each looked like rigour. Each narrowed what
could come in. Where something genuinely does not work, fix the engine — that is
what the even-odd fill and the stroke outliner are.

**Everything gets ingested.** The rights question is asked once, before release,
where there is a design to ask it about. Not at the door.

**Direction is the owner's.** The corpus settles register — it is how souvenir
Australiana was ruled out. It does not set a design direction. Reading its
medians as an instruction to make type-led work is the same category error as
reading "Australian" as an instruction to draw kangaroos.

**Market evidence has the same boundary.** Marketplace demand can strengthen or weaken
confidence in a layout, type treatment, integration pattern or other structural choice.
It never supplies the joke, phrase, depicted subject or creative direction. Source copy
is evidence to retain, not prompt material. See `studio/docs/MARKET_INTELLIGENCE_LAYER.md`.

**Look at it before saying it works.** Rendering has caught what the numbers
called fine five times: a ute's wheels, an EPS gradient burying six hundred
shapes, an ink the same colour as the garment, a design laid out at 756 pixels
in a 250-pixel card, a checker that drew every circle as a lens.

**Finish, then report.** Naming something as outstanding is not the same as
doing it.

## Where things actually are

- **World canon:** `studio/worlds/world-01/WORLD.md` — the deepest document here. Read it first.
- **Portable rules:** `studio/docs/CARRY_FORWARD_CANON.md` — what survives into new worlds.
- **Positioning:** `docs/foundations/POSITIONING.md` — high-end streetwear, and the
  rule that the Australian part lives in the words and characters, never in depicted
  subject matter. Read before writing any brief about what artwork should show.
- **Brand voice:** `docs/foundations/BRAND_VOICE.md` — the word, the tagline grammar,
  Identity vs Storefront voice. Holds consistency while design content changes.
- **Characters:** `docs/foundations/CHARACTERS.md` — canon since 10 August 2026: a
  family with a friend web attached, decided by the owner from their own people.
  Never named in a generation prompt regardless.
- **Production backlog:** `studio/worlds/world-01/SHOTLIST.md` and `CONTINUITY.md`.
- **Design constitution:** `docs/research/SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md`.
- **Concept libraries and the design backlog:** `docs/design/TSHIRT_CONCEPT_LIBRARY.md`
  (plus headwear and brand-garment siblings) is the authored seed; the operational
  queue is Studio PostgreSQL (`design_concepts` → `approved_designs`, migration 0026).
  Import with `python -m app.cli import-design-concepts`; numbering is permanent and
  the importer never renumbers or deletes. See ADR-015 in `studio/docs/DECISIONS.md`.
- **Market intelligence:** `studio/var/design_corpus_market/` is the local external-demand
  evidence cache. Import exports with `scripts/import_market_intelligence.py`, reuse the
  existing visual pass via `scripts/market_visual_queue.py`, then rank structural evidence
  with `scripts/score_market_intelligence.py`. Governing contract:
  `studio/docs/MARKET_INTELLIGENCE_LAYER.md`.
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
