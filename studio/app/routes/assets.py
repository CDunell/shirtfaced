"""Serving stored images.

Only assets recorded in the database are served. The path comes from the row, not
from the request, so a crafted URL cannot reach a file the application did not write.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStoreError, FilesystemAssetStore
from app.config import Settings, get_settings
from app.db.models import ImageAsset
from app.db.session import get_db_session

router = APIRouter(prefix="/assets", tags=["assets"])

SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]

# Generated images are immutable and addressed by a UUID that never points at
# different bytes, so they can be cached indefinitely.
CACHE_CONTROL = "private, max-age=31536000, immutable"


@router.get("/{asset_id}", summary="Fetch a stored image")
def get_asset(
    asset_id: uuid.UUID, session: SessionDependency, settings: SettingsDependency
) -> Response:
    """Return one image by its identifier."""
    asset = session.execute(
        select(ImageAsset).where(ImageAsset.id == asset_id)
    ).scalar_one_or_none()

    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such image.")

    store = FilesystemAssetStore(settings.assets_root_resolved)
    try:
        data = store.load(asset.relative_path)
    except AssetStoreError as error:
        # The row exists but the bytes do not: the volume is missing or was cleared.
        # Say so rather than returning a misleading 404.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"The image is recorded but its file could not be read. {error}",
        ) from error

    return Response(
        content=data,
        media_type=asset.mime_type,
        headers={"Cache-Control": CACHE_CONTROL},
    )
