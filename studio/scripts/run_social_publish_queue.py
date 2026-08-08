"""Run one bounded pass over due social publication jobs."""

from __future__ import annotations

from app.config import get_settings
from app.db.session import get_session_factory
from app.services.social_delivery import run_due_publications


def main() -> int:
    settings = get_settings()
    if not settings.social_publishing_enabled:
        print("Social publishing disabled; queue left untouched.")
        return 0
    with get_session_factory()() as session:
        jobs = run_due_publications(session, settings)
        print(f"Published {len(jobs)} due social job(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
