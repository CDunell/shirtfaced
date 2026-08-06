"""Putting a design on a photograph.

Separate from the generation API because nothing here generates anything. It lists
what can be printed on, takes photographs that came from somewhere else, remembers
where the design goes, and renders. No model is called and nothing is billed, so a
placement can be nudged as many times as it takes.
"""

from __future__ import annotations

import io
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, true
from sqlalchemy.orm import Session, selectinload

from app.adapters.asset_store import AssetStoreError, FilesystemAssetStore
from app.config import Settings, get_settings
from app.db.models import GenerationAttempt, Photo, Shot, World
from app.db.session import get_db_session
from app.domain.enums import AssetKind, AttemptState
from app.services.print_service import (
    NoSuchDesign,
    NoSuchPhoto,
    NoSuchPrompt,
    NotAPhoto,
    NotPlaced,
    available_designs,
    print_on_photo,
    read_placement,
    register_generated,
    save_placement,
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


class DesignResponse(BaseModel):
    """A design file that can be printed."""

    name: str


class PromptLineage(BaseModel):
    """The prompt a photograph came from."""

    shot_external_id: str
    variation: int


class PhotoResponse(BaseModel):
    """A photograph a design can go on, and whether one has been placed."""

    id: uuid.UUID
    url: str
    label: str
    # False for anything Studio generated, true for anything brought in.
    uploaded: bool
    width: int
    height: int
    placed: bool
    # Null for a photograph nobody attributed to a prompt.
    from_prompt: PromptLineage | None


class PlacementBody(BaseModel):
    """Where the design goes, as fractions of the image."""

    # Clockwise from the top left. Fractions rather than pixels so the placement
    # survives any resize of the photograph.
    corners: list[tuple[float, float]] = Field(min_length=4, max_length=4)
    settings: dict[str, float] = Field(default_factory=dict)
    design: str | None = None

    @field_validator("corners")
    @classmethod
    def _inside_the_photograph(
        cls, value: list[tuple[float, float]]
    ) -> list[tuple[float, float]]:
        """A corner outside the frame is a dragging accident, not an intention.

        A little slack is allowed: pulling a corner just past the edge to cover a
        shoulder that runs off frame is a real thing to want.
        """
        for x, y in value:
            if not (-0.5 <= x <= 1.5 and -0.5 <= y <= 1.5):
                raise ValueError("A corner is a long way outside the photograph.")
        return value


class PlacementResponse(BaseModel):
    corners: list[tuple[float, float]]
    settings: dict[str, float]
    design: str | None


def _photo_response(session: Session, photo: Photo) -> PhotoResponse:
    variation = photo.prompt_variation
    return PhotoResponse(
        id=photo.id,
        url=f"/api/photos/{photo.id}/image",
        label=photo.label,
        uploaded=photo.uploaded,
        width=photo.width,
        height=photo.height,
        placed=read_placement(session, photo.id) is not None,
        from_prompt=PromptLineage(
            shot_external_id=variation.shot.external_id, variation=variation.variation
        )
        if variation
        else None,
    )


@router.get("/designs", summary="Designs that can be printed")
def list_designs(settings: SettingsDependency) -> list[DesignResponse]:
    """Empty until artwork exists, which is a state rather than a failure."""
    return [
        DesignResponse(name=design.name)
        for design in available_designs(settings.assets_root_resolved)
    ]


@router.get("/photos", summary="Photographs a design can go on")
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

    return [_photo_response(session, photo) for photo in [*uploads, *generated]]


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

    Not every photograph worth printing on comes out of the image model, and a fresh
    deployment has no approved frames at all -- without this the library is empty and
    the editor has nothing to open.
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

    return _photo_response(session, photo)


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

    return Response(
        content=data, media_type=photo.mime_type, headers={"Cache-Control": IMMUTABLE}
    )


@router.get("/photos/{photo_id}/placement", summary="Where the design sits")
def get_placement(photo_id: uuid.UUID, session: SessionDependency) -> PlacementResponse | None:
    """Null when nobody has placed one yet."""
    row = read_placement(session, photo_id)
    if row is None:
        return None
    return PlacementResponse(
        corners=[(x, y) for x, y in row.corners], settings=row.settings, design=row.design
    )


@router.put("/photos/{photo_id}/placement", summary="Move the design")
def put_placement(
    photo_id: uuid.UUID, body: PlacementBody, session: SessionDependency
) -> PlacementResponse:
    """Replace the placement. Moving a design is an edit, not a new opinion."""
    try:
        row = save_placement(
            session,
            photo_id=photo_id,
            corners=[[x, y] for x, y in body.corners],
            settings=body.settings,
            design=body.design,
        )
    except NoSuchPhoto as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    return PlacementResponse(
        corners=[(x, y) for x, y in row.corners], settings=row.settings, design=row.design
    )


@router.post("/photos/{photo_id}/print", summary="Print the design onto the photograph")
def print_photo(
    photo_id: uuid.UUID,
    design: str,
    session: SessionDependency,
    settings: SettingsDependency,
) -> Response:
    """The rendered image itself.

    Returned as bytes rather than stored: this is looked at, adjusted and looked at
    again, and keeping every intermediate render would fill the disk with rejects.
    Saving the one that is right is a separate decision.
    """
    photo = session.get(Photo, photo_id)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such photograph.")

    store = FilesystemAssetStore(settings.assets_root_resolved)
    try:
        photo_bytes = store.load(photo.relative_path)
    except AssetStoreError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="The image file is missing."
        ) from error

    try:
        printed = print_on_photo(
            session,
            assets_root=settings.assets_root_resolved,
            photo_bytes=photo_bytes,
            photo_id=photo_id,
            design_name=design,
        )
    except NotPlaced as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except NoSuchDesign as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    buffer = io.BytesIO()
    printed.save(buffer, format="PNG")
    # Never cached: the whole point is that the next render is different.
    return Response(
        content=buffer.getvalue(),
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )
