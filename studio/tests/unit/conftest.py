"""Unit test fixtures.

Unit tests assert on documented defaults, so they must not see whatever the
developer or CI runner happens to export. Every settings key is cleared before each
test; only ``DATABASE_URL`` is reinstated, because it has no default and the
application cannot be constructed without it.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from app.config import Settings, get_settings
from app.db.session import get_engine, get_session_factory

PLACEHOLDER_DATABASE_URL = (
    "postgresql+psycopg://unit-tests:unit-tests@127.0.0.1:1/unit_tests_never_connected"
)

SETTINGS_ENV_KEYS = tuple(name.upper() for name in Settings.model_fields)


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for key in SETTINGS_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("DATABASE_URL", PLACEHOLDER_DATABASE_URL)

    # Settings and the engine are cached for the life of the process. Clear them so a
    # test sees the environment it set, not the one an earlier test happened to leave.
    for cached in (get_settings, get_engine, get_session_factory):
        cached.cache_clear()
    yield
    for cached in (get_settings, get_engine, get_session_factory):
        cached.cache_clear()
