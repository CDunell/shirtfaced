#!/usr/bin/env python3
"""Run one explicitly-approved Veo I2V validation from the latest approved pub seed."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from app.adapters.google_media import GoogleVideoClient, GoogleVideoRequest
from app.config import get_settings

MOTION_PROMPT = """Continue this exact approved first frame as a short accidental vertical phone video in a packed Australian pub. Do not redesign Damo, wardrobe, pool table, stool, beer, band, lighting or room. Damo keeps both boots planted on the pool table and keeps the cue overhead while rocking naturally with the chorus; small believable body movement only, no choreographed pose change. The surrounding crowd and band move independently. A nearby patron lightly bumps the phone once, causing a brief imperfect handheld reframe. Preserve the dark late-night exposure and localized practical lighting. Nobody acknowledges the camera. No cuts, no camera teleport, no slow motion, no added text, no invented tattoos or identity marks."""


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", required=True)
    args = p.parse_args()
    seed = Path(args.seed).resolve()
    if not seed.is_file():
        raise SystemExit(f"missing approved seed: {seed}")
    data = seed.read_bytes()
    settings = get_settings()
    if not settings.google_media_live or settings.gemini_api_key is None:
        raise SystemExit("Google media not live; no provider call made")
    mime = "image/png" if seed.suffix.lower() == ".png" else "image/jpeg"
    client = GoogleVideoClient(
        api_key=settings.gemini_api_key.get_secret_value(),
        model=settings.google_video_model,
        poll_seconds=settings.google_video_poll_seconds,
        timeout_seconds=settings.google_video_timeout_seconds,
    )
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = PROJECT_ROOT / "var" / "renderer-validation" / "pub-1105" / (stamp + "-veo")
    out.mkdir(parents=True, exist_ok=True)
    result = client.generate(
        GoogleVideoRequest(
            prompt=MOTION_PROMPT,
            first_frame=data,
            first_frame_mime=mime,
            aspect_ratio="9:16",
            resolution=settings.google_video_resolution,
        )
    )
    video = out / "video-1.mp4"
    video.write_bytes(result.data)
    manifest = {
        "scene": "pub-1105",
        "generated_at": stamp,
        "model": result.model,
        "operation_name": result.operation_name,
        "aspect_ratio": "9:16",
        "resolution": settings.google_video_resolution,
        "seed_path": str(seed),
        "seed_sha256": hashlib.sha256(data).hexdigest(),
        "video_bytes": len(result.data),
        "video_sha256": hashlib.sha256(result.data).hexdigest(),
        "manual_gate": "final_video_review_required",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "motion-prompt.txt").write_text(MOTION_PROMPT, encoding="utf-8")
    print(f"generated Veo candidate: {video}")
    print(f"RESULT_DIR={out}")


if __name__ == "__main__":
    main()
