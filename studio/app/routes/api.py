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

from app.adapters.factory import build_planning_client, planning_client_is_live
from app.adapters.markdown_store import WORLD_DOCUMENT, MarkdownStore
from app.adapters.planning import PlanningError
from app.config import Settings, get_settings
from app.db.models import Shot, World
from app.db.session import get_db_session
from app.domain.enums import ShotStatus, WorldStatus
from app.domain.errors import StudioError
from app.domain.schemas import PromptPlan
from app.services.prompt_planner import build_request, create_plan
from app.services.rotation import apply_continuity, rotation_from_shots
from app.services.shot_selector import NoSelection, Selection, select_next_shot

router = APIRouter(prefix="/api", tags=["worlds"])

SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


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


class SetAsideResponse(BaseModel):
    """A shot that was considered and not chosen."""

    external_id: str
    reason: str


class NextShotResponse(BaseModel):
    """The deterministic selection, with its explanation."""

    selected: ShotResponse | None
    reason: str
    eligible_count: int
    set_aside: list[SetAsideResponse]
    last_hero_product: str | None
    last_camera_position: str | None


class PlanPreviewResponse(BaseModel):
    """A production plan rendered before anything is generated."""

    shot: ShotResponse
    selection_reason: str
    plan: PromptPlan
    # Whether a billable model produced this, or the deterministic fake did.
    live: bool


def _load_world(session: Session, world_slug: str) -> World:
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
    return world


@router.get("/worlds", summary="List worlds")
def list_worlds(session: SessionDependency) -> list[WorldSummary]:
    """Every world known to the database, in slug order."""
    worlds = session.execute(select(World).order_by(World.slug)).scalars().all()
    return [WorldSummary.model_validate(world) for world in worlds]


@router.get("/worlds/{world_slug}", summary="World detail")
def get_world(world_slug: str, session: SessionDependency) -> WorldDetail:
    """One world with its shotlist."""
    world = _load_world(session, world_slug)

    shots = sorted(world.shots, key=lambda shot: shot.sequence)
    outcome = select_next_shot(world, shots)
    upcoming = outcome.shot if isinstance(outcome, Selection) else None

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


@router.get("/worlds/{world_slug}/next-shot", summary="Next shot and why")
def get_next_shot(world_slug: str, session: SessionDependency) -> NextShotResponse:
    """Run the deterministic selector.

    Costs nothing and calls no model: this is a pure function of database state.
    """
    world = _load_world(session, world_slug)
    shots = sorted(world.shots, key=lambda shot: shot.sequence)
    outcome = select_next_shot(world, shots)

    set_aside = [
        SetAsideResponse(external_id=candidate.external_id, reason=candidate.reason)
        for candidate in outcome.set_aside
    ]

    if isinstance(outcome, NoSelection):
        rotation = rotation_from_shots(shots)
        return NextShotResponse(
            selected=None,
            reason=outcome.reason,
            eligible_count=0,
            set_aside=set_aside,
            last_hero_product=rotation.last_hero_product,
            last_camera_position=rotation.last_camera_position,
        )

    return NextShotResponse(
        selected=ShotResponse.model_validate(outcome.shot),
        reason=outcome.reason,
        eligible_count=outcome.eligible_count,
        set_aside=set_aside,
        last_hero_product=outcome.rotation.last_hero_product,
        last_camera_position=outcome.rotation.last_camera_position,
    )


@router.post("/worlds/{world_slug}/plan-preview", summary="Preview the production prompt")
def preview_plan(
    world_slug: str, session: SessionDependency, settings: SettingsDependency
) -> PlanPreviewResponse:
    """Build the production prompt for the next shot without generating an image.

    Available in development only. It plans, it does not generate: no image is
    created and nothing is persisted.
    """
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt preview is available in development mode only.",
        )

    world = _load_world(session, world_slug)
    shots = sorted(world.shots, key=lambda shot: shot.sequence)
    outcome = select_next_shot(world, shots)

    if isinstance(outcome, NoSelection):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=outcome.reason)

    store = MarkdownStore(settings.worlds_root_resolved)
    try:
        documents = store.read_world_documents(world.slug)
    except StudioError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error

    rotation = apply_continuity(outcome.rotation, documents["CONTINUITY.md"].text)
    request = build_request(
        world_slug=world.slug,
        world_name=world.name,
        shot=outcome.shot,
        world_text=documents[WORLD_DOCUMENT].text,
        rotation=rotation,
        selection_reason=outcome.reason,
    )

    try:
        result = create_plan(build_planning_client(settings), request)
    except PlanningError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    return PlanPreviewResponse(
        shot=ShotResponse.model_validate(outcome.shot),
        selection_reason=outcome.reason,
        plan=result.plan,
        live=planning_client_is_live(settings),
    )
