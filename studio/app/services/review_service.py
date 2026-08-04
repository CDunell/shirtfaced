"""Reviewing a generated image.

The review looks at the stored bytes, not the prompt. It persists structured evidence
and, where the model proposes a genuinely new rule, records a *pending* proposal.

What this module must never do, and is tested for:

* approve or reject anything;
* change a shot's status;
* append to ``CONTINUITY.md``;
* edit ``WORLD.md``.

A review failure preserves the image. Reviewing again is a separate, cheap operation
that does not regenerate anything.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore, AssetStoreError
from app.adapters.review import (
    REVIEW_SCHEMA_VERSION,
    ImageReviewClient,
    ImageReviewRequest,
    ReviewError,
)
from app.db.models import AutomatedReview, CanonProposal, GenerationAttempt, ImageAsset
from app.domain.enums import AssetKind, AttemptState, CanonProposalStatus, FailureCode
from app.domain.schemas import CanonExcerpt, ImageReview
from app.services.markdown_sections import section_with_subsections
from app.services.prompt_planner import PLANNING_CANON_HEADINGS, truncate_excerpt
from app.services.rotation import RotationState

logger = logging.getLogger(__name__)

# The proposal's insertion point in WORLD.md. Applying it is the canon proposal
# phase's job; this only records where the model believed it belongs.
DEFAULT_INSERTION_ANCHOR = "Current Canon Notes"


class NothingToReview(ReviewError):
    """The attempt has no stored image to look at."""


def _original_asset(attempt: GenerationAttempt) -> ImageAsset | None:
    for asset in attempt.assets:
        if asset.kind is AssetKind.ORIGINAL:
            return asset
    return None


def build_review_request(
    attempt: GenerationAttempt,
    *,
    asset: ImageAsset,
    image_data: bytes,
    world_text: str,
    rotation: RotationState,
) -> ImageReviewRequest:
    """Assemble the reviewer's bounded context.

    The same canon the planner saw, so the image is judged against the rules it was
    built from rather than a different subset.
    """
    excerpts = [
        CanonExcerpt(heading=heading, body=truncate_excerpt(body))
        for heading in PLANNING_CANON_HEADINGS
        if (body := section_with_subsections(world_text, heading)) is not None and body.strip()
    ]

    plan = attempt.prompt_plan_json or {}

    return ImageReviewRequest(
        attempt_id=str(attempt.id),
        image_data=image_data,
        image_mime_type=asset.mime_type,
        shot_external_id=attempt.shot.external_id,
        scene=attempt.shot.title,
        # The snapshot, not the shot's current values: the shotlist may have moved on.
        required_hero_product=attempt.hero_product,
        required_camera_position=attempt.camera_position,
        production_prompt=attempt.production_prompt or "",
        selection_rationale=str(plan.get("selection_rationale") or attempt.selection_reason or ""),
        canon_excerpts=excerpts,
        canon_notes=rotation.canon_notes,
        rejected_drift=[f"{entry.title}: {entry.body}" for entry in rotation.rejected_drift[:3]],
        world_document_hash=attempt.world_document_hash,
    )


def review_attempt(
    session: Session,
    attempt: GenerationAttempt,
    *,
    review_client: ImageReviewClient,
    asset_store: AssetStore,
    world_text: str,
    rotation: RotationState,
) -> AutomatedReview | None:
    """Review one attempt's stored image.

    Returns the persisted review, or ``None`` when the review failed. Failure is
    recorded on the attempt and the image is kept, so a retry costs one review rather
    than a regeneration.
    """
    asset = _original_asset(attempt)
    if asset is None:
        raise NothingToReview(f"Attempt {attempt.id} has no stored image to review.")

    attempt.state = AttemptState.REVIEWING
    session.flush()
    session.commit()

    try:
        image_data = asset_store.load(asset.relative_path)
    except AssetStoreError as error:
        _fail(session, attempt, f"The stored image could not be read. {error}")
        return None

    request = build_review_request(
        attempt,
        asset=asset,
        image_data=image_data,
        world_text=world_text,
        rotation=rotation,
    )

    try:
        result = review_client.review(request)
    except ReviewError as error:
        _fail(session, attempt, str(error))
        return None

    review = _persist(session, attempt, result.review, result.model, result.provider_request_id)
    _record_proposal(session, attempt, result.review)

    # The image has been judged. The decision is the owner's.
    attempt.state = AttemptState.AWAITING_DECISION
    attempt.failure_code = None
    attempt.failure_message = None
    session.flush()
    session.commit()

    logger.info("Attempt %s reviewed: %s", attempt.id, result.review.recommendation.value)
    return review


def _persist(
    session: Session,
    attempt: GenerationAttempt,
    review: ImageReview,
    model: str,
    provider_request_id: str | None,
) -> AutomatedReview:
    record = AutomatedReview(
        attempt_id=attempt.id,
        review_model=model,
        schema_version=REVIEW_SCHEMA_VERSION,
        provider_request_id=provider_request_id,
        recommendation=review.recommendation,
        verdict=review.verdict,
        mood_score=review.mood_score,
        australian_authenticity_score=review.australian_authenticity_score,
        product_visibility_score=review.product_visibility_score,
        documentary_credibility_score=review.documentary_credibility_score,
        story_score=review.story_score,
        branding_compliant=review.branding_compliant,
        vehicle_compliant=review.vehicle_compliant,
        strongest_success=review.strongest_success,
        material_drift=review.material_drift,
        recommended_action=_recommended_action(review),
        next_hero_product=review.next_hero_product,
        next_camera=review.next_camera,
        raw_json=review.model_dump(mode="json"),
        world_document_hash=attempt.world_document_hash,
    )
    session.add(record)
    session.flush()
    return record


def _recommended_action(review: ImageReview) -> str:
    """A one-line summary of what the reviewer advises, for the history list."""
    blocking = review.blocking_gates
    if blocking:
        names = ", ".join(gate.value for gate in blocking)
        return f"{review.recommendation.value} — material failures: {names}"

    uncertain = review.uncertain_gates
    if uncertain:
        names = ", ".join(gate.value for gate in uncertain)
        return f"{review.recommendation.value} — human inspection suggested: {names}"

    return review.recommendation.value


def _record_proposal(
    session: Session, attempt: GenerationAttempt, review: ImageReview
) -> CanonProposal | None:
    """Record a proposed rule as pending. It never changes WORLD.md."""
    proposal_text = (review.new_rule_proposal or "").strip()
    if not proposal_text:
        return None

    proposal = CanonProposal(
        world_id=attempt.world_id,
        attempt_id=attempt.id,
        status=CanonProposalStatus.PENDING,
        proposed_heading=None,
        proposed_text=proposal_text,
        insertion_anchor=DEFAULT_INSERTION_ANCHOR,
        reason=review.material_drift or review.strongest_success,
    )
    session.add(proposal)
    session.flush()

    logger.info("Attempt %s proposed a canon rule; stored as pending.", attempt.id)
    return proposal


def _fail(session: Session, attempt: GenerationAttempt, message: str) -> None:
    """Record a review failure without losing the image.

    The attempt returns to ``generated``: it still holds a valid image, so it keeps
    occupying its world and can be reviewed again without regenerating.
    """
    attempt.state = AttemptState.GENERATED
    attempt.failure_code = FailureCode.REVIEW_FAILED
    attempt.failure_message = message[:2000]
    session.flush()
    session.commit()

    logger.warning("Review of attempt %s failed: %s", attempt.id, message)
