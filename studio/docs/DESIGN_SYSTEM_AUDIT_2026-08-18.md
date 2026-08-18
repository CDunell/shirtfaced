# Design system audit — 18 August 2026

**Scope:** the design generation system, the archives, and the corpus functions —
everything between "tens of thousands of reference designs" and "our take, ready
for approval". The world/photography pipeline is out of scope except where it
shares a file.

**Method:** three parallel code audits (corpus, element archive, generation
flow), every consumer traced to a file and line, read against
`DESIGN_ENGINE_ADAPTATION.md`, `ELEMENT_ARCHIVE.md`, `DESIGN_FLOW_PLAN.md` and
`PIPELINE_AUDIT_2026-08-14.md`. Where this audit contradicts the 14 August one,
this one is later and the difference is named in §6.

**Companion:** `DESIGN_PIPELINE_RUNBOOK.md` — the stepped pipeline this audit
concludes with, written for the person running it rather than the person
auditing it.

---

## 1. The organising fact

The complaint this audit was commissioned against — *tens of thousands of design
references and no reliable way to produce anything from their inspiration* — is
structurally accurate, and the cause is not missing code. Nearly everything
needed exists. The cause is three things that were each decided or built soundly
and never joined:

1. **The reference material is input to nothing that generates.** Two decisions,
   each locally right, intersect badly. Phase 0.1 (`DESIGN_FLOW_PLAN.md`)
   removed in-app image generation: the app owns the brief, the record, the
   measurement, the judgement and the decision — never the pixels.
   `ELEMENT_ARCHIVE.md` §6 removed the mined corpus from the generative role:
   designs assemble from authored parts, and the corpus becomes measurement
   evidence. Both defensible. Their intersection is that ~40,000 reference
   images now feed only an advisor and a threshold table — and neither has ever
   received the data (point 2).

2. **The mined artefacts were never produced where anything reads them.** Every
   corpus consumer that is wired — the advisor, the scoring thresholds, the
   template engine — reads a JSON file under `var/design_corpus/` that exists
   neither in git, nor locally, nor on the deployed box
   (`DESIGN_FLOW_PLAN.md` "The plan was wrong about the advisor"). The refusal
   machinery works exactly as designed: it declines to fabricate confidence,
   and so it declines everything, every time.

3. **The learning loop was never closed.** The architecture's own single thread
   to prove first ends: *"approve one → that approval measurably moves the
   template's confidence. If the approval does not move the number, the loop is
   decorative."* `DesignComposer.record_decision()`
   (`app/archive/design_composer.py:373`) has **zero callers**. Every decision
   the owner has ever made updated the database row and taught the composer
   nothing. By the architecture's own kill gate — twenty decisions with no
   movement — the loop is currently decorative.

Everything else in this audit is detail under those three.

## 2. The reference material, counted

Four pools, three of them invisible to the tools:

| Pool | Scale (as documented) | Reachable from the product pipeline? |
|---|---|---|
| `var/design_corpus/` — retail product photos | 12,151 images, 188 brands | Only via mined JSON that was never produced (§1.2) |
| Vintage evidence (eBay) | 3,639 listings, 11,544 images | **Yes** — the only pool the Research bench reads |
| `var/design_archive/` — vintage/archive collections | 18,633 images, 22 sources | No. The bridge (`scripts/adapt_archive_to_evidence.py`) has never been run; its output root is opt-in via an env var no deploy sets |
| `current-retail` (City Beach + 11 US shops) | 58+ designs on first pass | Images only; measurement refuses worn full-body shots (ADR-019, correctly) |

The scale numbers themselves do not reconcile — 12,151 vs 33,052
(`scripts/visual_pass_queue.py:4`) vs 40,070 (`VISUAL_PASS_HANDOVER.md:6`)
images, depending on which document is doing the counting — and the retail
corpus is truncated: the `PRODUCTS_PER_BRAND` cap bug was fixed
(`collect_design_corpus.py:657-658`, ADR at `DECISIONS.md:576-580`) but the
corpus was never re-collected, so 165 of 187 brands still sit at exactly 18
products.

**"Archive" means two unrelated things in this repository**, and the collision
obscures both. The **Element Archive** (`assets/` + `app/archive/`) is parts a
design is assembled *from* — 235 elements, deterministic composer, live UI. The
**design archive** (`var/design_archive/`) is finished work to be inspired *by*
— 18,633 images with no code path into generation at all. Its sole bridge to
generative work is `ARCHIVE_PROMPT_LIBRARY.md`: four era-and-register cells
read by hand, 28 prompts, a Markdown file no code reads.

## 3. What works, and is kept

Named plainly, because the fix builds on it rather than around it.

- **The design chain, end to end.** Concept → brief gate (collection role +
  graphic archetype, server-enforced) → attempt → brief package with evidence
  → artwork dropped back → measurement → thirteen gates and nine categories →
  server-side scorecard that returns 422 on any attempt to skip it → decision →
  approved version with frozen `production_spec` → print rendered into a real
  garment zone. Exit-tested in a browser on 14 August, smoke-checked on every
  deploy (`scripts/smoke_design_chain.py`). The 14 August audit's headline —
  *"no design can pass the scorecard, not one, ever, by construction"* — is no
  longer true and has not been true since Phase 1 passed.
- **The Research bench.** Evidence → breadth-first image selection → prepared
  prompts carried to a paid interface → ten concepts pasted back through a
  validator that rejects anything malformed → approve → a real design concept
  and attempt. No metered spend, by decision 0.1.
- **The element composer** (`app/archive/design_composer.py`). Deterministic —
  same seed, same bytes, asserted across restarts by
  `recompose()` — with honest refusal codes, licence provenance carried per
  element, and a real join into the attempt pipeline
  (`design_composition.py`, `routes/compose.py`).
- **The refusal discipline, everywhere.** The advisor marks defaults as
  defaults; the engine refuses `NO_CLUSTER` rather than guessing; measurement
  refuses worn photography rather than averaging it in. This is the
  architecture behaving correctly while starved. Nothing in the fix weakens it.
- **Collection and mining code.** Over-built if anything: ~7,500 lines, tier
  filters applied consistently across six of seven miners, the measurement
  function tested (`tests/unit/test_design_mining.py`) after its three failures
  were caught visually.

## 4. Where it is broken, precisely

### 4a. Wired consumers, absent data

- `design_advisor._load_joined()` (`app/services/design_advisor.py:121-133`)
  reads `var/design_corpus/joined.json`. Absent. Every recommendation degrades
  to `confidence: "default"`.
- `design_extraction.load_thresholds()` (`design_extraction.py:109`) reads
  `design_patterns.json`. Absent. Scoring runs on hardcoded fallbacks.
- `CompositionEngine` (`composition_engine.py:428`) reads
  `design_templates.json` via `app/archive/templates.py:31`. Absent. Refuses
  `NO_CLUSTER` with "run learn_design_templates.py".

The producers all exist (`mine_design_patterns.py`,
`mine_design_structure.py`, `learn_design_templates.py`,
`join_design_patterns.py`) and are hand-run scripts in an order nothing
records. No CI job, cron, deploy step or CLI command runs any of them.

### 4b. The learning loop, split three ways

Three disjoint notions of "an approval" exist:

1. `design_decisions` / `approved_designs` — the authoritative, scorecard-gated
   human record. Read by the workflow, read by nothing that learns.
2. `var/approvals.json` keyed by grammar — the live composer's learning store
   (`design_composition.py:45`). **Written by nothing**: both decision paths
   (`design_composition.decide()` and
   `design_pipeline._settle_linked_composition()`) update the row and skip the
   store. `r.json` at the studio root — a stray composer output dump — shows
   the result: `"approvals": 0, "decisions": 0` on every option ever offered.
3. The template engine's own store (`routes/range.py:41`) with the `n/(n+10)`
   confidence the architecture specified — wired to `POST /api/range/decision`,
   tested down to the assertion that the number moves
   (`tests/unit/test_range_route.py`), and called by **no frontend code**.

### 4c. Element archive: provenance and reach

- `_sync_archive` (`app/cli.py:526`) syncs `authored.ALL` — 53 elements — while
  the composer draws from `registry.all_elements()` — 235. The provenance join
  in `routes/compose.py` silently drops any part whose key is not in the
  database: **~83% of a composed design's parts produce no `ElementUse` row**,
  so "trace an element to everything it appears in" holds only for parametric
  shapes.
- ~600 of ~880 files under `assets/` sit in folders no loader reads
  (`garments/` and `type/` are legitimately separate; `neon_signs/`,
  `stock/`, `created_Ready_to_Process/` are simply unreached), and
  `library.illustrations()` points at `assets/illustration_parts`, a folder
  that does not exist — it returns `()` silently
  (`app/archive/library.py:216-217`).
- 235 elements against the owner's stated target of 2,000–3,000.

### 4d. Dead weight

Held for §8's cut list with reasons; the headline items: the never-wired
generator `app/services/design_generator.py` (zero importers, including
tests); the superseded `app/archive/composer.py` (431 lines, 18 tests, nothing
ships it); `app/archive/present.py` + `templates.py`'s dead half;
`app/archive/ingest.py` (only its test imports it); the `element_renders`
table (never written, never read); the entire pgvector similarity apparatus
(computed on every sync, queried by nothing in production); four mined
artefacts with zero readers (`arrangement.json`, `forms.json`,
`brand_voice.json`, `visual_queue.json`); and the write-only
`design_observations` schema — four migrations and ~40 columns of vocabulary
holding precedent nothing retrieves.

## 5. The root cause, in one sentence

**Between "references on disk" and "a design in front of the owner" every link
was built, but the three joins — data produced where consumers read it,
decisions fed back to the engine that offered the option, and the biggest
reference pool merged into the bench that reads references — were each left as
a manual step nobody ran, and nothing reported that they had never been run.**

## 6. Corrections to the 14 August audit

- *"No design can pass the scorecard, not one, ever"* — *superseded.* Phase 1's
  exit test persisted an 80/100 review and an approved v1.
- *"`POST /api/concepts/attempts/{id}/assets` exists and no screen calls it"* —
  *superseded.* `AttemptPanel.tsx:193` calls it.
- *"`design_advisor` answers this from 12,151 measured images"* — *was never
  true.* It answers from a documented default; the corpus behind it has not
  been mined (`DESIGN_FLOW_PLAN.md`, Phase 4 findings).

## 7. The fix

Split honestly into what this branch changes, what is a data operation on the
box, and what is the owner's to decide.

### 7a. Changed in this branch (code)

The organising decision, made by the owner mid-fix and correct: **derived
design data lives in PostgreSQL, not in JSON files.** The first version of
this fix built better plumbing for the files — a status command that watched
for their absence, a workflow that ferried them to the box. That was
infrastructure for the defect. A table cannot be absent from the box, and an
empty one is loudly visible, so the failure class that starved the advisor
for months simply does not exist in the database.

1. **The corpus is measured into `design_measurements`** (migration 0044) —
   one row per primary product shot, refusals recorded with their reason,
   identity columns matching `design_observations` so measured and observed
   join without sharing a column, per that schema's own rule. The advisor
   (`measurement_rows`) and the scoring thresholds (`load_thresholds`, now
   SQL percentiles) read the table; the documented-default fallback keeps its
   honest meaning when the table is empty. `joined.json` and
   `design_patterns.json` have no readers left.
2. **The learning loop is closed, with no store to drift.** The composer's
   per-grammar confidence derives from `composed_designs` at compose time
   (`grammar_history`): settling the row *is* the training signal. Approve
   and reject count; a variation request does not — it judges the content,
   not the construction. `var/approvals.json` is gone; the three disjoint
   approval stores of §4b are one table, which was the record all along.
   `recompose` composes uncapped and history-blind so determinism checks
   cannot mistake learning-moved ranking for drift.
3. **`sync-archive` syncs what the composer uses.** `registry.all_elements()`
   — authored and drawn both — so the provenance join stops dropping ~83% of
   parts.
4. **One command owns the data operation.** `python -m app.cli design-data`
   reports what the tables hold — measured frames by tradition, refusals,
   decisions per grammar — and `--refresh` measures the corpus into the
   database (reusing the mining scripts' analyser and walk order unchanged)
   and merges the design archive into the evidence root, the one genuinely
   file-domain step, since it feeds a bench that reads image files.

Proven on a real PostgreSQL: the full integration suite migrates from empty
through 0044 and passes, including the thread the architecture said to prove
first — compose, keep, decide, and the decision measurably reweights the
next compose, read straight from the table.

### 7b. Data operations (on the box — the runbook's Step 0)

**Where the corpora actually are — checked 18 August, not assumed.** The
production box holds neither `var/design_corpus` nor `var/design_archive`
(confirmed by running the refresh there: both absent), and its evidence root
holds 607 eBay listings at the service's default path against a documented
3,639 — either collection continued elsewhere or the box's `.env` points
`VINTAGE_EVIDENCE_ROOT` somewhere this check did not look. The cloud
session's clone has no corpora either (`var/` was never in git), and its
network policy blocks the retail domains, so re-collection cannot run there.
The corpora exist only on the machine that ran the collectors. One rsync of
the two directories to the box, then Step 0, closes this permanently.

- Deploy this branch (migrations run on deploy), then run
  `python -m app.cli design-data --refresh` on the box. That single command
  measures the corpus into the database and merges the archive into
  evidence; the advisor and thresholds are corpus-informed from that moment.
- Re-collect the retail corpus now the cap bug is fixed, if the 18-product
  truncation matters to the medians. Optional; the medians are honest about
  their pool size either way.

### 7c. Proposed, not done — the owner's decisions

- **Delete the dead weight in §8.** Each entry carries its reason; none is
  load-bearing; ~2,000 lines and two dead database structures go.
- **Surface the range engine or fold it into Compose.** The corpus-learned
  engine with the specified confidence arithmetic is mounted, tested and
  unreachable. Either give it a client or move its confidence display into the
  Compose bench's options.
- **Reconcile HF-10.** The scorecard's twelve hard-fails and the code's
  thirteen gate ids are still two lists; *Collection Redundancy* has no gate
  id. Deferred from Phase 4, still open, needs the owner.
- **Structured reading of the archive at scale.** The archive prompt library
  proves the method (era-and-register cells, rules not specifics) and hand
  reading caps it at four cells. A vision-model pass with a *small* schema
  matched to the corpus vocabulary — tradition, era markers, composition
  family, motif class, type treatment, palette structure, with
  `not_visible`/`uncertain` legal everywhere and refusal permitted — run
  batch-wise through the paid interfaces and imported through a validator,
  would give Research queryable facets and draft cells for a person to
  confirm. The generic per-image "style profile" schema the owner circulated
  is the right instinct with the wrong schema: per-image profiles at 18k scale
  recreate the unread-pile problem, mandatory completeness fabricates
  confidence, and "recreate this image" is imitation of one piece — the thing
  the scorecard's derivativeness gates exist to kill. Adapt the pattern, not
  the prompt.

## 8. The cut list

Every cut with its written reason, per the standing rule. None are made in
this branch; each is safe the day the owner nods.

| Cut | Reason |
|---|---|
| `app/services/design_generator.py` | Zero importers including tests. The generator §5 of `DESIGN_ENGINE_ADAPTATION.md` was written to replace; the replacement shipped, this stayed. |
| `app/archive/composer.py` + `test_archive_composer.py` | Superseded by `design_composer.py`, which states the rationale in its own docstring. 431 lines and 18 tests exercising a class nothing ships. |
| `app/archive/present.py`, and `templates.py`'s consumers beyond `composition_engine` | No importers. Built on the k-means templates `ELEMENT_ARCHIVE.md` §6 explicitly retired. |
| `app/archive/ingest.py` | Only its test imports it; the live ingestion path is `library.py`. Keep the test's *assertions about non-gating* by porting them to the live loaders first. |
| `element_renders` table | Never written, never read. The determinism claim it was built for is carried by `composed_designs.content_hash` + `recompose()`. |
| pgvector `feature` column, HNSW index, `similar_to()` | Computed on every sync for rows nothing queries. If "what else is like this" is wanted later, it returns with a caller. |
| `mine_arrangement.py`, `derive_forms.py`, `mine_placement.py`, `mine_brand_voice.py`, `visual_pass_queue.py` outputs | Zero readers; the first two additionally measured marketplace submissions and called it the corpus (`corpus_tiers.py:7-10`). |
| `join_design_patterns.py`, and `mine_design_patterns.py`'s report output | Superseded by `design-data --refresh` measuring into PostgreSQL. `mine_design_patterns.py` itself stays — the CLI imports its analyser — but nothing reads `joined.json` or `design_patterns.json` any more. |
| `design_observations` + `observation_zones` (schema kept, decision needed) | Write-only: ingested by one script, queried by nothing. Either build the reader the ingest script's own docstring promises, or stop ingesting. |
| `ix_archive_elements_usable` partial index | Filters on `licence_status = 'verified'` for a query that deliberately does not filter on licence. Can never serve. |
| `studio/r.json` | A stray composer output dump at the studio root. |

## 9. What "reliable" looks like when this lands

The runbook's five steps, each with one obvious next action, none requiring a
terminal after Step 0: references reachable in Evidence (all pools);
concepts made from them in Research for no metered spend; briefs advised by
the corpus instead of defaults; artwork brought back, measured, judged
against the full scorecard; approval recorded once and *felt* by the engine
that offered the option. The kill gate finally gets its twenty decisions.
