from __future__ import annotations

from app.services import generation_ledger


class _ScalarResult:
    def scalar(self) -> int:
        return 32


class _RecordingSession:
    statement: object | None = None

    def execute(self, statement: object) -> _ScalarResult:
        self.statement = statement
        return _ScalarResult()


def test_calls_for_scene_counts_failed_calls_as_attempts() -> None:
    session = _RecordingSession()

    count = generation_ledger.calls_for_scene(session, "W01-P28")  # type: ignore[arg-type]

    assert count == 32
    assert session.statement is not None
    query = str(session.statement).lower()
    assert "scene_key" in query
    assert "succeeded" not in query
