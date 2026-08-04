"""Unit test fixtures.

Unit tests assert on documented defaults, so they must not see whatever the
developer or CI runner happens to export. Every settings key is cleared before each
test; only ``DATABASE_URL`` is reinstated, because it has no default and the
application cannot be constructed without it.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from app.config import Settings

PLACEHOLDER_DATABASE_URL = (
    "postgresql+psycopg://unit-tests:unit-tests@127.0.0.1:1/unit_tests_never_connected"
)

SETTINGS_ENV_KEYS = tuple(name.upper() for name in Settings.model_fields)


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for key in SETTINGS_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("DATABASE_URL", PLACEHOLDER_DATABASE_URL)
    yield
