"""The photograph library.

Separate from the generation API because nothing here generates anything. It takes
photographs that came from somewhere else and hands them back.

This module was called printing, and printed a design onto a photograph through a
quadrilateral dragged over the garment by hand. That path never got off the ground
and was replaced by defined zones in real millimetres; the zone-based print reads
an approved design version and lives in ``app/services/approved_print.py``. The
drag path, its placement table and its ``/api/designs`` file listing were removed
on 15 August 2026. What remains is the library the world pipeline actually uses --
Prompts uploads into it, Social reads from it.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select, true
from sqlalchemy.orm import Session, selectinload

from app.adapters.asset_store import AssetStoreError, FilesystemAssetStore
from app.config import Settings, get_settings
from app.db.models import GenerationAttempt, Photo, Shot, World
from app.db.session import get_db_session
from app.domain.enums import AssetKind, AttemptState
from app.services.print_service import (
    NoSuchPrompt,
    NotAPhoto,
    register_generated,
    upload_photo,
)

router = APIRouter(prefix="/api", tags=["printing"])

SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]

# Photographs arrive here generated elsewhere and uploaded, so the ceiling has to
# clear a full-size frame with room over it -- an upscaled or print-resolution PNG
# runs well past ten megabytes. This is a guard against one request filling the
# disk, not a judgement about what a photograph should weigh.
MAX_UPLOAD_BYTES = 64 * 1024 * 1024

# A stored photograph is immutable and addressed by a UUID that never points at
# different bytes.
IMMUTABLE = "private, max-age=31536000, immutable"


class PromptLineage(BaseModel):
    """The prompt a photograph came from."""

    shot_external_id: str
    variation: int


class PhotoResponse(BaseModel):
    """A photograph, and where it came from."""

    id: uuid.UUID
    url: str
    label: str
    # False for anything Studio generated, true for anything brought in.
    uploaded: bool
    width: int
    height: int
    # Null for a photograph nobody attributed to a prompt.
    from_prompt: PromptLineage | None


def _photo_response(photo: Photo) -> PhotoResponse:
    variation = photo.prompt_variation
    return PhotoResponse(
        id=photo.id,
        url=f"/api/photos/{photo.id}/image",
        label=photo.label,
        uploaded=photo.uploaded,
        width=photo.width,
        height=photo.height,
        from_prompt=PromptLineage(
            shot_external_id=variation.shot.external_id, variation=variation.variation
        )
        if variation
        else None,
    )


@router.get("/photos", summary="The photograph library")
def list_photos(session: SessionDependency, world: str | None = None) -> list[PhotoResponse]:
    """Approved frames, and anything uploaded.

    Only approved attempts are registered: a rejected one is not a photograph
    anybody is going to sell from. Uploads belong to no world -- a photograph off a
    phone is not part of a shotlist -- so they are listed whatever the filter says,
    and first, because the one just brought in is the one being worked on.
    """
    attempts = (
        session.execute(
            select(GenerationAttempt)
            .join(Shot)
            .join(World)
            .where(GenerationAttempt.state == AttemptState.APPROVED)
            .where(World.slug == world if world else true())
            .options(selectinload(GenerationAttempt.shot), selectinload(GenerationAttempt.assets))
            .order_by(Shot.sequence)
        )
        .scalars()
        .all()
    )

    generated: list[Photo] = []
    for attempt in attempts:
        original = next(
            (asset for asset in attempt.assets if asset.kind == AssetKind.ORIGINAL), None
        )
        if original is None:
            continue
        label = f"{attempt.shot.external_id} — {attempt.shot.title}"
        generated.append(register_generated(session, original, label))
    session.commit()

    uploads = (
        session.execute(
            select(Photo).where(Photo.attempt_id.is_(None)).order_by(Photo.created_at.desc())
        )
        .scalars()
        .all()
    )

    return [_photo_response(photo) for photo in [*uploads, *generated]]


@router.post("/photos", summary="Upload a photograph", status_code=status.HTTP_201_CREATED)
async def upload(
    session: SessionDependency,
    settings: SettingsDependency,
    file: Annotated[UploadFile, File()],
    # Which prompt produced it. Sent when the upload comes from a prompt, which is
    # the only moment anybody knows.
    prompt_variation_id: Annotated[uuid.UUID | None, Form()] = None,
) -> PhotoResponse:
    """Bring in a photograph this application did not make.

    Not every photograph worth having comes out of the image model, and a fresh
    deployment has no approved frames at all -- without this the library is empty
    and Social has nothing to post.
    """
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"That file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)}MB.",
        )

    store = FilesystemAssetStore(settings.assets_root_resolved)
    try:
        photo = upload_photo(
            session,
            store,
            data=data,
            filename=file.filename or "photograph",
            prompt_variation_id=prompt_variation_id,
        )
    except NotAPhoto as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except NoSuchPrompt as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    return _photo_response(photo)


@router.get("/photos/{photo_id}/image", summary="The photograph itself")
def get_photo_image(
    photo_id: uuid.UUID, session: SessionDependency, settings: SettingsDependency
) -> Response:
    """Served from the row's own path, never from anything in the request."""
    photo = session.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such photograph.")

    store = FilesystemAssetStore(settings.assets_root_resolved)
    try:
        data = store.load(photo.relative_path)
    except AssetStoreError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="The image file is missing."
        ) from error

    return Response(content=data, media_type=photo.mime_type, headers={"Cache-Control": IMMUTABLE})
