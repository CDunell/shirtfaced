# The design flow: a phased plan

**Status:** agreed 2026-08-14. This supersedes ad-hoc work on the vintage
benches. Phases ship in order. A phase is not done until its exit test passes.

---

## The rule everything is judged against

> At every point there is **exactly one obvious next action**. Doing it reveals
> the next one. Following that chain from evidence to a finished design requires
> no knowledge of which screen owns what.

Anything that fails that rule is a defect, including things that "work".

Today the tool fails it completely. Each bench is an island: Research does not
know Designs exists, Designs does not know an attempt is waiting, and the chain
severs entirely at the point artwork is meant to arrive. The audit called this
"no single pipeline record"; in practice it means the user holds the state in
their head and the software holds none of it.

## What is actually broken, as of today

Established by tracing the code and testing production, not by assumption.

| | |
|---|---|
| **The chain severs at artwork** | `Send to design pipeline` opens a `DesignAttempt` in `PLANNED`. `uploadAsset()` exists in `api/concepts.ts` and **no screen calls it**. There is no way in the application to give an attempt its image. |
| **Nothing knows what is next** | No record carries state across benches. Nothing can answer "what should I do now". |
| **Research pre-selects an old run** | The bench auto-selects the most recent run, so ten historical concepts appear on load looking freshly generated. |
| **Three overlapping design journeys** | Designs, Compose and Score are separate top-level destinations for one workflow. |
| **Approval is scattered** | Decisions exist per bench; no single queue of what is waiting. |
| **Evidence never reaches generation** | Images inform the prompt text and are never sent to the image generator. Recorded as provenance only. |

## What is deliberately not a defect

**The manual generation hop.** Paid subscriptions to OpenAI, Gemini and
Anthropic already exist; an API key bills separately, so wiring generation
would charge twice for owned capability. The loop is: prompt out, image made in
a paid UI, file brought back. That stays. What is missing is that the software
does not *support* the hop — it does not hand off cleanly and cannot receive
the result.

---

## Phase 1 — Close the circuit

*Nothing else matters while the chain is severed.*

1. **Upload artwork to an attempt.** A drop zone on the attempt: choose or drag
   a file, it posts to `uploadAsset()`, the asset appears. Then Submit, then
   Decide.
2. **Stop pre-selecting a run.** Research lands on the prepare form. A previous
   run is opened deliberately, and is labelled with its date and source.
3. **Say what is next, on the attempt.** After upload: "Submit for decision".
   After submit: "Approve or reject". Plain sentences, not inferred from state.

**Exit test:** starting from an approved concept, a person who has never used
the tool uploads an image and reaches an approved design version without being
told which screen to visit. No terminal, no API call.

## Phase 2 — One record that knows its next action

The spine the audit asks for, reduced to what the flow needs.

A `ProductionItem` carrying: the design concept, the research run and concept
it came from, the attempt, the approved version, and a single derived
`next_action` — the one thing to do now, and the screen that does it.

Derived, never stored as a duplicate: state comes from the rows that already
exist, so it cannot drift from them.

**Exit test:** for any item, one API call returns what to do next and where.
That answer matches what the screens show.

## Phase 3 — One screen that asks the question

**Work** becomes the landing screen and replaces the current Dashboard: a list
of production items, each showing its next action as a button that goes
straight there. Nothing else on it.

**Exit test:** the whole flow can be driven from Work without using the top nav
at all.

## Phase 4 — Consolidate the design journey

Per the audit: Designs becomes the one screen. Compose becomes a generation
method inside it; Score becomes an evaluation panel inside it. Both leave the
top nav. Their services stay where they are — the duplicate is the journey, not
the code.

**Exit test:** top nav loses two entries and no capability is lost.

## Phase 5 — Approval inbox

One queue of everything awaiting a decision, across attempts, placements,
photography and social, with rejection reasons visible. Folds into Work rather
than becoming a sixth island.

**Exit test:** every pending decision in the system appears in one list.

## Phase 6 — Evidence reaches generation

Wire a `ReferenceImageStore` at the evidence root into the generation call, so
the images inform the artwork and not only the words. The adapter exists and
runs in production for photography today.

Gated behind a decision that is not mine: it likely means local generation to
stay off metered APIs. Raised, not assumed.

**Exit test:** an attempt records which evidence images were sent, and the
output visibly carries the era rather than a generic interpretation of it.

## Later, in the audit's order

Campaign and drop orchestration, video as a first-class asset, storefront
handoff, consolidating social rendering, reporting, operational health, removing
the confirmed fossils, rewriting the specs. None of these are started before
Phase 3 passes.

---

## How this gets worked

- **One phase at a time**, in order. No starting Phase 3 because Phase 2 is
  awkward.
- **Every phase ends with its exit test run and pasted**, not asserted.
- **Nothing ships without being exercised end to end in a browser.** Server
  checks pass while a screen throws; that has happened repeatedly.
- **No new top-level destinations.** Anything new folds into Work or Designs.
- **When something is found broken mid-phase**, it is written down here and
  fixed in the phase it belongs to, not immediately.

## Progress

| Phase | State |
|---|---|
| 1 — Close the circuit | not started |
| 2 — The spine | not started |
| 3 — Work screen | not started |
| 4 — Consolidate Designs | not started |
| 5 — Approval inbox | not started |
| 6 — Evidence into generation | not started |
