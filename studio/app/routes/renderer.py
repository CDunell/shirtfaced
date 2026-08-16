# ruff: noqa: E501
"""Renderer validation endpoints.

These endpoints expose the benchmark plan and per-scene production packages. They do
not initiate billable calls; generation remains behind explicit manual action.
"""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from PIL import Image

from app.config import PROJECT_ROOT, get_settings
from app.services.renderer_validation import harness_manifest, scene_package

router = APIRouter(prefix="/api/renderer", tags=["renderer"])

MAX_CANONICAL_BYTES = 50 * 1024 * 1024
CANONICAL_CAST_ROOT = PROJECT_ROOT / "var" / "cast"
CANONICAL_SLOTS = (
    ("damo_full", "Damo — full length", Path("damo/a-full-length.png")),
    ("damo_head", "Damo — head / shoulders", Path("damo/b-head-shoulders.png")),
    ("brock_full", "Brock — full length", Path("brock/a-full-length.png")),
    ("brock_head", "Brock — head / shoulders", Path("brock/b-head-shoulders.png")),
    ("emma_head", "Emma — head / shoulders", Path("emma/b-head-shoulders.png")),
    ("emma_full", "Emma — full length", Path("emma/a-full-length.png")),
)

UPLOAD_FORM = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SHIRTFACED Canon Upload</title>
<style>
body{font-family:system-ui,sans-serif;max-width:720px;margin:0 auto;padding:24px;background:#111;color:#eee}
h1{font-size:24px;margin:0 0 8px}p{line-height:1.45;color:#bbb}.slot{margin:18px 0;padding:16px;border:1px solid #444;border-radius:10px}.slot label{display:block;font-weight:700;margin-bottom:8px}input{width:100%}button{font:inherit;font-weight:800;padding:14px 18px;border:0;border-radius:8px;background:#eee;color:#111;width:100%;margin-top:12px}.note{font-size:14px}.order{color:#fff;font-weight:700}
</style>
</head>
<body>
<h1>World 01 — canonical cast originals</h1>
<p>Upload all six authoritative PNG originals in one transaction. Nothing is converted here. If any file is invalid, nothing is replaced.</p>
<form method="post" enctype="multipart/form-data">
<div class="slot"><label>1. Damo — full length</label><input required type="file" name="damo_full" accept="image/png,.png"></div>
<div class="slot"><label>2. Damo — head / shoulders</label><input required type="file" name="damo_head" accept="image/png,.png"></div>
<div class="slot"><label>3. Brock — full length</label><input required type="file" name="brock_full" accept="image/png,.png"></div>
<div class="slot"><label>4. Brock — head / shoulders</label><input required type="file" name="brock_head" accept="image/png,.png"></div>
<div class="slot"><label>5. Emma — head / shoulders</label><input required type="file" name="emma_head" accept="image/png,.png"></div>
<div class="slot"><label>6. Emma — full length</label><input required type="file" name="emma_full" accept="image/png,.png"></div>
<button type="submit">Validate and install all six</button>
</form>
<p class="note">Canonical originals are stored under persistent Studio <code>var/cast</code>. Existing files are backed up before replacement. This page does not call Gemini or Veo.</p>
</body>
</html>"""


async def _read_png(slot: str, upload: UploadFile) -> tuple[bytes, dict[str, object]]:
    data = await upload.read(MAX_CANONICAL_BYTES + 1)
    if not data:
        raise HTTPException(status_code=400, detail=f"{slot}: empty upload")
    if len(data) > MAX_CANONICAL_BYTES:
        raise HTTPException(status_code=413, detail=f"{slot}: file exceeds 50 MB")

    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            if image.format != "PNG":
                raise HTTPException(status_code=400, detail=f"{slot}: source must be a real PNG")
            width, height = image.size
            if width < 256 or height < 256:
                raise HTTPException(
                    status_code=400, detail=f"{slot}: implausibly small image {width}x{height}"
                )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"{slot}: unreadable or corrupt image") from exc

    sha256 = hashlib.sha256(data).hexdigest()
    return data, {
        "bytes": len(data),
        "sha256": sha256,
        "width": width,
        "height": height,
        "format": "PNG",
    }


@router.get("/cast-upload", response_class=HTMLResponse, include_in_schema=False)
def cast_upload_form() -> str:
    """Phone-friendly canonical cast installer; access is enforced by Cloudflare Access."""
    return UPLOAD_FORM


@router.post("/cast-upload", summary="Install the six canonical World 01 cast originals")
async def cast_upload(
    damo_full: Annotated[UploadFile, File()],
    damo_head: Annotated[UploadFile, File()],
    brock_full: Annotated[UploadFile, File()],
    brock_head: Annotated[UploadFile, File()],
    emma_head: Annotated[UploadFile, File()],
    emma_full: Annotated[UploadFile, File()],
) -> dict[str, object]:
    """Validate all six originals, then install them atomically into persistent storage."""
    supplied = {
        "damo_full": damo_full,
        "damo_head": damo_head,
        "brock_full": brock_full,
        "brock_head": brock_head,
        "emma_head": emma_head,
        "emma_full": emma_full,
    }

    validated: dict[str, tuple[bytes, dict[str, object]]] = {}
    for field, label, _relative_path in CANONICAL_SLOTS:
        validated[field] = await _read_png(label, supplied[field])

    CANONICAL_CAST_ROOT.mkdir(parents=True, exist_ok=True)
    backup_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_root = PROJECT_ROOT / "var" / "cast-backups" / backup_stamp

    with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "var", prefix="cast-stage-") as td:
        staging_root = Path(td)
        for field, _label, relative_path in CANONICAL_SLOTS:
            staged = staging_root / relative_path
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(validated[field][0])

        existing = [
            relative_path
            for _field, _label, relative_path in CANONICAL_SLOTS
            if (CANONICAL_CAST_ROOT / relative_path).is_file()
        ]
        if existing:
            for relative_path in existing:
                source = CANONICAL_CAST_ROOT / relative_path
                backup = backup_root / relative_path
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, backup)

        installed: list[dict[str, object]] = []
        for field, label, relative_path in CANONICAL_SLOTS:
            target = CANONICAL_CAST_ROOT / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            staged = staging_root / relative_path
            os.replace(staged, target)
            metadata = validated[field][1]
            installed.append(
                {
                    "slot": field,
                    "label": label,
                    "path": str(target.relative_to(PROJECT_ROOT)),
                    **metadata,
                }
            )

    return {
        "status": "installed",
        "count": 6,
        "canonical_root": str(CANONICAL_CAST_ROOT.relative_to(PROJECT_ROOT)),
        "backup": str(backup_root.relative_to(PROJECT_ROOT)) if existing else None,
        "files": installed,
        "provider_called": False,
    }


@router.get("/validation")
def validation_manifest() -> dict[str, object]:
    settings = get_settings()
    return harness_manifest(
        google_enabled=settings.google_media_live,
        image_model=settings.google_image_model,
        video_model=settings.google_video_model,
    ) | {
        "google_execution": {
            "enabled_requested": settings.google_media_enabled,
            "key_configured": settings.gemini_api_key is not None,
            "image_size": settings.google_image_size,
            "video_resolution": settings.google_video_resolution,
            "video_poll_seconds": settings.google_video_poll_seconds,
            "video_timeout_seconds": settings.google_video_timeout_seconds,
        },
        "budgets_usd": {
            "scene": settings.renderer_scene_budget_usd,
            "validation": settings.renderer_validation_budget_usd,
            "monthly": settings.renderer_monthly_budget_usd,
        },
        "candidate_policy": {
            "seed": settings.renderer_seed_candidates,
            "video": settings.renderer_video_candidates,
        },
        "billable_generation_exposed": False,
    }


@router.get("/validation/{scene_id}")
def validation_scene(scene_id: str) -> dict[str, object]:
    try:
        return scene_package(scene_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Unknown validation scene") from error
