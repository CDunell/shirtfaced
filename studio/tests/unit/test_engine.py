"""Engine construction.

These tests build an engine but never connect: SQLAlchemy creates the pool lazily.
"""

from __future__ import annotations

from sqlalchemy import make_url

from app.config import Settings
from app.db.session import build_engine, build_migration_engine, connect_args_for

VALID_URL = "postgresql+psycopg://app:secret@db.example:5432/shirtfaced_studio"


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {"database_url": VALID_URL}
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


def test_pool_is_configured_from_settings() -> None:
    engine = build_engine(_settings(db_pool_size=3, db_max_overflow=7))

    assert engine.pool.size() == 3
    assert engine.pool._max_overflow == 7


def test_pre_ping_is_always_enabled() -> None:
    """The Oracle-hosted endpoint may drop idle connections."""
    assert build_engine(_settings()).pool._pre_ping is True


def test_psycopg_3_driver_is_selected() -> None:
    assert build_engine(_settings()).dialect.driver == "psycopg"


def test_sslmode_is_passed_through_to_the_driver() -> None:
    settings = _settings(db_sslmode="verify-full")

    assert connect_args_for(settings, make_url(settings.database_url)) == {"sslmode": "verify-full"}


def test_sslmode_in_the_url_is_not_duplicated() -> None:
    """Supplying it twice would make psycopg reject the connection."""
    settings = _settings(database_url=f"{VALID_URL}?sslmode=disable", db_sslmode="require")

    assert connect_args_for(settings, make_url(settings.database_url)) == {}


def test_migration_engine_is_unpooled() -> None:
    """A release step uses one short-lived connection, not the application pool."""
    engine = build_migration_engine(_settings())

    assert type(engine.pool).__name__ == "NullPool"
    assert engine.dialect.driver == "psycopg"
