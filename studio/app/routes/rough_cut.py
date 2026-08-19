"""Scene-level AI rough-cut and audio-final API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.services import audio_library, rough_cut, scene_shot_library

router = APIRouter(prefix="/api", tags=["rough-cut"])
SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


class ShotEditOut(BaseModel):
    shot_id: str
    shot_name: str
    take_stamp: str
    decision: str
    in_seconds: float
    out_seconds: float
    identity_score: int
    deformation_score: int
    continuity_score: int
    world_score: int
    energy_score: int
    rationale: str


class AudioEditOut(BaseModel):
    asset_id: str
    filename: str
    mime_type: str
    duration_seconds: float | None
    in_seconds: float
    gain_db: float


class RoughCutOut(BaseModel):
    scene_key: str
    shots: list[ShotEditOut]
    audio: AudioEditOut | None
    output_exists: bool
    final_exists: bool


class ShotEditIn(BaseModel):
    decision: str | None = None
    in_seconds: float | None = Field(default=None, ge=0)
    out_seconds: float | None = Field(default=None, ge=0)
    take_stamp: str | None = None


class AudioEditIn(BaseModel):
    in_seconds: float | None = Field(default=None, ge=0)
    gain_db: float | None = Field(default=None, ge=-30, le=6)


def _out(state: rough_cut.RoughCutState) -> RoughCutOut:
    return RoughCutOut(
        scene_key=state.scene_key,
        shots=[ShotEditOut(**row.__dict__) for row in state.shots],
        audio=AudioEditOut(**state.audio.__dict__) if state.audio else None,
        output_exists=state.output_exists,
        final_exists=state.final_exists,
    )


@router.get("/scenes/{scene_key}/rough-cut")
def get_rough_cut(scene_key: str) -> RoughCutOut:
    try:
        return _out(rough_cut.load(scene_key))
    except rough_cut.RoughCutError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.post("/scenes/{scene_key}/rough-cut/analyse")
def analyse_rough_cut(
    scene_key: str,
    session: SessionDependency,
    settings: SettingsDependency,
) -> RoughCutOut:
    try:
        shots = scene_shot_library.list_scene(session, scene_key)
        return _out(rough_cut.analyse(settings, shots))
    except rough_cut.RoughCutError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.post("/scenes/{scene_key}/rough-cut/shots/{shot_id}")
def update_rough_cut_shot(scene_key: str, shot_id: str, body: ShotEditIn) -> RoughCutOut:
    try:
        return _out(
            rough_cut.update_shot(
                scene_key,
                shot_id,
                decision=body.decision,
                in_seconds=body.in_seconds,
                out_seconds=body.out_seconds,
                take_stamp=body.take_stamp,
            )
        )
    except rough_cut.RoughCutError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.post("/scenes/{scene_key}/rough-cut/render")
def render_rough_cut(scene_key: str, session: SessionDependency) -> RoughCutOut:
    try:
        shots = scene_shot_library.list_scene(session, scene_key)
        return _out(rough_cut.render(scene_key, shots))
    except rough_cut.RoughCutError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.get("/scenes/{scene_key}/rough-cut/video")
def rough_cut_video(scene_key: str) -> Response:
    path = rough_cut.output_path(scene_key)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No rough cut has been rendered yet.")
    return Response(content=path.read_bytes(), media_type="video/mp4")


@router.post("/scenes/{scene_key}/rough-cut/audio", status_code=status.HTTP_201_CREATED)
async def upload_rough_cut_audio(
    scene_key: str,
    session: SessionDependency,
    settings: SettingsDependency,
    file: Annotated[UploadFile, File()],
) -> RoughCutOut:
    data = await file.read(audio_library.MAX_AUDIO_BYTES + 1)
    filename = file.filename or "scene-audio.mp3"
    try:
        state = rough_cut.attach_audio(
            settings,
            session,
            scene_key,
            data=data,
            filename=filename,
        )
        session.commit()
        return _out(state)
    except rough_cut.RoughCutError as error:
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.post("/scenes/{scene_key}/rough-cut/audio-settings")
def update_rough_cut_audio(scene_key: str, body: AudioEditIn) -> RoughCutOut:
    try:
        return _out(
            rough_cut.update_audio(
                scene_key,
                in_seconds=body.in_seconds,
                gain_db=body.gain_db,
            )
        )
    except rough_cut.RoughCutError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.get("/scenes/{scene_key}/rough-cut/audio")
def rough_cut_audio(
    scene_key: str,
    session: SessionDependency,
    settings: SettingsDependency,
) -> Response:
    try:
        path, mime_type = rough_cut.audio_asset(settings, session, scene_key)
    except rough_cut.RoughCutError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    return Response(content=path.read_bytes(), media_type=mime_type)


@router.post("/scenes/{scene_key}/rough-cut/final")
def render_rough_cut_final(
    scene_key: str,
    session: SessionDependency,
    settings: SettingsDependency,
) -> RoughCutOut:
    try:
        return _out(rough_cut.render_final(settings, session, scene_key))
    except rough_cut.RoughCutError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


@router.get("/scenes/{scene_key}/rough-cut/final")
def rough_cut_final(scene_key: str) -> Response:
    path = rough_cut.final_output_path(scene_key)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No audio final has been rendered yet.")
    return Response(content=path.read_bytes(), media_type="video/mp4")
