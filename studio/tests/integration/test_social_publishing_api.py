"""The persistent Social Studio path from review package to fake publication."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import Photo
from app.db.session import get_db_session
from app.main import create_app

pytestmark = pytest.mark.integration
VALID_URL = "postgresql+psycopg://app:secret@db.example:5432/shirtfaced_studio"


@pytest.fixture
def client(session: Session, tmp_path: Path) -> Iterator[TestClient]:
    assets_root = tmp_path / "assets"
    assets_root.mkdir()
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=VALID_URL,
        db_sslmode="disable",
        assets_root=assets_root,
        debug=True,
    )
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: session
    application.dependency_overrides[get_settings] = lambda: settings
    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()


def test_review_queue_and_fake_publish_are_durable_and_idempotent(
    client: TestClient, session: Session
) -> None:
    photo = Photo(
        relative_path="uploads/source.jpg",
        label="Friday servo",
        mime_type="image/jpeg",
        width=1600,
        height=2000,
    )
    session.add(photo)
    session.flush()

    metadata = [
        {
            "output_key": "instagram_feed",
            "width": 1080,
            "height": 1350,
            "filename": "SF_FRIDAY-SERVO_IG-FEED.jpg",
        }
    ]
    created = client.post(
        "/api/social/posts",
        data={
            "source_photo_id": str(photo.id),
            "theme": "adaptive",
            "branding": "fingerprint",
            "caption": "",
            "derivative_metadata": json.dumps(metadata),
        },
        files={"files": ("feed.jpg", b"exact-social-derivative", "image/jpeg")},
    )
    assert created.status_code == 201, created.text
    package = created.json()
    assert package["state"] == "review_required"
    assert package["source_label"] == "Friday servo"
    assert len(package["derivatives"]) == 1
    derivative = package["derivatives"][0]

    downloaded = client.get(derivative["url"])
    assert downloaded.status_code == 200
    assert downloaded.content == b"exact-social-derivative"

    approved = client.post(f"/api/social/posts/{package['id']}/approve", json={})
    assert approved.status_code == 200
    assert approved.json()["state"] == "approved"

    queued = client.post(
        f"/api/social/posts/{package['id']}/queue",
        json={"timezone": "Australia/Brisbane", "scheduled_at": None},
    )
    assert queued.status_code == 200, queued.text
    jobs = queued.json()
    assert len(jobs) == 1
    assert jobs[0]["state"] == "scheduled"
    assert jobs[0]["locked"] is False
    assert jobs[0]["recommended_at"] is not None
    job_id = jobs[0]["id"]

    first = client.post(f"/api/social/jobs/{job_id}/publish-now", json={})
    second = client.post(f"/api/social/jobs/{job_id}/publish-now", json={})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["state"] == "published"
    assert first.json()["external_post_id"] == second.json()["external_post_id"]

    live = client.get("/api/social/live")
    assert live.status_code == 200
    assert [item["id"] for item in live.json()] == [job_id]

    persisted = client.get("/api/social/posts?state=live")
    assert persisted.status_code == 200
    assert [item["id"] for item in persisted.json()] == [package["id"]]
