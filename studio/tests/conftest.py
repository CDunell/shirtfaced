"""Shared test configuration.

Unit tests must never touch a real database or a real OpenAI account. A placeholder
``DATABASE_URL`` is installed before the application is imported so that settings
load, while the engine stays lazy and is never connected.

Integration tests use ``TEST_DATABASE_URL``. When it is absent they are skipped
rather than silently passing.
"""

from __future__ import annotations

import os

# Must run before ``app.config`` is imported anywhere. These are set rather than
# defaulted: a developer machine may already export DATABASE_URL for an unrelated
# project, and a test run must never inherit it.
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://unit-tests:unit-tests@127.0.0.1:1/unit_tests_never_connected"
)
os.environ["DB_SSLMODE"] = "disable"
# Guard against a developer's real key leaking into a test run.
os.environ.pop("OPENAI_API_KEY", None)

TEST_DATABASE_URL_ENV = "TEST_DATABASE_URL"
