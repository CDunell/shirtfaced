"""Engine and session construction.

The engine is created lazily and cached, so importing the application never opens a
connection. Pool settings come from the environment; ``pool_pre_ping`` is always on
because the Oracle-hosted PostgreSQL endpoint may drop idle connections.
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from sqlalchemy import URL, Engine, create_engine, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import Settings, get_settings


def connect_args_for(settings: Settings, url: URL) -> dict[str, Any]:
    """Driver keyword arguments derived from settings.

    ``sslmode`` is only supplied when the URL does not already carry one, otherwise
    psycopg receives the option twice.
    """
    if "sslmode" in url.query:
        return {}
    return {"sslmode": settings.db_sslmode}


def build_engine(settings: Settings) -> Engine:
    """Create a pooled engine for ``settings.database_url``."""
    url = make_url(settings.database_url)

    return create_engine(
        url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout_seconds,
        pool_recycle=settings.db_pool_recycle_seconds,
        pool_pre_ping=True,
        connect_args=connect_args_for(settings, url),
        future=True,
        echo=False,
    )


def build_migration_engine(settings: Settings) -> Engine:
    """Create an unpooled engine for a migration run.

    A migration is a short-lived, single-connection release step, so it does not use
    the application pool.
    """
    url = make_url(settings.database_url)

    return create_engine(
        url,
        poolclass=NullPool,
        connect_args=connect_args_for(settings, url),
        future=True,
        echo=False,
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return the process-wide engine, creating it on first use."""
    return build_engine(get_settings())


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """Return the process-wide session factory."""
    return sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)


def get_db_session() -> Iterator[Session]:
    """FastAPI dependency yielding a session and closing it afterwards.

    Transactions are kept short: the caller commits explicitly, and anything left
    open is rolled back when the request finishes.
    """
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
