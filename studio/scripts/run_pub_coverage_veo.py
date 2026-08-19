#!/usr/bin/env python3
"""Animate one approved scene observation with bounded Veo motion.

The supplied first frame is already the camera composition. A direct shot master
is preferred when the scene owns one with this shot name; older scenes continue
to resolve their approved coverage frame. Veo is never asked to invent a new
camera composition before it starts moving.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.adapters.google_media import GoogleVideoClient, GoogleVideoRequest
from app.config import get_settings
from app.services.veo_prompt import build_motion_prompt


def resolve_seed(scene_key: str, shot: str):
    """Resolve the exact approved first frame, preferring a direct shot master."""
    from app.adapters.asset_store import FilesystemAssetStore
    from app.db.session import get_session_factory
    from app.services.coverage_library import CoverageRejected, resolve_veo_seed
    from app.services.reference_resolution import ReferenceUnavailable
    from app.services.scene_shot_library import (
        DirectShotNotFound,
        DirectShotUnavailable,
        resolve as resolve_direct_shot,
    )

    store = FilesystemAssetStore(get_settings().assets_root_resolved)
    try:
        with get_session_factory()() as session:
            try:
                resolved = resolve_direct_shot(session, store, scene_key=scene_key, name=shot)
                return resolved, "direct_shot_master"
            except DirectShotNotFound:
                resolved = resolve_veo_seed(session, store, scene_key=scene_key, name=shot)
                return resolved, "legacy_coverage"
            except DirectShotUnavailable:
                raise
    except (CoverageRejected, ReferenceUnavailable, DirectShotUnavailable) as error:
        raise SystemExit(f"{error} No provider call made.") from error


def scene_lineage(seed: Path, scene_key: str) -> dict:
    """Legacy explicit-file verification."""
    from app.adapters.asset_store import FilesystemAssetStore
    from app.config import get_settings
    from app.db.session import get_session_factory
    from app.services.reference_resolution import ReferenceUnavailable, verify_coverage_seed

    store = FilesystemAssetStore(get_settings().assets_root_resolved)
    try:
        with get_session_factory()() as session:
            return verify_coverage_seed(session, store, seed=seed, scene_key=scene_key)
    except ReferenceUnavailable as error:
        raise SystemExit(f"{error} No provider call made.") from error


DEV_MODEL = "veo-3.1-lite-generate-preview"
DEV_RESOLUTION = "720p"


def motion_prompt(scene_key: str, shot: str) -> str:
    """Use a saved per-master override before repo-configured direction."""
    from app.db.session import get_session_factory
    from app.services.scene_shot_library import DirectShotNotFound, by_scene_name, effective_motion_prompt

    with get_session_factory()() as session:
        try:
            direct = by_scene_name(session, scene_key, shot)
        except DirectShotNotFound:
            direct = None
        if direct is not None:
            prompt, _source = effective_motion_prompt(direct)
            if prompt:
                return build_motion_prompt(prompt)

    worlds = get_settings().worlds_root_resolved
    for candidate in (f"{scene_key}.{shot}.veo-motion.txt", f"{scene_key}.veo-motion.txt"):
        for shots in sorted(worlds.glob("*/shots")):
            path = shots / candidate
            if path.is_file():
                return build_motion_prompt(path.read_text(encoding="utf-8"))
    raise SystemExit(
        f"{scene_key}/{shot}: no motion direction. Save one in Scenes or write "
        f"worlds/<world>/shots/{scene_key}.{shot}.veo-motion.txt."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", help="Legacy: a file. Omit to resolve the approved frame.")
    parser.add_argument("--expected-sha256", help="Required with --seed.")
    parser.add_argument("--shot", required=True)
    parser.add_argument("--scene", required=True)
    args = parser.parse_args()

    if args.seed:
        if not args.expected_sha256:
            raise SystemExit("--seed requires --expected-sha256")
        seed = Path(args.seed).resolve()
        if not seed.is_file():
            raise SystemExit(f"missing seed: {seed}")
        data = seed.read_bytes()
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha != args.expected_sha256:
            raise SystemExit(
                f"seed SHA mismatch: expected {args.expected_sha256}, got {actual_sha}"
            )
        lineage = scene_lineage(seed, args.scene)
        lineage["first_frame_source"] = "legacy_explicit_file"
        seed_path = str(seed)
        source_format = "PNG" if seed.suffix.lower() == ".png" else "JPEG"
        with Image.open(BytesIO(data)) as image:
            source_dimensions = list(image.size)
    else:
        resolved, source_kind = resolve_seed(args.scene, args.shot)
        data = resolved.data
        seed_path = None
        actual_sha = resolved.sha256
        source_dimensions = [resolved.width, resolved.height]
        source_format = "PNG" if resolved.mime_type == "image/png" else "JPEG"
        lineage = {
            "scene": args.scene,
            "shot": args.shot,
            "first_frame_source": source_kind,
            "first_frame_asset_id": str(resolved.asset_id),
            "first_frame_sha256": resolved.sha256,
        }

    width, height = source_dimensions
    aspect_ratio = "16:9" if width >= height else "9:16"

    settings = get_settings()
    if not settings.google_media_live or settings.gemini_api_key is None:
        raise SystemExit("Google media not live")

    mime = "image/png" if source_format == "PNG" else "image/jpeg"
    client = GoogleVideoClient(
        api_key=settings.gemini_api_key.get_secret_value(),
        model=DEV_MODEL,
        poll_seconds=settings.google_video_poll_seconds,
        timeout_seconds=settings.google_video_timeout_seconds,
    )
    prompt = motion_prompt(args.scene, args.shot)
    result = client.generate(
        GoogleVideoRequest(
            prompt=prompt,
            first_frame=data,
            first_frame_mime=mime,
            aspect_ratio=aspect_ratio,
            resolution=DEV_RESOLUTION,
        )
    )

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "var/renderer-validation" / args.scene / f"{stamp}-coverage-{args.shot}"
    out.mkdir(parents=True, exist_ok=True)
    raw = out / "video-generated.mp4"
    raw.write_bytes(result.data)
    manifest = {
        **lineage,
        "shot": args.shot,
        "experiment": "approved-first-frame-to-bounded-motion-veo",
        "generated_at": stamp,
        "model": result.model,
        "aspect_ratio": aspect_ratio,
        "resolution": DEV_RESOLUTION,
        "seed_path": seed_path,
        "seed_sha256": actual_sha,
        "source_dimensions": source_dimensions,
        "source_format": source_format,
        "camera": "composition_locked_observational_handheld",
        "prompt_contract": "bounded_motion_state_v1",
        "audio": "strip_in_post",
        "raw_video_sha256": hashlib.sha256(result.data).hexdigest(),
        "manual_gate": "inspect identity continuity motion realism and usable seconds",
    }
    silent = out / "video-1.mp4"
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(raw), "-map", "0:v:0", "-c:v", "copy", "-an", str(silent)],
            check=True,
            capture_output=True,
        )
        streams = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream=index",
                "-of",
                "csv=p=0",
                str(silent),
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if streams:
            raise SystemExit(f"audio survived the strip: {streams}")
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=width,height,r_frame_rate",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(silent),
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        (out / "probe.json").write_text(probe)
        silent_bytes = silent.read_bytes()
        manifest["silent_video_sha256"] = hashlib.sha256(silent_bytes).hexdigest()
        manifest["silent_video_bytes"] = len(silent_bytes)
        manifest["audio"] = "stripped"
        (out / "video-1.sha256").write_text(manifest["silent_video_sha256"])
    else:
        manifest["audio"] = "strip_pending_no_ffmpeg"

    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "motion-prompt.txt").write_text(prompt)
    print(f"RESULT_DIR={out}")


if __name__ == "__main__":
    main()
