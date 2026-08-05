"""Coordinating one generation attempt.

The order here is the point of the module.

1. Take a transaction-scoped advisory lock on the world, so two Continue World
   requests cannot interleave between the eligibility check and the insert.
2. Refuse if an attempt is already active. The partial unique index is the real
   guarantee; this check exists to produce a clear message rather than a constraint
   violation.
3. Select the shot and persist the attempt **before** anything is paid for. A crash
   after the money is spent must still leave a record of what it was spent on.
4. Plan, generate, store.

Every state transition is committed, so the attempt is restart-safe: whatever the
process was doing when it died is readable from the row afterwards.

The orchestrator never approves anything. A generated image is an image, not a
decision.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore, AssetStoreError, attempt_key
from app.adapters.image_generation import (
    GeneratedImage,
    ImageGenerationClient,
    ImageGenerationError,
    ImageGenerationRequest,
)
from app.adapters.markdown_store import (
    CONTINUITY_DOCUMENT,
    WORLD_DOCUMENT,
    MarkdownStore,
)
from app.adapters.planning import PlanningError, PromptPlanningClient
from app.db.models import GenerationAttempt, ImageAsset, Shot, World
from app.domain.enums import ACTIVE_ATTEMPT_STATES, AssetKind, AttemptState, FailureCode
from app.domain.errors import StudioError
from app.services import images, reference_service
from app.services.prompt_planner import build_request, create_plan
from app.services.retry import DEFAULT_POLICY, RetryPolicy, call_with_retry
from app.services.rotation import apply_continuity
from app.services.shot_selector import NoSelection, Selection, select_next_shot

logger = logging.getLogger(__name__)

ORIGINAL_FILENAME = "original"
THUMBNAIL_FILENAME = "thumbnail.webp"


class GenerationConflict(StudioError):
    """A generation is already active for this world."""


class NothingToGenerate(StudioError):
    """No shot is eligible."""


@dataclass(frozen=True)
class GenerationSettings:
    """Image settings for one run, taken from configuration."""

    model: str
    size: str
    quality: str
    # A draft runs on the cheap model to check framing and composition. Its review
    # scores are not comparable with a full frame's, so it cannot become a reference.
    is_draft: bool = False


def acquire_world_lock(session: Session, world: World) -> None:
    """Take a transaction-scoped advisory lock keyed by the world.

    Released automatically when the transaction ends, including on rollback, so a
    crash cannot leave a world locked.
    """
    session.execute(select(func.pg_advisory_xact_lock(func.hashtext(str(world.id)))))


def active_attempt(session: Session, world: World) -> GenerationAttempt | None:
    """The attempt currently occupying this world, if any."""
    return session.execute(
        select(GenerationAttempt)
        .where(GenerationAttempt.world_id == world.id)
        .where(GenerationAttempt.state.in_(ACTIVE_ATTEMPT_STATES))
    ).scalar_one_or_none()


def _next_attempt_number(session: Session, shot: Shot) -> int:
    highest = session.execute(
        select(func.max(GenerationAttempt.attempt_number)).where(
            GenerationAttempt.shot_id == shot.id
        )
    ).scalar_one_or_none()
    return (highest or 0) + 1


def start_attempt(
    session: Session,
    world: World,
    *,
    parent: GenerationAttempt | None = None,
) -> tuple[GenerationAttempt, Selection]:
    """Lock the world, choose a shot and persist a planned attempt.

    Nothing has been paid for when this returns.
    """
    acquire_world_lock(session, world)

    existing = active_attempt(session, world)
    if existing is not None:
        raise GenerationConflict(
            f"Attempt {existing.attempt_number} for this world is already "
            f"{existing.state.value}. Only one generation runs at a time."
        )

    shots = sorted(world.shots, key=lambda shot: shot.sequence)
    outcome = select_next_shot(world, shots)
    if isinstance(outcome, NoSelection):
        raise NothingToGenerate(outcome.reason)

    attempt = GenerationAttempt(
        world_id=world.id,
        shot_id=outcome.shot.id,
        parent_attempt_id=parent.id if parent else None,
        attempt_number=_next_attempt_number(session, outcome.shot),
        state=AttemptState.PLANNED,
        selection_reason=outcome.reason,
        # Snapshot the shot and the canon version: both can change afterwards, and a
        # generated image must stay traceable to what produced it.
        hero_product=outcome.shot.hero_product,
        camera_position=outcome.shot.camera_position,
        world_document_hash=world.world_document_hash,
        continuity_document_hash=world.continuity_document_hash,
        shotlist_document_hash=world.shotlist_document_hash,
    )
    session.add(attempt)
    session.flush()

    return attempt, outcome


def run_attempt(
    session: Session,
    attempt: GenerationAttempt,
    selection: Selection,
    *,
    markdown_store: MarkdownStore,
    planning_client: PromptPlanningClient,
    image_client: ImageGenerationClient,
    asset_store: AssetStore,
    settings: GenerationSettings,
    retry_policy: RetryPolicy = DEFAULT_POLICY,
) -> GenerationAttempt:
    """Plan, generate and store. Failures are recorded, never raised past here.

    The attempt row always ends in a terminal-for-this-phase state: ``generated`` or
    ``failed``.
    """
    world = attempt.world
    shot = attempt.shot

    try:
        documents = markdown_store.read_world_documents(world.slug)
    except StudioError as error:
        return _fail(session, attempt, FailureCode.INTERNAL, str(error))

    # --- plan (no charge if this fails) ---------------------------------------
    try:
        rotation = apply_continuity(selection.rotation, documents[CONTINUITY_DOCUMENT].text)
        request = build_request(
            world_slug=world.slug,
            world_name=world.name,
            shot=shot,
            world_text=documents[WORLD_DOCUMENT].text,
            rotation=rotation,
            selection_reason=attempt.selection_reason or "",
            # What the world has already got right. Active and pinned frames only:
            # archived ones are history, and feeding them back would keep steering
            # towards frames the library has already judged weaker.
            reference_frames=reference_service.reference_notes(session, world.id),
        )
        plan = create_plan(planning_client, request).plan
    except PlanningError as error:
        # No image was requested, so nothing was charged. The shot stays planned.
        return _fail(session, attempt, FailureCode.PLANNING_FAILED, str(error))

    attempt.production_prompt = plan.production_prompt
    attempt.prompt_plan_json = plan.model_dump()
    attempt.image_model = settings.model
    attempt.image_size = settings.size
    attempt.image_quality = settings.quality
    attempt.is_draft = settings.is_draft
    attempt.state = AttemptState.PROMPT_READY
    session.flush()
    # Committed before the paid call: if the process dies mid-generation, the prompt
    # that was paid for is still on record.
    session.commit()

    # --- generate --------------------------------------------------------------
    attempt.state = AttemptState.GENERATING
    session.flush()
    session.commit()

    image_request = ImageGenerationRequest(
        prompt=plan.production_prompt,
        model=settings.model,
        size=settings.size,
        quality=settings.quality,
    )

    try:
        generated = call_with_retry(lambda: image_client.generate(image_request), retry_policy)
    except ImageGenerationError as error:
        return _fail(session, attempt, error.code, str(error))

    attempt.image_format = generated.output_format
    attempt.provider_request_id = generated.provider_request_id

    # --- store -----------------------------------------------------------------
    try:
        _store_assets(session, attempt, generated, asset_store, world.slug)
    except ImageGenerationError as error:
        return _fail(session, attempt, error.code, str(error))
    except AssetStoreError as error:
        return _fail(session, attempt, FailureCode.STORAGE_FAILED, str(error))

    attempt.state = AttemptState.GENERATED
    attempt.failure_code = None
    attempt.failure_message = None
    session.flush()
    session.commit()

    logger.info("Attempt %s generated for shot %s", attempt.id, shot.external_id)
    return attempt


def _store_assets(
    session: Session,
    attempt: GenerationAttempt,
    generated: GeneratedImage,
    asset_store: AssetStore,
    world_slug: str,
) -> None:
    """Save the original and a thumbnail, recording metadata for each."""
    dimensions = images.measure(generated.data)
    extension = generated.mime_type.removeprefix("image/")

    original = asset_store.save(
        attempt_key(world_slug, str(attempt.id), f"{ORIGINAL_FILENAME}.{extension}"),
        generated.data,
        generated.mime_type,
    )
    session.add(
        ImageAsset(
            attempt_id=attempt.id,
            kind=AssetKind.ORIGINAL,
            relative_path=original.key,
            sha256=original.sha256,
            mime_type=original.mime_type,
            width=dimensions.width,
            height=dimensions.height,
            byte_size=original.byte_size,
        )
    )

    thumbnail_bytes, thumbnail_size = images.make_thumbnail(generated.data)
    thumbnail = asset_store.save(
        attempt_key(world_slug, str(attempt.id), THUMBNAIL_FILENAME),
        thumbnail_bytes,
        images.THUMBNAIL_MIME_TYPE,
    )
    session.add(
        ImageAsset(
            attempt_id=attempt.id,
            kind=AssetKind.THUMBNAIL,
            relative_path=thumbnail.key,
            sha256=thumbnail.sha256,
            mime_type=thumbnail.mime_type,
            width=thumbnail_size.width,
            height=thumbnail_size.height,
            byte_size=thumbnail.byte_size,
        )
    )
    session.flush()


def _fail(
    session: Session, attempt: GenerationAttempt, code: FailureCode, message: str
) -> GenerationAttempt:
    """Record a failure. No phantom asset is created."""
    attempt.state = AttemptState.FAILED
    attempt.failure_code = code
    attempt.failure_message = message[:2000]
    session.flush()
    session.commit()

    logger.warning("Attempt %s failed (%s): %s", attempt.id, code.value, message)
    return attempt
