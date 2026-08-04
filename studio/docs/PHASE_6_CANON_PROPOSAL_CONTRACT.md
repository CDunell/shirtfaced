# SHIRTFACED STUDIO — PHASE 6 CANON PROPOSAL CONTRACT

**Status:** Owner's specification, recorded 5 August 2026
**Depends on:** Phase 4 pending `CanonProposal` records, Phase 5 decisions and the safe
Markdown update algorithm
**Authority:** the owner. ADR-005 — no model changes permanent canon.

## 1. Purpose

Phase 6 is the only path by which `WORLD.md` changes without the owner editing it
directly, and it changes nothing until the owner approves an exact diff.

## 2. Workflow

1. A review supplies an optional permanent lesson.
2. Studio compares it against `WORLD.md`.
3. Studio classifies the proposal as one of:
   - **already covered** — an existing rule says this;
   - **genuine addition** — a new rule with no existing home;
   - **refinement** — an existing rule should be tightened or clarified;
   - **contradiction** — it conflicts with a rule already in canon;
   - **too specific** — scene-level, not canon.
4. Studio produces the exact proposed diff.
5. Nothing changes until the diff is explicitly approved.
6. Approval applies the diff and records: the source rejection, the reviewer, the
   approved wording, the affected section and a timestamp.
7. Rejection leaves `WORLD.md` untouched.

## 3. Permanent lessons are never inferred

A permanent lesson narrows the world for every future image. It must be deliberate.

Only a reviewer's `new_rule_proposal` may become one. `material_drift` is ordinary
review prose describing a single frame and must never be promoted, and neither may a
rejection reason. A rejection with no proposed rule records
`**Permanent lesson:** No new permanent lesson.` and that is the correct outcome.

*Implemented and tested as of Phase 5.* An earlier version wrote `material_drift` into
the permanent lesson line; that was a defect, not a design.

## 4. Classification

Classification is advisory. It orders the queue and explains the recommendation; it
never decides.

The owner's standing guidance, from the two live cases on 5 August 2026:

- **House Party — Branded Clothing and Packaging** → *already covered*. Blank
  Shirtfaced garments and no visible commercial branding are already permanent canon.
  A duplicate rule adds nothing.
- **Lookout Alternate — Pickup Tub** → *do not promote on the label alone*. The vehicle
  canon already requires an Australian tray-back ute and prohibits heroic automotive
  photography. Anything more specific is scene-level unless it recurs.

The general principle both cases share: **a lesson that an existing rule already
implies is not a new rule.** Recurrence, not severity, is what promotes a scene-level
observation to canon.

## 5. The diff

The proposed change is shown as an exact diff against the current `WORLD.md`, with the
affected section named. The owner approves the wording, not a summary of it.

Application: the Phase 5 safe update algorithm, unchanged — validate the candidate with
the loader, write atomically, re-import, commit only the intended file, record the
hash and commit.

A canon proposal that fails to apply leaves `WORLD.md` untouched and flags
reconciliation. It never half-applies.

## 6. Record of an approved proposal

- source rejection (attempt and shot);
- reviewer (the model that proposed it);
- approved wording, as applied;
- affected section;
- timestamp.

`CanonProposal` already carries `world_id`, `attempt_id`, `status`, `proposed_text`,
`insertion_anchor`, `reason`, `human_note`, `git_commit`, `created_at` and `decided_at`.

## 7. Explicitly out of scope

`# Next Prompt Brief`, `# Status Key`, `## Future Buckets` and the two rotation tables
stay unread by Phase 6.

They either become real application inputs later through a deliberate decision, or they
remain human-only documentation. Wiring dead sections into canon proposals would, in
the owner's words, "give the furniture voting rights".

## 8. Approved reference frames — a separate concern

Not Phase 6, recorded here so it is not lost. Approvals append to
`# Approved Reference Frames` and the section grows without limit.

The intended model:

- **Active** — the strongest 12 to 20 references, and the only ones planning reads;
- **Archive** — the full approval history, still searchable;
- **Pinned** — exceptional frames that never age out automatically.

This needs its own phase. Nothing in the current implementation reads the section, so
it is presently a record rather than an input.
