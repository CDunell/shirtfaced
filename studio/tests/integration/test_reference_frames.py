"""The reference library: active, archived, pinned.

The behaviour that matters is what reaches the planner. An approved frame is both a
record and an input, so ageing out must change its state and never lose it.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.adapters.git_store import DisabledGitStore
from app.adapters.image_generation import FakeImageGenerationClient
from app.adapters.markdown_store import CONTINUITY_DOCUMENT, MarkdownStore
from app.adapters.planning import FakePromptPlanningClient
from app.adapters.review import FakeImageReviewClient
from app.db.models import GenerationAttempt, ImageAsset, ReferenceFrame, World
from app.domain.enums import AssetKind, AttemptState, HumanDecisionKind, ReferenceState
from app.services import reference_service
from app.services.decision_service import decide
from app.services.generation_orchestrator import GenerationSettings, run_attempt, start_attempt
from app.services.retry import RetryPolicy
from app.services.review_service import review_attempt
from app.services.rotation import apply_continuity, rotation_from_shots
from app.services.world_importer import import_world
from tests.fixtures.reviews import build_review
from tests.fixtures.worlds import write_world

pytestmark = pytest.mark.integration

SETTINGS = GenerationSettings(model="a-test-model", size="128x96", quality="high")
NO_RETRY = RetryPolicy(max_attempts=1, initial_delay_seconds=0.0)


@pytest.fixture
def worlds_root(tmp_path: Path) -> Path:
    root = tmp_path / "worlds"
    write_world(root)
    return root


@pytest.fixture
def assets_root(tmp_path: Path) -> Path:
    return tmp_path / "assets"


@pytest.fixture
def world(session: Session, worlds_root: Path) -> World:
    import_world(session, MarkdownStore(worlds_root), "world-01")
    session.flush()
    return session.execute(select(World).where(World.slug == "world-01")).scalar_one()


def _make_frame(
    session: Session, world: World, *, strength: int, offset_seconds: int = 0, label: str = "frame"
) -> ReferenceFrame:
    """A frame without going through generation, for library behaviour."""
    shot = sorted(world.shots, key=lambda s: s.sequence)[0]
    # Approved, not planned: a reference derives from an approved attempt, and only
    # one attempt per world may be active at a time.
    attempt = GenerationAttempt(
        world_id=world.id,
        shot_id=shot.id,
        attempt_number=_next_number(session, shot.id),
        state=AttemptState.APPROVED,
    )
    session.add(attempt)
    session.flush()

    asset = ImageAsset(
        attempt_id=attempt.id,
        kind=AssetKind.ORIGINAL,
        relative_path=f"worlds/world-01/attempts/{attempt.id}/original.png",
        sha256="a" * 64,
        mime_type="image/png",
        byte_size=1,
    )
    session.add(asset)
    session.flush()

    frame = ReferenceFrame(
        world_id=world.id,
        attempt_id=attempt.id,
        asset_id=asset.id,
        state=ReferenceState.ACTIVE,
        label=label,
        strength=strength,
    )
    frame.created_at = dt.datetime(2026, 1, 1, tzinfo=dt.UTC) + dt.timedelta(seconds=offset_seconds)
    session.add(frame)
    session.flush()
    return frame


def _next_number(session: Session, shot_id: object) -> int:
    from sqlalchemy import func

    highest = session.execute(
        select(func.max(GenerationAttempt.attempt_number)).where(
            GenerationAttempt.shot_id == shot_id
        )
    ).scalar_one_or_none()
    return (highest or 0) + 1


# --- ageing ------------------------------------------------------------------------


def test_the_active_set_is_capped(session: Session, world: World) -> None:
    for index in range(6):
        _make_frame(session, world, strength=index, offset_seconds=index, label=f"f{index}")

    reference_service.rebalance(session, world.id, active_limit=3)

    counts = reference_service.counts(session, world.id)
    assert counts.active == 3
    assert counts.archived == 3


def test_the_weakest_frames_age_out(session: Session, world: World) -> None:
    weak = _make_frame(session, world, strength=5, label="weak")
    strong = _make_frame(session, world, strength=25, label="strong")

    reference_service.rebalance(session, world.id, active_limit=1)

    assert strong.state is ReferenceState.ACTIVE
    assert weak.state is ReferenceState.ARCHIVED


def test_recency_breaks_a_strength_tie(session: Session, world: World) -> None:
    older = _make_frame(session, world, strength=20, offset_seconds=0, label="older")
    newer = _make_frame(session, world, strength=20, offset_seconds=60, label="newer")

    reference_service.rebalance(session, world.id, active_limit=1)

    assert newer.state is ReferenceState.ACTIVE
    assert older.state is ReferenceState.ARCHIVED


def test_ageing_out_never_deletes_anything(session: Session, world: World) -> None:
    """An approved frame records a decision as well as feeding one."""
    for index in range(5):
        _make_frame(session, world, strength=index, offset_seconds=index)

    reference_service.rebalance(session, world.id, active_limit=2)

    stored = session.execute(select(ReferenceFrame)).scalars().all()
    assert len(stored) == 5
    assert all(
        frame.archived_at is not None for frame in stored if frame.state is ReferenceState.ARCHIVED
    )


def test_rebalancing_is_idempotent(session: Session, world: World) -> None:
    for index in range(5):
        _make_frame(session, world, strength=index, offset_seconds=index)

    reference_service.rebalance(session, world.id, active_limit=2)
    second = reference_service.rebalance(session, world.id, active_limit=2)

    assert second == []
    assert reference_service.counts(session, world.id).active == 2


# --- pinning -----------------------------------------------------------------------


def test_a_pinned_frame_never_ages_out(session: Session, world: World) -> None:
    weak = _make_frame(session, world, strength=0, label="weak but pinned")
    for index in range(5):
        _make_frame(session, world, strength=20 + index, offset_seconds=index)

    reference_service.set_pinned(session, weak, pinned=True, active_limit=2)

    assert weak.state is ReferenceState.PINNED
    assert reference_service.counts(session, world.id).active == 2


def test_pinned_frames_sit_outside_the_cap(session: Session, world: World) -> None:
    pinned = _make_frame(session, world, strength=1, label="pinned")
    reference_service.set_pinned(session, pinned, pinned=True, active_limit=2)
    for index in range(4):
        _make_frame(session, world, strength=10 + index, offset_seconds=index)

    reference_service.rebalance(session, world.id, active_limit=2)

    counts = reference_service.counts(session, world.id)
    assert counts.pinned == 1
    assert counts.active == 2
    assert counts.reaching_planner == 3


def test_unpinning_returns_a_frame_to_the_contest(session: Session, world: World) -> None:
    """It takes its chances rather than silently disappearing."""
    weak = _make_frame(session, world, strength=0, label="weak")
    reference_service.set_pinned(session, weak, pinned=True, active_limit=2)
    for index in range(3):
        _make_frame(session, world, strength=20 + index, offset_seconds=index)

    reference_service.set_pinned(session, weak, pinned=False, active_limit=2)

    assert weak.state is ReferenceState.ARCHIVED


# --- what the planner sees ---------------------------------------------------------


def test_only_active_and_pinned_frames_reach_the_planner(session: Session, world: World) -> None:
    for index in range(5):
        _make_frame(session, world, strength=index, offset_seconds=index, label=f"f{index}")
    reference_service.rebalance(session, world.id, active_limit=2)

    frames = reference_service.planner_frames(session, world.id)

    assert len(frames) == 2
    assert all(frame.reaches_planner for frame in frames)


def test_pinned_frames_come_first(session: Session, world: World) -> None:
    _make_frame(session, world, strength=30, label="strongest")
    pinned = _make_frame(session, world, strength=1, label="pinned")
    reference_service.set_pinned(session, pinned, pinned=True, active_limit=5)

    frames = reference_service.planner_frames(session, world.id)

    assert frames[0].label == "pinned"


def test_the_planner_note_names_the_product_and_camera(session: Session, world: World) -> None:
    frame = _make_frame(session, world, strength=20, label="W01-011 — Car interior")
    frame.hero_product = "Tote bag"
    frame.camera_position = "Rear seat"
    frame.why_it_works = "The moment reads as taken."
    session.flush()

    notes = reference_service.reference_notes(session, world.id)

    assert "Tote bag" in notes[0]
    assert "Rear seat" in notes[0]
    assert "reads as taken" in notes[0]


def test_the_planner_reference_list_is_bounded(session: Session, world: World) -> None:
    for index in range(20):
        _make_frame(session, world, strength=index, offset_seconds=index)

    frames = reference_service.planner_frames(session, world.id)

    assert len(frames) <= reference_service.PLANNER_REFERENCE_LIMIT


def test_an_empty_library_yields_no_notes(session: Session, world: World) -> None:
    assert reference_service.reference_notes(session, world.id) == []


def test_generation_actually_sends_the_library_to_the_planner(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    """The service can be right while the caller never asks it anything.

    Every other test here drives reference_service directly, so the library could work
    perfectly and still reach no real request. This asserts the wiring.
    """
    frame = _make_frame(session, world, strength=22, label="W01-011 — Car interior")
    frame.hero_product = "Tote bag"
    session.flush()

    planning_client = FakePromptPlanningClient()
    attempt, selection = start_attempt(session, world)
    run_attempt(
        session,
        attempt,
        selection,
        markdown_store=MarkdownStore(worlds_root),
        planning_client=planning_client,
        image_client=FakeImageGenerationClient(),
        asset_store=FilesystemAssetStore(assets_root),
        settings=SETTINGS,
        retry_policy=NO_RETRY,
    )

    assert planning_client.requests, "The planner was never called."
    notes = planning_client.requests[0].reference_frames
    assert any("W01-011" in note and "Tote bag" in note for note in notes), notes


def test_archived_frames_do_not_reach_a_real_request(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    """Feeding archived frames back would steer towards what the library rejected."""
    aged = _make_frame(session, world, strength=1, label="W01-099 — aged out")
    _make_frame(session, world, strength=30, offset_seconds=10, label="W01-011 — kept")
    reference_service.rebalance(session, world.id, active_limit=1)
    assert aged.state is ReferenceState.ARCHIVED

    planning_client = FakePromptPlanningClient()
    attempt, selection = start_attempt(session, world)
    run_attempt(
        session,
        attempt,
        selection,
        markdown_store=MarkdownStore(worlds_root),
        planning_client=planning_client,
        image_client=FakeImageGenerationClient(),
        asset_store=FilesystemAssetStore(assets_root),
        settings=SETTINGS,
        retry_policy=NO_RETRY,
    )

    notes = planning_client.requests[0].reference_frames
    assert not any("W01-099" in note for note in notes), notes
    assert any("W01-011" in note for note in notes), notes


# --- promotion through approval ----------------------------------------------------


def test_approving_with_promotion_enters_the_library(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    store = MarkdownStore(worlds_root)
    attempt, selection = start_attempt(session, world)
    run_attempt(
        session,
        attempt,
        selection,
        markdown_store=store,
        planning_client=FakePromptPlanningClient(),
        image_client=FakeImageGenerationClient(),
        asset_store=FilesystemAssetStore(assets_root),
        settings=SETTINGS,
        retry_policy=NO_RETRY,
    )
    documents = store.read_world_documents("world-01")
    rotation = apply_continuity(
        rotation_from_shots(sorted(world.shots, key=lambda s: s.sequence)),
        documents[CONTINUITY_DOCUMENT].text,
    )
    review_attempt(
        session,
        attempt,
        review_client=FakeImageReviewClient(result=build_review(mood_score=5, story_score=5)),
        asset_store=FilesystemAssetStore(assets_root),
        world_text=documents["WORLD.md"].text,
        rotation=rotation,
    )

    decide(
        session,
        attempt,
        HumanDecisionKind.APPROVED,
        markdown_store=store,
        git_store=DisabledGitStore(),
        asset_store=FilesystemAssetStore(assets_root),
        git_enabled=False,
        promote_to_reference=True,
    )

    frame = session.execute(select(ReferenceFrame)).scalar_one()
    assert frame.state is ReferenceState.ACTIVE
    assert frame.attempt_id == attempt.id
    # Strength comes from the review: 5 + 4 + 4 + 4 + 5.
    assert frame.strength == 22
    assert "W01-011" in frame.label


def test_promotion_is_idempotent(session: Session, world: World) -> None:
    frame = _make_frame(session, world, strength=10)
    attempt = session.get(GenerationAttempt, frame.attempt_id)
    assert attempt is not None

    again = reference_service.promote(session, attempt)

    assert again.id == frame.id
    assert len(session.execute(select(ReferenceFrame)).scalars().all()) == 1


def test_a_frame_without_a_review_scores_zero(session: Session, world: World) -> None:
    """An unreviewed frame has not earned a place ahead of a reviewed one."""
    shot = sorted(world.shots, key=lambda s: s.sequence)[0]
    attempt = GenerationAttempt(
        world_id=world.id, shot_id=shot.id, attempt_number=99, state=AttemptState.APPROVED
    )
    session.add(attempt)
    session.flush()
    session.add(
        ImageAsset(
            attempt_id=attempt.id,
            kind=AssetKind.ORIGINAL,
            relative_path="p.png",
            sha256="b" * 64,
            mime_type="image/png",
            byte_size=1,
        )
    )
    session.flush()

    frame = reference_service.promote(session, attempt)

    assert frame.strength == 0
