"""Selection endpoints, against PostgreSQL.

No test here reaches OpenAI: without a key and a model the factory returns the
deterministic fake, and these settings supply neither.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.markdown_store import MarkdownStore
from app.config import Settings, get_settings
from app.db.models import Shot, World
from app.db.session import get_db_session
from app.domain.enums import ShotStatus
from app.main import create_app
from app.services.world_importer import import_world
from tests.fixtures.worlds import write_world

pytestmark = pytest.mark.integration

VALID_URL = "postgresql+psycopg://app:secret@db.example:5432/shirtfaced_studio"


def _settings(worlds_root: Path, *, debug: bool) -> Settings:
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=VALID_URL,
        db_sslmode="disable",
        worlds_root=worlds_root,
        debug=debug,
    )


def _client(session: Session, worlds_root: Path, *, debug: bool) -> TestClient:
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_settings] = lambda: _settings(worlds_root, debug=debug)
    return TestClient(application)


@pytest.fixture
def worlds_root(tmp_path: Path) -> Path:
    write_world(tmp_path)
    return tmp_path


@pytest.fixture
def imported(session: Session, worlds_root: Path) -> Session:
    import_world(session, MarkdownStore(worlds_root), "world-01")
    session.flush()
    return session


@pytest.fixture
def client(imported: Session, worlds_root: Path) -> Iterator[TestClient]:
    with _client(imported, worlds_root, debug=True) as test_client:
        yield test_client


def _shots(session: Session) -> dict[str, Shot]:
    world = session.execute(select(World).where(World.slug == "world-01")).scalar_one()
    rows = session.execute(select(Shot).where(Shot.world_id == world.id)).scalars().all()
    return {shot.external_id: shot for shot in rows}


# --- next-shot ---------------------------------------------------------------------


def test_selects_the_next_shot_and_explains_why(client: TestClient) -> None:
    payload = client.get("/api/worlds/world-01/next-shot").json()

    assert payload["selected"]["external_id"] == "W01-011"
    assert "W01-011" in payload["reason"]
    assert payload["eligible_count"] == 2


def test_reports_the_shots_it_set_aside(client: TestClient) -> None:
    payload = client.get("/api/worlds/world-01/next-shot").json()

    reasons = {entry["external_id"]: entry["reason"] for entry in payload["set_aside"]}
    assert reasons["W01-001"] == "already approved"
    assert "rejected" in reasons["W01-008"]


def test_reports_the_rotation_it_used(client: TestClient) -> None:
    payload = client.get("/api/worlds/world-01/next-shot").json()

    assert payload["last_hero_product"] == "T-shirt"


def test_selection_costs_nothing_and_is_repeatable(client: TestClient) -> None:
    first = client.get("/api/worlds/world-01/next-shot").json()
    second = client.get("/api/worlds/world-01/next-shot").json()

    assert first == second


def test_a_disabled_shot_is_skipped(client: TestClient, imported: Session) -> None:
    _shots(imported)["W01-011"].disabled = True
    imported.flush()

    payload = client.get("/api/worlds/world-01/next-shot").json()

    assert payload["selected"]["external_id"] == "W01-012"


def test_reports_when_nothing_remains(client: TestClient, imported: Session) -> None:
    for external_id in ("W01-011", "W01-012"):
        _shots(imported)[external_id].status = ShotStatus.ABANDONED
    imported.flush()

    payload = client.get("/api/worlds/world-01/next-shot").json()

    assert payload["selected"] is None
    assert "No planned shot is eligible" in payload["reason"]


def test_an_unknown_world_returns_404(client: TestClient) -> None:
    assert client.get("/api/worlds/world-99/next-shot").status_code == 404
