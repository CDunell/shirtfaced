"""Liveness endpoint.

``/health`` confirms only that the process is alive. It deliberately performs no
database or filesystem work, so a reverse proxy or supervisor can use it without a
slow dependency turning a healthy process into a restart loop.

``/ready``, which checks PostgreSQL, migrations, world files and asset storage, is
added by a later phase.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app import __version__

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Liveness payload."""

    status: str
    version: str


@router.get("/health", summary="Liveness check")
def health() -> HealthResponse:
    """Report that the application process is running."""
    return HealthResponse(status="ok", version=__version__)
