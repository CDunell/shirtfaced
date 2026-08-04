"""Review against PostgreSQL.

The fake reviewer is used, so nothing is billed, but persistence, state transitions,
proposal recording and the boundaries the review must not cross are all real.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.adapters.image_generation import FakeImageGenerationClient
from app.adapters.markdown_store import MarkdownStore
from app.adapters.planning import FakePromptPlanningClient
from app.adapters.review import FakeImageReviewClient, ReviewError
from app.db.models import AutomatedReview, CanonProposal, GenerationAttempt, World
from app.domain.enums import (
    AttemptState,
    CanonProposalStatus,
    FailureCode,
    GateName,
    ReviewRecommendation,
    ShotStatus,
)
from app.services.generation_orchestrator import GenerationSettings, run_attempt, start_attempt
from app.services.retry import RetryPolicy
from app.services.review_service import NothingToReview, review_attempt
from app.services.rotation import apply_continuity, rotation_from_shots
from app.services.world_importer import import_world
from tests.fixtures.reviews import ACCEPTANCE_SET
from tests.fixtures.worlds import write_world

pytestmark = pytest.mark.integration

SETTINGS = GenerationSettings(model="a-test-model", size="128x96", quality="high")
NO_RETRY = RetryPolicy(max_attempts=1, initial_delay_seconds=0.0)


@pytest.fixture
def worlds_root(tmp_path: Path) -> Path:
    write_world(tmp_path)
    return tmp_path


@pytest.fixture
def assets_root(tmp_path: Path) -> Path:
    return tmp_path / "assets"


@pytest.fixture
def world(session: Session, worlds_root: Path) -> World:
    import_world(session, MarkdownStore(worlds_root), "world-01")
    session.flush()
    return session.execute(select(World).where(World.slug == "world-01")).scalar_one()


@pytest.fixture
def generated(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> GenerationAttempt:
    attempt, selection = start_attempt(session, world)
    return run_attempt(
        session,
        attempt,
        selection,
        markdown_store=MarkdownStore(worlds_root),
        planning_client=FakePromptPlanningClient(),
        image_client=FakeImageGenerationClient(),
        asset_store=FilesystemAssetStore(assets_root),
        settings=SETTINGS,
        retry_policy=NO_RETRY,
    )


def _review(
    session: Session,
    attempt: GenerationAttempt,
    worlds_root: Path,
    assets_root: Path,
    *,
    client: FakeImageReviewClient | None = None,
) -> AutomatedReview | None:
    store = MarkdownStore(worlds_root)
    documents = store.read_world_documents("world-01")
    shots = sorted(attempt.world.shots, key=lambda shot: shot.sequence)
    rotation = apply_continuity(rotation_from_shots(shots), documents["CONTINUITY.md"].text)

    return review_attempt(
        session,
        attempt,
        review_client=client or FakeImageReviewClient(),
        asset_store=FilesystemAssetStore(assets_root),
        world_text=documents["WORLD.md"].text,
        rotation=rotation,
    )


# --- the happy path ----------------------------------------------------------------


def test_a_generated_image_receives_a_validated_review(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    review = _review(session, generated, worlds_root, assets_root)

    assert review is not None
    assert len(review.raw_json["gates"]) == 9
    assert review.recommendation is ReviewRecommendation.APPROVE


def test_the_attempt_comes_to_rest_awaiting_a_decision(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    _review(session, generated, worlds_root, assets_root)

    assert generated.state is AttemptState.AWAITING_DECISION


def test_scores_and_compliance_are_persisted(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    review = _review(session, generated, worlds_root, assets_root)

    assert review is not None
    assert 1 <= review.mood_score <= 5
    assert review.branding_compliant is True
    assert review.vehicle_compliant is True


def test_the_gate_evidence_survives_intact(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    review = _review(session, generated, worlds_root, assets_root)

    assert review is not None
    mood = review.raw_json["gates"][GateName.MOOD.value]
    assert mood["evidence"]
    assert "confidence" in mood


def test_the_reviewer_is_sent_the_stored_image_not_the_prompt_alone(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    client = FakeImageReviewClient()

    _review(session, generated, worlds_root, assets_root, client=client)

    request = client.requests[0]
    assert request.image_data.startswith(b"\x89PNG")
    assert request.image_mime_type == "image/png"


def test_the_reviewer_is_told_what_was_asked_for(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    client = FakeImageReviewClient()

    _review(session, generated, worlds_root, assets_root, client=client)

    request = client.requests[0]
    assert request.required_hero_product == "Tote bag"
    assert request.required_camera_position == "Rear seat"
    assert request.shot_external_id == "W01-011"


def test_the_reviewer_receives_the_canon(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    client = FakeImageReviewClient()

    _review(session, generated, worlds_root, assets_root, client=client)

    headings = [excerpt.heading for excerpt in client.requests[0].canon_excerpts]
    # The same allowlist the planner uses. The real WORLD.md's branding and vehicle
    # sections are covered against the actual document in test_planning_context.py.
    assert "Composition" in headings
    assert "Wardrobe" in headings
    assert "An Unknown Section" not in headings


def test_the_canon_version_judged_against_is_recorded(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    review = _review(session, generated, worlds_root, assets_root)

    assert review is not None
    assert review.world_document_hash == generated.world_document_hash


# --- boundaries the review must not cross ------------------------------------------


def test_a_review_does_not_change_the_shot_status(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    """Models propose. The user decides."""
    _review(
        session,
        generated,
        worlds_root,
        assets_root,
        client=FakeImageReviewClient(result=ACCEPTANCE_SET["correct_car_interior"]),
    )
    session.refresh(generated.shot)

    assert generated.shot.status is ShotStatus.PLANNED


def test_a_rejection_recommendation_does_not_reject_anything(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    _review(
        session,
        generated,
        worlds_root,
        assets_root,
        client=FakeImageReviewClient(result=ACCEPTANCE_SET["branded_chip_packet"]),
    )
    session.refresh(generated.shot)

    assert generated.state is AttemptState.AWAITING_DECISION
    assert generated.shot.status is ShotStatus.PLANNED


def test_a_review_does_not_touch_the_markdown(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    world_md = worlds_root / "world-01" / "WORLD.md"
    continuity_md = worlds_root / "world-01" / "CONTINUITY.md"
    before = (world_md.read_bytes(), continuity_md.read_bytes())

    _review(
        session,
        generated,
        worlds_root,
        assets_root,
        client=FakeImageReviewClient(result=ACCEPTANCE_SET["american_pickup"]),
    )

    assert (world_md.read_bytes(), continuity_md.read_bytes()) == before


# --- canon proposals ---------------------------------------------------------------


def test_a_proposed_rule_is_recorded_as_pending(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    _review(
        session,
        generated,
        worlds_root,
        assets_root,
        client=FakeImageReviewClient(result=ACCEPTANCE_SET["american_pickup"]),
    )

    proposal = session.execute(select(CanonProposal)).scalar_one()
    assert proposal.status is CanonProposalStatus.PENDING
    assert "alloy tray" in proposal.proposed_text
    assert proposal.attempt_id == generated.id


def test_no_proposal_is_recorded_when_none_was_offered(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    _review(
        session,
        generated,
        worlds_root,
        assets_root,
        client=FakeImageReviewClient(result=ACCEPTANCE_SET["correct_car_interior"]),
    )

    assert session.execute(select(CanonProposal)).scalars().all() == []


# --- failure and retry -------------------------------------------------------------


def test_a_review_failure_preserves_the_image(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    review = _review(
        session,
        generated,
        worlds_root,
        assets_root,
        client=FakeImageReviewClient(fail_with="the reviewer was unavailable"),
    )

    assert review is None
    assert generated.state is AttemptState.GENERATED
    assert generated.failure_code is FailureCode.REVIEW_FAILED
    assert len(generated.assets) == 2


def test_a_failed_review_can_be_retried_without_regenerating(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    _review(
        session,
        generated,
        worlds_root,
        assets_root,
        client=FakeImageReviewClient(fail_with="temporary"),
    )
    original_asset_ids = {asset.id for asset in generated.assets}

    review = _review(session, generated, worlds_root, assets_root)

    assert review is not None
    assert generated.state is AttemptState.AWAITING_DECISION
    assert {asset.id for asset in generated.assets} == original_asset_ids


def test_reviews_are_immutable_so_a_retry_adds_another(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    first = _review(session, generated, worlds_root, assets_root)
    second = _review(
        session,
        generated,
        worlds_root,
        assets_root,
        client=FakeImageReviewClient(result=ACCEPTANCE_SET["miserable_hangover"]),
    )

    assert first is not None
    assert second is not None
    assert first.id != second.id

    stored = session.execute(select(AutomatedReview)).scalars().all()
    assert len(stored) == 2


def test_the_latest_review_is_the_last_one(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    _review(session, generated, worlds_root, assets_root)
    _review(
        session,
        generated,
        worlds_root,
        assets_root,
        client=FakeImageReviewClient(result=ACCEPTANCE_SET["miserable_hangover"]),
    )
    session.refresh(generated)

    latest = generated.latest_review
    assert latest is not None
    assert latest.recommendation is ReviewRecommendation.REJECT


def test_an_attempt_without_an_image_cannot_be_reviewed(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    attempt, _ = start_attempt(session, world)

    with pytest.raises(NothingToReview):
        _review(session, attempt, worlds_root, assets_root)


def test_an_unreadable_image_fails_the_review_not_the_attempt(
    session: Session, generated: GenerationAttempt, worlds_root: Path, assets_root: Path
) -> None:
    for file in assets_root.rglob("*.png"):
        file.unlink()

    review = _review(session, generated, worlds_root, assets_root)

    assert review is None
    assert generated.state is AttemptState.GENERATED
    assert generated.failure_code is FailureCode.REVIEW_FAILED


def test_a_review_error_is_a_studio_error() -> None:
    """So callers can catch the domain base class rather than the SDK's."""
    from app.domain.errors import StudioError

    assert issubclass(ReviewError, StudioError)
