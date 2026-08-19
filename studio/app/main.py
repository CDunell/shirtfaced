"""FastAPI application factory.

Schema changes are never applied here. Migrations run as a controlled release step
with ``alembic upgrade head``.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
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
