"""The gate in front of every request.

Studio's generate endpoint bills OpenAI and Studio has no login of its own. It was
briefly reachable from the public internet with a live key behind it, so what this
covers is not hypothetical: with a secret configured, nothing gets through without
a session admin signed.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app
from app.security import SESSION_COOKIE
from tests.unit.test_security import ADMIN_ISSUED, SECRET, mint


@pytest.fixture
def protected(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """An application configured the way a deployment is."""
    base = get_settings()
    settings = Settings(
        **{**base.model_dump(), "session_secret": SECRET, "login_url": "https://admin.example/login"}
    )
    monkeypatch.setattr("app.main.get_settings", lambda: settings)
    with TestClient(create_app()) as client:
        yield client


def test_the_api_refuses_a_request_with_no_session(protected: TestClient) -> None:
    response = protected.get("/api/worlds")

    assert response.status_code == 401


def test_the_api_refuses_a_forged_session(protected: TestClient) -> None:
    """The signature is the only thing standing between a stranger and the key."""
    protected.cookies.set(SESSION_COOKIE, mint("admin@shirtfaced.wtf", 4102444800, secret="nope"))

    response = protected.get("/api/worlds")

    assert response.status_code == 401


def test_a_browser_is_sent_to_the_login_it_has(protected: TestClient) -> None:
    """Studio has no login page of its own to send anyone to."""
    response = protected.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].startswith("https://admin.example/login?next=")


def test_a_session_admin_issued_gets_through(protected: TestClient) -> None:
    """Checked against a route that needs no database, so this tests the gate
    and not the connection behind it."""
    protected.cookies.set(SESSION_COOKIE, ADMIN_ISSUED)

    response = protected.get("/openapi.json")

    assert response.status_code == 200


@pytest.mark.parametrize("path", ["/health", "/ready"])
def test_the_deploy_can_still_ask_whether_it_worked(protected: TestClient, path: str) -> None:
    """Locking these would leave a deploy unable to tell broken from protected."""
    response = protected.get(path)

    assert response.status_code != 401
    assert response.status_code != 307


def test_without_a_secret_nothing_is_checked() -> None:
    """Local development, where Studio is reachable from this machine alone.

    Pinned because it is the dangerous half of the behaviour: it must depend on
    the secret being absent, never on anything about the request.
    """
    with TestClient(create_app()) as client:
        assert client.get("/openapi.json").status_code == 200
