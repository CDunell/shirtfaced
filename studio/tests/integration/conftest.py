"""Integration test fixtures.

These tests run against a real PostgreSQL database given by ``TEST_DATABASE_URL``.
SQLite is not substituted: advisory locks, JSONB, partial indexes and transaction
behaviour differ, so a passing SQLite run would prove nothing about production.

Each run starts from an empty ``public`` schema and applies migrations with the same
``alembic upgrade head`` command a deployment uses.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.session import build_migration_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not url:
        pytest.skip(
            "TEST_DATABASE_URL is not set; start the throwaway PostgreSQL container "
            "described in docs/LOCAL_RUNBOOK.md and export it."
        )
    return url


def run_alembic(*args: str, database_url: str) -> subprocess.CompletedProcess[str]:
    """Run the Alembic CLI exactly as a release step would."""
    env = {
        **os.environ,
        "DATABASE_URL": database_url,
        "DB_SSLMODE": os.environ.get("TEST_DB_SSLMODE", "disable"),
    }
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="session")
def database_url() -> str:
    return _test_database_url()


@pytest.fixture(scope="session")
def clean_database(database_url: str) -> str:
    """Drop and recreate the ``public`` schema so migrations run from nothing."""
    settings = Settings(_env_file=None, database_url=database_url, db_sslmode="disable")  # type: ignore[call-arg]
    engine = build_migration_engine(settings)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    engine.dispose()
    return database_url


@pytest.fixture(scope="session")
def migrated_database(clean_database: str) -> str:
    """A database at ``head``."""
    result = run_alembic("upgrade", "head", database_url=clean_database)
    assert result.returncode == 0, f"alembic upgrade head failed:\n{result.stderr}"
    return clean_database


@pytest.fixture
def engine(migrated_database: str) -> Iterator[Engine]:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None, database_url=migrated_database, db_sslmode="disable"
    )
    created = build_migration_engine(settings)
    yield created
    created.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    """A session whose changes are rolled back, keeping tests independent."""
    connection = engine.connect()
    transaction = connection.begin()
    open_session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield open_session
    finally:
        open_session.close()
        transaction.rollback()
        connection.close()
