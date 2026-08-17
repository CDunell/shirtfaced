# ruff: noqa: E501
"""Renderer validation endpoints."""

from __future__ import annotations

from typing import Any, NoReturn

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.services.renderer_validation import harness_manifest, scene_package

router = APIRouter(prefix="/api/renderer", tags=["renderer"])
MAX_CANONICAL_BYTES = 50 * 1024 * 1024


# The six-slot cast installer was here. It wrote two fixed filenames for three
# characters, which is why Damo's third photograph had nowhere to go, and why
# renaming the frames on 17 August 2026 broke every caller at once. Retired at
# the Phase 5 cutover: the cast is `cast_members` + `visual_assets`, references
# resolve by asset ID and SHA, and uploads happen in the Cast bench.
@router.get("/cast-upload", include_in_schema=False, response_model=None)
@router.post("/cast-upload", include_in_schema=False, response_model=None)
def cast_upload_retired() -> NoReturn:
    raise HTTPException(
        410,
        "The fixed six-slot cast installer is gone. Cast references are managed in Studio under Cast, or POST /api/cast/{slug}/assets. A member may hold any number of references, each with a role and an approval state.",
    )


# And the scene-reference uploader was here. It wrote one fixed
# `composition-gpt.*` file into `var/scene-references/pub-1105/` -- a scene the
# world's own canon calls W01-P28, in a directory whose name was the only place
# the other name ever came from. Retired for the same reason as the cast
# installer: a master is a `scene_masters` row over an ingested asset, resolved
# by SHA, and the scene it belongs to is named once.
@router.get("/scene-reference-upload", include_in_schema=False, response_model=None)
@router.post("/scene-reference-upload", response_model=None)
def scene_reference_upload_retired() -> NoReturn:
    raise HTTPException(
        410,
        "The fixed scene-reference uploader is gone. Register a scene master in Studio under Scenes, or POST /api/scenes/{scene_key}/masters. The pub scene is W01-P28.",
    )


@router.get("/validation")
def validation_manifest() -> dict[str, Any]:
    s = get_settings()
    return harness_manifest(
        google_enabled=s.google_media_live,
        image_model=s.google_image_model,
        video_model=s.google_video_model,
    ) | {"billable_generation_exposed": False}


@router.get("/validation/{scene_id}")
def validation_scene(scene_id: str) -> dict[str, Any]:
    try:
        return scene_package(scene_id)
    except KeyError as error:
        raise HTTPException(404, "Unknown validation scene") from error
