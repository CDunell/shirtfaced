# SHIRTFACED — Google Renderer Validation Plan

**Status:** ACTIVE experiment plan  
**Goal:** prove an image-to-video workflow that is creatively acceptable **and** economically sustainable before cancelling/downgrading overlapping AI subscriptions.

## Decision principle

Development experimentation may spend aggressively to learn quickly. Production does not inherit that spend profile.

The experiment is successful only if it yields measured pass rates, known failure classes and a cheaper repeatable production policy. A visually impressive demo with unknown retry cost is a failed validation.

## Phase 0 — lock the contracts — COMPLETE

- canonical recurring character authority
- reference/appearance hierarchy
- seed-image recipe
- Flow/Nano/Veo mode-aware production spec
- attempt-vs-scene status separation
- no unauthorised identity invention

## Phase 1 — validation harness — IMPLEMENTED

Studio carries five deliberately difficult benchmark scenes:

1. pub 11:05pm — crowded hero shot, Damo identity, cue/stool geometry, I2V
2. ute tray 3:41am — close identity, contact physics, wet-night environment
3. takeaway 2:30am — ensemble continuity and exact object counting
4. side street 9:26pm — moving group geography, stool + milk crates
5. continuity bridge — reuse an approved in-world frame without identity reset

Manual gates remain:

- owner/canon lock when new facts are introduced
- seed still approval
- final video/performance approval
- promotion of a generated frame into continuity state

Everything between those gates is an automation target.

## Phase 2 — Nano seed generation

Target provider: Gemini API image models.

Default test model: `gemini-3.1-flash-image` (Nano Banana 2). Use Pro only when the benchmark shows a material acceptance-rate gain that offsets its additional cost.

For each benchmark scene:

1. resolve canon and references
2. build one seed prompt package
3. generate configured candidate count
4. record every attempt and reference manifest
5. run automated structural/continuity review
6. owner selects or rejects seed

### Seed metrics

Record:

- candidates generated
- candidates passing fatal gates
- owner-accepted candidate number
- identity failures
- anatomy/contact failures
- prop/geography failures
- average image cost per accepted seed
- time to accepted seed

The long-run target is not minimum image cost. Images are cheap relative to failed video generations; the target is **high seed acceptance before video spend begins**.

## Phase 3 — Veo I2V

Default benchmark path: approved seed → first-frame image-to-video.

Prompt only changes through time: hero motion, secondary/environmental motion, physically motivated camera behaviour and audio.

Initial development may use multiple video candidates. Production should converge toward one primary candidate plus one retry only when classified failure evidence justifies it.

### Video metrics

Record:

- video attempts per accepted shot
- owner acceptance rate on first video
- identity drift
- physics/prop drift
- camera/performance failures
- audio failures
- average cost per accepted video
- time to accepted video

## Phase 4 — retry policy

A failed generation must be classified before another billable call.

Allowed retry classes:

- SOURCE — return to seed; do not spend another video call
- IDENTITY — strengthen reference strategy
- ACTION / ORDER — edit motion instruction only
- PHYSICS / PROP — simplify action or repair source state
- CAMERA — edit camera instruction only
- CROWD — reduce secondary direction
- AUDIO — edit audio instruction only
- CONTINUITY — return to canonical state

No blind `try again` button in production.

## Phase 5 — cost policy

Studio has explicit workflow ceilings:

- per-scene budget
- complete five-scene validation budget
- monthly renderer budget
- seed candidate count
- video candidate count

These are operational ceilings, not hard-coded assumptions about provider prices. Provider prices change; the workflow budgets are our decision.

### Development mode

Spend ceiling may be raised deliberately to answer a specific question such as:

- does Pro materially outperform Flash for multi-character identity?
- do Veo reference images improve I2V enough to justify them?
- is 1080p direct generation worth the latency/cost versus 720p development renders?

Each expensive experiment must have a decision it can change.

### Production mode

After validation, ratchet toward:

- cheap/high-throughput image model by default
- premium image model only for demonstrated hard cases
- approved seed before any video call
- Fast Veo variant for ordinary shots when it passes quality target
- expensive/full-quality video only for hero shots where measured acceptance improves
- one classified retry maximum by default

## Phase 6 — subscription rationalisation

Do not cancel subscriptions because a feature exists on paper. Cancel/downgrade only after the benchmark proves replacement in the user's actual workflow.

Decision gates:

### Grok

Candidate for cancellation when Google passes the five-scene video benchmark with acceptable cost and performance. Video is its current unique job in this stack.

### Claude high tier

Evaluate separately against real coding/repo workloads. Media validation does not prove coding replacement.

### ChatGPT

Evaluate against orchestration, repo operations, research, planning and review workflows after Google media production is stable.

### Google AI Pro

Keep while Flow provides useful manual/directorial value beyond API rendering. Reassess after API workflow is mature.

## Phase 7 — long-run acceptance criteria

Do not declare the renderer stack production-ready until all five benchmark scenes have completed both seed and video stages.

Required report:

- pass/fail by scene
- accepted attempts / total attempts
- cost per accepted seed
- cost per accepted video
- failure distribution
- manual minutes per accepted shot
- which model/mode won each class of scene
- recommended default model policy
- expected monthly cost at 10 / 25 / 50 / 100 finished clips
- subscription cancellation/downgrade recommendation

The winning system is the cheapest **repeatable accepted outcome**, not the cheapest individual API call.

## Deployment safety

`GOOGLE_MEDIA_ENABLED=false` by default. A deployed Studio without a Gemini key remains planning-only and cannot create Google media spend.

Turning on billable rendering requires both:

1. `GEMINI_API_KEY`
2. `GOOGLE_MEDIA_ENABLED=true`

Budget values must be reviewed at the same time.

## Current implementation state

Implemented:

- five-scene validation manifest
- per-scene production packages
- Google image adapter
- Google Veo first-frame I2V adapter
- model/config switches
- budget/candidate guardrails
- read-only validation API

Not yet enabled in production:

- billable Generate controls
- automatic persistence of video bytes/usage into the existing attempt schema
- automated multimodal video review
- live Gemini secret

Those remain intentionally behind the validation gate rather than being smuggled into production as an unmetered button.
