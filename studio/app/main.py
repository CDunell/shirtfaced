"""FastAPI application factory.

Schema changes are never applied here. Migrations run as a controlled release step
with ``alembic upgrade head``.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app import __version__
from app.config import get_settings
from app.routes import api, health
from app.web import mount_interface

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Build the application."""
    settings = get_settings()

    application = FastAPI(
        title="Shirtfaced Studio",
        summary="Creative production workflow for Shirtfaced photographic worlds",
        version=__version__,
        debug=settings.debug,
    )

    # API routes are registered before the interface so the root mount never shadows
    # them.
    application.include_router(health.router)
    application.include_router(api.router)

    dist_root = settings.web_dist_root_resolved
    if mount_interface(application, dist_root):
        logger.info("Serving the built interface from %s", dist_root)
    else:
        logger.info(
            "No built interface at %s; run 'npm run build' in web/, or use the Vite "
            "dev server. The API is unaffected.",
            dist_root,
        )

    return application


app = create_app()
