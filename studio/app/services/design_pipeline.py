"""The design pipeline: concept -> attempt -> asset -> decision -> version.

This is the design-side counterpart of ``generation_orchestrator`` and
``decision_service``, holding the same guarantees in the same order:

* An attempt row exists before any work is done in its name, so a crash
  mid-execution leaves a record rather than a mystery file.
* Assets are stored through the asset store and recorded with their hash, so
  the database can vouch for the bytes.
* A decision is immutable, signed, and singular. The second decision is a
  conflict, not an overwrite -- unless it carries the same idempotency key, in
  which case it is the same decision asking again.
* Approval is a separate, versioned milestone. A concept can hold seventeen
  attempts; only ``approved_designs`` rows may reach anything downstream.

Concept status is moved as a side effect of the work -- backlog to exploring on
the first attempt, to approved on the first version -- never as a direct edit.
The one exception is the queue itself: ``ready`` is the owner's to set, and
this module only reads it.
"""

from __future__ import annotations

import datetime as dt
import re
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore, design_attempt_key
from app.db.concept_models import (
    ApprovedDesign,
    DesignAsset,
    DesignAttempt,
    DesignAttemptElement,
    DesignConcept,
    DesignDecision,
)
from app.db.models import AuditEvent
from app.domain.enums import (
    DESIGN_DECISION_ATTEMPT_STATES,
    AuditEventType,
    ConceptLibrary,
    ConceptStatus,
    DesignAssetKind,
    DesignAttemptMethod,
    DesignAttemptState,
    DesignDecisionKind,
    FailureCode,
)
from app.domain.errors import StudioError

__all__ = [
    "DesignPipelineConflict",
    "ElementUse",
    "InvalidDesignAction",
    "abandon_attempt",
    "approve_design",
    "create_attempt",
    "create_concept",
    "decide_attempt",
    "next_concept",
    "record_asset",
    "submit_attempt",
]


class DesignPipelineConflict(StudioError):
    """The action collides with something already recorded. HTTP 409."""


class InvalidDesignAction(StudioError):
    """The action is not valid from the current state. HTTP 422."""


@dataclass(frozen=True)
class ElementUse:
    """One archive element an attempt is assembled from."""

    element_id: uuid.UUID
    role: str
    render_id: uuid.UUID | None = None
    settings: dict[str, Any] = dataclass_field(default_factory=dict)


def next_concept(session: Session, library: ConceptLibrary | None = None) -> DesignConcept | None:
    """The concept "next" means: lowest priority number, then lowest external
    number, ready ones ahead of the backlog. ``None`` when the queue is empty.

    Across every library unless one is named. Defaulting to the tee library
    meant "what is next" quietly answered "what is next in one library", and a
    concept created from Research was never the answer no matter how long it
    had waited.
    """
    for status in (ConceptStatus.READY, ConceptStatus.BACKLOG):
        statement = (
            select(DesignConcept)
            .where(DesignConcept.status == status)
            .order_by(DesignConcept.priority, DesignConcept.external_number, DesignConcept.library)
            .limit(1)
        )
        if library is not None:
            statement = statement.where(DesignConcept.library == library)
        concept = session.execute(statement).scalar_one_or_none()
        if concept is not None:
            return concept
    return None


def create_concept(
    session: Session,
    library: ConceptLibrary,
    title: str,
    concept_text: str,
    *,
    source_path: str,
    source_document_hash: str = "",
    garments: Sequence[str] = (),
    treatment_lanes: Sequence[str] = (),
    parsed_json: dict[str, Any] | None = None,
    notes: str = "",
) -> DesignConcept:
    """Put a new idea into the backlog and give it a permanent number.

    Until this existed the only way into the backlog was ``concept_importer``
    reading a Markdown file, so ten researched concepts could not become ten
    backlog concepts -- the gap the 14 August audit names. The research bench
    could only ever bind its output to an idea somebody had already written
    down.

    The number is ``max + 1`` within the library and permanent from here on,
    the same contract the importer honours: nothing is ever renumbered and a
    retired entry keeps its number. Callers must pass a library the importer
    does not read -- ``VINTAGE_RESEARCH`` -- because the importer matches on
    ``(library, external_number)`` and would overwrite the authored fields of
    anything holding a number its document later reaches.
    """
    title = title.strip()
    if not title:
        raise InvalidDesignAction("a concept with no title cannot be found again")

    number = (
        session.execute(
            select(func.coalesce(func.max(DesignConcept.external_number), 0)).where(
                DesignConcept.library == library
            )
        ).scalar_one()
        + 1
    )

    concept = DesignConcept(
        library=library,
        external_number=number,
        slug=_slug(title, number),
        title=title[:200],
        concept_text=concept_text,
        garments=list(garments),
        round=0,
        round_label="",
        source_path=source_path,
        source_document_hash=source_document_hash,
        parsed_json=parsed_json or {},
        status=ConceptStatus.BACKLOG,
        treatment_lanes=list(treatment_lanes),
        notes=notes,
    )
    session.add(concept)
    session.flush()
    return concept


def _require_brief(concept: DesignConcept) -> None:
    """The constitution's steps 2 and 4, enforced where artwork begins."""
    brief = concept.brief
    if brief is not None and brief.ready_for_artwork:
        return

    missing = []
    if brief is None or brief.collection_role is None:
        missing.append("a collection role")
    if brief is None or brief.graphic_archetype is None:
        missing.append("a graphic archetype")

    raise InvalidDesignAction(
        f"#{concept.external_number} {concept.title} has no brief with "
        f"{' and '.join(missing)}. The constitution decides what a product is "
        "before any artwork exists -- open the brief and choose them, and the "
        "advisor will recommend from the corpus as you do."
    )


def _slug(title: str, number: int) -> str:
    """``0261-a-title-like-this``. The number leads because titles repeat --
    "shirtfaced" appears three times in the tee library -- and the slug is
    unique on its own."""
    words = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"{number:04d}-{words}"[:160].rstrip("-")


def create_attempt(
    session: Session,
    concept: DesignConcept,
    method: DesignAttemptMethod,
    *,
    brief_overrides: dict[str, Any] | None = None,
    production_prompt: str = "",
    model: str = "",
    model_settings: dict[str, Any] | None = None,
    reference_inputs: dict[str, Any] | None = None,
    execution_rules: dict[str, Any] | None = None,
    parent_attempt: DesignAttempt | None = None,
    elements: Sequence[ElementUse] = (),
) -> DesignAttempt:
    """Open one execution of a concept. The row exists before any work does.

    Refuses without a brief carrying a collection role and a graphic archetype.
    That is the constitution's own order -- "define the product, define its role
    in the range, select the garment architecture, select the graphic
    architecture" all precede "construct the composition" -- and the 14 August
    audit's diagnosis of why output arrived as competent generic work: the
    research bench produced a graphic idea and jumped straight to artwork.

    Deliberately narrower than §3, which requires eleven fields before artwork.
    Gating on two is enough to stop an undeclared design and cheap enough that
    it does not become ceremony before a first sketch. Widening it is the
    owner's decision, not a thing to creep.
    """
    _require_brief(concept)
    if parent_attempt is not None and parent_attempt.concept_id != concept.id:
        raise InvalidDesignAction(
            f"attempt {parent_attempt.id} belongs to another concept; "
            "a variation cannot cross concepts"
        )

    number = session.execute(
        select(func.coalesce(func.max(DesignAttempt.attempt_number), 0)).where(
            DesignAttempt.concept_id == concept.id
        )
    ).scalar_one()

    # The concept as it stands, frozen with the attempt: the library can be
    # re-imported afterwards and the attempt must still be explicable.
    snapshot: dict[str, Any] = {
        "library": concept.library.value,
        "external_number": concept.external_number,
        "slug": concept.slug,
        "title": concept.title,
        "concept_text": concept.concept_text,
        "garments": list(concept.garments),
        "treatment_lanes": list(concept.treatment_lanes),
    }
    snapshot.update(brief_overrides or {})

    attempt = DesignAttempt(
        concept_id=concept.id,
        parent_attempt_id=None if parent_attempt is None else parent_attempt.id,
        attempt_number=number + 1,
        method=method,
        state=DesignAttemptState.PLANNED,
        brief_snapshot=snapshot,
        source_concept_hash=concept.source_document_hash,
        production_prompt=production_prompt,
        model=model,
        model_settings=model_settings or {},
        reference_inputs=reference_inputs or {},
        execution_rules=execution_rules or {},
    )
    session.add(attempt)
    session.flush()

    for use in elements:
        session.add(
            DesignAttemptElement(
                design_attempt_id=attempt.id,
                element_id=use.element_id,
                role=use.role,
                render_id=use.render_id,
                settings=dict(use.settings),
            )
        )

    if concept.status in (ConceptStatus.BACKLOG, ConceptStatus.READY):
        concept.status = ConceptStatus.EXPLORING

    session.flush()
    return attempt


def record_asset(
    session: Session,
    store: AssetStore,
    attempt: DesignAttempt,
    kind: DesignAssetKind,
    name: str,
    data: bytes,
    mime_type: str,
    *,
    width: int | None = None,
    height: int | None = None,
) -> DesignAsset:
    """Store one file for an attempt and record what was stored."""
    if attempt.state not in (
        DesignAttemptState.PLANNED,
        DesignAttemptState.GENERATING,
        DesignAttemptState.GENERATED,
    ):
        raise InvalidDesignAction(
            f"attempt is {attempt.state.value}; assets are added before review, not after"
        )

    concept = attempt.concept
    key = design_attempt_key(concept.library.value, concept.external_number, str(attempt.id), name)
    stored = store.save(key, data, mime_type)

    asset = DesignAsset(
        design_attempt_id=attempt.id,
        kind=kind,
        relative_path=stored.key,
        sha256=stored.sha256,
        mime_type=stored.mime_type,
        width=width,
        height=height,
        byte_size=stored.byte_size,
    )
    session.add(asset)

    if attempt.state in (DesignAttemptState.PLANNED, DesignAttemptState.GENERATING):
        attempt.state = DesignAttemptState.GENERATED

    session.flush()
    return asset


def abandon_attempt(session: Session, attempt: DesignAttempt, reason: str) -> DesignAttempt:
    """Close an attempt that will never be worked, with the reason recorded.

    The hole this fills: ``decide_attempt`` only accepts ``awaiting_decision``,
    and an attempt only reaches that state by having artwork submitted. So an
    attempt opened in error -- the wrong concept, a prompt that belongs to
    another idea, a path that no longer exists -- had no exit at all. It sat in
    ``planned`` forever, at the top of the queue, and the only way to remove it
    was to delete the row.

    Deleting is the wrong answer in a system whose whole argument is that
    decisions are recorded rather than erased. This settles it the way
    everything else here is settled: a terminal state, a reason, an audit event,
    and the row intact so the mistake stays legible.

    Not a decision: ``design_decisions`` is the owner's judgement on artwork, and
    there is no artwork here. Abandoning is bookkeeping about a row that should
    not have been made.
    """
    reason = reason.strip()
    if not reason:
        raise InvalidDesignAction("an attempt abandoned for no stated reason is just a gap")
    if attempt.state in (
        DesignAttemptState.APPROVED,
        DesignAttemptState.REJECTED,
        DesignAttemptState.VARIATION_REQUESTED,
    ):
        raise InvalidDesignAction(
            f"attempt is {attempt.state.value}; a decided attempt is already settled and "
            "abandoning it would overwrite the decision"
        )
    if attempt.approved_design is not None:
        raise DesignPipelineConflict(
            "this attempt is an approved version of its concept and cannot be abandoned"
        )

    attempt.state = DesignAttemptState.FAILED
    attempt.failure_code = FailureCode.CONFIGURATION
    attempt.failure_message = reason

    session.add(
        AuditEvent(
            event_type=AuditEventType.DESIGN_DECISION_RECORDED,
            actor="owner",
            payload_json={
                "concept_id": str(attempt.concept_id),
                "attempt_id": str(attempt.id),
                "attempt_number": attempt.attempt_number,
                "decision": "abandoned",
                "reason": reason,
            },
        )
    )
    session.flush()
    return attempt


def submit_attempt(session: Session, attempt: DesignAttempt) -> DesignAttempt:
    """Put an attempt in front of the owner. Requires something to look at."""
    if attempt.state is not DesignAttemptState.GENERATED:
        raise InvalidDesignAction(
            f"attempt is {attempt.state.value}; only a generated attempt can be submitted"
        )
    if not attempt.assets:
        raise InvalidDesignAction("an attempt with no assets has nothing to review")

    attempt.state = DesignAttemptState.AWAITING_DECISION
    session.flush()
    return attempt


def decide_attempt(
    session: Session,
    attempt: DesignAttempt,
    decision: DesignDecisionKind,
    actor: str,
    *,
    reason: str | None = None,
    note: str | None = None,
    instruction: str | None = None,
    idempotency_key: str | None = None,
) -> DesignDecision:
    """Record the owner's judgment. Immutable, signed, and exactly one."""
    actor = actor.strip()
    if not actor:
        raise InvalidDesignAction("an approval nobody signed is not an approval")

    # Queried rather than read off the relationship: a decision inserted by
    # this same session does not invalidate the parent's cached collection,
    # and the second call must see the first either way.
    existing = session.execute(
        select(DesignDecision).where(DesignDecision.design_attempt_id == attempt.id)
    ).scalar_one_or_none()
    if existing is not None:
        if idempotency_key is not None and existing.idempotency_key == idempotency_key:
            return existing
        raise DesignPipelineConflict(
            f"attempt already decided: {existing.decision.value} by {existing.actor}. "
            "A second decision is a mistake or a disagreement, and overwriting the "
            "first would lose which it was."
        )
    if attempt.state is not DesignAttemptState.AWAITING_DECISION:
        raise InvalidDesignAction(
            f"attempt is {attempt.state.value}; only awaiting_decision can be decided"
        )

    recorded = DesignDecision(
        design_attempt_id=attempt.id,
        decision=decision,
        reason=reason,
        note=note,
        instruction=instruction,
        actor=actor,
        idempotency_key=idempotency_key,
    )
    session.add(recorded)
    # The decision lands first. Everything after this is bookkeeping that must
    # never undo it.
    session.flush()

    attempt.state = DESIGN_DECISION_ATTEMPT_STATES[decision]

    _settle_linked_composition(session, attempt, decision, actor, note)

    session.add(
        AuditEvent(
            event_type=AuditEventType.DESIGN_DECISION_RECORDED,
            actor=actor,
            payload_json={
                "concept_id": str(attempt.concept_id),
                "concept_number": attempt.concept.external_number,
                "attempt_id": str(attempt.id),
                "attempt_number": attempt.attempt_number,
                "decision": decision.value,
            },
        )
    )
    session.flush()
    return recorded


def _settle_linked_composition(
    session: Session,
    attempt: DesignAttempt,
    decision: DesignDecisionKind,
    actor: str,
    note: str | None,
) -> None:
    """Keep a linked composed design consistent with the attempt's decision.

    One decision surface: the attempt. The composed row's in-row state mirrors
    it so the compose bench and the designs bench never tell different stories
    about the same artwork.
    """
    from app.db.archive_models import ComposedDesign
    from app.domain.enums import AttemptState

    design = session.execute(
        select(ComposedDesign).where(ComposedDesign.design_attempt_id == attempt.id)
    ).scalar_one_or_none()
    if design is None:
        return

    states = {
        DesignDecisionKind.APPROVED: AttemptState.APPROVED,
        DesignDecisionKind.REJECTED: AttemptState.REJECTED,
        DesignDecisionKind.VARIATION_REQUESTED: AttemptState.VARIATION_REQUESTED,
    }
    design.state = states[decision].value
    design.decided_by = actor
    design.decided_at = dt.datetime.now(dt.UTC)
    design.decision_note = note or ""

    # The decision is also the composer's training signal. Approve and reject
    # feed its per-grammar confidence; a variation request does not, because it
    # judges the content rather than the construction that set it.
    if decision in (DesignDecisionKind.APPROVED, DesignDecisionKind.REJECTED):
        from app.services.design_composition import record_learning

        record_learning(design.grammar_key, decision is DesignDecisionKind.APPROVED)


def approve_design(
    session: Session,
    attempt: DesignAttempt,
    approved_by: str,
    *,
    master_asset: DesignAsset | None = None,
    production_spec: dict[str, Any] | None = None,
) -> ApprovedDesign:
    """Freeze one approved attempt as the concept's next production version."""
    approved_by = approved_by.strip()
    if not approved_by:
        raise InvalidDesignAction("an approval nobody signed is not an approval")
    if attempt.state is not DesignAttemptState.APPROVED:
        raise InvalidDesignAction(
            f"attempt is {attempt.state.value}; only an approved attempt becomes a version"
        )
    existing = session.execute(
        select(ApprovedDesign).where(ApprovedDesign.design_attempt_id == attempt.id)
    ).scalar_one_or_none()
    if existing is not None:
        raise DesignPipelineConflict(
            f"attempt is already version {existing.version} of this concept"
        )

    master = master_asset or _default_master(attempt)
    if master is None:
        raise InvalidDesignAction(
            "no print_master or artwork asset to pin; an approved design must keep its master"
        )
    if master.design_attempt_id != attempt.id:
        raise InvalidDesignAction("the master asset belongs to a different attempt")

    concept = attempt.concept
    current = session.execute(
        select(func.coalesce(func.max(ApprovedDesign.version), 0)).where(
            ApprovedDesign.concept_id == concept.id
        )
    ).scalar_one()

    # The older versions become history the moment a newer one exists. Their
    # one mutable field records when that happened. Queried, not read off the
    # relationship, for the same session-cache reason as the decision check.
    now = dt.datetime.now(dt.UTC)
    standing = session.execute(
        select(ApprovedDesign).where(
            ApprovedDesign.concept_id == concept.id,
            ApprovedDesign.superseded_at.is_(None),
        )
    ).scalars()
    for previous in standing:
        previous.superseded_at = now

    version = ApprovedDesign(
        concept_id=concept.id,
        design_attempt_id=attempt.id,
        master_asset_id=master.id,
        version=current + 1,
        approved_by=approved_by,
        production_spec=production_spec or {},
    )
    session.add(version)
    concept.status = ConceptStatus.APPROVED

    session.add(
        AuditEvent(
            event_type=AuditEventType.DESIGN_APPROVED,
            actor=approved_by,
            payload_json={
                "concept_id": str(concept.id),
                "concept_number": concept.external_number,
                "attempt_id": str(attempt.id),
                "version": current + 1,
                "master_asset_id": str(master.id),
            },
        )
    )
    session.flush()
    return version


def _default_master(attempt: DesignAttempt) -> DesignAsset | None:
    """The print master if one exists, else the artwork. Never a preview."""
    for kind in (DesignAssetKind.PRINT_MASTER, DesignAssetKind.ARTWORK):
        for asset in attempt.assets:
            if asset.kind is kind:
                return asset
    return None
