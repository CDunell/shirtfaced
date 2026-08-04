"""Importing worlds into PostgreSQL."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.markdown_store import MarkdownStore
from app.db.models import Shot, World
from app.domain.enums import ShotStatus
from app.services.world_importer import import_world
from tests.fixtures.worlds import VALID_SHOTLIST, write_world

pytestmark = pytest.mark.integration


@pytest.fixture
def store(tmp_path: Path) -> MarkdownStore:
    write_world(tmp_path)
    return MarkdownStore(tmp_path)


def _shots(session: Session, world: World) -> dict[str, Shot]:
    rows = session.execute(select(Shot).where(Shot.world_id == world.id)).scalars().all()
    return {shot.external_id: shot for shot in rows}


def _world(session: Session, slug: str = "world-01") -> World:
    return session.execute(select(World).where(World.slug == slug)).scalar_one()


def test_creates_the_world_and_its_shots(session: Session, store: MarkdownStore) -> None:
    report = import_world(session, store, "world-01")

    assert report.world_created is True
    assert report.shots_created == 4

    world = _world(session)
    assert world.name.startswith("SHIRTFACED")
    assert len(_shots(session, world)) == 4


def test_records_the_document_hashes(session: Session, store: MarkdownStore) -> None:
    import_world(session, store, "world-01")

    world = _world(session)
    assert world.world_document_hash is not None
    assert world.continuity_document_hash is not None
    assert world.shotlist_document_hash is not None
    assert (
        len(
            {
                world.world_document_hash,
                world.continuity_document_hash,
                world.shotlist_document_hash,
            }
        )
        == 3
    )


def test_import_is_idempotent(session: Session, store: MarkdownStore) -> None:
    import_world(session, store, "world-01")
    session.flush()

    second = import_world(session, store, "world-01")

    assert second.world_created is False
    assert second.shots_created == 0
    assert second.shots_updated == 0
    assert second.shots_unchanged == 4
    assert len(_shots(session, _world(session))) == 4


def test_an_edited_shot_is_updated_not_duplicated(
    session: Session, store: MarkdownStore, tmp_path: Path
) -> None:
    import_world(session, store, "world-01")
    session.flush()

    write_world(
        tmp_path,
        shotlist=VALID_SHOTLIST.replace("Car interior transition", "Car interior handover"),
    )
    report = import_world(session, store, "world-01")

    assert report.shots_updated == 1
    shots = _shots(session, _world(session))
    assert len(shots) == 4
    assert shots["W01-011"].title == "Car interior handover"


def test_a_changed_document_is_reported(
    session: Session, store: MarkdownStore, tmp_path: Path
) -> None:
    import_world(session, store, "world-01")
    session.flush()

    write_world(tmp_path, shotlist=VALID_SHOTLIST + "\nAn added note.\n")
    report = import_world(session, store, "world-01")

    assert "SHOTLIST.md" in report.documents_changed


def test_a_workflow_decision_is_not_overwritten_by_the_markdown(
    session: Session, store: MarkdownStore
) -> None:
    """The database records what actually happened; the Markdown is advisory."""
    import_world(session, store, "world-01")
    session.flush()

    shot = _shots(session, _world(session))["W01-011"]
    shot.status = ShotStatus.APPROVED
    session.flush()

    report = import_world(session, store, "world-01")

    assert _shots(session, _world(session))["W01-011"].status is ShotStatus.APPROVED
    assert any("W01-011" in conflict for conflict in report.status_conflicts)


def test_a_planned_shot_still_follows_the_markdown(
    session: Session, store: MarkdownStore, tmp_path: Path
) -> None:
    import_world(session, store, "world-01")
    session.flush()

    write_world(
        tmp_path,
        shotlist=VALID_SHOTLIST.replace("Rear seat           ⬜", "Rear seat           🟡"),
    )
    import_world(session, store, "world-01")

    assert _shots(session, _world(session))["W01-011"].status is ShotStatus.IN_PROGRESS


def test_shot_ids_are_unique_per_world(session: Session, store: MarkdownStore) -> None:
    import_world(session, store, "world-01")
    session.flush()
    world = _world(session)

    session.add(Shot(world_id=world.id, external_id="W01-011", sequence=99, title="Duplicate"))

    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        session.flush()


def test_deleting_a_world_removes_its_shots(session: Session, store: MarkdownStore) -> None:
    import_world(session, store, "world-01")
    session.flush()

    session.delete(_world(session))
    session.flush()

    assert session.execute(select(Shot)).scalars().all() == []
