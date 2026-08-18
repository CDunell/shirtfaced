# The design pipeline, stepped

From existing designs to our take, ready for approval. Five steps, one obvious
next action each. Everything after Step 0 happens in the browser on
`studio.shirtfaced.wtf`; nothing bills a metered API at any step.

Written against `DESIGN_SYSTEM_AUDIT_2026-08-18.md`. The governing documents
for what happens inside each step are `DESIGN_FLOW_PLAN.md` (the chain),
`VINTAGE_HOW_TO_USE.md` (Research), and
`docs/research/DESIGN_REVIEW_SCORECARD.md` (the judgement).

---

## Step 0 — measure the references into the database (on the box, once, and after each collection run)

```
python -m app.cli design-data            # what the tables hold, and what each consumer runs on
python -m app.cli design-data --refresh  # measure the corpus into PostgreSQL, merge archive into evidence
```

`--refresh` does two things, stopping at the first failure:

1. Hard-links the 18,633-image design archive into the vintage evidence root,
   so Research sees every pool, not just eBay. The one file-domain step —
   the bench reads image files.
2. Measures the retail corpus into `design_measurements` — one row per
   primary product shot, refusals recorded with their reason. This is what
   the advisor and the scoring thresholds read; the composer's confidence
   needs nothing here, deriving from the decisions table on its own.

There are no files to copy anywhere. The measurements live in the same
PostgreSQL the rest of the pipeline already uses, and the status command
reports the tables directly. Until the corpus is measured, the advisor and
the thresholds run on documented defaults and say so — that is them working,
not failing.

## Step 1 — Research: from references to ten concepts (no spend)

**Evidence** → filter by era and tradition → **Research** → set images per run
→ **Prepare manual run**. Save the images, copy Pass 1 into ChatGPT or Gemini
with them, then Pass 2 into the same chat. Paste the JSON back and press
**Import concepts**. The validator refuses anything malformed and says exactly
what was wrong.

Approve the concepts worth keeping; **Send to design pipeline** turns one into
a numbered design concept.

## Step 2 — Brief: decide what the product is (advisor now corpus-backed)

Open the concept in **Designs**. Choose the collection role and the graphic
archetype — the advisor recommends from the corpus as you do (after Step 0 its
recommendations say `corpus`, not `default`; if they still say `default`, Step
0 has not landed). An attempt cannot open without the brief; that gate is the
constitution working.

## Step 3 — Artwork: made outside, brought back

Open the attempt. **Copy brief** — it carries the prompt and the evidence
images that inspired the concept. Make the artwork in ChatGPT, Gemini or
Claude. Drop the file on the attempt's drop zone.

For type-led and badge/frame work, **Compose artwork** on the same screen is
the deterministic alternative: garment, words, seed — same seed, same bytes,
and every part traceable to the element archive. Keeping a composed option
files it as an attempt on the concept automatically.

## Step 4 — Judge: measure, answer, submit

**Measure this artwork** — coverage, inks, legibility checks, persisted on the
attempt. Answer the thirteen gates and nine categories, in their three groups.
The scorecard runs server-side; nothing can be approved past it, and it names
what is missing. Submit for a decision.

## Step 5 — Approve: one decision, recorded and felt

Approve, reject, or request a variation. Approving records the version with
its garment, print zone and width frozen in `production_spec` — Print renders
it into the real zone from there. The decision also feeds the composition
engine's confidence, so what you approve changes what is offered next. That
is the learning loop; it only learns from real decisions, so decide honestly
and let the numbers accumulate.

---

**If a step has no obvious next action, that is a defect — file it.** The
chain's rule (from `DESIGN_FLOW_PLAN.md`): at every point there is exactly one
obvious next action, and following the chain to a finished design requires no
knowledge of which screen owns what.
