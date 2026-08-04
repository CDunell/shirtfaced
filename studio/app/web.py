"""Serving the built Base Web interface.

The application is a single deployable service: FastAPI serves the JSON API and the
compiled front-end from the same origin, so there is no CORS surface and no second
process to run in production.

In development the Vite dev server serves the interface instead and proxies the API,
so ``web/dist`` may not exist. That is not an error; the API simply runs without a UI
mounted.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope


class SinglePageApp(StaticFiles):
    """Static files that fall back to ``index.html`` for unknown paths.

    The interface is a single-page application, so a deep link such as
    ``/worlds/world-01`` must return the app shell rather than a 404. API routes are
    registered before this mount and are matched first, so they are unaffected.
    """

    def __init__(self, directory: Path) -> None:
        super().__init__(directory=directory, html=True, check_dir=True)

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            # Starlette raises rather than returning a 404 response.
            if exc.status_code != 404:
                raise
            return await super().get_response("index.html", scope)


def mount_interface(application: FastAPI, dist_root: Path) -> bool:
    """Mount the built interface at the root when it has been built.

    Returns whether it was mounted, so startup can say so plainly instead of leaving
    an operator guessing why the browser shows nothing.
    """
    if not (dist_root / "index.html").is_file():
        return False

    application.mount("/", SinglePageApp(dist_root), name="web")
    return True
