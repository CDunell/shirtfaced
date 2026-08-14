"""The design backlog over HTTP.

The concept library holds 260 numbered ideas, and until this router existed
"what is next" was answered from whichever conversation last remembered. Now it
is a query: concepts come from PostgreSQL with their attempts, decisions and
approved versions attached, and the queue endpoint returns the one thing to do
next.

The state changes here follow the pipeline's rules, not their own: a decision
needs a person's name, an approval is a versioned milestone, and nothing on
this router can move a concept except by doing the work that moves it.
"""

from __future__ import annotations

import datetime as dt
import tempfile
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.adapters.asset_store import AssetStoreError, FilesystemAssetStore
from app.config import Settings, get_settings
from app.db.concept_models import (
    ApprovedDesign,
    DesignAsset,
    DesignAttempt,
    DesignConcept,
    DesignDecision,
    DesignReviewRecord,
)
from app.db.session import get_db_session
from app.domain.design_review import (
    CATEGORY_LIMITS,
    GATE_LABELS,
    HARD_GATE_IDS,
    DesignReviewInput,
    HardGate,
    ReviewDecision,
    ReviewResult,
    ScoreCategory,
)
from app.domain.enums import (
    ConceptLibrary,
    ConceptStatus,
    DesignAssetKind,
    DesignAttemptMethod,
    DesignAttemptState,
    DesignDecisionKind,
)
from app.services.approved_print import PrintRefused, available_garments, print_approved
from app.services.design_extraction import measure, to_review
from app.services.design_pipeline import (
    DesignPipelineConflict,
    InvalidDesignAction,
    approve_design,
    create_attempt,
    decide_attempt,
    next_concept,
    record_asset,
    submit_attempt,
)
from app.services.design_scoring import (
    NotEligible,
    ReviewFrozen,
    empty_review,
    evaluate_review,
    guard_decision,
    load_review,
    rubric,
    score_design,
)
from app.services.next_action import next_action

router = APIRouter(prefix="/api/concepts", tags=["concepts"])

SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]

# Design artwork arrives as files. Generous but bounded, like photo uploads.
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


# --- Views -------------------------------------------------------------------


class AssetView(BaseModel):
    id: str
    kind: str
    relative_path: str
    sha256: str
    mime_type: str
    width: int | None
    height: int | None
    byte_size: int

    @classmethod
    def of(cls, asset: DesignAsset) -> AssetView:
        return cls(
            id=str(asset.id),
            kind=asset.kind.value,
            relative_path=asset.relative_path,
            sha256=asset.sha256,
            mime_type=asset.mime_type,
            width=asset.width,
            height=asset.height,
            byte_size=asset.byte_size,
        )


class DecisionView(BaseModel):
    id: str
    decision: str
    reason: str | None
    note: str | None
    instruction: str | None
    actor: str
    created_at: dt.datetime

    @classmethod
    def of(cls, decision: DesignDecision) -> DecisionView:
        return cls(
            id=str(decision.id),
            decision=decision.decision.value,
            reason=decision.reason,
            note=decision.note,
            instruction=decision.instruction,
            actor=decision.actor,
            created_at=decision.created_at,
        )


class ApprovedDesignView(BaseModel):
    id: str
    version: int
    approved_by: str
    approved_at: dt.datetime
    superseded_at: dt.datetime | None
    master_asset_id: str
    design_attempt_id: str

    @classmethod
    def of(cls, version: ApprovedDesign) -> ApprovedDesignView:
        return cls(
            id=str(version.id),
            version=version.version,
            approved_by=version.approved_by,
            approved_at=version.approved_at,
            superseded_at=version.superseded_at,
            master_asset_id=str(version.master_asset_id),
            design_attempt_id=str(version.design_attempt_id),
        )


class AttemptView(BaseModel):
    id: str
    concept_id: str
    attempt_number: int
    method: str
    state: str
    parent_attempt_id: str | None
    created_at: dt.datetime
    assets: list[AssetView]
    decision: DecisionView | None
    approved_version: int | None

    @classmethod
    def of(cls, attempt: DesignAttempt) -> AttemptView:
        return cls(
            id=str(attempt.id),
            concept_id=str(attempt.concept_id),
            attempt_number=attempt.attempt_number,
            method=attempt.method.value,
            state=attempt.state.value,
            parent_attempt_id=(
                None if attempt.parent_attempt_id is None else str(attempt.parent_attempt_id)
            ),
            created_at=attempt.created_at,
            assets=[AssetView.of(asset) for asset in attempt.assets],
            decision=None if attempt.decision is None else DecisionView.of(attempt.decision),
            approved_version=(
                None if attempt.approved_design is None else attempt.approved_design.version
            ),
        )


class ConceptView(BaseModel):
    id: str
    library: str
    external_number: int
    slug: str
    title: str
    concept_text: str
    status: str
    concept_kind: str
    retirement: str
    salvage: str
    garments: list[str]
    round: int
    round_label: str
    priority: int
    tags: list[str]
    treatment_lanes: list[str]
    notes: str
    # Derived: what has actually happened to this concept.
    attempt_count: int
    latest_attempt_state: str | None
    approved_versions: int

    @classmethod
    def of(
        cls,
        concept: DesignConcept,
        *,
        attempt_count: int = 0,
        latest_attempt_state: str | None = None,
        approved_versions: int = 0,
    ) -> ConceptView:
        return cls(
            id=str(concept.id),
            library=concept.library.value,
            external_number=concept.external_number,
            slug=concept.slug,
            title=concept.title,
            concept_text=concept.concept_text,
            status=concept.status.value,
            concept_kind=concept.concept_kind.value,
            retirement=concept.retirement,
            salvage=str(concept.parsed_json.get("salvage", "")),
            garments=list(concept.garments),
            round=concept.round,
            round_label=concept.round_label,
            priority=concept.priority,
            tags=list(concept.tags),
            treatment_lanes=list(concept.treatment_lanes),
            notes=concept.notes,
            attempt_count=attempt_count,
            latest_attempt_state=latest_attempt_state,
            approved_versions=approved_versions,
        )


class ConceptDetailView(ConceptView):
    attempts: list[AttemptView]
    versions: list[ApprovedDesignView]


# --- Request bodies ----------------------------------------------------------


class AttemptIn(BaseModel):
    method: DesignAttemptMethod
    production_prompt: str = ""
    model: str = ""
    model_settings: dict[str, Any] = Field(default_factory=dict)
    reference_inputs: dict[str, Any] = Field(default_factory=dict)
    execution_rules: dict[str, Any] = Field(default_factory=dict)
    brief_overrides: dict[str, Any] = Field(default_factory=dict)
    parent_attempt_id: uuid.UUID | None = None


class DecisionIn(BaseModel):
    decision: DesignDecisionKind
    # No default. A decision has an author or it is not a decision.
    actor: str = Field(min_length=1, max_length=64)
    reason: str | None = None
    note: str | None = None
    instruction: str | None = None
    idempotency_key: str | None = Field(default=None, max_length=128)


class ApproveDesignIn(BaseModel):
    approved_by: str = Field(min_length=1, max_length=64)
    master_asset_id: uuid.UUID | None = None
    production_spec: dict[str, Any] = Field(default_factory=dict)
    # Frozen with the approval so Print has something to print into. A raster
    # brought back from a paid interface carries no millimetres, so the size is
    # a decision recorded here rather than a property read off the file.
    garment_key: str = Field(default="", max_length=120)
    zone_key: str = Field(default="", max_length=60)
    print_width_mm: float | None = Field(default=None, gt=0, le=600)
    garment_colour: str = Field(default="", max_length=32)


class GateIn(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    result: ReviewResult
    evidence: str = Field(default="", max_length=2000)


class CategoryIn(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    # The 0-5 rating the scorecard states, not points. One conversion, in
    # ScoreCategory.from_rating, so a rating typed into a form and a rating
    # measured off an image land on the same scale.
    rating: int = Field(ge=0, le=5)
    notes: str = Field(default="", max_length=2000)


class ReviewIn(BaseModel):
    reviewer: str = Field(min_length=1, max_length=64)
    gates: list[GateIn] = Field(default_factory=list)
    categories: list[CategoryIn] = Field(default_factory=list)
    rationale: str = Field(default="", max_length=4000)
    decision: ReviewDecision = ReviewDecision.DESIGN_APPROVED


class ReviewView(BaseModel):
    """The review, its verdict, and what to do about it."""

    attempt_id: str
    reviewer: str
    gates: list[dict[str, Any]]
    categories: list[dict[str, Any]]
    rationale: str
    decision: str
    measurements: dict[str, Any]
    evaluation: dict[str, Any]
    frozen: bool
    next_action: str


# --- Helpers -----------------------------------------------------------------


def _concept(session: Session, concept_id: uuid.UUID) -> DesignConcept:
    concept = session.get(DesignConcept, concept_id)
    if concept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such concept")
    return concept


def _attempt(session: Session, attempt_id: uuid.UUID) -> DesignAttempt:
    attempt = session.get(DesignAttempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such attempt")
    return attempt


def _conflict(error: DesignPipelineConflict) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


def _invalid(error: InvalidDesignAction) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))


def _conflict_message(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)


def _invalid_message(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)


def _extraction(
    session: Session, concept_ids: list[uuid.UUID]
) -> dict[uuid.UUID, tuple[int, str | None, int]]:
    """attempt count, latest attempt state and version count, in one pass each."""
    if not concept_ids:
        return {}

    stats: dict[uuid.UUID, tuple[int, str | None, int]] = dict.fromkeys(concept_ids, (0, None, 0))

    latest = (
        select(
            DesignAttempt.concept_id,
            func.count().label("attempts"),
            func.max(DesignAttempt.attempt_number).label("latest_number"),
        )
        .where(DesignAttempt.concept_id.in_(concept_ids))
        .group_by(DesignAttempt.concept_id)
        .subquery()
    )
    rows = session.execute(
        select(
            latest.c.concept_id,
            latest.c.attempts,
            DesignAttempt.state,
        ).join(
            DesignAttempt,
            (DesignAttempt.concept_id == latest.c.concept_id)
            & (DesignAttempt.attempt_number == latest.c.latest_number),
        )
    ).all()
    for concept_id, attempts, state in rows:
        stats[concept_id] = (attempts, state.value, 0)

    versions = session.execute(
        select(ApprovedDesign.concept_id, func.count())
        .where(ApprovedDesign.concept_id.in_(concept_ids))
        .group_by(ApprovedDesign.concept_id)
    ).all()
    for concept_id, count in versions:
        attempts, state, _ = stats[concept_id]
        stats[concept_id] = (attempts, state, count)

    return stats


def _view(session: Session, concept: DesignConcept) -> ConceptView:
    stats = _extraction(session, [concept.id]).get(concept.id, (0, None, 0))
    return ConceptView.of(
        concept,
        attempt_count=stats[0],
        latest_attempt_state=stats[1],
        approved_versions=stats[2],
    )


# --- Routes ------------------------------------------------------------------


@router.get("", response_model=list[ConceptView], summary="The backlog, in queue order")
def list_concepts(
    session: SessionDependency,
    status_filter: Annotated[
        ConceptStatus | None, Query(alias="status", description="Filter by status")
    ] = None,
    library: Annotated[ConceptLibrary, Query()] = ConceptLibrary.TSHIRT,
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
) -> list[ConceptView]:
    statement = (
        select(DesignConcept)
        .where(DesignConcept.library == library)
        .order_by(DesignConcept.priority, DesignConcept.external_number)
        .limit(limit)
    )
    if status_filter is not None:
        statement = statement.where(DesignConcept.status == status_filter)

    concepts = list(session.execute(statement).scalars())
    stats = _extraction(session, [concept.id for concept in concepts])
    return [
        ConceptView.of(
            concept,
            attempt_count=stats.get(concept.id, (0, None, 0))[0],
            latest_attempt_state=stats.get(concept.id, (0, None, 0))[1],
            approved_versions=stats.get(concept.id, (0, None, 0))[2],
        )
        for concept in concepts
    ]


@router.get("/next", response_model=ConceptView, summary="What next actually means")
def get_next_concept(
    session: SessionDependency,
    library: Annotated[ConceptLibrary, Query()] = ConceptLibrary.TSHIRT,
) -> ConceptView:
    """The lowest-priority, lowest-numbered live concept; ready outranks backlog."""
    concept = next_concept(session, library)
    if concept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="no concept is ready or backlogged"
        )
    return _view(session, concept)


@router.get(
    "/queue",
    response_model=list[AttemptView],
    summary="Attempts awaiting the owner, oldest first",
)
def review_queue(session: SessionDependency) -> list[AttemptView]:
    attempts = session.execute(
        select(DesignAttempt)
        .where(DesignAttempt.state == DesignAttemptState.AWAITING_DECISION)
        .order_by(DesignAttempt.created_at)
        .options(selectinload(DesignAttempt.assets), selectinload(DesignAttempt.decision))
    ).scalars()
    return [AttemptView.of(attempt) for attempt in attempts]


@router.get("/{concept_id}", response_model=ConceptDetailView, summary="One concept, in full")
def get_concept(concept_id: uuid.UUID, session: SessionDependency) -> ConceptDetailView:
    concept = _concept(session, concept_id)
    stats = _extraction(session, [concept.id]).get(concept.id, (0, None, 0))
    base = ConceptView.of(
        concept,
        attempt_count=stats[0],
        latest_attempt_state=stats[1],
        approved_versions=stats[2],
    )
    return ConceptDetailView(
        **base.model_dump(),
        attempts=[AttemptView.of(attempt) for attempt in concept.attempts],
        versions=[ApprovedDesignView.of(version) for version in concept.approved_versions],
    )


@router.post(
    "/{concept_id}/attempts",
    response_model=AttemptView,
    status_code=status.HTTP_201_CREATED,
    summary="Open one execution of a concept",
)
def post_attempt(concept_id: uuid.UUID, body: AttemptIn, session: SessionDependency) -> AttemptView:
    concept = _concept(session, concept_id)
    parent = None
    if body.parent_attempt_id is not None:
        parent = _attempt(session, body.parent_attempt_id)
    try:
        attempt = create_attempt(
            session,
            concept,
            body.method,
            brief_overrides=body.brief_overrides or None,
            production_prompt=body.production_prompt,
            model=body.model,
            model_settings=body.model_settings or None,
            reference_inputs=body.reference_inputs or None,
            execution_rules=body.execution_rules or None,
            parent_attempt=parent,
        )
    except InvalidDesignAction as error:
        raise _invalid(error) from error
    session.commit()
    return AttemptView.of(attempt)


@router.post(
    "/attempts/{attempt_id}/assets",
    response_model=AssetView,
    status_code=status.HTTP_201_CREATED,
    summary="Store one file for an attempt",
)
async def post_asset(
    attempt_id: uuid.UUID,
    session: SessionDependency,
    settings: SettingsDependency,
    file: Annotated[UploadFile, File()],
    kind: Annotated[DesignAssetKind, Form()] = DesignAssetKind.ARTWORK,
    width: Annotated[int | None, Form()] = None,
    height: Annotated[int | None, Form()] = None,
) -> AssetView:
    attempt = _attempt(session, attempt_id)
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"That file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)}MB.",
        )
    store = FilesystemAssetStore(settings.assets_root_resolved)
    try:
        asset = record_asset(
            session,
            store,
            attempt,
            kind,
            file.filename or "artwork",
            data,
            file.content_type or "application/octet-stream",
            width=width,
            height=height,
        )
    except InvalidDesignAction as error:
        raise _invalid(error) from error
    session.commit()
    return AssetView.of(asset)


@router.post(
    "/attempts/{attempt_id}/submit",
    response_model=AttemptView,
    summary="Put an attempt in front of the owner",
)
def post_submit(attempt_id: uuid.UUID, session: SessionDependency) -> AttemptView:
    attempt = _attempt(session, attempt_id)
    try:
        submit_attempt(session, attempt)
    except InvalidDesignAction as error:
        raise _invalid(error) from error
    session.commit()
    return AttemptView.of(attempt)


@router.post(
    "/attempts/{attempt_id}/decision",
    response_model=DecisionView,
    summary="Record the owner's judgment on an attempt",
)
def post_decision(
    attempt_id: uuid.UUID, body: DecisionIn, session: SessionDependency
) -> DecisionView:
    """Immutable, signed, and exactly one. The only way out of awaiting_decision.

    An approval is checked against the attempt's review before it is recorded.
    Rejecting and asking for a variation are not: an owner who can see it is
    wrong should not have to fill in twenty-two controls to say so, and the
    scorecard's own conduct rules put the burden on approval rather than on
    refusal.
    """
    attempt = _attempt(session, attempt_id)
    try:
        guard_decision(session, attempt, body.decision)
    except NotEligible as error:
        raise _invalid_message(str(error)) from error
    try:
        decision = decide_attempt(
            session,
            attempt,
            body.decision,
            body.actor,
            reason=body.reason,
            note=body.note,
            instruction=body.instruction,
            idempotency_key=body.idempotency_key,
        )
    except DesignPipelineConflict as error:
        raise _conflict(error) from error
    except InvalidDesignAction as error:
        raise _invalid(error) from error
    session.commit()
    return DecisionView.of(decision)


@router.post(
    "/attempts/{attempt_id}/approve-design",
    response_model=ApprovedDesignView,
    status_code=status.HTTP_201_CREATED,
    summary="Freeze an approved attempt as the concept's next version",
)
def post_approve_design(
    attempt_id: uuid.UUID, body: ApproveDesignIn, session: SessionDependency
) -> ApprovedDesignView:
    attempt = _attempt(session, attempt_id)
    master = None
    if body.master_asset_id is not None:
        master = session.get(DesignAsset, body.master_asset_id)
        if master is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such asset")

    # The print spec is frozen with the approval rather than recalled later,
    # which is what production_spec exists for. Print needs all three: a raster
    # brought back from a paid interface carries no millimetres, so the size is
    # a decision recorded here, not a property read off the file.
    spec = dict(body.production_spec)
    for key, value in (
        ("garment_key", body.garment_key.strip()),
        ("zone_key", body.zone_key.strip()),
        ("print_width_mm", body.print_width_mm),
        ("garment_colour", body.garment_colour.strip()),
    ):
        if value:
            spec[key] = value

    try:
        version = approve_design(
            session,
            attempt,
            body.approved_by,
            master_asset=master,
            production_spec=spec or None,
        )
    except DesignPipelineConflict as error:
        raise _conflict(error) from error
    except InvalidDesignAction as error:
        raise _invalid(error) from error
    session.commit()
    return ApprovedDesignView.of(version)


@router.get("/rubric", summary="Every gate and category a review has to answer")
def get_rubric() -> dict[str, Any]:
    """The form's whole content: three groups, thirteen gates, nine categories.

    Served rather than hardcoded in the client so a change to the scorecard
    reaches the screen without a second edit in another language.
    """
    return rubric()


def _review_view(
    session: Session, attempt: DesignAttempt, record: DesignReviewRecord | None
) -> ReviewView:
    source = _stored_input(attempt, record)
    evaluation = evaluate_review(source)
    return ReviewView(
        attempt_id=str(attempt.id),
        reviewer="" if record is None else record.reviewer,
        gates=[gate.to_dict() for gate in source.hard_gates],
        categories=[category.to_dict() for category in source.score_categories],
        rationale="" if record is None else record.rationale,
        decision=source.decision.value,
        measurements={} if record is None else record.measurements,
        evaluation=evaluation.to_dict(),
        frozen=attempt.decision is not None,
        next_action=next_action(attempt, evaluation),
    )


def _stored_input(attempt: DesignAttempt, record: DesignReviewRecord | None) -> DesignReviewInput:
    if record is None:
        return empty_review(str(attempt.id))
    answered = {gate["id"]: HardGate.of(gate) for gate in record.hard_gates}
    return DesignReviewInput(
        design_id=str(attempt.id),
        reviewer_id=record.reviewer,
        # Every gate present, answered or not, so the form always renders
        # thirteen rows and "not answered" is a state rather than a missing key.
        hard_gates=[
            answered.get(
                gate_id,
                HardGate(id=gate_id, label=GATE_LABELS[gate_id], result=ReviewResult.NOT_TESTED),
            )
            for gate_id in HARD_GATE_IDS
        ],
        score_categories=[ScoreCategory.of(raw) for raw in record.score_categories],
        decision=ReviewDecision(record.requested_decision),
        rationale=record.rationale,
    )


@router.get(
    "/attempts/{attempt_id}/review",
    response_model=ReviewView,
    summary="The attempt's review, answered or not",
)
def get_review(attempt_id: uuid.UUID, session: SessionDependency) -> ReviewView:
    attempt = _attempt(session, attempt_id)
    return _review_view(session, attempt, load_review(session, attempt))


@router.put(
    "/attempts/{attempt_id}/review",
    response_model=ReviewView,
    summary="Answer the gates and rate the categories",
)
def put_review(attempt_id: uuid.UUID, body: ReviewIn, session: SessionDependency) -> ReviewView:
    """Save the answers and evaluate them. Partial answers are welcome.

    A half-filled review is stored and reported as "not eligible, and here is
    what is missing" rather than refused. Refusing would mean a reviewer could
    not put the work down and come back to it, and the review would go back to
    living in somebody's head -- which is where it lived before this existed.
    """
    attempt = _attempt(session, attempt_id)

    unknown_gates = [gate.id for gate in body.gates if gate.id not in GATE_LABELS]
    unknown_categories = [item.id for item in body.categories if item.id not in CATEGORY_LIMITS]
    if unknown_gates or unknown_categories:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "not part of the scorecard: " + ", ".join([*unknown_gates, *unknown_categories])
            ),
        )

    answered = {gate.id: gate for gate in body.gates}
    review = DesignReviewInput(
        design_id=str(attempt.id),
        reviewer_id=body.reviewer,
        hard_gates=[
            HardGate(
                id=gate_id,
                label=GATE_LABELS[gate_id],
                result=(
                    answered[gate_id].result if gate_id in answered else ReviewResult.NOT_TESTED
                ),
                evidence=answered[gate_id].evidence if gate_id in answered else "",
            )
            for gate_id in HARD_GATE_IDS
        ],
        score_categories=[
            ScoreCategory.from_rating(item.id, item.rating, item.notes) for item in body.categories
        ],
        decision=body.decision,
        rationale=body.rationale,
    )

    try:
        scored = score_design(session, attempt, review)
    except ReviewFrozen as error:
        raise _conflict_message(str(error)) from error
    except NotEligible as error:
        raise _invalid_message(str(error)) from error
    session.commit()
    return _review_view(session, attempt, scored.record)


@router.post(
    "/attempts/{attempt_id}/measure",
    response_model=ReviewView,
    summary="Measure the attempt's own artwork",
)
def post_measure(
    attempt_id: uuid.UUID, session: SessionDependency, settings: SettingsDependency
) -> ReviewView:
    """Measure the artwork already attached to this attempt.

    The gap this closes: ``/api/design/score`` took an uploaded file and
    referenced no attempt, so a measurement attached to nothing and persisted
    nowhere. Here the artwork is the attempt's own, and the result lands on the
    attempt's review.

    Measurement only fills what nobody has answered. A gate a person has
    already ruled on is left exactly as they left it -- the machine's T1 result
    is evidence for a reviewer, never a correction of one. What it measured is
    stored in full either way, so the evidence is present even where it did not
    move an answer.
    """
    attempt = _attempt(session, attempt_id)
    artwork = next(
        (asset for asset in attempt.assets if asset.kind is DesignAssetKind.ARTWORK),
        None,
    ) or next(iter(attempt.assets), None)
    if artwork is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="There is no artwork on this attempt yet. Attach a file first.",
        )

    store = FilesystemAssetStore(settings.assets_root_resolved)
    try:
        data = store.load(artwork.relative_path)
    except AssetStoreError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"The artwork is recorded but its file could not be read. {error}",
        ) from error

    suffix = Path(artwork.relative_path).suffix or ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        temp_path = Path(handle.name)
    try:
        measurements = measure(temp_path)
        measured = to_review(str(attempt.id), str(attempt.id), measurements)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"The artwork could not be measured: {error}",
        ) from error
    finally:
        temp_path.unlink(missing_ok=True)

    record = load_review(session, attempt)
    current = _stored_input(attempt, record)
    already = {gate.id: gate for gate in current.hard_gates}
    machine = {gate["id"]: HardGate.of(gate) for gate in measured["hardGates"]}

    merged_gates = [
        machine[gate_id]
        if already[gate_id].result is ReviewResult.NOT_TESTED and gate_id in machine
        else already[gate_id]
        for gate_id in HARD_GATE_IDS
    ]
    rated = {category.id for category in current.score_categories}
    merged_categories = list(current.score_categories) + [
        ScoreCategory.of(raw) for raw in measured["scoreCategories"] if raw["id"] not in rated
    ]

    try:
        scored = score_design(
            session,
            attempt,
            DesignReviewInput(
                design_id=str(attempt.id),
                reviewer_id=current.reviewer_id or "measurement",
                hard_gates=merged_gates,
                score_categories=merged_categories,
                decision=current.decision,
                rationale=current.rationale,
            ),
            measurements=measurements.to_dict(),
        )
    except ReviewFrozen as error:
        raise _conflict_message(str(error)) from error
    session.commit()
    return _review_view(session, attempt, scored.record)


@router.get("/garments", summary="Garments and the zones they declare")
def get_garments(settings: SettingsDependency) -> dict[str, list[dict[str, Any]]]:
    """What an approval can choose from, read off the garment files themselves."""
    return {
        key: [
            {
                "key": zone.key,
                "width_mm": round(zone.width_mm, 1),
                "height_mm": round(zone.height_mm, 1),
            }
            for zone in zones
        ]
        for key, zones in available_garments(settings.assets_root_resolved).items()
    }


@router.get(
    "/versions/{version_id}/print.svg",
    response_class=Response,
    summary="The approved version, printed into its zone",
)
def get_printed_version(
    version_id: uuid.UUID,
    session: SessionDependency,
    settings: SettingsDependency,
    show_zones: Annotated[bool, Query(description="Outline every zone")] = False,
) -> Response:
    """The approved artwork on its garment, at the size and zone approved with it.

    Everything is read off the approved row. Nothing about what is printed
    comes from the request, because the point of an approved version is that it
    renders the same every time it is asked for.
    """
    version = session.get(ApprovedDesign, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such version")
    store = FilesystemAssetStore(settings.assets_root_resolved)
    try:
        document = print_approved(
            session, store, settings.assets_root_resolved, version, show_zones=show_zones
        )
    except PrintRefused as error:
        raise _invalid_message(str(error)) from error
    return Response(content=document, media_type="image/svg+xml")


@router.get("/assets/{asset_id}", summary="One design asset's bytes")
def get_asset(
    asset_id: uuid.UUID, session: SessionDependency, settings: SettingsDependency
) -> Response:
    """Served from the row's own path, never from anything in the request."""
    asset = session.get(DesignAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such asset")
    store = FilesystemAssetStore(settings.assets_root_resolved)
    try:
        data = store.load(asset.relative_path)
    except AssetStoreError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"The asset is recorded but its file could not be read. {error}",
        ) from error
    return Response(
        content=data,
        media_type=asset.mime_type,
        headers={"Cache-Control": "private, max-age=31536000, immutable"},
    )
