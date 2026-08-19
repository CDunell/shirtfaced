"""API for direct 9:16 scene shot masters."""

from __future__ import annotations

import subprocess
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStoreError, FilesystemAssetStore
from app.config import Settings, get_settings
from app.db.models import Shot
from app.db.scene_shot_models import SceneShotMaster
from app.db.session import get_db_session
from app.services import motion_run, scene_metadata, scene_shot_library, visual_library

router = APIRouter(prefix="/api", tags=["scene-shot-masters"])
SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


def _store(settings: Settings) -> FilesystemAssetStore:
    return FilesystemAssetStore(settings.assets_root_resolved)


class AssetOut(BaseModel):
    id: uuid.UUID
    sha256: str
    width: int
    height: int
    mime_type: str
    status: str


class ShotMasterOut(BaseModel):
    id: uuid.UUID
    scene_key: str
    name: str
    status: str
    sort_order: int
    notes: str | None
    approved_at: str | None
    motion_prompt: str | None
    motion_prompt_source: str
    asset: AssetOut


class SceneShotMastersOut(BaseModel):
    scene_key: str
    title: str | None
    description: str | None
    approved_count: int
    maximum_approved: int
    shot_masters: list[ShotMasterOut]


class TakeOut(BaseModel):
    stamp: str
    duration_seconds: float | None
    width: int | None
    height: int | None
    silent: bool


class MotionPromptIn(BaseModel):
    prompt: str | None


def _out(shot: SceneShotMaster) -> ShotMasterOut:
    prompt, source = scene_shot_library.effective_motion_prompt(shot)
    return ShotMasterOut(
        id=shot.id,
        scene_key=shot.scene_key,
        name=shot.name,
        status=shot.status,
        sort_order=shot.sort_order,
        notes=shot.notes,
        approved_at=shot.approved_at.isoformat() if shot.approved_at else None,
        motion_prompt=prompt,
        motion_prompt_source=source,
        asset=AssetOut(
            id=shot.asset.id,
            sha256=shot.asset.sha256,
            width=shot.asset.width,
            height=shot.asset.height,
            mime_type=shot.asset.mime_type,
            status=shot.asset.status.value,
        ),
    )


def _scene_out(session: Session, scene_key: str) -> SceneShotMastersOut:
    shots = scene_shot_library.list_scene(session, scene_key)
    configured_title, configured_description = scene_metadata.configured(scene_key)
    canon = session.execute(select(Shot).where(Shot.external_id == scene_key)).scalars().first()
    return SceneShotMastersOut(
        scene_key=scene_key,
        title=configured_title or (canon.title if canon else None),
        description=configured_description or (canon.description if canon else None),
        approved_count=sum(one.status == "approved" for one in shots),
        maximum_approved=scene_shot_library.MAX_APPROVED_SHOT_MASTERS,
        shot_masters=[_out(one) for one in shots],
    )


@router.get("/shot-master-scenes", summary="Scenes holding direct shot masters")
def list_scene_keys(session: SessionDependency) -> list[str]:
    return list(
        session.execute(
            select(SceneShotMaster.scene_key).distinct().order_by(SceneShotMaster.scene_key)
        ).scalars()
    )


@router.get("/scenes/{scene_key}/shot-masters")
def list_shot_masters(scene_key: str, session: SessionDependency) -> SceneShotMastersOut:
    return _scene_out(session, scene_key)


@router.post(
    "/scenes/{scene_key}/shot-masters",
    status_code=status.HTTP_201_CREATED,
    summary="Register one native shot frame",
)
async def register_shot_master(
    scene_key: str,
    session: SessionDependency,
    settings: SettingsDependency,
    file: Annotated[UploadFile, File()],
    name: Annotated[str, Form()],
    notes: Annotated[str | None, Form()] = None,
) -> ShotMasterOut:
    data = await file.read(visual_library.MAX_ASSET_BYTES + 1)
    try:
        shot = scene_shot_library.register(
            session, _store(settings), scene_key=scene_key, name=name, data=data, notes=notes
        )
    except (scene_shot_library.DirectShotError, visual_library.AssetRejected) as error:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except AssetStoreError as error:
        session.rollback()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    session.commit()
    session.refresh(shot)
    return _out(shot)


@router.post("/shot-masters/{shot_id}/replace")
async def replace_shot_master(
    shot_id: uuid.UUID,
    session: SessionDependency,
    settings: SettingsDependency,
    file: Annotated[UploadFile, File()],
) -> ShotMasterOut:
    data = await file.read(visual_library.MAX_ASSET_BYTES + 1)
    try:
        shot = scene_shot_library.by_id(session, shot_id)
        scene_shot_library.replace(session, _store(settings), shot=shot, data=data)
    except (scene_shot_library.DirectShotError, visual_library.AssetRejected) as error:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except AssetStoreError as error:
        session.rollback()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    session.commit()
    session.refresh(shot)
    return _out(shot)


@router.post("/shot-masters/{shot_id}/motion-prompt")
def update_motion_prompt(
    shot_id: uuid.UUID, body: MotionPromptIn, session: SessionDependency
) -> ShotMasterOut:
    try:
        shot = scene_shot_library.by_id(session, shot_id)
        scene_shot_library.set_motion_prompt(shot, body.prompt)
    except scene_shot_library.DirectShotError as error:
        session.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    session.commit()
    session.refresh(shot)
    return _out(shot)


@router.post("/shot-masters/{shot_id}/approve")
def approve_shot_master(shot_id: uuid.UUID, session: SessionDependency) -> SceneShotMastersOut:
    try:
        shot = scene_shot_library.by_id(session, shot_id)
        scene_shot_library.approve(session, shot)
    except scene_shot_library.DirectShotError as error:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    session.commit()
    return _scene_out(session, shot.scene_key)


@router.post("/shot-masters/{shot_id}/reject")
def reject_shot_master(shot_id: uuid.UUID, session: SessionDependency) -> SceneShotMastersOut:
    try:
        shot = scene_shot_library.by_id(session, shot_id)
        scene_shot_library.reject(session, shot, note="Rejected in Scenes")
    except scene_shot_library.DirectShotError as error:
        session.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    session.commit()
    return _scene_out(session, shot.scene_key)


@router.post("/shot-masters/{shot_id}/animate", summary="Animate this exact approved first frame")
def animate_shot_master(shot_id: uuid.UUID, session: SessionDependency) -> TakeOut:
    try:
        shot = scene_shot_library.by_id(session, shot_id)
        if shot.status != "approved":
            raise scene_shot_library.DirectShotUnavailable(
                f"{shot.scene_key}/{shot.name}: approve this shot master before Veo."
            )
        prompt, _ = scene_shot_library.effective_motion_prompt(shot)
        if not prompt:
            raise scene_shot_library.DirectShotUnavailable(
                f"{shot.scene_key}/{shot.name}: no Veo motion prompt is configured."
            )
        result = motion_run.animate(shot.scene_key, shot.name)
    except (scene_shot_library.DirectShotError, motion_run.MotionRunFailed) as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except subprocess.TimeoutExpired as error:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, "Veo did not answer.") from error

    takes = motion_run.takes_for(shot.scene_key, shot.name)
    latest = takes[0] if takes else None
    return TakeOut(
        stamp=latest.stamp if latest else result.directory.name,
        duration_seconds=latest.duration_seconds if latest else None,
        width=latest.width if latest else None,
        height=latest.height if latest else None,
        silent=bool(latest and latest.has_silent),
    )


@router.get("/shot-masters/{shot_id}/takes")
def takes(shot_id: uuid.UUID, session: SessionDependency) -> list[TakeOut]:
    try:
        shot = scene_shot_library.by_id(session, shot_id)
    except scene_shot_library.DirectShotError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return [
        TakeOut(
            stamp=one.stamp,
            duration_seconds=one.duration_seconds,
            width=one.width,
            height=one.height,
            silent=one.has_silent,
        )
        for one in motion_run.takes_for(shot.scene_key, shot.name)
    ]


@router.get("/shot-masters/{shot_id}/take")
def newest_take(shot_id: uuid.UUID, session: SessionDependency) -> Response:
    try:
        shot = scene_shot_library.by_id(session, shot_id)
    except scene_shot_library.DirectShotError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    found = motion_run.takes_for(shot.scene_key, shot.name)
    if not found:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No Veo take for this shot master yet.")
    path = motion_run.ensure_silent(found[0].directory)
    if path is None or not path.is_file():
        raise HTTPException(status.HTTP_409_CONFLICT, "The take exists but no silent video is available.")
    return Response(content=path.read_bytes(), media_type="video/mp4")
