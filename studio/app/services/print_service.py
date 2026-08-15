"""The photograph library: bringing frames in, and finding them again.

This module used to print a design onto a photograph through a quadrilateral
dragged over the garment by hand, with the placement saved against the frame. That
path never got off the ground and was replaced by defined zones in real
millimetres, so it was removed on 15 August 2026 along with its table, its
``assets/designs`` file listing and the screen that drove it. The zone-based print
is ``app/services/approved_print.py`` and reads an approved design version.

What survives is the part that was never about printing: registering an approved
frame as a photograph, and taking one that was made elsewhere.
"""

from __future__ import annotations

import io
from pathlib import Path
from uuid import UUID, uuid4

from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore
from app.db.models import ImageAsset, Photo, PromptVariation
from app.domain.errors import StudioError


class NotAPhoto(StudioError):
    """The uploaded file is not an image this can print on."""


class NoSuchPrompt(StudioError):
    """The prompt a photograph is being attributed to does not exist."""


# What a browser will actually hand over, and what Pillow will open without help.
UPLOAD_FORMATS = frozenset({"PNG", "JPEG", "WEBP"})
UPLOADS_PREFIX = "photos/uploads"


def register_generated(session: Session, asset: ImageAsset, label: str) -> Photo:
    """The photograph row for an approved frame, made on first sight.

    Registering lazily rather than at approval keeps this feature out of the
    generation path entirely: nothing about approving an image had to change for a
    design to be printable on it.
    """
    existing = session.execute(
        select(Photo).where(Photo.attempt_id == asset.attempt_id)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    photo = Photo(
        relative_path=asset.relative_path,
        label=label,
        mime_type=asset.mime_type,
        width=asset.width or 0,
        height=asset.height or 0,
        attempt_id=asset.attempt_id,
    )
    session.add(photo)
    session.flush()
    return photo


def upload_photo(
    session: Session,
    store: AssetStore,
    *,
    data: bytes,
    filename: str,
    prompt_variation_id: UUID | None = None,
) -> Photo:
    """Take a photograph that this application did not make.

    The bytes are opened before anything is written: a file that Pillow cannot read
    is not a photograph, whatever it is called, and finding that out after storing it
    leaves rubbish in the asset store.

    ``prompt_variation_id`` records which prompt produced it. The frames are made
    elsewhere and brought back, so the moment of upload is the only moment anybody
    knows -- ask later and it is a memory test.
    """
    if prompt_variation_id is not None:
        attributed = session.get(PromptVariation, prompt_variation_id)
        if attributed is None:
            raise NoSuchPrompt(f"No prompt with id {prompt_variation_id}.")

    try:
        with Image.open(io.BytesIO(data)) as image:
            image_format = image.format
            width, height = image.size
    except (OSError, ValueError) as error:
        raise NotAPhoto("That file is not an image.") from error

    if image_format not in UPLOAD_FORMATS:
        raise NotAPhoto(f"{image_format or 'That file'} is not a format this can print on.")

    label = Path(filename).name or "photograph"
    suffix = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}[image_format]
    key = f"{UPLOADS_PREFIX}/{uuid4()}.{suffix}"
    store.save(key, data, f"image/{'jpeg' if suffix == 'jpg' else suffix}")

    photo = Photo(
        relative_path=key,
        label=label,
        mime_type=f"image/{'jpeg' if suffix == 'jpg' else suffix}",
        width=width,
        height=height,
        prompt_variation_id=prompt_variation_id,
    )
    session.add(photo)
    session.commit()
    return photo
