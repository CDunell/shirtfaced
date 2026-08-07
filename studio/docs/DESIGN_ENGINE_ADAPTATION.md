# SHIRTFACED — Design Engine Adaptation

*How the FF / hunter_core engine pattern becomes a design composition engine.*

**Status:** Design document. Written before the build, deliberately — the first
attempt went straight to code and produced a Python duplicate of
`admin/src/design-system/workflow.ts`, a scorer with no interface, and a
generator that averages four layout families into one shape that matches none of
them.

**Precedents read in full:** `C:\crypto` Feature Factory (FF), `C:\orveris-work`
hunter_core + marketing_hunter, `C:\orveris-work\cliniix_site` +
`C:\cliniix` (the worked adaptation).

---

## 1. The isomorphism

Cliniix rests on one sentence — *award↔opportunity matching is the same fact
arriving via multiple documents* — and its own lesson is that if you cannot state
the isomorphism in a sentence, the reuse claim is decoration.

Ours:

> **A set of elements to arrange is a situation. Which arrangement works is
> learned separately, from how the corpus composed comparable situations and
> from which compositions the owner approves.**

That is FF's split exactly. FF clusters *tick shape* — pure morphology, nothing
about outcome — and learns what to do at each address from closed trades. We
cluster *brief shape* — how many elements, of what kinds, in what proportions —
and learn which layout to use from the corpus, then from approvals.

`CLUSTER_MODEL.md` states FF's version of the rule and it transfers unchanged:
*"Clusters are unsupervised — they describe tick shape, not strategy outcome."*
A composition cluster is an address in brief-space, not a verdict.

---

## 2. The engine as it stands

FF, as seven daemons each polling a table and writing another:

```
Tick → Feature → Cluster → Enrich → Hash → Match → Bouncer → Execute
```

hunter_core, as a library of pure functions with the orchestration outside it:

```
sources → adapters → canonical → matcher → features → scoring → surfacing → evidence
```

Ours, at the scale this actually needs:

```
Elements → Feature → Cluster → Enrich → Qualify → Compose → Bouncer → Present
                                            ↑                            │
                                            └──── approvals ─────────────┘
```

The feedback edge is the point. FF's `refresh_strategy_state.py` rebuilds its
cluster→outcome map from **closed trades** on a four-hour cron. Ours rebuilds
from **approve/reject decisions**. That means the approve/reject controls in the
UI are not workflow furniture — they are the training signal, and must be built
that way from the first version rather than retrofitted.

---

## 3. Component-by-component

Graded the way cliniix graded its own, and committed to a number:
**roughly 70% of the pattern carries, and about 15% of any actual code.**
marketing_hunter claims 90–95% shared platform and measures at 12.6%; that gap
is the thing to avoid repeating, so the number here is deliberately low.

| Component | Verdict | Note |
|---|---|---|
| Pipeline-as-stages, each with durable state | **Reuse the pattern** | Not seven daemons. One module per stage, each independently runnable and inspectable. |
| Normalised feature vector | **Reuse the discipline, rebuild the content** | §4. |
| StandardScaler + MiniBatchKMeans, bundled with its scaler | **Reuse nearly as-is** | Including `random_state` fixed, and the bundle carrying its own preconditions. |
| Cluster→outcome map with shrinkage confidence | **Reuse as-is** | `n / (n + 10)`. Ten lines, and the single most portable thing in FF. |
| Refusal as first-class output | **Reuse as-is, fix the flaw** | §6. |
| Rejections as durable rows with reason codes | **Reuse as-is** | So `GROUP BY reason` can show which doubts are load-bearing. |
| Graded doubt as a multiplier | **Reuse, re-target** | FF shrinks position size. We shrink the number of options offered and the confidence shown. |
| Synthesis / scoring split | **Reuse as-is** | marketing_hunter's clearest idea: qualification gates are separate from ranking weights. |
| `FitResult(score, factors, gaps, recommendations, components, confidence)` | **Reuse as-is** | Six fields. `gaps` is what makes it honest. |
| Read-time prioritisation, orthogonal factors | **Reuse the shape** | Impact / confidence / effort / alignment, plain if-else bucketing, alignment downgrades only. |
| Earned trust promotion | **Reuse as-is** | §7 — this is what gates artwork generation. |
| Evidence store, sha256 idempotent | **Reuse the discipline** | Already have it in the corpus provenance records. |
| Workflow state machine | **Already exists — do not rebuild** | `admin/src/design-system/workflow.ts`. §8. |
| `hunter_core` as a shared platform | **Do not build** | It is 1,396 lines of which marketing_hunter uses 7 symbols. Write this concretely; extract when a second domain asks. |
| Order flow, regimes, sessions, funding, PESO, RFM | **Drop** | No analogue. |

---

## 4. Concept → signal translation

FF's dimensions are all **ratios** — "dimensionless, comparable across symbols at
any price level" — which is what lets one model serve a $0.00001 token and a
$100k coin. marketing_hunter had to tear out absolute dollar ceilings that were
"implicitly tuned to one synthetic fixture's economics." Both point the same way,
and the first version of our generator already fell into it with absolute pixel
constants.

**Every feature below is a ratio or a count. No pixels, no absolute sizes.**

| FF / hunter concept | Design signal |
|---|---|
| Tick | One brief: the supplied elements |
| 8D normalised vector | Brief shape: element count, kind mix (text/image/logo), words per text element, aspect ratio per image element, longest-word ratio |
| `CATEGORY_ORDINAL` | Design tradition — **but not ordinal.** Traditions do not lie on a line; band-merch is not "between" varsity and skate. One-hot, or cluster within tradition. |
| Pattern cluster | Composition cluster — which brief-shape family this is |
| `cluster_ev`, `cluster_confidence` | Layout template's approval rate and `n/(n+10)` confidence |
| Best strategy for cluster | Best layout template for this composition cluster |
| Regime | Garment and surface — a cap front panel and a back print are different worlds, and like regime this gates *which* templates apply without changing the cluster |
| `tradeable: false / INSUFFICIENT_EDGE` | `composable: false / INSUFFICIENT_EVIDENCE` |
| Position size multiplier | Options offered, and the confidence shown against each |
| Closed trade outcome | Owner approve / reject on a presented option |
| Fit score | Layout fit — how closely this brief matches the cluster's centroid |
| `gaps` | What the corpus cannot speak to for this brief |

---

## 5. Synthesis before scoring

marketing_hunter separates *which candidates exist at all* (cheap gates:
`MIN_ORDERS`, `LIFT_THRESHOLD`) from *how good each is* (weighted components),
because otherwise threshold logic leaks into weights.

Ours:

**Synthesis** — which layout templates are even eligible for this brief. A
template needs the right slot count, must not require an element kind that was
not supplied, and must have at least a floor of corpus examples behind it.

**Scoring** — of the survivors, which fits best. Centroid distance, tradition
match, approval history.

The current generator has no synthesis stage. It returns three options always,
whether the corpus supports them or not. That is the defect this split fixes.

---

## 6. The refusal path

FF's stated philosophy: *"If FF cannot explain why a coin is tradeable right now,
it emits `tradeable: false, reason: INSUFFICIENT_EDGE`. No recommendation is
created."*

Its actual implementation has two refusal conditions — `NO_CLUSTER` (could not
place the observation) and `NO_CLUSTER_DATA` (placed it, zero recorded outcomes)
— and three flaws worth not inheriting:

1. **The gate is too weak.** `total_samples > 0` means one observation counts as
   knowledge, while `cluster_confidence` sits computed and unused three lines
   away.
2. **It fails open.** A crash while deciding whether it knows enough resolves to
   "yes, I know enough."
3. **~70 gates in one 5,000-line file**, past the point where anyone can see what
   is enforced.

Ours:

| Reason | Condition |
|---|---|
| `NO_CLUSTER` | The brief could not be placed in composition-space at all |
| `INSUFFICIENT_EVIDENCE` | Placed, but the cluster's confidence is below floor — **not** merely `n > 0` |
| `NO_ELIGIBLE_TEMPLATE` | Placed and confident, but nothing survives synthesis |
| `UNMEASURABLE_INPUT` | A supplied image cannot be read well enough to place |

**Refusal fails closed.** An exception while deciding whether we know enough
resolves to *no*. FF's fail-open split is defensible for them because their money
layer fails closed separately; we have no second layer, so the doubt layer is the
only one.

**Each refusal is a durable row with one reason string**, so `GROUP BY reason`
answers which doubt is doing work.

**Gates are a registry of small named predicates ordered by a list**, not a
cascade in one file.

---

## 7. The blocking decision

Cliniix labelled its PHI×LLM question "Phase 0, blocking" and settled it before
building. Ours:

> **How is the print separated from the garment?**

Everything measured downstream — coverage, zone, band structure, therefore every
cluster and every template — depends on it, and the current heuristic
demonstrably fails. Verified visually: a small left-breast skull print measured
as 93.8% "full front", because colour distance from a garment median cannot
survive multi-colour garments, worn shots, or a model's skin and hair inside the
garment box.

| Option | For | Against |
|---|---|---|
| **A. Heuristic only** | No dependency, fast | Demonstrably wrong on a large share of shots |
| **B. Segmentation model** | Actually works on worn shots | A real dependency and runtime cost |
| **C. Restrict to measurable shots** | Honest, no dependency | Discards data — but the corpus now holds six images per product precisely so the measurable frame is present |
| **D. C now, B earned** | Ships, and improves on evidence | Two paths to maintain during promotion |

**Recommendation: D.** Restrict to the frames where the garment is isolated and
the heuristic is reliable — flat lays and close crops — and record which shot
type each measurement came from. Add segmentation later, promoted per shot-type
by §7's agreement rule rather than by assertion.

This mirrors cliniix's own reversal: they recommended LLM-first, then a code
audit found the deterministic path already had the data for free, and the cheap
path won on evidence.

### Earned trust

`template_registry.py` promotes a cheap parser only after **20 documents where
it matched the expensive one exactly** (`PROMOTION_MIN_AGREED = 20`,
`PROMOTION_MIN_RATE = 0.9`) — *"a template only earns trust by matching the LLM
exactly, not approximately."*

Two things get promoted this way here:

1. **Measurement** — the heuristic earns each shot type by agreeing with
   segmentation.
2. **Generation** — composition ships first; generating artwork and type
   treatment unlocks per template family once composition has been approved
   often enough. Owner-stated sequence: the first until it can be trusted, then
   the second.

---

## 8. What gets deleted

`admin/src/design-system/` already holds a tested design contract and workflow —
`domain.ts` (Zod schemas, 11 statuses, 8 layout archetypes, 9 graphic archetypes)
and `workflow.ts` (legal transitions, the 12 hard-gate IDs, `evaluateReview`,
75%/85% approval thresholds). It arrived in the first pull of the session and was
not read.

`studio/app/domain/design_review.py` and `studio/app/services/design_scoring.py`
reimplement it in Python, in a different app, without the workflow — strictly
worse, and it deepened exactly the admin/studio disjointedness the overhaul is
meant to fix.

**Both are deleted.** Measurement and composition emit `HardGate[]` and
`ScoreCategory[]` in `domain.ts`'s shape; `workflow.ts` decides status. One
engine, the one that was already specified and tested.

---

## 9. Prove one thread first

Cliniix's highest-leverage item was one engineer-week proving a single thread end
to end — *"upload pathology PDF → parse → canonical Observation → timeline card
with provenance. That thread de-risks the whole Phase 1 build."*

Ours:

> **Supply a phrase and a logo → cluster the brief → retrieve the matched
> template with its evidence and confidence → render three options → approve one
> → that approval measurably moves the template's confidence.**

If the approval does not move the number, the loop is decorative and the whole
design is wrong. Build that thread before anything else.

---

## 10. Traps, named

From the precedents, and from this session:

- **Don't build the platform first.** hunter_core was abstracted ahead of its
  second consumer and is mostly unused.
- **Don't normalise against absolutes.** Every anchor relative to the corpus.
- **Don't average what you should cluster.** One median layout across four
  families matches none of them.
- **Don't let the docs outrank the code.** Two FF architecture docs describe
  dimensions and tables that do not match the implementation. The code is the
  spec.
- **Don't fabricate confidence.** Missing data is a gap, never evidence of
  absence.
- **Every cut needs a written reason.** Cliniix silently dropped half its work
  packages and had to reconstruct why.
- **The engine gets a kill gate.** Cliniix's is 50 retained users before Phase 2
  spend. Ours: if the approval loop does not move template confidence within the
  first twenty decisions, stop and re-derive.
