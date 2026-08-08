"""FastAPI application factory.

Schema changes are never applied here. Migrations run as a controlled release step
with ``alembic upgrade head``.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles

from app import __version__
from app.config import PROJECT_ROOT, Settings, get_settings
from app.routes import api, archive_files, assets, compose, design, health, printing, social
from app.security import SESSION_COOKIE, verify_session_token
from app.web import mount_interface

logger = logging.getLogger(__name__)

UNAUTHENTICATED_PATHS = frozenset({"/health", "/ready"})


class RequireAdminSession(BaseHTTPMiddleware):
    """Let through only requests carrying a session admin signed."""

    def __init__(self, application: FastAPI, settings: Settings) -> None:
        super().__init__(application)
        self._settings = settings

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        if request.url.path in UNAUTHENTICATED_PATHS:
            return await call_next(request)

        email = verify_session_token(
            request.cookies.get(SESSION_COOKIE), self._settings.session_secret
        )
        if email:
            return await call_next(request)

        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": "Not signed in."}, status_code=401)
        return RedirectResponse(f"{self._settings.login_url}?next={request.url}", status_code=307)


def create_app() -> FastAPI:
    """Build the application."""
    settings = get_settings()

    application = FastAPI(
        title="Shirtfaced Studio",
        summary="Creative production workflow for Shirtfaced photographic worlds",
        version=__version__,
        debug=settings.debug,
    )

    if settings.auth_enabled:
        application.add_middleware(RequireAdminSession, settings=settings)  # type: ignore[arg-type]
        logger.info("Requiring an admin session on every request.")
    else:
        logger.warning(
            "SESSION_SECRET is not set, so requests are NOT authenticated. This is "
            "only safe while Studio is reachable from this machine alone."
        )

    application.include_router(health.router)
    application.include_router(api.router)
    application.include_router(printing.router)
    application.include_router(assets.router)
    application.include_router(design.router)
    application.include_router(compose.router)
    application.include_router(archive_files.router)
    application.include_router(social.router)

    # Social templates are generated from the repository's real wordmark/smiley
    # into public/social-assets. Studio consumes exactly those files rather than
    # maintaining a second copy of the brand assets.
    social_assets = PROJECT_ROOT.parent / "public" / "social-assets"
    if social_assets.is_dir():
        application.mount(
            "/social-assets",
            StaticFiles(directory=social_assets, check_dir=True),
            name="social-assets",
        )
    else:
        logger.warning(
            "Social assets are missing at %s; run the social asset builder.",
            social_assets,
        )

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
