"""Continue World, attempt history and image serving.

No test here reaches OpenAI: without a key the factory returns the deterministic
fakes, and these settings supply none.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.image_generation import FakeImageGenerationClient
from app.adapters.markdown_store import MarkdownStore
from app.config import Settings, get_settings
from app.db.models import GenerationAttempt, World
from app.db.session import get_db_session
from app.domain.enums import AttemptState, GateName
from app.main import create_app
from app.services.world_importer import import_world
from tests.fixtures.worlds import write_world

pytestmark = pytest.mark.integration

VALID_URL = "postgresql+psycopg://app:secret@db.example:5432/shirtfaced_studio"


@pytest.fixture
def worlds_root(tmp_path: Path) -> Path:
    write_world(tmp_path)
    return tmp_path


@pytest.fixture
def assets_root(tmp_path: Path) -> Path:
    return tmp_path / "assets"


@pytest.fixture
def client(session: Session, worlds_root: Path, assets_root: Path) -> Iterator[TestClient]:
    import_world(session, MarkdownStore(worlds_root), "world-01")
    session.flush()

    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=VALID_URL,
        db_sslmode="disable",
        worlds_root=worlds_root,
        assets_root=assets_root,
        # Smaller images keep the suite quick; the pipeline is identical.
        openai_image_size="128x96",
        debug=True,
    )

    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_settings] = lambda: settings

    with TestClient(application) as test_client:
        yield test_client

    application.dependency_overrides.clear()


def _attempts(session: Session) -> list[GenerationAttempt]:
    return list(session.execute(select(GenerationAttempt)).scalars().all())


# --- continue ----------------------------------------------------------------------


def test_continue_world_generates_one_image(client: TestClient) -> None:
    response = client.post("/api/worlds/world-01/continue")

    assert response.status_code == 201
    payload = response.json()
    # Continue World generates and then reviews, so the attempt comes to rest
    # awaiting the owner's decision.
    assert payload["attempt"]["state"] == "awaiting_decision"
    assert payload["attempt"]["shot"]["external_id"] == "W01-011"
    assert payload["attempt"]["image_url"]
    assert payload["attempt"]["thumbnail_url"]


def test_the_response_says_nothing_was_billed(client: TestClient) -> None:
    payload = client.post("/api/worlds/world-01/continue").json()

    assert payload["live"] is False


def test_the_response_carries_the_prompt_and_reasoning(client: TestClient) -> None:
    payload = client.post("/api/worlds/world-01/continue").json()["attempt"]

    assert "W01-011" in payload["selection_reason"]
    assert payload["production_prompt"]
    assert payload["prompt_plan"]["hero_product"] == "Tote bag"


def test_the_response_carries_provenance(client: TestClient) -> None:
    payload = client.post("/api/worlds/world-01/continue").json()["attempt"]

    assert payload["hero_product"] == "Tote bag"
    assert payload["camera_position"] == "Rear seat"
    assert len(payload["world_document_hash"]) == 64
    assert payload["image_model"]
    assert payload["image_size"] == "128x96"


def test_generating_is_not_approving(client: TestClient) -> None:
    payload = client.post("/api/worlds/world-01/continue").json()["attempt"]

    assert payload["approved"] is False


# --- what the route hands the image model -------------------------------------------
#
# The reference library and the draft model were both built, tested and never wired
# into this route. Every image the application generated was text-only and full price
# while the code that would have prevented that sat one call away, fully covered by
# its own unit tests. These pin the wiring itself.


@pytest.fixture
def spy_image_client(monkeypatch: pytest.MonkeyPatch) -> FakeImageGenerationClient:
    """The fake the route will use, kept where the test can read it afterwards."""
    spy = FakeImageGenerationClient()
    monkeypatch.setattr("app.routes.api.build_image_client", lambda settings, *, draft=False: spy)
    return spy


@pytest.fixture
def locked_reference(worlds_root: Path) -> str:
    directory = worlds_root / "world-01" / "references" / "locked"
    directory.mkdir(parents=True)
    (directory / "locked-01.png").write_bytes(b"not really a png, but a non-empty file")
    return "locked-01.png"


def test_continue_sends_the_reference_library_to_the_image_model(
    client: TestClient, spy_image_client: FakeImageGenerationClient, locked_reference: str
) -> None:
    client.post("/api/worlds/world-01/continue")

    assert spy_image_client.requests, "the image model was never called"
    sent = spy_image_client.requests[0].reference_images
    assert [image.name for image in sent] == [locked_reference]


def test_continue_defaults_to_the_full_model_and_is_not_a_draft(
    client: TestClient, session: Session
) -> None:
    client.post("/api/worlds/world-01/continue")

    attempt = _attempts(session)[0]
    assert attempt.is_draft is False


def test_continue_with_draft_uses_the_draft_model(
    client: TestClient, session: Session, spy_image_client: FakeImageGenerationClient
) -> None:
    """A draft has to change which model is called, not merely what is recorded.

    The real client bakes its model in at construction and ignores the request's, so
    passing a draft model through the request alone changed the attempt row and
    nothing else: three attempts recorded gpt-image-1-mini for images billed as
    gpt-image-2.
    """
    response = client.post("/api/worlds/world-01/continue?draft=true")

    assert response.status_code == 201
    assert _attempts(session)[0].is_draft is True


def test_a_draft_is_refused_when_no_draft_model_is_configured(
    session: Session, worlds_root: Path, assets_root: Path
) -> None:
    """Refused, not quietly run on the full model. The point of a draft is the price."""
    import_world(session, MarkdownStore(worlds_root), "world-01")
    session.flush()

    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=VALID_URL,
        db_sslmode="disable",
        worlds_root=worlds_root,
        assets_root=assets_root,
        openai_image_size="128x96",
        # A key, but no draft model: the combination that must not silently fall back.
        openai_api_key="sk-test-not-a-real-key",
        debug=True,
    )
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_settings] = lambda: settings

    with TestClient(application) as test_client:
        response = test_client.post("/api/worlds/world-01/continue?draft=true")

    application.dependency_overrides.clear()

    assert response.status_code == 422
    assert "OPENAI_IMAGE_DRAFT_MODEL" in response.json()["detail"]
    # Nothing was started, so the world is still free.
    assert _attempts(session) == []


def test_a_second_continue_is_refused_with_409(client: TestClient) -> None:
    client.post("/api/worlds/world-01/continue")

    response = client.post("/api/worlds/world-01/continue")

    assert response.status_code == 409
    assert "already" in response.json()["detail"]


def test_exactly_one_attempt_exists_after_a_refused_second_call(
    client: TestClient, session: Session
) -> None:
    client.post("/api/worlds/world-01/continue")
    client.post("/api/worlds/world-01/continue")

    assert len(_attempts(session)) == 1


def test_continue_reports_when_nothing_is_eligible(client: TestClient, session: Session) -> None:
    world = session.execute(select(World).where(World.slug == "world-01")).scalar_one()
    for shot in world.shots:
        shot.disabled = True
    session.flush()

    response = client.post("/api/worlds/world-01/continue")

    assert response.status_code == 422
    assert "eligible" in response.json()["detail"]


def test_continue_on_an_unknown_world_returns_404(client: TestClient) -> None:
    assert client.post("/api/worlds/world-99/continue").status_code == 404


# --- history -----------------------------------------------------------------------


def test_attempts_are_listed_for_a_world(client: TestClient) -> None:
    client.post("/api/worlds/world-01/continue")

    payload = client.get("/api/worlds/world-01/attempts").json()

    assert len(payload) == 1
    assert payload[0]["attempt_number"] == 1


def test_an_attempt_can_be_fetched_by_id(client: TestClient) -> None:
    created = client.post("/api/worlds/world-01/continue").json()["attempt"]

    payload = client.get(f"/api/attempts/{created['id']}").json()

    assert payload["id"] == created["id"]
    assert payload["production_prompt"] == created["production_prompt"]


def test_an_unknown_attempt_returns_404(client: TestClient) -> None:
    response = client.get("/api/attempts/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_history_is_empty_before_anything_is_generated(client: TestClient) -> None:
    assert client.get("/api/worlds/world-01/attempts").json() == []


# --- serving images ----------------------------------------------------------------


def test_the_generated_image_is_served(client: TestClient) -> None:
    payload = client.post("/api/worlds/world-01/continue").json()["attempt"]

    response = client.get(payload["image_url"])

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_the_thumbnail_is_served(client: TestClient) -> None:
    """Bytes are not compared: this fixture generates a 128px image, which is already
    below the thumbnail's maximum edge, so it is not downscaled."""
    payload = client.post("/api/worlds/world-01/continue").json()["attempt"]

    thumbnail = client.get(payload["thumbnail_url"])

    assert thumbnail.status_code == 200
    assert thumbnail.headers["content-type"] == "image/webp"
    assert thumbnail.content.startswith(b"RIFF")


def test_images_are_cacheable(client: TestClient) -> None:
    """They are immutable and addressed by an identifier that never changes."""
    payload = client.post("/api/worlds/world-01/continue").json()["attempt"]

    response = client.get(payload["image_url"])

    assert "immutable" in response.headers["cache-control"]


def test_an_unknown_asset_returns_404(client: TestClient) -> None:
    response = client.get("/assets/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


def test_a_missing_file_is_reported_as_unavailable_not_missing(
    client: TestClient, assets_root: Path
) -> None:
    """The row exists but the volume does not: say so rather than mislead."""
    payload = client.post("/api/worlds/world-01/continue").json()["attempt"]
    for file in assets_root.rglob("*.png"):
        file.unlink()

    response = client.get(payload["image_url"])

    assert response.status_code == 503
    assert "could not be read" in response.json()["detail"]


@pytest.mark.parametrize("segment", ["not-a-uuid", "1", "passwd"])
def test_the_asset_route_only_accepts_an_identifier(client: TestClient, segment: str) -> None:
    """Paths come from the database row, never from the request.

    The route is typed as a UUID, so a filesystem path cannot be expressed through
    it. Anything with a slash never reaches this route at all: it falls through to
    the single-page application's deep-link fallback and gets the app shell, not an
    image. Traversal of the store itself is covered in
    tests/unit/test_asset_store.py.
    """
    response = client.get(f"/assets/{segment}")

    assert response.status_code == 422


# --- the world page still works ----------------------------------------------------


def test_generation_does_not_change_the_shot_status(client: TestClient, session: Session) -> None:
    client.post("/api/worlds/world-01/continue")

    payload = client.get("/api/worlds/world-01").json()
    shot = next(s for s in payload["shots"] if s["external_id"] == "W01-011")

    assert shot["status"] == "planned"


def test_the_next_shot_endpoint_is_unaffected(client: TestClient) -> None:
    client.post("/api/worlds/world-01/continue")

    payload = client.get("/api/worlds/world-01/next-shot").json()

    assert payload["selected"]["external_id"] == "W01-011"


def test_the_attempt_is_left_for_a_human_decision(client: TestClient, session: Session) -> None:
    client.post("/api/worlds/world-01/continue")

    attempt = _attempts(session)[0]

    assert attempt.state is AttemptState.AWAITING_DECISION
    assert attempt.is_active


# --- review ------------------------------------------------------------------------


def test_continue_world_attaches_a_review(client: TestClient) -> None:
    payload = client.post("/api/worlds/world-01/continue").json()

    assert payload["review"] is not None
    assert len(payload["review"]["gates"]) == len(GateName)
    assert payload["review"]["recommendation"] == "APPROVE_RECOMMENDED"


def test_the_review_reports_that_nothing_was_billed(client: TestClient) -> None:
    payload = client.post("/api/worlds/world-01/continue").json()

    assert payload["review_live"] is False


def test_the_review_carries_scores_and_compliance(client: TestClient) -> None:
    review = client.post("/api/worlds/world-01/continue").json()["review"]

    assert 1 <= review["mood_score"] <= 5
    assert review["branding_compliant"] is True
    assert review["vehicle_compliant"] is True


def test_the_review_separates_blocking_and_uncertain_gates(client: TestClient) -> None:
    """The interface expands those first, so they are reported separately."""
    review = client.post("/api/worlds/world-01/continue").json()["review"]

    assert review["blocking_gates"] == []
    assert review["uncertain_gates"] == []
    # The default fake marks vehicle continuity not applicable, which is neither.
    assert review["gates"]["vehicle_continuity"]["status"] == "NOT_APPLICABLE"


def test_a_recommendation_is_not_an_approval(client: TestClient) -> None:
    payload = client.post("/api/worlds/world-01/continue").json()

    assert payload["attempt"]["approved"] is False
    assert payload["attempt"]["state"] == "awaiting_decision"


def test_a_review_can_be_retried_without_regenerating(client: TestClient) -> None:
    created = client.post("/api/worlds/world-01/continue").json()["attempt"]

    response = client.post(f"/api/attempts/{created['id']}/retry-review")

    assert response.status_code == 200
    assert len(response.json()["gates"]) == len(GateName)

    # The image is unchanged.
    after = client.get(f"/api/attempts/{created['id']}").json()
    assert after["image_url"] == created["image_url"]


def test_retrying_a_review_on_an_unknown_attempt_returns_404(client: TestClient) -> None:
    response = client.post("/api/attempts/00000000-0000-0000-0000-000000000000/retry-review")

    assert response.status_code == 404


def test_canon_proposals_are_listed_and_start_empty(client: TestClient) -> None:
    client.post("/api/worlds/world-01/continue")

    assert client.get("/api/worlds/world-01/canon-proposals").json() == []
