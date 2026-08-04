"""FastAPI application factory.

Schema changes are never applied here. Migrations run as a controlled release step
with ``alembic upgrade head``.
"""

from __future__ import annotations

from fastapi import FastAPI

from app import __version__
from app.config import get_settings
from app.routes import health


def create_app() -> FastAPI:
    """Build the application."""
    settings = get_settings()

    application = FastAPI(
        title="Shirtfaced Studio",
        summary="Creative production workflow for Shirtfaced photographic worlds",
        version=__version__,
        debug=settings.debug,
    )
    application.include_router(health.router)
    return application


app = create_app()
