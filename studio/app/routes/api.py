"""Read-only world endpoints.

Phase 1 exposes what the world page needs. Continue World, decisions and canon
proposals arrive with the phases that implement them.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Shot, World
from app.db.session import get_db_session
from app.domain.enums import ShotStatus, WorldStatus

router = APIRouter(prefix="/api", tags=["worlds"])

SessionDependency = Annotated[Session, Depends(get_db_session)]


class ShotResponse(BaseModel):
    """One row of the shotlist."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: str
    sequence: int
    priority: int
    title: str
    hero_product: str | None
    camera_position: str | None
    lighting_source: str | None
    status: ShotStatus
    disabled: bool
    source_line: int | None


class WorldSummary(BaseModel):
    """A world without its shots."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    status: WorldStatus
    world_document_hash: str | None
    continuity_document_hash: str | None
    shotlist_document_hash: str | None


class ShotCounts(BaseModel):
    """How the shotlist breaks down, for the world page header."""

    total: int
    planned: int
    in_progress: int
    approved: int
    rejected: int
    abandoned: int


class WorldDetail(WorldSummary):
    """A world with its shots and counts."""

    shots: list[ShotResponse]
    counts: ShotCounts
    next_planned_shot: ShotResponse | None


def _counts(shots: list[Shot]) -> ShotCounts:
    def total_for(wanted: ShotStatus) -> int:
        return sum(1 for shot in shots if shot.status is wanted)

    return ShotCounts(
        total=len(shots),
        planned=total_for(ShotStatus.PLANNED),
        in_progress=total_for(ShotStatus.IN_PROGRESS),
        approved=total_for(ShotStatus.APPROVED),
        rejected=total_for(ShotStatus.REJECTED),
        abandoned=total_for(ShotStatus.ABANDONED),
    )


def _next_planned(shots: list[Shot]) -> Shot | None:
    """The first eligible planned shot by priority, then sequence.

    This is the ordering half of next-shot selection. Product and camera rotation,
    and the recorded selection reason, belong to the selector in Phase 2.
    """
    eligible = [shot for shot in shots if shot.status is ShotStatus.PLANNED and not shot.disabled]
    if not eligible:
        return None
    return min(eligible, key=lambda shot: (shot.priority, shot.sequence))


@router.get("/worlds", summary="List worlds")
def list_worlds(session: SessionDependency) -> list[WorldSummary]:
    """Every world known to the database, in slug order."""
    worlds = session.execute(select(World).order_by(World.slug)).scalars().all()
    return [WorldSummary.model_validate(world) for world in worlds]


@router.get("/worlds/{world_slug}", summary="World detail")
def get_world(world_slug: str, session: SessionDependency) -> WorldDetail:
    """One world with its shotlist."""
    world = session.execute(
        select(World).where(World.slug == world_slug).options(selectinload(World.shots))
    ).scalar_one_or_none()

    if world is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No world named {world_slug!r} has been imported. "
                "Run 'python -m app.cli import-world <slug>'."
            ),
        )

    shots = sorted(world.shots, key=lambda shot: shot.sequence)
    upcoming = _next_planned(shots)

    return WorldDetail(
        id=world.id,
        slug=world.slug,
        name=world.name,
        status=world.status,
        world_document_hash=world.world_document_hash,
        continuity_document_hash=world.continuity_document_hash,
        shotlist_document_hash=world.shotlist_document_hash,
        shots=[ShotResponse.model_validate(shot) for shot in shots],
        counts=_counts(shots),
        next_planned_shot=(ShotResponse.model_validate(upcoming) if upcoming else None),
    )
