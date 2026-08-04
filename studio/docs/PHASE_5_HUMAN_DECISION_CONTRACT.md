# SHIRTFACED STUDIO — PHASE 5 HUMAN DECISION CONTRACT

**Status:** Implementation specification aligned to current repository contracts  
**Depends on:** Phase 4 attempt, asset, review and pending-canon-proposal records  
**Authority:** `PRODUCT_SPEC.md`, `DATA_MODEL.md`, `API_CONTRACT.md`, `WORKFLOW.md`, ADR-005 and ADR-010

## 1. Purpose

Phase 5 makes the owner’s decision final. It implements approval, rejection, variation requests, optional reference promotion, duplicate-decision protection and the first safe writes to `CONTINUITY.md` and `SHOTLIST.md`.

The automated review remains advice. Its recommendation, verdict, scores, compliance flags and nine gates never substitute for the owner’s decision.

Phase 5 does not apply permanent `WORLD.md` canon proposals. That remains the separately approved canon-proposal path.

## 2. Preconditions shared by all decisions

A decision may be created only when:

- the attempt exists;
- the attempt belongs to an imported world;
- the attempt is in `awaiting_decision`;
- the attempt has an original stored image;
- no `HumanDecision` already exists for the attempt;
- the current actor is the owner;
- the world-level advisory lock can be acquired;
- current world files load and validate before any file-changing decision;
- the attempt’s provenance remains inspectable even when current document hashes have changed.

The latest review may be displayed but is not a decision prerequisite if the application deliberately permits human action after review failure. If that exception is supported, the UI must state that automated review is unavailable.

## 3. Integrity and idempotency

Enforce one final decision per attempt with a database unique constraint on `HumanDecision.attempt_id`, not only an application check.

Decision endpoints accept an idempotency key or return the existing semantically identical decision when the same request is retried. A different decision for an already decided attempt returns `409` and changes nothing.

Every decision writes an append-only `AuditEvent` containing the attempt, decision, actor, request metadata and resulting file/Git state. It must not store secrets or signed asset URLs.

## 4. Approve

Endpoint: `POST /api/attempts/{attempt_id}/approve`

Body remains:

```json
{
  "promote_to_reference": false,
  "note": ""
}
```

### Database result

1. Create `HumanDecision(decision="approved")`.
2. Move the attempt to terminal `approved`.
3. Mark the shot `approved`.
4. Persist the optional human note.
5. If requested, promote the existing approved image through the repository’s reference-asset representation.
6. Record audit events.

An approved shot must reference at least one approved attempt. A reference must derive from an approved attempt. Reference promotion cannot occur independently of approval.

### Markdown result

Application code constructs, validates and applies:

- the selected shot’s `SHOTLIST.md` marker becomes approved;
- one structured approved entry is added to `CONTINUITY.md` using verified attempt, shot, prompt, review and human-decision data;
- relevant rotation audit tables may be updated without changing their established headings or table formats;
- `Next Rotation Priority`, `Next Camera Priority` and `Next Prompt Brief` are not model-authored automatically.

The continuity entry records factual state, not invented narrative: shot ID/scene, hero product, camera, status, strongest success or human note, and reference status where applicable.

### Git result

After candidate files validate and replace successfully, stage only the intended world documents and create one repository-standard commit. Store the commit hash in audit metadata or the existing decision reconciliation record.

## 5. Reject

Endpoint: `POST /api/attempts/{attempt_id}/reject`

Body:

```json
{
  "reason": "The group reads as resigned rather than optimistic."
}
```

Rejection reason is required, trimmed and length-bounded. Generic values such as “bad” may be accepted only if product requirements explicitly allow them; the interface should request a material reason.

### Database result

1. Create `HumanDecision(decision="rejected")` with the owner’s exact reason.
2. Move the attempt to terminal `rejected`.
3. Keep the shot `planned` unless the owner separately abandons it.
4. Preserve the image, prompt, review and attempt provenance.
5. Record audit events.

### Rejected-drift result

The full rejection history is retained, but the current planner reads only the first three `###` subsections under `# Rejected Drift`, each truncated to 600 characters.

Therefore Phase 5 must use this explicit policy:

- insert the newest human-confirmed drift entry at the top of `# Rejected Drift`;
- keep older entries below it as history;
- the first three entries are the active planner set;
- never delete or overwrite older drift silently;
- keep each active entry’s permanent lesson inside the first 600 characters;
- do not turn a one-off rendering artefact into a permanent lesson;
- when a displaced lesson remains globally essential, promote it through a separately approved canon proposal or a deliberate human edit to planner-visible canon.

The model may propose a draft lesson, but application code constructs the final Markdown from validated fields. The owner’s reason remains verbatim data; generalisation is either an explicitly accepted concise lesson or omitted.

Recommended deterministic entry shape:

```markdown
### <Shot ID> — <short drift label>

**Status:** REJECTED

**Reason:** <human reason>

**Permanent lesson:** <accepted repeatable lesson, or “No new permanent lesson.”>
```

The heading and generated structure are escaped/sanitised so user text cannot create unintended headings or tables.

No rejection changes `WORLD.md`.

## 6. Variation request

Endpoint: `POST /api/attempts/{attempt_id}/variation`

Body:

```json
{
  "instruction": "Keep the rear-seat view but reveal the tote through a natural handle-carrying action."
}
```

### Result

1. Require a non-empty, length-bounded instruction.
2. Create `HumanDecision(decision="variation_requested")`.
3. Move the parent attempt to a terminal variation state after the state-machine conflict below is resolved.
4. Keep the shot planned/active for another attempt.
5. Do not update `CONTINUITY.md`, `SHOTLIST.md` status or permanent canon.
6. Release the world for the next explicit action.

The variation endpoint records intent only. It does not call a model or generate an image.

A separate explicit generation action creates a child attempt with `parent_attempt_id`, next attempt number, prior prompt, latest review and exact human instruction. It does not silently reuse the same seed/settings and never mutates the parent attempt.

### Required specification reconciliation

`WORKFLOW.md` says to mark the attempt `variation_requested`, and `HumanDecision` permits that decision. However `ARCHITECTURE.md`, the PostgreSQL attempt-state enum and Python `AttemptState` currently end attempts only as `approved`, `rejected` or `failed`; they do not contain `variation_requested`.

Phase 5 must resolve this explicitly before implementation. Recommended resolution:

- add terminal attempt state `variation_requested`;
- update `ARCHITECTURE.md`, `DATA_MODEL.md`, Python enum and PostgreSQL enum through a migration;
- keep it outside the active-attempt partial index so the world is released;
- retain `HumanDecision.decision="variation_requested"`;
- do not map a variation to `rejected`, because that would falsely record the owner’s decision and pollute rejected-drift learning.

Record the reconciliation as an ADR. Until it is resolved, the variation endpoint is not implementation-ready.

## 7. Reference promotion

Reference promotion is an approval option, not a fourth decision.

The reference record must:

- point to or derive from the approved original asset;
- preserve the original bytes and SHA-256;
- record actor and timestamp;
- appear in world/history views;
- never make an unapproved attempt a reference;
- be idempotent for repeated identical approval requests.

If reference promotion fails after the approval decision persists, approval remains final and reconciliation is flagged. The interface must not report reference success.

## 8. Safe Markdown update algorithm

Models never write canonical files directly.

For approval or rejection:

1. acquire the world advisory lock;
2. read current files and hashes;
3. parse and validate all current documents;
4. construct candidate text in memory with deterministic application code;
5. preserve encoding, established headings and supported table structure;
6. validate the complete candidate document set with the existing loader;
7. write candidate files to temporary siblings on the same filesystem;
8. fsync/close as supported and atomically replace intended targets;
9. import the resulting world state into PostgreSQL;
10. stage only intended files and create a Git commit;
11. persist the resulting hashes/commit and success audit event;
12. release the lock.

Never interpolate untrusted user/model text into a shell command or Git commit command.

## 9. Cross-system failure policy

The database, filesystem and Git cannot share one transaction. Follow `WORKFLOW.md`:

### Database decision succeeds; Markdown fails

- preserve the final human decision;
- keep prior valid world files untouched where atomic replacement has not happened;
- append `reconciliation_required` audit metadata with exact stage/error;
- release the lock;
- return a response that distinguishes decision success from document-sync failure;
- block contradictory second decisions.

### Markdown succeeds; import fails

- restore the last valid file snapshot where safe;
- preserve the decision;
- flag reconciliation;
- never claim import success.

### Markdown/import succeeds; Git commit fails

- preserve valid files and imported state;
- preserve the decision;
- flag `uncommitted_changes` with exact safe error;
- do not automatically reset or discard files;
- provide an explicit reconciliation action.

### Reference promotion fails

- preserve approval;
- flag only reference reconciliation;
- do not duplicate or corrupt the original asset.

## 10. API responses

Successful responses return:

- attempt ID and terminal state;
- persisted human decision;
- shot status;
- reference result when requested;
- continuity/shotlist sync status;
- resulting document hashes where changed;
- Git commit hash where created;
- reconciliation state and safe message.

Errors:

- `404` — attempt not found;
- `409` — attempt not awaiting decision, duplicate conflicting decision or world lock unavailable;
- `422` — invalid reason/instruction, missing required asset or world documents fail validation;
- `500`/repository-standard operational response — decision persisted but downstream reconciliation failed. The body must not imply the decision rolled back.

## 11. Interface contract

The decision panel shows:

- image and provenance;
- latest automated review with “This is advice. You decide.”;
- Approve, Reject and Request variation;
- optional Promote to reference on approval;
- required rejection reason;
- required variation instruction;
- explicit confirmation for a final decision;
- disabled controls after a decision;
- distinct success states for database decision, document sync, reference promotion and Git commit;
- reconciliation warning with an actionable next step.

Double clicks, refreshes and network retries must not create duplicate decisions or child attempts.

## 12. Required tests

### Database and concurrency

- unique final decision per attempt;
- simultaneous approve/reject produces one winner;
- world advisory lock behaviour;
- decided attempt releases active-attempt constraint;
- decision and audit rows persist.

### Approval

- attempt and shot approved;
- approved continuity entry constructed and validated;
- shotlist marker updated;
- optional reference only from approved attempt;
- exact intended Git files committed;
- repeat identical request is idempotent.

### Rejection

- attempt rejected, shot remains planned;
- reason required and persisted;
- newest rejected drift becomes first subsection;
- only first three are active in planner request;
- permanent lesson remains inside 600 characters;
- older drift remains in the file;
- `WORLD.md` byte-identical.

### Variation

- parent reaches the explicitly reconciled terminal variation state;
- no Markdown change;
- no generation during request;
- child created only by later explicit action;
- child links parent and receives instruction/review context.

### Failure and safety

- malicious Markdown-looking reason cannot inject headings;
- Markdown validation failure preserves decision and prior valid files;
- import failure flagged;
- Git failure leaves valid files and flags uncommitted state;
- reference failure preserves approval/original asset;
- model text never directly reaches file-write functions.

### End to end

Use three isolated attempts for the same planned shot:

1. approve one and optionally promote it to reference;
2. reject one with a repeatable drift lesson;
3. request variation on one and explicitly create its child.

Confirm history, locks, files, hashes, audit events and restart persistence after each path.

## 13. Definition of done

Phase 5 is complete when the owner can make exactly one durable final decision per attempt; approval safely updates shot/continuity state and may promote a reference; rejection preserves the attempt, keeps the shot planned and makes the newest confirmed drift planner-visible; variation records intent without hidden generation; every document mutation is deterministically constructed, fully validated and auditable; and any cross-system failure is reported honestly without losing the owner’s decision.
