"""The World model against a real PostgreSQL database."""

from __future__ import annotations

import datetime as dt
import uuid

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import World, WorldStatus

pytestmark = pytest.mark.integration


def _world(slug: str = "world-01") -> World:
    return World(slug=slug, name="Shirtfaced World 1", directory_path=f"{slug}")


def test_a_world_round_trips(session: Session) -> None:
    session.add(_world())
    session.flush()

    stored = session.execute(select(World).where(World.slug == "world-01")).scalar_one()

    assert isinstance(stored.id, uuid.UUID)
    assert stored.name == "Shirtfaced World 1"
    assert stored.status is WorldStatus.ACTIVE
    assert stored.world_document_hash is None


def test_timestamps_are_populated_and_utc(session: Session) -> None:
    world = _world()
    session.add(world)
    session.flush()
    session.refresh(world)

    assert world.created_at.tzinfo is not None
    assert world.created_at.utcoffset() == dt.timedelta(0)
    assert world.updated_at.tzinfo is not None


def test_slug_uniqueness_is_enforced_by_the_database(session: Session) -> None:
    session.add(_world())
    session.flush()

    session.add(_world())
    with pytest.raises(IntegrityError):
        session.flush()


def test_status_is_constrained_to_the_enum(engine: Engine) -> None:
    """Integrity comes from the database, not only from application validation."""
    from sqlalchemy import text

    with engine.begin() as connection, pytest.raises(Exception, match="world_status"):
        connection.execute(
            text(
                "INSERT INTO worlds (slug, name, directory_path, status) "
                "VALUES ('bad', 'Bad', 'bad', 'deleted')"
            )
        )


def test_document_hashes_can_be_recorded(session: Session) -> None:
    world = _world()
    world.world_document_hash = "a" * 64
    world.continuity_document_hash = "b" * 64
    world.shotlist_document_hash = "c" * 64
    session.add(world)
    session.flush()
    session.refresh(world)

    assert world.world_document_hash == "a" * 64
    assert world.shotlist_document_hash == "c" * 64
