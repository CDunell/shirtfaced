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
from sqlalchemy import Engine, make_url, text
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.session import build_migration_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# Tests build into their own schema rather than their own database. Same server, same
# connection settings, no second database to create or keep in step -- and dropping a
# schema cannot take the application's tables with it.
TEST_SCHEMA = os.environ.get("TEST_SCHEMA", "studio_test").strip() or "studio_test"


def _test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not url:
        pytest.skip(
            "TEST_DATABASE_URL is not set; start the throwaway PostgreSQL container "
            "described in docs/LOCAL_RUNBOOK.md and export it."
        )
    return _with_search_path(url)


def _with_search_path(url: str) -> str:
    """Point every connection at the test schema, and only at the test schema.

    ``public`` is deliberately off the path. Leaving it on as a fallback looks
    harmless and is not: Alembic looks up ``alembic_version``, finds the
    application's copy in ``public``, concludes it is already at head and creates no
    tables at all. The suite then runs green against the application's own tables
    while the freshly created test schema sits empty.

    Only pg_catalog is needed beyond this, and that is always on the path.
    """
    if TEST_SCHEMA == "public":
        raise RuntimeError(
            "TEST_SCHEMA is 'public', which is the application's own schema. These "
            "tests drop their schema before every run, so that would destroy real "
            "data. Choose another name."
        )
    parsed = make_url(url)
    if "options" in parsed.query:
        return url  # Already carries connection options; do not fight the caller.
    updated = parsed.set(query={**parsed.query, "options": f"-csearch_path={TEST_SCHEMA}"})
    # str() on a URL masks the password, which would then be sent literally as "***".
    return updated.render_as_string(hide_password=False)


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
    """Drop and recreate the test schema so migrations run from nothing.

    Only the test schema is touched. ``public`` belongs to the application and is
    never dropped, so running the suite against the working database costs nothing
    more than a schema nobody else reads.
    """
    settings = Settings(_env_file=None, database_url=database_url, db_sslmode="disable")  # type: ignore[call-arg]
    engine = build_migration_engine(settings)
    with engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE'))
        connection.execute(text(f'CREATE SCHEMA "{TEST_SCHEMA}"'))
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
