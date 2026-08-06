"""Putting a design on a photograph.

Separate from the generation API because nothing here generates anything. It lists
what can be printed on, remembers where the design goes, and renders. No model is
called and nothing is billed, so a placement can be nudged as many times as it takes.
"""

from __future__ import annotations

import io
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.adapters.asset_store import AssetStoreError, FilesystemAssetStore
from app.config import Settings, get_settings
from app.db.models import GenerationAttempt, ImageAsset, Shot, World
from app.db.session import get_db_session
from app.domain.enums import AssetKind, AttemptState
from app.services.print_service import (
    NoSuchDesign,
    NoSuchPhoto,
    NotPlaced,
    available_designs,
    print_on_photo,
    read_placement,
    save_placement,
)

router = APIRouter(prefix="/api", tags=["printing"])

SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


class DesignResponse(BaseModel):
    """A design file that can be printed."""

    name: str


class PhotoResponse(BaseModel):
    """An approved photograph, and whether a design has been placed on it."""

    asset_id: uuid.UUID
    url: str
    shot_external_id: str
    shot_title: str
    hero_product: str | None
    placed: bool


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


@router.get("/designs", summary="Designs that can be printed")
def list_designs(settings: SettingsDependency) -> list[DesignResponse]:
    """Empty until artwork exists, which is a state rather than a failure."""
    return [
        DesignResponse(name=design.name)
        for design in available_designs(settings.assets_root_resolved)
    ]


@router.get("/worlds/{world_slug}/photos", summary="Photographs a design can go on")
def list_photos(world_slug: str, session: SessionDependency) -> list[PhotoResponse]:
    """Approved frames only.

    A rejected attempt is not a photograph anybody is going to sell from, and
    offering it makes the list harder to use for no gain.
    """
    attempts = (
        session.execute(
            select(GenerationAttempt)
            .join(Shot)
            .join(World)
            .where(World.slug == world_slug, GenerationAttempt.state == AttemptState.APPROVED)
            .options(selectinload(GenerationAttempt.shot), selectinload(GenerationAttempt.assets))
            .order_by(Shot.sequence)
        )
        .scalars()
        .all()
    )

    photos: list[PhotoResponse] = []
    for attempt in attempts:
        original = next(
            (asset for asset in attempt.assets if asset.kind == AssetKind.ORIGINAL), None
        )
        if original is None:
            continue
        photos.append(
            PhotoResponse(
                asset_id=original.id,
                url=f"/assets/{original.id}",
                shot_external_id=attempt.shot.external_id,
                shot_title=attempt.shot.title,
                hero_product=attempt.shot.hero_product,
                placed=read_placement(session, original.id) is not None,
            )
        )
    return photos


@router.get("/photos/{asset_id}/placement", summary="Where the design sits")
def get_placement(asset_id: uuid.UUID, session: SessionDependency) -> PlacementResponse | None:
    """Null when nobody has placed one yet."""
    row = read_placement(session, asset_id)
    if row is None:
        return None
    return PlacementResponse(
        corners=[(x, y) for x, y in row.corners], settings=row.settings, design=row.design
    )


@router.put("/photos/{asset_id}/placement", summary="Move the design")
def put_placement(
    asset_id: uuid.UUID, body: PlacementBody, session: SessionDependency
) -> PlacementResponse:
    """Replace the placement. Moving a design is an edit, not a new opinion."""
    try:
        row = save_placement(
            session,
            asset_id=asset_id,
            corners=[[x, y] for x, y in body.corners],
            settings=body.settings,
            design=body.design,
        )
    except NoSuchPhoto as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    return PlacementResponse(
        corners=[(x, y) for x, y in row.corners], settings=row.settings, design=row.design
    )


@router.post("/photos/{asset_id}/print", summary="Print the design onto the photograph")
def print_photo(
    asset_id: uuid.UUID,
    design: str,
    session: SessionDependency,
    settings: SettingsDependency,
) -> Response:
    """The rendered image itself.

    Returned as bytes rather than stored: this is looked at, adjusted and looked at
    again, and keeping every intermediate render would fill the disk with rejects.
    Saving the one that is right is a separate decision.
    """
    asset = session.get(ImageAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such photograph.")

    store = FilesystemAssetStore(settings.assets_root_resolved)
    try:
        photo_bytes = store.load(asset.relative_path)
    except AssetStoreError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="The image file is missing."
        ) from error

    try:
        printed = print_on_photo(
            session,
            assets_root=settings.assets_root_resolved,
            photo_bytes=photo_bytes,
            asset_id=asset_id,
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
