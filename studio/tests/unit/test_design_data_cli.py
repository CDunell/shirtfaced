"""The design-data report, which makes the state of the measured corpus loud.

The consumers read PostgreSQL now -- design_measurements for the corpus,
composed_designs for the decisions -- so the report is a set of queries, and
the one honest thing it can do without a database is say so and fail.
"""

from __future__ import annotations

from app.cli import EXIT_FAILED, _design_data


def test_without_a_database_the_report_says_so_and_fails(capsys, monkeypatch) -> None:
    """A report that cannot reach its source must not pretend to be one."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert _design_data(refresh=False) == EXIT_FAILED
    assert "database unreachable" in capsys.readouterr().out
