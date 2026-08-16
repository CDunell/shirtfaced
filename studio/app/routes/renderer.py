"""Renderer validation endpoints.

These endpoints expose the benchmark plan and per-scene production packages. They do
not initiate billable calls; generation remains behind explicit manual action.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.services.renderer_validation import harness_manifest, scene_package

router = APIRouter(prefix="/api/renderer", tags=["renderer"])


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
