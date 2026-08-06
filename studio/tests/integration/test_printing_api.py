"""Placing a design on a photograph, and printing it.

Nothing here calls a model. The whole point of this feature is that moving a design
and looking again costs nothing, so these run against the real database and the real
compositor.
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
from app.services.print_service import designs_root
from app.services.world_importer import import_world
from tests.fixtures.worlds import write_world

pytestmark = pytest.mark.integration

VALID_URL = "postgresql+psycopg://app:secret@db.example:5432/shirtfaced_studio"
MIDDLE = [[0.25, 0.25], [0.75, 0.25], [0.75, 0.75], [0.25, 0.75]]


@pytest.fixture
def assets_root(tmp_path: Path) -> Path:
    root = tmp_path / "assets"
    designs_root(root).mkdir(parents=True)
    Image.new("RGBA", (40, 40), (255, 0, 0, 255)).save(designs_root(root) / "send-it.png")
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
def photo(session: Session, assets_root: Path) -> ImageAsset:
    """An approved attempt with a flat grey photograph behind it."""
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
    Image.new("RGB", (200, 200), (90, 90, 90)).save(path)

    asset = ImageAsset(
        attempt_id=attempt.id,
        kind=AssetKind.ORIGINAL,
        relative_path=relative,
        sha256="0" * 64,
        mime_type="image/png",
        width=200,
        height=200,
        byte_size=path.stat().st_size,
    )
    session.add(asset)
    session.flush()
    return asset


def test_designs_are_listed(client: TestClient) -> None:
    assert client.get("/api/designs").json() == [{"name": "send-it.png"}]


def test_only_approved_photographs_are_offered(client: TestClient, photo: ImageAsset) -> None:
    """A rejected frame is not something anybody is going to sell from."""
    photos = client.get("/api/worlds/world-01/photos").json()

    assert [item["asset_id"] for item in photos] == [str(photo.id)]
    assert photos[0]["placed"] is False


def test_a_photograph_starts_with_no_placement(client: TestClient, photo: ImageAsset) -> None:
    assert client.get(f"/api/photos/{photo.id}/placement").json() is None


def test_a_placement_is_kept_and_can_be_moved(client: TestClient, photo: ImageAsset) -> None:
    """Moving a design is an edit. The second placement replaces the first."""
    client.put(f"/api/photos/{photo.id}/placement", json={"corners": MIDDLE})

    moved = [[0.3, 0.4], [0.8, 0.4], [0.8, 0.9], [0.3, 0.9]]
    client.put(f"/api/photos/{photo.id}/placement", json={"corners": moved, "design": "send-it.png"})

    stored = client.get(f"/api/photos/{photo.id}/placement").json()
    assert stored["corners"] == moved
    assert stored["design"] == "send-it.png"
    assert client.get("/api/worlds/world-01/photos").json()[0]["placed"] is True


def test_a_corner_a_long_way_off_the_photograph_is_refused(
    client: TestClient, photo: ImageAsset
) -> None:
    """That is a dragging accident, not an intention."""
    response = client.put(
        f"/api/photos/{photo.id}/placement",
        json={"corners": [[0.0, 0.0], [9.0, 0.0], [9.0, 1.0], [0.0, 1.0]]},
    )

    assert response.status_code == 422


def test_printing_before_placing_says_so(client: TestClient, photo: ImageAsset) -> None:
    response = client.post(f"/api/photos/{photo.id}/print", params={"design": "send-it.png"})

    assert response.status_code == 422
    assert "where the design goes" in response.json()["detail"]


def test_printing_returns_the_photograph_with_the_design_on_it(
    client: TestClient, photo: ImageAsset
) -> None:
    client.put(f"/api/photos/{photo.id}/placement", json={"corners": MIDDLE})

    response = client.post(f"/api/photos/{photo.id}/print", params={"design": "send-it.png"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    printed = Image.open(io.BytesIO(response.content)).convert("RGB")
    assert printed.size == (200, 200)
    # Red in the middle where the design is, untouched grey in the corner.
    assert printed.getpixel((100, 100))[0] > 150
    assert printed.getpixel((5, 5)) == (90, 90, 90)


def test_a_design_that_is_not_there_is_a_404(client: TestClient, photo: ImageAsset) -> None:
    client.put(f"/api/photos/{photo.id}/placement", json={"corners": MIDDLE})

    response = client.post(f"/api/photos/{photo.id}/print", params={"design": "nope.png"})

    assert response.status_code == 404


def test_a_render_is_never_cached(client: TestClient, photo: ImageAsset) -> None:
    """The next render is meant to be different; a cached one hides the change."""
    client.put(f"/api/photos/{photo.id}/placement", json={"corners": MIDDLE})

    response = client.post(f"/api/photos/{photo.id}/print", params={"design": "send-it.png"})

    assert response.headers["cache-control"] == "no-store"
