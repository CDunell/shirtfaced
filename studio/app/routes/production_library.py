"""Scene masters, coverage and locations over HTTP.

``VISUAL_ASSET_LIBRARY.md`` §6, §7, §8 and §11. The tables and the rules were
built first and reachable only from the command line, which meant the two
decisions that gate every paid run — which image is a scene's master, and which
coverage frames may be animated — could only be made by someone with an SSH
session. They are the owner's decisions, so they belong on a screen.

Every refusal from the services below is passed through with its own wording.
"No approved master for pub-1105, 1 registered (candidate)" tells a person what
to do next; a bare 409 does not.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.adapters.asset_store import AssetStoreError, FilesystemAssetStore
from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.db.visual_models import (
    CoverageFrame,
    LocationAsset,
    SceneMaster,
    ScoutLocation,
    VisualAsset,
)
from app.domain.enums import LocationAssetRole, VisualAssetKind, VisualAssetSourceType
from app.services import coverage_library, location_library, visual_library
from app.services.reference_resolution import ReferenceUnavailable

router = APIRouter(prefix="/api", tags=["production-library"])

SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


def _store(settings: Settings) -> FilesystemAssetStore:
    return FilesystemAssetStore(settings.assets_root_resolved)


class AssetBrief(BaseModel):
    """Enough of an asset to show it and say what it is."""

    id: uuid.UUID
    sha256: str
    width: int
    height: int
    mime_type: str
    status: str
    rights_status: str

    @classmethod
    def of(cls, asset: VisualAsset) -> AssetBrief:
        return cls(
            id=asset.id,
            sha256=asset.sha256,
            width=asset.width,
            height=asset.height,
            mime_type=asset.mime_type,
            status=asset.status.value,
            rights_status=asset.rights_status.value,
        )


class CoverageFrameOut(BaseModel):
    id: uuid.UUID
    name: str
    x: int
    y: int
    width: int
    height: int
    approved_for_veo: bool
    frame_sha256: str
    source_master_sha256: str
    # True when the frame was cut from a master that is no longer the approved
    # one. It cannot be animated and needs re-cutting.
    stale: bool
    asset: AssetBrief


class SceneMasterOut(BaseModel):
    id: uuid.UUID
    scene_key: str
    status: str
    approved_at: str | None
    notes: str | None
    asset: AssetBrief
    coverage: list[CoverageFrameOut]


class SceneOut(BaseModel):
    """One scene, its masters newest decision first, and its coverage."""

    scene_key: str
    approved_master_id: uuid.UUID | None
    masters: list[SceneMasterOut]


class LocationAssetOut(BaseModel):
    id: uuid.UUID
    role: str
    sort_order: int
    is_base_master: bool
    camera_position: str | None
    notes: str | None
    asset: AssetBrief
    # Why this plate can or cannot be the thing a scene is built into.
    blocking: list[str]
    ratio: float
    lateral_room_px: int
    meets_wide_preference: bool


class LocationOut(BaseModel):
    id: uuid.UUID
    slug: str
    display_name: str
    parent_slug: str | None
    location_type: str | None
    description: str | None
    status: str
    assets: list[LocationAssetOut]


class LocationIn(BaseModel):
    slug: str = Field(min_length=1, max_length=96)
    display_name: str = Field(min_length=1, max_length=200)
    parent_slug: str | None = None
    location_type: str | None = None
    description: str | None = None


class DecisionIn(BaseModel):
    note: str | None = None
    actor: str = "owner"


def _coverage_out(frame: CoverageFrame) -> CoverageFrameOut:
    return CoverageFrameOut(
        id=frame.id,
        name=frame.name,
        x=frame.x,
        y=frame.y,
        width=frame.width,
        height=frame.height,
        approved_for_veo=frame.approved_for_veo,
        frame_sha256=frame.frame_sha256,
        source_master_sha256=frame.source_master_sha256,
        stale=frame.source_master_sha256 != frame.master.asset.sha256,
        asset=AssetBrief.of(frame.asset),
    )


def _master_out(session: Session, master: SceneMaster) -> SceneMasterOut:
    frames = (
        session.execute(
            select(CoverageFrame)
            .where(CoverageFrame.scene_master_id == master.id)
            .order_by(CoverageFrame.name)
        )
        .scalars()
        .all()
    )
    return SceneMasterOut(
        id=master.id,
        scene_key=master.scene_key,
        status=master.status,
        approved_at=master.approved_at.isoformat() if master.approved_at else None,
        notes=master.notes,
        asset=AssetBrief.of(master.asset),
        coverage=[_coverage_out(frame) for frame in frames],
    )


@router.get("/scenes", summary="Every scene with a registered master")
def list_scenes(session: SessionDependency) -> list[SceneOut]:
    masters = (
        session.execute(select(SceneMaster).order_by(SceneMaster.scene_key, SceneMaster.created_at))
        .scalars()
        .unique()
        .all()
    )

    scenes: dict[str, list[SceneMaster]] = {}
    for master in masters:
        scenes.setdefault(master.scene_key, []).append(master)

    return [
        SceneOut(
            scene_key=scene_key,
            approved_master_id=next((one.id for one in group if one.status == "approved"), None),
            masters=[_master_out(session, one) for one in group],
        )
        for scene_key, group in sorted(scenes.items())
    ]


@router.post(
    "/scenes/{scene_key}/masters",
    status_code=status.HTTP_201_CREATED,
    summary="Register an image as a candidate master for this scene",
)
async def register_master(
    scene_key: str,
    session: SessionDependency,
    settings: SettingsDependency,
    file: Annotated[UploadFile, File()],
    approve: Annotated[bool, Form()] = False,
    notes: Annotated[str | None, Form()] = None,
) -> SceneMasterOut:
    """Registering is not approving: a candidate resolves for nothing."""
    data = await file.read(visual_library.MAX_ASSET_BYTES + 1)
    try:
        ingested = visual_library.ingest_asset(
            session,
            _store(settings),
            data=data,
            kind=VisualAssetKind.SCENE_MASTER,
            source_type=VisualAssetSourceType.GENERATED,
            role=scene_key,
            description=f"Scene master candidate for {scene_key}",
        )
        master = visual_library.register_scene_master(
            session, scene_key=scene_key, asset=ingested.asset, notes=notes
        )
        if approve:
            visual_library.approve_asset(session, ingested.asset, note=notes)
            visual_library.approve_scene_master(session, master, note=notes)
    except visual_library.AssetRejected as error:
        session.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except visual_library.SceneMasterConflict as error:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except AssetStoreError as error:
        session.rollback()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error

    session.commit()
    session.refresh(master)
    return _master_out(session, master)


@router.post("/scene-masters/{master_id}/approve", summary="Make this the scene's master")
def approve_master(
    master_id: uuid.UUID, payload: DecisionIn, session: SessionDependency
) -> SceneMasterOut:
    master = session.get(SceneMaster, master_id)
    if master is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such scene master.")
    try:
        if master.asset.status.value != "approved":
            visual_library.approve_asset(session, master.asset, note=payload.note)
        visual_library.approve_scene_master(session, master, actor=payload.actor, note=payload.note)
    except visual_library.SceneMasterConflict as error:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error

    session.commit()
    session.refresh(master)
    return _master_out(session, master)


class CoverageIn(BaseModel):
    name: str = Field(min_length=1, max_length=96, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    x: int = Field(ge=0)
    y: int = Field(default=0, ge=0)
    height: int = Field(default=0, ge=0)


@router.post(
    "/scenes/{scene_key}/coverage",
    status_code=status.HTTP_201_CREATED,
    summary="Cut a named 9:16 frame from the scene's approved master",
)
def cut_coverage(
    scene_key: str, payload: CoverageIn, session: SessionDependency, settings: SettingsDependency
) -> CoverageFrameOut:
    try:
        frame = coverage_library.derive_coverage_frame(
            session,
            _store(settings),
            scene_key=scene_key,
            name=payload.name,
            x=payload.x,
            y=payload.y,
            height=payload.height,
        )
    except (coverage_library.CoverageRejected, ReferenceUnavailable) as error:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error

    session.commit()
    session.refresh(frame)
    return _coverage_out(frame)


@router.post("/coverage/{frame_id}/approve", summary="Let Veo animate this frame")
def approve_coverage(
    frame_id: uuid.UUID, payload: DecisionIn, session: SessionDependency
) -> CoverageFrameOut:
    frame = session.get(CoverageFrame, frame_id)
    if frame is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such coverage frame.")
    try:
        coverage_library.approve_for_veo(session, frame, actor=payload.actor, note=payload.note)
    except coverage_library.CoverageRejected as error:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error

    session.commit()
    session.refresh(frame)
    return _coverage_out(frame)


def _location_asset_out(link: LocationAsset) -> LocationAssetOut:
    readiness = location_library.assess_base_master(link)
    return LocationAssetOut(
        id=link.id,
        role=link.role.value,
        sort_order=link.sort_order,
        is_base_master=link.is_base_master,
        camera_position=link.camera_position,
        notes=link.notes,
        asset=AssetBrief.of(link.asset),
        blocking=list(readiness.problems),
        ratio=readiness.ratio,
        lateral_room_px=readiness.lateral_room_px,
        meets_wide_preference=readiness.meets_the_wide_preference,
    )


def _location_out(location: ScoutLocation) -> LocationOut:
    return LocationOut(
        id=location.id,
        slug=location.slug,
        display_name=location.display_name,
        parent_slug=location.parent.slug if location.parent else None,
        location_type=location.location_type,
        description=location.description,
        status=location.status,
        assets=[_location_asset_out(link) for link in location.assets],
    )


@router.get("/locations", summary="Every scouted place and its plates")
def list_locations(session: SessionDependency) -> list[LocationOut]:
    locations = (
        session.execute(
            select(ScoutLocation)
            .options(selectinload(ScoutLocation.assets).selectinload(LocationAsset.asset))
            .order_by(ScoutLocation.slug)
        )
        .scalars()
        .unique()
        .all()
    )
    return [_location_out(location) for location in locations]


@router.get("/locations/roles", summary="The scouting classes a plate can be filed as")
def location_roles() -> list[str]:
    return [role.value for role in LocationAssetRole]


@router.post("/locations", status_code=status.HTTP_201_CREATED, summary="Record a place")
def create_location(payload: LocationIn, session: SessionDependency) -> LocationOut:
    parent = None
    if payload.parent_slug:
        parent = session.execute(
            select(ScoutLocation).where(ScoutLocation.slug == payload.parent_slug)
        ).scalar_one_or_none()
        if parent is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"No parent location {payload.parent_slug!r}."
            )

    location = location_library.register_location(
        session,
        slug=payload.slug,
        display_name=payload.display_name,
        parent=parent,
        location_type=payload.location_type,
        description=payload.description,
    )
    session.commit()
    session.refresh(location)
    return _location_out(location)


@router.post(
    "/locations/{slug}/plates",
    status_code=status.HTTP_201_CREATED,
    summary="Add a scouting plate",
)
async def add_plate(
    slug: str,
    session: SessionDependency,
    settings: SettingsDependency,
    file: Annotated[UploadFile, File()],
    role: Annotated[LocationAssetRole, Form()],
    camera_position: Annotated[str | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
    promote: Annotated[bool, Form()] = False,
) -> LocationAssetOut:
    location = session.execute(
        select(ScoutLocation).where(ScoutLocation.slug == slug)
    ).scalar_one_or_none()
    if location is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No location {slug!r}.")

    data = await file.read(visual_library.MAX_ASSET_BYTES + 1)
    try:
        ingested = visual_library.ingest_asset(
            session,
            _store(settings),
            data=data,
            kind=VisualAssetKind.LOCATION,
            source_type=VisualAssetSourceType.GENERATED,
            role=role.value,
            description=f"{location.display_name} — {role.value.replace('_', ' ')}",
        )
        link = location_library.attach_plate(
            session,
            location,
            ingested.asset,
            role=role,
            camera_position=camera_position,
            notes=notes,
        )
        if promote:
            visual_library.approve_asset(session, ingested.asset)
            location_library.promote_to_base_master(session, link)
    except visual_library.AssetRejected as error:
        session.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except location_library.LocationRejected as error:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except AssetStoreError as error:
        session.rollback()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error

    session.commit()
    session.refresh(link)
    return _location_asset_out(link)


@router.post(
    "/location-plates/{link_id}/promote", summary="Make this the plate scenes are built into"
)
def promote_plate(
    link_id: uuid.UUID, payload: DecisionIn, session: SessionDependency
) -> LocationAssetOut:
    link = session.get(LocationAsset, link_id)
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such plate.")
    try:
        if link.asset.status.value != "approved":
            visual_library.approve_asset(session, link.asset, note=payload.note)
        location_library.promote_to_base_master(
            session, link, actor=payload.actor, note=payload.note
        )
    except location_library.LocationRejected as error:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error

    session.commit()
    session.refresh(link)
    return _location_asset_out(link)


@router.get("/visual-assets/{asset_id}/preview", summary="An asset's bytes, for the interface")
def preview(
    asset_id: uuid.UUID, session: SessionDependency, settings: SettingsDependency
) -> Response:
    asset = session.get(VisualAsset, asset_id)
    if asset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such asset.")
    try:
        data = _store(settings).load(asset.storage_key)
    except AssetStoreError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    return Response(
        content=data,
        media_type=asset.mime_type,
        headers={"Cache-Control": "private, max-age=31536000, immutable"},
    )
