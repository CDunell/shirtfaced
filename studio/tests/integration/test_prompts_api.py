"""Prompts are kept, and a shot accumulates them.

Writing a prompt used to record nothing, so asking a second time replaced the
first and there was nothing to compare a variation against. These pin the
behaviour that replaced it.

No test here reaches OpenAI: without a key the factory returns the deterministic
fakes, and these settings supply none.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.adapters.markdown_store import MarkdownStore
from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.main import create_app
from app.services.world_importer import import_world
from tests.fixtures.worlds import write_world

pytestmark = pytest.mark.integration

VALID_URL = "postgresql+psycopg://app:secret@db.example:5432/shirtfaced_studio"


@pytest.fixture
def client(session: Session, tmp_path: Path) -> Iterator[TestClient]:
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
        assets_root=tmp_path / "assets",
        debug=True,
    )

    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_settings] = lambda: settings

    with TestClient(application) as test_client:
        yield test_client

    application.dependency_overrides.clear()


def test_a_shot_with_no_prompts_yet_is_not_an_error(client: TestClient) -> None:
    """An empty history is a fact about the shot, not a failure to find it."""
    response = client.get("/api/worlds/world-01/prompts", params={"shot": "W01-001"})

    assert response.status_code == 200
    assert response.json()["variations"] == []


def test_a_shot_that_does_not_exist_is_a_404(client: TestClient) -> None:
    response = client.get("/api/worlds/world-01/prompts", params={"shot": "W01-999"})

    assert response.status_code == 404


def test_the_first_prompt_written_is_variation_one(client: TestClient) -> None:
    response = client.post("/api/worlds/world-01/prompts", params={"shot": "W01-001"})

    assert response.status_code == 200
    assert response.json()["variation"] == 1


def test_writing_again_adds_a_variation_rather_than_replacing(client: TestClient) -> None:
    """The whole point: the earlier prompt is still there to compare against."""
    first = client.post("/api/worlds/world-01/prompts", params={"shot": "W01-001"}).json()
    second = client.post("/api/worlds/world-01/prompts", params={"shot": "W01-001"}).json()

    assert [first["variation"], second["variation"]] == [1, 2]

    history = client.get("/api/worlds/world-01/prompts", params={"shot": "W01-001"}).json()

    # Newest first: the reason for opening the page is usually the last one written.
    assert [item["variation"] for item in history["variations"]] == [2, 1]
    assert history["variations"][1]["image_prompt"] == first["image_prompt"]


def test_a_written_prompt_survives_a_rollback(client: TestClient, session: Session) -> None:
    """It has to be committed, not merely flushed.

    Every other test here shares one session with the application, so a flush that
    is never committed looks exactly like a write -- and loses every prompt the
    moment a real request closes its session. Rolling back can only remove work
    that was not committed.
    """
    client.post("/api/worlds/world-01/prompts", params={"shot": "W01-001"})

    session.rollback()

    history = client.get("/api/worlds/world-01/prompts", params={"shot": "W01-001"}).json()
    assert [item["variation"] for item in history["variations"]] == [1]


def test_numbering_is_per_shot(client: TestClient) -> None:
    """Two scenes each start at one; they do not share a counter."""
    client.post("/api/worlds/world-01/prompts", params={"shot": "W01-001"})
    other = client.post("/api/worlds/world-01/prompts", params={"shot": "W01-011"})

    assert other.status_code == 200
    assert other.json()["variation"] == 1


def test_the_history_carries_what_a_variation_needs_to_be_read(client: TestClient) -> None:
    client.post("/api/worlds/world-01/prompts", params={"shot": "W01-001"})

    only = client.get("/api/worlds/world-01/prompts", params={"shot": "W01-001"}).json()[
        "variations"
    ][0]

    assert only["image_prompt"]
    assert only["video_prompt"]
    assert only["written_at"]
    # Written by the fake, so nothing was billed. A fake prompt reads like a real
    # one, which is exactly why the flag has to survive into the history.
    assert only["live"] is False
