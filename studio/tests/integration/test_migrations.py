"""Migrations against a real PostgreSQL database."""

from __future__ import annotations

import pytest
from sqlalchemy import Engine, inspect, text

from tests.integration.conftest import run_alembic

pytestmark = pytest.mark.integration


def test_upgrade_head_creates_the_expected_schema(engine: Engine) -> None:
    inspector = inspect(engine)

    assert "worlds" in inspector.get_table_names()
    columns = {column["name"]: column for column in inspector.get_columns("worlds")}
    assert set(columns) == {
        "id",
        "slug",
        "name",
        "directory_path",
        "status",
        "world_document_hash",
        "continuity_document_hash",
        "shotlist_document_hash",
        "created_at",
        "updated_at",
    }


def test_timestamps_are_timezone_aware(engine: Engine) -> None:
    """The data model requires timestamptz so everything is stored as UTC."""
    with engine.connect() as connection:
        types = dict(
            connection.execute(
                text(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_name = 'worlds' AND column_name IN "
                    "('created_at', 'updated_at')"
                )
            ).all()
        )

    assert types == {
        "created_at": "timestamp with time zone",
        "updated_at": "timestamp with time zone",
    }


def test_id_is_a_native_uuid_column(engine: Engine) -> None:
    with engine.connect() as connection:
        data_type = connection.execute(
            text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name = 'worlds' AND column_name = 'id'"
            )
        ).scalar_one()

    assert data_type == "uuid"


def test_world_slug_is_unique(engine: Engine) -> None:
    """A required index from the data model."""
    unique_constraints = inspect(engine).get_unique_constraints("worlds")

    assert any(c["column_names"] == ["slug"] for c in unique_constraints)


def test_alembic_version_is_at_head(engine: Engine, migrated_database: str) -> None:
    with engine.connect() as connection:
        version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()

    heads = run_alembic("heads", database_url=migrated_database)
    assert heads.returncode == 0, heads.stderr
    assert version in heads.stdout


def test_upgrade_is_idempotent(migrated_database: str) -> None:
    """Re-running the release step on an up-to-date database is a no-op, not an error."""
    result = run_alembic("upgrade", "head", database_url=migrated_database)

    assert result.returncode == 0, result.stderr


def test_downgrade_and_upgrade_round_trip(migrated_database: str) -> None:
    """A migration that cannot be reversed cannot be rolled back in production."""
    down = run_alembic("downgrade", "base", database_url=migrated_database)
    assert down.returncode == 0, down.stderr

    up = run_alembic("upgrade", "head", database_url=migrated_database)
    assert up.returncode == 0, up.stderr


def test_models_match_the_migrated_schema(migrated_database: str) -> None:
    """Autogenerate finds nothing outstanding, so the ORM and the database agree."""
    result = run_alembic(
        "check",
        database_url=migrated_database,
    )

    assert result.returncode == 0, (
        f"The ORM models and the migrations have drifted apart:\n{result.stdout}\n{result.stderr}"
    )
