# ruff: noqa: E501
"""Renderer validation endpoints."""

from __future__ import annotations

import hashlib
import io
import os
from typing import Annotated, Any, NoReturn

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from PIL import Image

from app.config import PROJECT_ROOT, get_settings
from app.services.renderer_validation import harness_manifest, scene_package

router = APIRouter(prefix="/api/renderer", tags=["renderer"])
MAX_CANONICAL_BYTES = 50 * 1024 * 1024
SCENE_REFERENCE_ROOT = PROJECT_ROOT / "var" / "scene-references"
SCENE_REFERENCE_FORM = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font-family:system-ui;max-width:680px;margin:auto;padding:24px;background:#111;color:#eee}input,button{width:100%;margin:16px 0;padding:14px}button{font-weight:800}</style></head><body><h1>pub-1105 composition reference</h1><p>Upload the approved GPT composition/energy reference once. It is stored persistently and never deployed from Git.</p><form method="post" enctype="multipart/form-data"><input required type="file" name="reference" accept="image/png,image/jpeg,.png,.jpg,.jpeg"><button>Validate and install reference</button></form><p>No Gemini or Veo call occurs here.</p></body></html>"""


async def _read_image(
    label: str, upload: UploadFile, png_only: bool = False
) -> tuple[bytes, dict[str, Any]]:
    data = await upload.read(MAX_CANONICAL_BYTES + 1)
    if not data:
        raise HTTPException(400, f"{label}: empty upload")
    if len(data) > MAX_CANONICAL_BYTES:
        raise HTTPException(413, f"{label}: exceeds 50 MB")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            fmt = image.format
            width, height = image.size
            if png_only and fmt != "PNG":
                raise HTTPException(400, f"{label}: source must be PNG")
            if fmt not in {"PNG", "JPEG"}:
                raise HTTPException(400, f"{label}: source must be PNG/JPEG")
            if width < 256 or height < 256:
                raise HTTPException(400, f"{label}: implausibly small {width}x{height}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, f"{label}: unreadable/corrupt image") from exc
    return data, {
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "width": width,
        "height": height,
        "format": fmt,
    }


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


@router.get("/scene-reference-upload", response_class=HTMLResponse, include_in_schema=False)
def scene_reference_upload_form() -> str:
    return SCENE_REFERENCE_FORM


@router.post("/scene-reference-upload")
async def scene_reference_upload(reference: Annotated[UploadFile, File()]) -> dict[str, Any]:
    data, meta = await _read_image("pub-1105 composition reference", reference, False)
    root = SCENE_REFERENCE_ROOT / "pub-1105"
    root.mkdir(parents=True, exist_ok=True)
    ext = ".png" if meta["format"] == "PNG" else ".jpg"
    target = root / ("composition-gpt" + ext)
    tmp = root / (".composition-upload" + ext)
    tmp.write_bytes(data)
    os.replace(tmp, target)
    return {
        "status": "installed",
        "scene": "pub-1105",
        "role": "composition-energy-reference",
        "path": str(target.relative_to(PROJECT_ROOT)),
        **meta,
        "provider_called": False,
    }


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
