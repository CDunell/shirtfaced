"""FastAPI application factory.

Schema changes are never applied here. Migrations run as a controlled release step
with ``alembic upgrade head``.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request, Response
from starlette.responses import JSONResponse, RedirectResponse
from starlette.staticfiles import StaticFiles

from app import __version__
from app.config import PROJECT_ROOT, get_settings
from app.routes import (
    api,
    archive_files,
    assets,
    compose,
    concepts,
    coverage,
    design,
    design_advisor,
    email,
    health,
    printing,
    production_library,
    renderer,
    rough_cut,
    scene_shot_masters,
    social,
    vintage_agents,
    vintage_api,
    vintage_design,
    vintage_design_page,
    vintage_evidence,
    visual_library,
)
from app.routes import range as design_range
from app.session_auth import SESSION_COOKIE, verify_session_token
from app.web import mount_interface

logger = logging.getLogger(__name__)


def _social_assets_root() -> Path | None:
    candidates = (
        PROJECT_ROOT / "public" / "social-assets",
        PROJECT_ROOT.parent / "public" / "social-assets",
    )
    return next((candidate for candidate in candidates if candidate.is_dir()), None)


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="Shirtfaced Studio",
        summary="Creative production workflow for Shirtfaced photographic worlds",
        version=__version__,
        debug=settings.debug,
    )

    if settings.require_session_auth:
        secret = settings.session_secret
        assert secret is not None  # enforced by config.py's validator at startup

        @application.middleware("http")
        async def require_session(
            request: Request, call_next: Callable[[Request], Awaitable[Response]]
        ) -> Response:
            # /health must stay reachable with no session: a supervisor or
            # uptime check has no cookie and shouldn't need one just to
            # confirm the process is alive.
            if request.url.path == "/health":
                return await call_next(request)

            token = request.cookies.get(SESSION_COOKIE)
            if verify_session_token(token, secret.get_secret_value()) is None:
                next_url = str(request.url)
                login_url = f"{settings.admin_login_url}?next={next_url}"
                accept = request.headers.get("accept", "")
                if "application/json" in accept:
                    return JSONResponse(
                        {"detail": "Sign in required.", "login_url": login_url},
                        status_code=401,
                    )
                return RedirectResponse(login_url, status_code=302)

            return await call_next(request)

    application.include_router(health.router)
    application.include_router(api.router)
    application.include_router(renderer.router)
    application.include_router(coverage.router)
    application.include_router(printing.router)
    application.include_router(assets.router)
    application.include_router(visual_library.router)
    application.include_router(production_library.router)
    application.include_router(scene_shot_masters.router)
    application.include_router(rough_cut.router)
    application.include_router(design.router)
    application.include_router(design_advisor.router)
    application.include_router(compose.router)
    application.include_router(concepts.router)
    application.include_router(archive_files.router)
    application.include_router(design_range.router)
    application.include_router(social.router)
    application.include_router(email.router)
    application.include_router(vintage_api.router)
    application.include_router(vintage_evidence.router)
    application.include_router(vintage_agents.router)
    application.include_router(vintage_design.router)
    application.include_router(vintage_design_page.router)

    social_assets = _social_assets_root()
    if social_assets is not None:
        application.mount(
            "/social-assets",
            StaticFiles(directory=social_assets, check_dir=True),
            name="social-assets",
        )
    else:
        logger.error(
            "Social assets are missing. Expected them in %s or %s.",
            PROJECT_ROOT / "public" / "social-assets",
            PROJECT_ROOT.parent / "public" / "social-assets",
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
