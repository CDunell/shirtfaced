"""The read-only world endpoints, against PostgreSQL."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.adapters.markdown_store import MarkdownStore
from app.db.session import get_db_session
from app.main import create_app
from app.services.world_importer import import_world
from tests.fixtures.worlds import write_world

pytestmark = pytest.mark.integration


@pytest.fixture
def client(session: Session, tmp_path: Path) -> Iterator[TestClient]:
    """A client whose requests share the test transaction, so nothing is committed."""
    write_world(tmp_path)
    import_world(session, MarkdownStore(tmp_path), "world-01")
    session.flush()

    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session

    with TestClient(application) as test_client:
        yield test_client

    application.dependency_overrides.clear()


def test_lists_worlds(client: TestClient) -> None:
    response = client.get("/api/worlds")

    assert response.status_code == 200
    payload = response.json()
    assert [world["slug"] for world in payload] == ["world-01"]
    assert payload[0]["status"] == "active"


def test_returns_world_detail_with_its_shots(client: TestClient) -> None:
    response = client.get("/api/worlds/world-01")

    assert response.status_code == 200
    payload = response.json()
    assert payload["slug"] == "world-01"
    assert [shot["external_id"] for shot in payload["shots"]] == [
        "W01-001",
        "W01-008",
        "W01-011",
        "W01-012",
    ]


def test_reports_shot_counts(client: TestClient) -> None:
    payload = client.get("/api/worlds/world-01").json()

    assert payload["counts"] == {
        "total": 4,
        "planned": 2,
        "in_progress": 0,
        "approved": 1,
        "rejected": 1,
        "abandoned": 0,
    }


def test_reports_the_next_planned_shot(client: TestClient) -> None:
    payload = client.get("/api/worlds/world-01").json()

    assert payload["next_planned_shot"]["external_id"] == "W01-011"


def test_exposes_the_document_hashes(client: TestClient) -> None:
    """The world page shows which version of the canon is loaded."""
    payload = client.get("/api/worlds/world-01").json()

    assert len(payload["world_document_hash"]) == 64
    assert len(payload["shotlist_document_hash"]) == 64


def test_an_unknown_world_returns_404_with_guidance(client: TestClient) -> None:
    response = client.get("/api/worlds/world-99")

    assert response.status_code == 404
    assert "import-world" in response.json()["detail"]


@pytest.mark.parametrize("slug", ["..etc", ".hidden", "world-01.bak"])
def test_a_path_like_slug_is_only_ever_a_database_lookup(client: TestClient, slug: str) -> None:
    """This endpoint never resolves a path.

    Filesystem traversal is the Markdown store's responsibility and is covered by
    tests/unit/test_markdown_store.py; here a path-shaped slug is simply not a world.
    """
    response = client.get(f"/api/worlds/{slug}")

    assert response.status_code == 404
