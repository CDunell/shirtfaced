"""Alembic environment.

The connection string comes from application settings rather than ``alembic.ini`` so
that no credentials are committed and migrations use exactly the same database the
application uses.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context

from app.config import get_settings

# The same registry the application uses, so the two cannot drift.
from app.db import registry  # noqa: F401
from app.db.base import Base
from app.db.session import build_migration_engine

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting, for review before a production release."""
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database."""
    engine = build_migration_engine(get_settings())

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
