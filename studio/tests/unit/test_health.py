"""The liveness endpoint."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app import __version__
from app.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client


def test_health_reports_the_process_is_alive(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__}


def test_health_does_not_touch_the_database(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Liveness must not depend on PostgreSQL, or a slow database looks like a dead process."""
    from app.db import session as db_session

    def fail(*args: object, **kwargs: object) -> object:
        raise AssertionError("/health must not open a database connection")

    monkeypatch.setattr(db_session, "get_engine", fail)
    monkeypatch.setattr(db_session, "get_session_factory", fail)

    assert client.get("/health").status_code == 200


def test_openapi_schema_is_generated(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "Shirtfaced Studio"
    assert "/health" in schema["paths"]
