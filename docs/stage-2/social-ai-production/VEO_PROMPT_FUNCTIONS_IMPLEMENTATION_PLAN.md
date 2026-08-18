# Veo Prompt Functions — Implementation Plan

**Branch:** `gpt/prompt-functions-audit`  
**Status:** pre-implementation authority for the prompt-function work  
**Scope:** motion-prompt construction only. The working Nano coverage, extraction, approval, Studio orchestration, Veo transport, audio stripping and take persistence are not redesigned by this work.

## 1. Why this exists

The end-to-end production pipeline now works. The current failure is the motion instruction itself.

A good approved first frame is reaching Veo, but the flat motion paragraph still gives Veo enough semantic freedom to invent an action arc: a subject progressively changes pose, crowd behaviour converges, and the take develops choreography that was never present in the seed.

The fix is not another larger paragraph. Motion direction needs explicit responsibilities that can be composed, tested and inspected before a paid provider call.

The existing production boundary stays:

`approved standalone frame -> resolved motion prompt -> existing Veo runner -> existing Google adapter -> stripped/probed take`

The new work replaces only **resolved motion prompt**.

---

## 2. Resolved authority tensions

### 2.1 Prompt-construction hierarchy versus Veo motion prompts

`studio/docs/PROMPT_CONSTRUCTION_PRINCIPLES.md` governs construction of a scene/image: emotional truth, relationships and event exist before camera and technical treatment.

`NANO_BANANA_VEO_SCENE_PRODUCTION_PIPELINE.md` §14 governs a later production stage: once an approved frame exists, appearance and composition already exist and the Veo prompt should primarily describe change through time.

These are not competing rules. They apply at different stages.

**Decision:** the photographic prompt hierarchy creates the seed. The Veo prompt does not recreate that hierarchy. It inherits the approved seed and expresses temporal behaviour, preservation rules and allowed camera behaviour only.

### 2.2 "The camera observes" versus crowd-level phone footage

World 01's observer rule forbids impossible or embedded camera positions in small built enclosures such as car cabins and lifts. It does not require every camera to stand outside an entire pub room or outside a crowd.

**Decision:** a phone may be physically held by a plausible observer within an open pub room/crowd. It remains observational because nobody performs for or acknowledges it. The small-enclosure prohibition remains unchanged.

### 2.3 Scene-master authority versus motion generation

The approved master and extracted seed own appearance, geography, blocking, scale, visible identity, lighting and composition. Veo does not receive permission to improve or reinterpret them.

**Decision:** motion functions may describe preservation and time. They may not re-author spatial composition.

### 2.4 Natural movement versus "hold everything still"

A living documentary scene needs continuous motion, but allowing generic "energetic movement" invites progressive pose changes and action completion.

**Decision:** motion is expressed as bounded state behaviour. A function states the continuing state, allowed local variation and explicitly forbidden state transitions. Start and end remain within the same state unless a shot specification deliberately defines a transition.

### 2.5 Positive direction versus negative constraints

Long negative lists can become the dominant semantic content of a prompt and can conflict with natural movement.

**Decision:** compilation order is positive state first, then allowed motion, then preservation anchors, then prohibited transitions/failure modes. Negatives protect an already-defined behaviour; they do not define the behaviour.

---

## 3. Legacy cleanup completed before implementation

Three obsolete production paths were still capable of confusing the audit and, in two cases, of triggering paid pub-specific generations:

- `studio/scripts/run_renderer_video.py` — hard-coded W01-P28/pub runner with an embedded `MOTION_PROMPT` and forced 9:16 output;
- `.github/workflows/renderer-video-validation.yml` — old pub validation route invoking that script;
- `.github/workflows/renderer-paid-video-validation.yml` — duplicate paid pub validation route invoking the same script.

They are removed on this branch. Historical trigger JSON and past result directories remain evidence and are not rewritten.

The active production path remains `motion_run.py -> run_pub_coverage_veo.py -> GoogleVideoClient`.

`run_pub_coverage_veo.py` is now generic despite its legacy filename. Renaming it is **not part of this prompt change** because the name is referenced by the active workflow, service, tests and historical ADRs. A cosmetic rename is lower value than preserving one proven runner during prompt work. The file name is accepted compatibility debt, not a second production path.

---

## 4. Prompt-function model

The first implementation will use typed, deterministic prompt components. They are functions in the production sense: each has one job and can be tested independently before compilation.

### F1 — Temporal mode

Defines the topology of the take.

Examples:

- `ongoing_state` — begins mid-event and ends mid-event; no completion;
- `single_micro_event` — one bounded action may occur once;
- `transition` — explicit A -> B state, only when the shot specification asks for it.

Default for W01-P28 Shot A: `ongoing_state`.

### F2 — Immutable visual state

Names visible anchors that must persist because the approved frame already establishes them.

For W01-P28 Shot A this includes the table, stool, pint, cue relationship, band/crowd density and the established subject state.

This function never invents appearance details absent from authority.

### F3 — Primary subject motion

Describes allowed local motion as ranges/repetition rather than a narrative arc.

For example: small knee flexion, alternating weight shift, torso bounce, imperfect balance, mouth/face movement associated with shouting the chorus.

### F4 — Secondary/distributed motion

Describes independent background/crowd activity without synchronising it.

It should emphasise simultaneous unrelated micro-actions, temporary occlusion and distributed attention rather than a shared crowd command.

### F5 — Camera behaviour

Defines only physically plausible operator behaviour for the selected observation: handheld sway, small crowd bump, momentary obstruction, minor correction.

It does not request a new angle, reveal or composition.

### F6 — Preservation anchors

Names relationships with high drift cost: held prop orientation, stable furniture/drink, established lighting contrast, no identity additions, no population multiplication or room simplification.

### F7 — Forbidden transitions

Names state changes that would turn an ongoing observation into an invented sequence.

For Shot A: no progressive crouch/kneel/sit/climb-down; no cue lowering/rotation into a microphone; no crowd convergence; no room settling; no hero re-lighting/reframing.

### F8 — Output/editorial constraints

No cuts, text or slow motion where the shot does not require them. Generated audio is irrelevant because the production runner strips it; this component should not waste prompt weight explaining post-production unless provider behaviour requires it.

---

## 5. Compilation contract

The prompt compiler will produce one final plain-text Veo prompt because the existing Google adapter accepts a string. No adapter change is required.

Deterministic order:

1. temporal mode;
2. immutable state;
3. primary motion;
4. distributed/secondary motion;
5. camera behaviour;
6. preservation anchors;
7. forbidden transitions;
8. output constraints.

Rules:

- omit empty components rather than emitting boilerplate;
- never duplicate the same constraint in multiple components;
- never add scene facts not supplied by scene/shot configuration;
- final prompt is persisted unchanged in `motion-prompt.txt` by the existing runner;
- compilation must be deterministic for identical inputs;
- no provider call occurs in compiler tests.

---

## 6. Configuration boundary

Generic component vocabulary and compilation live in code.

Scene/shot facts remain configuration beside the scene:

`worlds/<world>/shots/<SCENE>.veo-motion.*`

and optional shot-specific override:

`worlds/<world>/shots/<SCENE>.<shot>.veo-motion.*`

The implementation may introduce a structured format for component data, but the existing `.veo-motion.txt` resolver remains available as a compatibility fallback until W01-P28 has passed a paid comparison. No bulk migration of worlds is allowed before that proof.

The engine must remain capable of adding a second scene without Python changes.

---

## 7. Phased implementation

### Phase 0 — Audit, isolate and remove conflicting legacy paths

**Status: complete on this branch.**

- branch from current working `main`;
- identify active Studio -> runner -> provider route;
- identify and remove obsolete hard-coded pub runner/workflows;
- record authority/tension decisions in this document;
- no paid generation.

**Gate:** only one active production runner family remains.

### Phase 1 — Prompt component domain and compiler

Create a small service module containing typed component data and deterministic compilation.

Tests first:

- order is fixed;
- empty functions disappear;
- duplicate constraints are rejected or normalised;
- `ongoing_state` cannot contain an allowed terminal transition;
- compiled output is stable;
- no scene names or pub facts exist in generic code.

No change to Google adapter, Studio UI or provider invocation.

**Gate:** compiler passes unit tests with synthetic scenes.

### Phase 2 — Resolver integration with backwards compatibility

Extend the existing motion resolver so it can load structured prompt-function configuration when present and otherwise use the existing flat `.veo-motion.txt` file unchanged.

The runner still receives one resolved string.

Tests protect:

- structured shot override beats structured scene default;
- existing flat files still resolve;
- second-world/second-scene resolution remains configuration-only;
- missing direction still refuses before provider spend.

**Gate:** current production scenes still resolve without migration.

### Phase 3 — W01-P28 Shot A migration

Translate the current Shot A intent into components without adding new creative facts.

The migration will be derived from:

- approved W01-P28 shot specification;
- current seed state;
- observed failure in the bad Veo take;
- existing accepted motion requirements.

Create a snapshot/golden test for the exact resolved prompt.

Keep the current flat prompt as a comparison fixture/history until the experiment is accepted.

**Gate:** human inspection of old versus newly compiled prompts before any paid call.

### Phase 4 — Static failure-mode audit

Evaluate the compiled prompt against a checklist derived from the failed take:

- no implicit beginning/climax/end;
- no progressive Damo pose transition;
- no collective crowd command;
- no camera hero move;
- no cue state change;
- no stool/pint action;
- no instruction to recreate appearance already present in the seed.

No provider call.

**Gate:** prompt passes review as temporal direction rather than scene reconstruction.

### Phase 5 — One controlled Veo Lite comparison

Run one approved Shot A seed through the new prompt using the existing production runner.

Compare against the prior take on:

- state persistence through the full duration;
- amount of progressive crouch/pose drift;
- crowd convergence/synchronisation;
- cue stability;
- stool/pint continuity;
- camera plausibility;
- usable editorial seconds.

Do not change seed and prompt simultaneously.

**Gate:** measurable qualitative improvement. If it fails, change components/configuration, not the transport pipeline.

### Phase 6 — Shot-specific functions

Only after Shot A passes, encode B/C/D/E as shot-specific configurations where their motion genuinely differs. Do not force every shot through Damo's function set.

**Gate:** each shot's resolved prompt contains only behaviour visible/relevant to that shot.

### Phase 7 — Generalisation proof

Configure one non-pub scene using the same component vocabulary without modifying compiler code.

This proves the functions describe motion production rather than W01-P28.

**Gate:** second scene resolves and dry-runs from configuration only.

### Phase 8 — Merge/deploy

Before merge:

- compare branch to `main` file-by-file;
- run Python unit/integration suite relevant to motion and production library;
- run Studio frontend checks if any UI/API contracts changed (they should not in early phases);
- verify no deleted legacy workflow is still referenced by documentation as active;
- review resolved W01-P28 prompt text manually;
- merge only reviewed commits, then deploy through the normal main workflow.

No direct experimental edits on `main`.

---

## 8. Explicit non-goals

This work does not:

- redesign Nano character sheets;
- redesign Nano scene coverage;
- change structural panel extraction;
- change approval lineage;
- change first-frame selection;
- change the Google video API adapter;
- create another motion runner;
- reintroduce generated audio;
- make Studio store a second copy of take state;
- regenerate the scene to solve continuity.

---

## 9. Definition of success

The prompt system succeeds when a shot configuration states **what is allowed to move, how it may vary, what state must persist and what transitions are forbidden**, and the existing pipeline can compile and send that direction without knowing anything about the pub.

For W01-P28 Shot A specifically, the generated take should feel like six seconds sampled from an event that was already happening before frame one and is still happening after the last frame — not six seconds in which Veo invents a tiny story.