"""Read-only world endpoints.

Phase 1 exposes what the world page needs. Continue World, decisions and canon
proposals arrive with the phases that implement them.
"""

from __future__ import annotations

import datetime as dt
import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.adapters.asset_store import FilesystemAssetStore
from app.adapters.canon_classifier import ClassificationError
from app.adapters.factory import (
    build_canon_classifier,
    build_image_client,
    build_planning_client,
    build_review_client,
    image_client_is_live,
    image_model_for,
    review_client_is_live,
)
from app.adapters.git_store import build_git_store
from app.adapters.markdown_store import WORLD_DOCUMENT, MarkdownStore
from app.adapters.planning import PlanningError
from app.adapters.reference_images import FilesystemReferenceImageStore
from app.adapters.review import ReviewError
from app.config import Settings, get_settings
from app.db.models import (
    AutomatedReview,
    CanonProposal,
    GenerationAttempt,
    Shot,
    World,
)
from app.db.session import get_db_session
from app.domain.enums import (
    AssetKind,
    AttemptState,
    CanonProposalStatus,
    FailureCode,
    GateName,
    GateStatus,
    HumanDecisionKind,
    ProposalClassification,
    ReviewRecommendation,
    ReviewVerdict,
    ShotStatus,
    SyncState,
    WorldStatus,
)
from app.domain.errors import StudioError
from app.domain.schemas import GateResult, PromptPlan
from app.services.canon_service import (
    InvalidTarget,
    ProposalConflict,
    approve_proposal,
    build_diff,
    classify_proposal,
    reject_proposal,
)
from app.services.decision_service import (
    DecisionConflict,
    DecisionOutcome,
    InvalidDecision,
    decide,
    repository_root_for,
)
from app.services.generation_orchestrator import (
    GenerationConflict,
    GenerationSettings,
    NothingToGenerate,
    run_attempt,
    start_attempt,
)
from app.services.prompt_planner import PLANNING_CANON_HEADINGS
from app.services.prompt_service import (
    NothingToPlan,
    PromptSet,
    prompts_for_shot,
    variations_for_shot,
)
from app.services.review_service import NothingToReview, review_attempt
from app.services.rotation import apply_continuity, rotation_from_shots
from app.services.shot_selector import NoSelection, Selection, select_next_shot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["worlds"])

SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


class ShotResponse(BaseModel):
    """One row of the shotlist."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: str
    sequence: int
    priority: int
    title: str
    hero_product: str | None
    camera_position: str | None
    lighting_source: str | None
    status: ShotStatus
    disabled: bool
    source_line: int | None


class WorldSummary(BaseModel):
    """A world without its shots."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    status: WorldStatus
    world_document_hash: str | None
    continuity_document_hash: str | None
    shotlist_document_hash: str | None


class ShotCounts(BaseModel):
    """How the shotlist breaks down, for the world page header."""

    total: int
    planned: int
    in_progress: int
    approved: int
    rejected: int
    abandoned: int


class WorldDetail(WorldSummary):
    """A world with its shots and counts."""

    shots: list[ShotResponse]
    counts: ShotCounts
    next_planned_shot: ShotResponse | None


def _counts(shots: list[Shot]) -> ShotCounts:
    def total_for(wanted: ShotStatus) -> int:
        return sum(1 for shot in shots if shot.status is wanted)

    return ShotCounts(
        total=len(shots),
        planned=total_for(ShotStatus.PLANNED),
        in_progress=total_for(ShotStatus.IN_PROGRESS),
        approved=total_for(ShotStatus.APPROVED),
        rejected=total_for(ShotStatus.REJECTED),
        abandoned=total_for(ShotStatus.ABANDONED),
    )


class SetAsideResponse(BaseModel):
    """A shot that was considered and not chosen."""

    external_id: str
    reason: str


class NextShotResponse(BaseModel):
    """The deterministic selection, with its explanation."""

    selected: ShotResponse | None
    reason: str
    eligible_count: int
    set_aside: list[SetAsideResponse]
    last_hero_product: str | None
    last_camera_position: str | None


class DecisionSummary(BaseModel):
    """The decision on an attempt, as shown in history."""

    model_config = ConfigDict(from_attributes=True)

    decision: HumanDecisionKind
    reason: str | None
    note: str | None
    instruction: str | None
    promote_to_reference: bool
    markdown_sync: SyncState
    git_sync: SyncState
    git_commit: str | None
    reconciliation_required: bool
    reconciliation_detail: str | None
    created_at: dt.datetime


class AssetResponse(BaseModel):
    """A stored image."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: AssetKind
    sha256: str
    mime_type: str
    width: int | None
    height: int | None
    byte_size: int

    @property
    def url(self) -> str:
        return f"/assets/{self.id}"


class AttemptResponse(BaseModel):
    """One generation attempt with everything needed to explain it."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    attempt_number: int
    state: AttemptState
    shot: ShotResponse
    selection_reason: str | None
    production_prompt: str | None
    prompt_plan: PromptPlan | None
    image_model: str | None
    image_size: str | None
    image_quality: str | None
    provider_request_id: str | None
    # The shot and canon versions as they stood when this ran.
    hero_product: str | None
    camera_position: str | None
    world_document_hash: str | None
    shotlist_document_hash: str | None
    failure_code: FailureCode | None
    failure_message: str | None
    parent_attempt_id: uuid.UUID | None
    created_at: dt.datetime
    image_url: str | None
    thumbnail_url: str | None
    # The most recent review, if the image has been reviewed. Reviews are immutable;
    # retrying adds another, and the last one stands.
    review: ReviewResponse | None = None
    # Present once decided. The interface disables the controls when it is set.
    decision: DecisionSummary | None = None
    # A generated image is an image, not a decision.
    approved: bool


def _asset_url(attempt: GenerationAttempt, kind: AssetKind) -> str | None:
    for asset in attempt.assets:
        if asset.kind is kind:
            return f"/assets/{asset.id}"
    return None


def _attempt_response(attempt: GenerationAttempt) -> AttemptResponse:
    plan = attempt.prompt_plan_json
    return AttemptResponse(
        id=attempt.id,
        attempt_number=attempt.attempt_number,
        state=attempt.state,
        shot=ShotResponse.model_validate(attempt.shot),
        selection_reason=attempt.selection_reason,
        production_prompt=attempt.production_prompt,
        prompt_plan=PromptPlan.model_validate(plan) if plan else None,
        image_model=attempt.image_model,
        image_size=attempt.image_size,
        image_quality=attempt.image_quality,
        provider_request_id=attempt.provider_request_id,
        hero_product=attempt.hero_product,
        camera_position=attempt.camera_position,
        world_document_hash=attempt.world_document_hash,
        shotlist_document_hash=attempt.shotlist_document_hash,
        failure_code=attempt.failure_code,
        failure_message=attempt.failure_message,
        parent_attempt_id=attempt.parent_attempt_id,
        created_at=attempt.created_at,
        image_url=_asset_url(attempt, AssetKind.ORIGINAL),
        thumbnail_url=_asset_url(attempt, AssetKind.THUMBNAIL),
        review=(
            _review_response(attempt.latest_review) if attempt.latest_review is not None else None
        ),
        decision=(
            DecisionSummary.model_validate(attempt.decision)
            if attempt.decision is not None
            else None
        ),
        approved=attempt.state is AttemptState.APPROVED,
    )


def _load_world(session: Session, world_slug: str) -> World:
    world = session.execute(
        select(World).where(World.slug == world_slug).options(selectinload(World.shots))
    ).scalar_one_or_none()

    if world is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No world named {world_slug!r} has been imported. "
                "Run 'python -m app.cli import-world <slug>'."
            ),
        )
    return world


@router.get("/worlds", summary="List worlds")
def list_worlds(session: SessionDependency) -> list[WorldSummary]:
    """Every world known to the database, in slug order."""
    worlds = session.execute(select(World).order_by(World.slug)).scalars().all()
    return [WorldSummary.model_validate(world) for world in worlds]


@router.get("/worlds/{world_slug}", summary="World detail")
def get_world(world_slug: str, session: SessionDependency) -> WorldDetail:
    """One world with its shotlist."""
    world = _load_world(session, world_slug)

    shots = sorted(world.shots, key=lambda shot: shot.sequence)
    outcome = select_next_shot(world, shots)
    upcoming = outcome.shot if isinstance(outcome, Selection) else None

    return WorldDetail(
        id=world.id,
        slug=world.slug,
        name=world.name,
        status=world.status,
        world_document_hash=world.world_document_hash,
        continuity_document_hash=world.continuity_document_hash,
        shotlist_document_hash=world.shotlist_document_hash,
        shots=[ShotResponse.model_validate(shot) for shot in shots],
        counts=_counts(shots),
        next_planned_shot=(ShotResponse.model_validate(upcoming) if upcoming else None),
    )


@router.get("/worlds/{world_slug}/next-shot", summary="Next shot and why")
def get_next_shot(world_slug: str, session: SessionDependency) -> NextShotResponse:
    """Run the deterministic selector.

    Costs nothing and calls no model: this is a pure function of database state.
    """
    world = _load_world(session, world_slug)
    shots = sorted(world.shots, key=lambda shot: shot.sequence)
    outcome = select_next_shot(world, shots)

    set_aside = [
        SetAsideResponse(external_id=candidate.external_id, reason=candidate.reason)
        for candidate in outcome.set_aside
    ]

    if isinstance(outcome, NoSelection):
        rotation = rotation_from_shots(shots)
        return NextShotResponse(
            selected=None,
            reason=outcome.reason,
            eligible_count=0,
            set_aside=set_aside,
            last_hero_product=rotation.last_hero_product,
            last_camera_position=rotation.last_camera_position,
        )

    return NextShotResponse(
        selected=ShotResponse.model_validate(outcome.shot),
        reason=outcome.reason,
        eligible_count=outcome.eligible_count,
        set_aside=set_aside,
        last_hero_product=outcome.rotation.last_hero_product,
        last_camera_position=outcome.rotation.last_camera_position,
    )


class GenerationResponse(BaseModel):
    """The result of one Continue World action."""

    attempt: AttemptResponse
    # Null when the review failed; the attempt records why and can be retried.
    review: ReviewResponse | None = None
    # Whether billable models produced these, or the deterministic fakes did.
    live: bool
    review_live: bool = False


class PromptsResponse(BaseModel):
    """Both prompts for one shot. Nothing was generated; the prompt itself is kept."""

    shot: ShotResponse
    selection_reason: str
    image_prompt: str
    video_prompt: str
    # Whether a billable model wrote these, or the deterministic fake did.
    live: bool
    # 1 for the first prompt written for this shot, and up from there.
    variation: int
    written_at: dt.datetime


class PromptHistoryResponse(BaseModel):
    """Every prompt already written for one shot, newest first."""

    shot: ShotResponse
    variations: list[PromptsResponse]


def _prompts_response(prompts: PromptSet) -> PromptsResponse:
    return PromptsResponse(
        shot=ShotResponse.model_validate(prompts.shot),
        selection_reason=prompts.selection_reason,
        image_prompt=prompts.image_prompt,
        video_prompt=prompts.video_prompt,
        live=prompts.live,
        variation=prompts.variation,
        written_at=prompts.written_at,
    )


@router.get("/worlds/{world_slug}/prompts", summary="Prompts already written for a shot")
def read_prompts(
    world_slug: str,
    shot: str,
    session: SessionDependency,
) -> PromptHistoryResponse:
    """What has been written for this shot already.

    Writes nothing and costs nothing: this is the read that makes a new variation
    worth comparing against the ones before it. A shot nobody has planned yet
    returns an empty list rather than an error.
    """
    try:
        variations = variations_for_shot(session, world_slug=world_slug, external_id=shot)
    except NothingToPlan as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error

    found = session.execute(
        select(Shot).join(World).where(World.slug == world_slug, Shot.external_id == shot)
    ).scalar_one()
    return PromptHistoryResponse(
        shot=ShotResponse.model_validate(found),
        variations=[_prompts_response(item) for item in variations],
    )


@router.post("/worlds/{world_slug}/prompts", summary="Write the prompts for a shot")
def write_prompts(
    world_slug: str,
    session: SessionDependency,
    settings: SettingsDependency,
    shot: str | None = None,
) -> PromptsResponse:
    """Plan one shot and stop.

    No image, no attempt row, no world lock, no decision. ``shot`` names a shot such
    as W01-015; without it the next eligible shot is planned. Generation happens
    elsewhere, so this is the endpoint that actually gets used.

    Each call adds a variation. It never replaces the prompt written last time.
    """
    try:
        prompts = prompts_for_shot(
            session,
            settings=settings,
            store=MarkdownStore(settings.worlds_root_resolved),
            world_slug=world_slug,
            external_id=shot,
        )
    except NothingToPlan as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except PlanningError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    return _prompts_response(prompts)


@router.post(
    "/worlds/{world_slug}/continue",
    summary="Continue Shirtfaced World",
    status_code=status.HTTP_201_CREATED,
)
def continue_world(
    world_slug: str,
    session: SessionDependency,
    settings: SettingsDependency,
    draft: bool = False,
) -> GenerationResponse:
    """Select the next shot, plan its prompt and generate one image.

    Synchronous, per ADR-010, and exactly one image per action, per ADR-009. The
    attempt is left awaiting a human decision; nothing here approves anything.

    ``draft`` runs the cheap model for checking framing and geometry. A draft cannot
    be promoted to a reference and its scores are not comparable with a full frame's.
    """
    world = _load_world(session, world_slug)

    # Refused rather than quietly run at full price, which is the whole point of
    # asking for a draft.
    if draft and settings.openai_api_key and not settings.openai_image_draft_model:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Drafting is unavailable: OPENAI_IMAGE_DRAFT_MODEL is not set. "
                "Generating without it would cost full price."
            ),
        )

    try:
        attempt, selection = start_attempt(session, world)
    except GenerationConflict as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except NothingToGenerate as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error

    completed = run_attempt(
        session,
        attempt,
        selection,
        markdown_store=MarkdownStore(settings.worlds_root_resolved),
        planning_client=build_planning_client(settings),
        image_client=build_image_client(settings, draft=draft),
        asset_store=FilesystemAssetStore(settings.assets_root_resolved),
        settings=GenerationSettings(
            model=image_model_for(settings, draft=draft) or "fake-image-model",
            size=settings.openai_image_size,
            quality=settings.openai_image_quality,
            is_draft=draft,
            reference_image_limit=settings.reference_image_limit,
        ),
        # Without this the world's reference library never reaches the image model
        # and every frame is generated from text alone.
        reference_store=FilesystemReferenceImageStore(settings.worlds_root_resolved),
    )

    review: AutomatedReview | None = None
    if completed.state is AttemptState.GENERATED:
        # An image exists, so it is reviewed. A review failure is recorded on the
        # attempt and leaves the image intact; retry-review is then cheap.
        try:
            review = _run_review(session, completed, settings)
        except StudioError as error:
            logger.warning("Review could not run for attempt %s: %s", completed.id, error)

    return GenerationResponse(
        attempt=_attempt_response(completed),
        review=_review_response(review) if review else None,
        live=image_client_is_live(settings, draft=draft),
        review_live=review_client_is_live(settings),
    )


@router.get("/worlds/{world_slug}/attempts", summary="Attempt history")
def list_attempts(
    world_slug: str, session: SessionDependency, limit: int = 20
) -> list[AttemptResponse]:
    """Attempts for a world, newest first."""
    world = _load_world(session, world_slug)

    attempts = (
        session.execute(
            select(GenerationAttempt)
            .where(GenerationAttempt.world_id == world.id)
            .order_by(GenerationAttempt.created_at.desc())
            .limit(max(1, min(limit, 100)))
            .options(
                selectinload(GenerationAttempt.assets),
                selectinload(GenerationAttempt.shot),
                selectinload(GenerationAttempt.reviews),
                selectinload(GenerationAttempt.decision),
            )
        )
        .scalars()
        .all()
    )

    return [_attempt_response(attempt) for attempt in attempts]


@router.get("/attempts/{attempt_id}", summary="One attempt")
def get_attempt(attempt_id: uuid.UUID, session: SessionDependency) -> AttemptResponse:
    """One attempt with its prompt, image and provenance."""
    attempt = session.execute(
        select(GenerationAttempt)
        .where(GenerationAttempt.id == attempt_id)
        .options(
            selectinload(GenerationAttempt.assets),
            selectinload(GenerationAttempt.shot),
            selectinload(GenerationAttempt.reviews),
            selectinload(GenerationAttempt.decision),
        )
    ).scalar_one_or_none()

    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such attempt.")

    return _attempt_response(attempt)


class ReviewResponse(BaseModel):
    """One automated review."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    review_model: str
    recommendation: ReviewRecommendation
    verdict: ReviewVerdict
    gates: dict[GateName, GateResult]
    mood_score: int
    australian_authenticity_score: int
    product_visibility_score: int
    documentary_credibility_score: int
    story_score: int
    branding_compliant: bool
    vehicle_compliant: bool
    structurally_sound: bool
    strongest_success: str
    material_drift: str | None
    recommended_action: str | None
    next_hero_product: str | None
    next_camera: str | None
    created_at: dt.datetime
    # Gates that materially failed, and gates the model was unsure about. The
    # interface expands these first.
    blocking_gates: list[GateName]
    uncertain_gates: list[GateName]


class CanonProposalResponse(BaseModel):
    """A proposed permanent rule.

    Nothing here has changed WORLD.md. The classification is advisory: it orders the
    queue and explains a recommendation, and never decides.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: CanonProposalStatus
    proposed_text: str
    reason: str | None
    human_note: str | None
    classification: ProposalClassification | None
    classification_reason: str | None
    classified_by: str | None
    target_heading: str | None
    reviewer_model: str | None
    applied_wording: str | None
    applied_at: dt.datetime | None
    failure_detail: str | None
    git_commit: str | None
    created_at: dt.datetime
    decided_at: dt.datetime | None
    # The sections a rule may join. Anything else is invisible to the planner.
    allowed_headings: list[str] = []


def _review_response(review: AutomatedReview) -> ReviewResponse:
    raw = review.raw_json or {}
    gates = {
        GateName(name): GateResult.model_validate(value)
        for name, value in (raw.get("gates") or {}).items()
    }
    blocking = [
        name
        for name in GateName
        if name in gates and gates[name].status is GateStatus.FAIL and gates[name].material
    ]
    uncertain = [
        name for name in GateName if name in gates and gates[name].status is GateStatus.UNCERTAIN
    ]

    return ReviewResponse(
        id=review.id,
        review_model=review.review_model,
        recommendation=review.recommendation,
        verdict=review.verdict,
        gates=gates,
        mood_score=review.mood_score,
        australian_authenticity_score=review.australian_authenticity_score,
        product_visibility_score=review.product_visibility_score,
        documentary_credibility_score=review.documentary_credibility_score,
        story_score=review.story_score,
        branding_compliant=review.branding_compliant,
        vehicle_compliant=review.vehicle_compliant,
        structurally_sound=review.structurally_sound,
        strongest_success=review.strongest_success,
        material_drift=review.material_drift,
        recommended_action=review.recommended_action,
        next_hero_product=review.next_hero_product,
        next_camera=review.next_camera,
        created_at=review.created_at,
        blocking_gates=blocking,
        uncertain_gates=uncertain,
    )


def _load_attempt(session: Session, attempt_id: uuid.UUID) -> GenerationAttempt:
    attempt = session.execute(
        select(GenerationAttempt)
        .where(GenerationAttempt.id == attempt_id)
        .options(
            selectinload(GenerationAttempt.assets),
            selectinload(GenerationAttempt.shot),
            selectinload(GenerationAttempt.reviews),
            selectinload(GenerationAttempt.decision),
        )
    ).scalar_one_or_none()

    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such attempt.")
    return attempt


def _run_review(
    session: Session, attempt: GenerationAttempt, settings: Settings
) -> AutomatedReview | None:
    """Review one attempt, using the same canon the planner saw."""
    store = MarkdownStore(settings.worlds_root_resolved)
    documents = store.read_world_documents(attempt.world.slug)

    shots = sorted(attempt.world.shots, key=lambda shot: shot.sequence)
    rotation = apply_continuity(rotation_from_shots(shots), documents["CONTINUITY.md"].text)

    return review_attempt(
        session,
        attempt,
        review_client=build_review_client(settings),
        asset_store=FilesystemAssetStore(settings.assets_root_resolved),
        world_text=documents[WORLD_DOCUMENT].text,
        rotation=rotation,
    )


@router.post("/attempts/{attempt_id}/retry-review", summary="Review again")
def retry_review(
    attempt_id: uuid.UUID, session: SessionDependency, settings: SettingsDependency
) -> ReviewResponse:
    """Review the existing image again without regenerating it.

    Reviews are immutable, so this adds another rather than replacing the last.
    """
    attempt = _load_attempt(session, attempt_id)

    try:
        review = _run_review(session, attempt, settings)
    except NothingToReview as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except (ReviewError, StudioError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=attempt.failure_message or "The review failed.",
        )

    return _review_response(review)


@router.get("/worlds/{world_slug}/canon-proposals", summary="Pending canon proposals")
def list_canon_proposals(
    world_slug: str, session: SessionDependency
) -> list[CanonProposalResponse]:
    """Rules the reviewer proposed. None of them has changed WORLD.md."""
    world = _load_world(session, world_slug)

    proposals = (
        session.execute(
            select(CanonProposal)
            .where(CanonProposal.world_id == world.id)
            .order_by(CanonProposal.created_at.desc())
        )
        .scalars()
        .all()
    )

    return [_proposal_response(proposal) for proposal in proposals]


class ApproveRequest(BaseModel):
    """Approving an image."""

    promote_to_reference: bool = False
    note: str = ""
    idempotency_key: str | None = None


class RejectRequest(BaseModel):
    """Rejecting an image. A reason is required."""

    reason: str
    idempotency_key: str | None = None


class VariationRequest(BaseModel):
    """Asking for another take. Records intent; generates nothing."""

    instruction: str
    idempotency_key: str | None = None


class DecisionResponse(BaseModel):
    """The decision, and what each downstream system did about it.

    The four outcomes are reported separately because they cannot succeed or fail
    together. A decision is final the moment it is recorded, even if the documents or
    the commit did not follow.
    """

    attempt_id: uuid.UUID
    attempt_state: AttemptState
    decision: HumanDecisionKind
    shot_external_id: str
    shot_status: ShotStatus
    reason: str | None
    note: str | None
    instruction: str | None
    promote_to_reference: bool
    markdown_sync: SyncState
    git_sync: SyncState
    reference_sync: SyncState
    git_commit: str | None
    document_hashes: dict[str, str]
    reconciliation_required: bool
    reconciliation: list[str]


def _decision_response(outcome: DecisionOutcome) -> DecisionResponse:
    decision = outcome.decision
    return DecisionResponse(
        attempt_id=outcome.attempt.id,
        attempt_state=outcome.attempt.state,
        decision=decision.decision,
        shot_external_id=outcome.attempt.shot.external_id,
        shot_status=outcome.attempt.shot.status,
        reason=decision.reason,
        note=decision.note,
        instruction=decision.instruction,
        promote_to_reference=decision.promote_to_reference,
        markdown_sync=outcome.markdown_sync,
        git_sync=outcome.git_sync,
        reference_sync=outcome.reference_sync,
        git_commit=outcome.git_commit,
        document_hashes=outcome.document_hashes,
        reconciliation_required=outcome.reconciliation_required,
        reconciliation=outcome.reconciliation,
    )


def _decide(
    session: Session,
    settings: Settings,
    attempt_id: uuid.UUID,
    kind: HumanDecisionKind,
    **fields: Any,
) -> DecisionResponse:
    attempt = _load_attempt(session, attempt_id)
    worlds_root = settings.worlds_root_resolved

    try:
        outcome = decide(
            session,
            attempt,
            kind,
            markdown_store=MarkdownStore(worlds_root),
            git_store=build_git_store(
                repository_root_for(worlds_root), enabled=settings.git_enabled
            ),
            asset_store=FilesystemAssetStore(settings.assets_root_resolved),
            git_enabled=settings.git_enabled,
            # Without this the service falls back to its own module constant and
            # REFERENCE_ACTIVE_LIMIT does nothing, which is how the reference limit
            # and the draft model were both dead for weeks.
            active_limit=settings.reference_active_limit,
            **fields,
        )
    except DecisionConflict as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except InvalidDecision as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error

    return _decision_response(outcome)


@router.post("/attempts/{attempt_id}/approve", summary="Approve an image")
def approve_attempt(
    attempt_id: uuid.UUID,
    body: ApproveRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> DecisionResponse:
    """Approve. Marks the shot approved and records it in the world documents."""
    return _decide(
        session,
        settings,
        attempt_id,
        HumanDecisionKind.APPROVED,
        note=body.note,
        promote_to_reference=body.promote_to_reference,
        idempotency_key=body.idempotency_key,
    )


@router.post("/attempts/{attempt_id}/reject", summary="Reject an image")
def reject_attempt(
    attempt_id: uuid.UUID,
    body: RejectRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> DecisionResponse:
    """Reject with a reason. The shot stays planned and the drift is recorded."""
    return _decide(
        session,
        settings,
        attempt_id,
        HumanDecisionKind.REJECTED,
        reason=body.reason,
        idempotency_key=body.idempotency_key,
    )


@router.post("/attempts/{attempt_id}/variation", summary="Request a variation")
def request_variation(
    attempt_id: uuid.UUID,
    body: VariationRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> DecisionResponse:
    """Record that another take is wanted.

    Calls no model and generates nothing. The world is released so an explicit
    Continue World can create the child attempt.
    """
    return _decide(
        session,
        settings,
        attempt_id,
        HumanDecisionKind.VARIATION_REQUESTED,
        instruction=body.instruction,
        idempotency_key=body.idempotency_key,
    )


class ProposalDiffResponse(BaseModel):
    """The exact change a proposal would make."""

    proposal_id: uuid.UUID
    target_heading: str
    unified_diff: str
    applied_wording: str


class ApproveProposalRequest(BaseModel):
    """Approving a canon rule. The target must be a section the planner reads."""

    target_heading: str | None = None
    note: str = ""


class RejectProposalRequest(BaseModel):
    """Declining a canon rule."""

    note: str = ""


def _proposal_response(proposal: CanonProposal) -> CanonProposalResponse:
    response = CanonProposalResponse.model_validate(proposal)
    return response.model_copy(update={"allowed_headings": list(PLANNING_CANON_HEADINGS)})


def _load_proposal(session: Session, proposal_id: uuid.UUID) -> CanonProposal:
    proposal = session.execute(
        select(CanonProposal).where(CanonProposal.id == proposal_id)
    ).scalar_one_or_none()
    if proposal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such proposal.")
    return proposal


def _world_text(settings: Settings, slug: str) -> str:
    store = MarkdownStore(settings.worlds_root_resolved)
    return store.read_world_documents(slug)[WORLD_DOCUMENT].text


@router.post("/canon-proposals/{proposal_id}/classify", summary="Classify a proposal")
def classify_canon_proposal(
    proposal_id: uuid.UUID, session: SessionDependency, settings: SettingsDependency
) -> CanonProposalResponse:
    """Weigh the proposal against canon. Advisory only; it changes nothing."""
    proposal = _load_proposal(session, proposal_id)

    try:
        classify_proposal(
            session,
            proposal,
            classifier=build_canon_classifier(settings),
            world_text=_world_text(settings, proposal.world.slug),
        )
    except (ClassificationError, StudioError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error

    return _proposal_response(proposal)


@router.get("/canon-proposals/{proposal_id}/diff", summary="The exact proposed change")
def get_proposal_diff(
    proposal_id: uuid.UUID,
    session: SessionDependency,
    settings: SettingsDependency,
    target_heading: str | None = None,
) -> ProposalDiffResponse:
    """Show precisely what would change. Nothing is written."""
    proposal = _load_proposal(session, proposal_id)

    try:
        diff = build_diff(proposal, _world_text(settings, proposal.world.slug), target_heading)
    except InvalidTarget as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except StudioError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error

    return ProposalDiffResponse(
        proposal_id=proposal.id,
        target_heading=diff.target_heading,
        unified_diff=diff.unified_diff,
        applied_wording=diff.applied_wording,
    )


@router.post("/canon-proposals/{proposal_id}/approve", summary="Apply a canon rule")
def approve_canon_proposal(
    proposal_id: uuid.UUID,
    body: ApproveProposalRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> CanonProposalResponse:
    """Apply the diff to WORLD.md.

    The only write the application makes to permanent canon, and only here.
    """
    proposal = _load_proposal(session, proposal_id)
    worlds_root = settings.worlds_root_resolved

    try:
        approve_proposal(
            session,
            proposal,
            markdown_store=MarkdownStore(worlds_root),
            git_store=build_git_store(
                repository_root_for(worlds_root), enabled=settings.git_enabled
            ),
            git_enabled=settings.git_enabled,
            target_heading=body.target_heading,
            note=body.note,
        )
    except ProposalConflict as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except InvalidTarget as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error

    return _proposal_response(proposal)


@router.post("/canon-proposals/{proposal_id}/reject", summary="Decline a canon rule")
def reject_canon_proposal(
    proposal_id: uuid.UUID, body: RejectProposalRequest, session: SessionDependency
) -> CanonProposalResponse:
    """Decline. WORLD.md is untouched."""
    proposal = _load_proposal(session, proposal_id)

    try:
        reject_proposal(session, proposal, body.note)
    except ProposalConflict as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    return _proposal_response(proposal)
