"""The photograph library over HTTP.

Nothing here calls a model. Frames are generated elsewhere and brought back, so
what these cover is bringing one in, listing it once rather than twice, and
remembering which prompt it came from.

This file used to cover placing a design on a photograph by dragged corners and
printing it. That path was removed on 15 August 2026 -- see
``app/routes/printing.py`` -- and its tests went with it.
"""

from __future__ import annotations

import io
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.adapters.markdown_store import MarkdownStore
from app.config import Settings, get_settings
from app.db.models import GenerationAttempt, ImageAsset, Shot
from app.db.session import get_db_session
from app.domain.enums import AssetKind, AttemptState
from app.main import create_app
from app.services.world_importer import import_world
from tests.fixtures.worlds import write_world

pytestmark = pytest.mark.integration

VALID_URL = "postgresql+psycopg://app:secret@db.example:5432/shirtfaced_studio"


def grey_png(size: tuple[int, int] = (200, 200)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (90, 90, 90)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def assets_root(tmp_path: Path) -> Path:
    root = tmp_path / "assets"
    root.mkdir(parents=True)
    return root


@pytest.fixture
def client(session: Session, tmp_path: Path, assets_root: Path) -> Iterator[TestClient]:
    worlds_root = tmp_path / "worlds"
    worlds_root.mkdir()
    write_world(worlds_root)
    import_world(session, MarkdownStore(worlds_root), "world-01")
    session.flush()

    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=VALID_URL,
        db_sslmode="disable",
        worlds_root=worlds_root,
        assets_root=assets_root,
        debug=True,
    )

    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_settings] = lambda: settings

    with TestClient(application) as test_client:
        yield test_client

    application.dependency_overrides.clear()


@pytest.fixture
def approved(session: Session, assets_root: Path) -> None:
    """One approved attempt with a flat grey photograph behind it."""
    shot = session.query(Shot).order_by(Shot.sequence).first()
    assert shot is not None

    attempt = GenerationAttempt(
        shot_id=shot.id,
        world_id=shot.world_id,
        attempt_number=1,
        state=AttemptState.APPROVED,
    )
    session.add(attempt)
    session.flush()

    relative = f"worlds/world-01/attempts/{attempt.id}/original.png"
    path = assets_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(grey_png())

    session.add(
        ImageAsset(
            attempt_id=attempt.id,
            kind=AssetKind.ORIGINAL,
            relative_path=relative,
            sha256="0" * 64,
            mime_type="image/png",
            width=200,
            height=200,
            byte_size=path.stat().st_size,
        )
    )
    session.flush()


def upload(client: TestClient, name: str = "kitchen.png", data: bytes | None = None):  # type: ignore[no-untyped-def]
    return client.post(
        "/api/photos", files={"file": (name, data if data is not None else grey_png(), "image/png")}
    )


def test_the_library_starts_empty(client: TestClient) -> None:
    """A fresh deployment has approved nothing, which is why upload exists."""
    assert client.get("/api/photos").json() == []


def test_an_uploaded_photograph_joins_the_library(client: TestClient) -> None:
    created = upload(client)

    assert created.status_code == 201
    body = created.json()
    assert body["uploaded"] is True
    assert body["label"] == "kitchen.png"
    assert (body["width"], body["height"]) == (200, 200)
    assert [item["id"] for item in client.get("/api/photos").json()] == [body["id"]]


def test_an_uploaded_photograph_can_be_fetched_back(client: TestClient) -> None:
    photo_id = upload(client).json()["id"]

    response = client.get(f"/api/photos/{photo_id}/image")

    assert response.status_code == 200
    assert Image.open(io.BytesIO(response.content)).size == (200, 200)


def test_a_file_that_is_not_an_image_is_refused(client: TestClient) -> None:
    response = upload(client, name="notes.txt", data=b"this is not a photograph")

    assert response.status_code == 422
    assert client.get("/api/photos").json() == [], "rubbish was stored anyway"


def test_approved_frames_are_in_the_library_too(client: TestClient, approved: None) -> None:
    photos = client.get("/api/photos").json()

    assert len(photos) == 1
    assert photos[0]["uploaded"] is False


def test_listing_twice_does_not_duplicate_a_frame(client: TestClient, approved: None) -> None:
    """Registration happens on first sight, so the list must be idempotent."""
    client.get("/api/photos")

    assert len(client.get("/api/photos").json()) == 1


def test_uploads_are_listed_whatever_world_is_asked_for(client: TestClient) -> None:
    """A photograph off a phone is not part of a shotlist."""
    upload(client)

    assert len(client.get("/api/photos", params={"world": "world-01"}).json()) == 1


def test_a_photograph_remembers_the_prompt_that_made_it(client: TestClient) -> None:
    """The join the whole feature exists for.

    The frames are generated elsewhere from a prompt written here and brought back,
    so the upload is the only moment anybody knows which prompt made which picture.
    """
    prompt = client.post("/api/worlds/world-01/prompts", params={"shot": "W01-001"}).json()

    created = client.post(
        "/api/photos",
        files={"file": ("frame.png", grey_png(), "image/png")},
        data={"prompt_variation_id": prompt["id"]},
    )

    assert created.status_code == 201
    assert created.json()["from_prompt"] == {"shot_external_id": "W01-001", "variation": 1}
    # And it survives into the library, which is where it gets read.
    assert client.get("/api/photos").json()[0]["from_prompt"]["variation"] == 1


def test_a_photograph_with_no_prompt_behind_it_is_fine(client: TestClient) -> None:
    """Not every photograph came from a prompt written here."""
    assert upload(client).json()["from_prompt"] is None


def test_a_photograph_cannot_be_attributed_to_a_prompt_that_does_not_exist(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/photos",
        files={"file": ("frame.png", grey_png(), "image/png")},
        data={"prompt_variation_id": "0f7f3f9c-0000-4000-8000-000000000000"},
    )

    assert response.status_code == 404
    assert client.get("/api/photos").json() == [], "the photograph was stored anyway"
