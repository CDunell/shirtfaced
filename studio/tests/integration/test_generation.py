"""Generation against PostgreSQL.

These use the fake image client, so nothing is billed, but everything else is real:
the advisory lock, the partial unique index, the transitions, the stored files.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.adapters.image_generation import (
    FakeImageGenerationClient,
    ImageGenerationError,
)
from app.adapters.markdown_store import MarkdownStore
from app.adapters.planning import FakePromptPlanningClient
from app.db.models import GenerationAttempt, ImageAsset, Shot, World
from app.domain.enums import AssetKind, AttemptState, FailureCode
from app.services import images
from app.services.generation_orchestrator import (
    GenerationConflict,
    GenerationSettings,
    NothingToGenerate,
    run_attempt,
    start_attempt,
)
from app.services.retry import RetryPolicy
from app.services.world_importer import import_world
from tests.fixtures.worlds import write_world

pytestmark = pytest.mark.integration

SETTINGS = GenerationSettings(model="a-test-model", size="256x192", quality="high")
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


def _generate(
    session: Session,
    world: World,
    worlds_root: Path,
    assets_root: Path,
    *,
    image_client: FakeImageGenerationClient | None = None,
    planning_client: FakePromptPlanningClient | None = None,
) -> GenerationAttempt:
    attempt, selection = start_attempt(session, world)
    return run_attempt(
        session,
        attempt,
        selection,
        markdown_store=MarkdownStore(worlds_root),
        planning_client=planning_client or FakePromptPlanningClient(),
        image_client=image_client or FakeImageGenerationClient(),
        asset_store=FilesystemAssetStore(assets_root),
        settings=SETTINGS,
        retry_policy=NO_RETRY,
    )


# --- the happy path ----------------------------------------------------------------


def test_one_action_creates_exactly_one_durable_image(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    attempt = _generate(session, world, worlds_root, assets_root)

    assert attempt.state is AttemptState.GENERATED
    originals = [a for a in attempt.assets if a.kind is AssetKind.ORIGINAL]
    assert len(originals) == 1
    assert (assets_root / originals[0].relative_path).is_file()


def test_the_selected_shot_is_the_one_the_selector_chose(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    attempt = _generate(session, world, worlds_root, assets_root)

    assert attempt.shot.external_id == "W01-011"
    assert "W01-011" in (attempt.selection_reason or "")


def test_the_prompt_and_plan_are_persisted(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    attempt = _generate(session, world, worlds_root, assets_root)

    assert attempt.production_prompt
    assert attempt.prompt_plan_json is not None
    assert attempt.prompt_plan_json["hero_product"] == "Tote bag"


def test_the_attempt_records_the_model_that_was_actually_called(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    """What ran, not what was asked for. These differ, and the difference cost money.

    The real client fixes its model at construction and ignores the one on the
    request. While the attempt recorded the requested model, three runs went into the
    database reading gpt-image-1-mini for images billed as gpt-image-2 at full size
    and quality -- and carrying is_draft, which also barred them from ever becoming
    references.

    The existing settings test cannot catch this: the fake echoes request.model back,
    so the requested and actual models coincide. This client reports a different one,
    which is what the real one does.
    """

    class DifferentModelClient(FakeImageGenerationClient):
        def generate(self, request):  # type: ignore[no-untyped-def]
            generated = super().generate(request)
            return replace(generated, model="the-model-actually-called")

    attempt = _generate(
        session, world, worlds_root, assets_root, image_client=DifferentModelClient()
    )

    assert attempt.image_model == "the-model-actually-called"
    assert attempt.image_model != SETTINGS.model


def test_model_settings_are_recorded(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    attempt = _generate(session, world, worlds_root, assets_root)

    assert attempt.image_model == "a-test-model"
    assert attempt.image_size == "256x192"
    assert attempt.image_quality == "high"
    assert attempt.image_format == "png"
    assert attempt.provider_request_id == "fake-request"


def test_provenance_is_snapshotted(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    """A generated image must stay traceable even after the documents change."""
    attempt = _generate(session, world, worlds_root, assets_root)

    assert attempt.hero_product == "Tote bag"
    assert attempt.camera_position == "Rear seat"
    assert attempt.world_document_hash == world.world_document_hash
    assert attempt.shotlist_document_hash == world.shotlist_document_hash


def test_a_thumbnail_is_stored_alongside_the_original(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    attempt = _generate(session, world, worlds_root, assets_root)

    kinds = {asset.kind for asset in attempt.assets}
    assert kinds == {AssetKind.ORIGINAL, AssetKind.THUMBNAIL}


def test_asset_bytes_match_their_recorded_hash_and_size(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    import hashlib

    attempt = _generate(session, world, worlds_root, assets_root)
    store = FilesystemAssetStore(assets_root)

    for asset in attempt.assets:
        data = store.load(asset.relative_path)
        assert hashlib.sha256(data).hexdigest() == asset.sha256
        assert len(data) == asset.byte_size


def test_image_dimensions_are_recorded(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    attempt = _generate(session, world, worlds_root, assets_root)
    original = next(a for a in attempt.assets if a.kind is AssetKind.ORIGINAL)

    assert (original.width, original.height) == (256, 192)


def test_the_shot_is_not_approved_by_generating_an_image(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    """Models propose. The user decides."""
    attempt = _generate(session, world, worlds_root, assets_root)
    session.refresh(attempt.shot)

    assert attempt.shot.status.value == "planned"
    assert attempt.state is not AttemptState.APPROVED


# --- persist before the paid call --------------------------------------------------


def test_the_attempt_exists_before_any_image_is_requested(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    """A crash after the money is spent must still leave a record of what for."""
    attempt, _ = start_attempt(session, world)

    stored = session.execute(
        select(GenerationAttempt).where(GenerationAttempt.id == attempt.id)
    ).scalar_one()
    assert stored.state is AttemptState.PLANNED
    assert stored.shot_id is not None


def test_the_prompt_is_committed_before_the_image_call(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    recorded: dict[str, str | None] = {}

    class Recorder(FakeImageGenerationClient):
        def generate(self, request):  # type: ignore[no-untyped-def]
            # At this point the paid call is about to happen: the prompt must
            # already be on the row.
            recorded["prompt"] = attempt.production_prompt
            recorded["state"] = attempt.state.value
            return super().generate(request)

    attempt, selection = start_attempt(session, world)
    run_attempt(
        session,
        attempt,
        selection,
        markdown_store=MarkdownStore(worlds_root),
        planning_client=FakePromptPlanningClient(),
        image_client=Recorder(),
        asset_store=FilesystemAssetStore(assets_root),
        settings=SETTINGS,
        retry_policy=NO_RETRY,
    )

    assert recorded["prompt"]
    assert recorded["state"] == "generating"


# --- concurrency -------------------------------------------------------------------


def test_a_second_generation_is_refused_while_one_is_active(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    _generate(session, world, worlds_root, assets_root)

    with pytest.raises(GenerationConflict, match="already"):
        start_attempt(session, world)


def test_the_database_refuses_two_active_attempts_even_without_the_service_check(
    session: Session, world: World
) -> None:
    """The partial unique index is the real guarantee, not the application check."""
    shot = session.execute(select(Shot).where(Shot.external_id == "W01-011")).scalar_one()
    other = session.execute(select(Shot).where(Shot.external_id == "W01-012")).scalar_one()

    session.add(
        GenerationAttempt(
            world_id=world.id, shot_id=shot.id, attempt_number=1, state=AttemptState.GENERATING
        )
    )
    session.flush()

    session.add(
        GenerationAttempt(
            world_id=world.id, shot_id=other.id, attempt_number=1, state=AttemptState.PLANNED
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_a_finished_attempt_does_not_block_the_next_one(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    first = _generate(session, world, worlds_root, assets_root)
    first.state = AttemptState.REJECTED
    session.flush()

    second, _ = start_attempt(session, world)

    assert second.id != first.id


def test_attempt_numbers_increment_per_shot(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    first = _generate(session, world, worlds_root, assets_root)
    first_shot_id = first.shot_id
    first.state = AttemptState.REJECTED
    session.flush()

    second = _generate(session, world, worlds_root, assets_root)

    if second.shot_id == first_shot_id:
        assert second.attempt_number == first.attempt_number + 1
    else:
        assert second.attempt_number == 1


def test_the_advisory_lock_is_held_for_the_transaction(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    start_attempt(session, world)

    held = session.execute(
        text("SELECT count(*) FROM pg_locks WHERE locktype = 'advisory'")
    ).scalar_one()
    assert held >= 1


# --- failures ----------------------------------------------------------------------


def test_a_planning_failure_costs_nothing_and_is_recorded(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    image_client = FakeImageGenerationClient()
    attempt, selection = start_attempt(session, world)

    completed = run_attempt(
        session,
        attempt,
        selection,
        markdown_store=MarkdownStore(worlds_root),
        planning_client=FakePromptPlanningClient(fail_with="the planner was unavailable"),
        image_client=image_client,
        asset_store=FilesystemAssetStore(assets_root),
        settings=SETTINGS,
        retry_policy=NO_RETRY,
    )

    assert completed.state is AttemptState.FAILED
    assert completed.failure_code is FailureCode.PLANNING_FAILED
    assert image_client.requests == []  # no image was ever requested


def test_a_provider_failure_creates_no_phantom_asset(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    failing = FakeImageGenerationClient(
        fail_with=ImageGenerationError("upstream exploded", FailureCode.PROVIDER_ERROR)
    )

    attempt = _generate(session, world, worlds_root, assets_root, image_client=failing)

    assert attempt.state is AttemptState.FAILED
    assert attempt.failure_code is FailureCode.PROVIDER_ERROR
    assert session.execute(select(ImageAsset)).scalars().all() == []


def test_a_failure_message_is_recorded(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    failing = FakeImageGenerationClient(
        fail_with=ImageGenerationError("the provider timed out", FailureCode.PROVIDER_TIMEOUT)
    )

    attempt = _generate(session, world, worlds_root, assets_root, image_client=failing)

    assert "timed out" in (attempt.failure_message or "")


def test_a_failed_attempt_frees_the_world(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    """Failure is terminal, so it must not occupy the world forever."""
    failing = FakeImageGenerationClient(
        fail_with=ImageGenerationError("nope", FailureCode.PROVIDER_ERROR)
    )
    _generate(session, world, worlds_root, assets_root, image_client=failing)

    second, _ = start_attempt(session, world)

    assert second.state is AttemptState.PLANNED


def test_undecodable_output_fails_rather_than_being_stored(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    class BadBytes(FakeImageGenerationClient):
        def generate(self, request):  # type: ignore[no-untyped-def]
            generated = super().generate(request)
            return type(generated)(
                data=b"not an image at all",
                mime_type="image/png",
                model=generated.model,
                size=generated.size,
                quality=generated.quality,
                output_format="png",
                provider_request_id=None,
            )

    attempt = _generate(session, world, worlds_root, assets_root, image_client=BadBytes())

    assert attempt.state is AttemptState.FAILED
    assert attempt.failure_code is FailureCode.INVALID_IMAGE
    assert session.execute(select(ImageAsset)).scalars().all() == []


def test_nothing_eligible_is_reported_before_anything_is_created(
    session: Session, world: World
) -> None:
    for shot in world.shots:
        shot.disabled = True
    session.flush()

    with pytest.raises(NothingToGenerate):
        start_attempt(session, world)

    assert session.execute(select(GenerationAttempt)).scalars().all() == []


# --- restart safety ----------------------------------------------------------------


def test_state_is_readable_without_the_objects_in_memory(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    """Every transition is committed, so nothing depends on in-memory state.

    A genuinely separate connection cannot be used here: these tests run inside a
    transaction that is rolled back afterwards. Clearing the identity map forces the
    values to come from the database rather than from the objects already loaded.
    """
    attempt_id = _generate(session, world, worlds_root, assets_root).id
    session.expunge_all()

    reloaded = session.execute(
        select(GenerationAttempt).where(GenerationAttempt.id == attempt_id)
    ).scalar_one()

    assert reloaded.state is AttemptState.GENERATED
    assert reloaded.production_prompt
    assert len(reloaded.assets) == 2
    assert reloaded.shot.external_id == "W01-011"


def test_the_stored_original_is_a_valid_image(
    session: Session, world: World, worlds_root: Path, assets_root: Path
) -> None:
    attempt = _generate(session, world, worlds_root, assets_root)
    original = next(a for a in attempt.assets if a.kind is AssetKind.ORIGINAL)

    data = FilesystemAssetStore(assets_root).load(original.relative_path)

    assert images.measure(data).width == 256
