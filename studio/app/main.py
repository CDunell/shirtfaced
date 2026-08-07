"""FastAPI application factory.

Schema changes are never applied here. Migrations run as a controlled release step
with ``alembic upgrade head``.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__
from app.config import Settings, get_settings
from app.routes import api, assets, design, health, printing
from app.security import SESSION_COOKIE, verify_session_token
from app.web import mount_interface

logger = logging.getLogger(__name__)

# Checked before anything else. Both are used by the deploy to decide whether the
# release worked, they expose no data, and locking them out would mean a deploy
# could not tell a broken Studio from a protected one.
UNAUTHENTICATED_PATHS = frozenset({"/health", "/ready"})


class RequireAdminSession(BaseHTTPMiddleware):
    """Let through only requests carrying a session admin signed.

    Studio has no login of its own, deliberately. Admin has one, Studio shares its
    secret, and being logged into admin is being logged into Studio.
    """

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

        # An API caller gets a status it can act on; a browser gets sent to the
        # login it actually has, with the way back.
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
        # Starlette types this against a factory protocol a
        # BaseHTTPMiddleware subclass does not structurally satisfy, though
        # this is the documented way to register one.
        application.add_middleware(RequireAdminSession, settings=settings)  # type: ignore[arg-type]
        logger.info("Requiring an admin session on every request.")
    else:
        # Loud, because the only thing standing between this API and someone
        # else's bill is the fact that nothing can route to it.
        logger.warning(
            "SESSION_SECRET is not set, so requests are NOT authenticated. This is "
            "only safe while Studio is reachable from this machine alone."
        )

    # API routes are registered before the interface so the root mount never shadows
    # them.
    application.include_router(health.router)
    application.include_router(api.router)
    application.include_router(printing.router)
    application.include_router(assets.router)
    application.include_router(design.router)

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
