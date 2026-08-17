#!/usr/bin/env python3
"""Run one silent Veo coverage test: Damo -> Emma/Brock whip pan from the wide pub master."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.adapters.google_media import GoogleVideoClient, GoogleVideoRequest
from app.config import get_settings

DEV_MODEL = "veo-3.1-lite-generate-preview"
DEV_RESOLUTION = "720p"

PROMPT = """Continue this exact supplied pub image as one piece of accidental handheld vertical phone footage from inside the same packed Australian pub at the same instant. Preserve the existing room, red-lit back bar, pool table, hanging lamp, stool and full beer, crowd density, lighting, wardrobe, faces, body positions and spatial relationships.

CAMERA MOVE: begin from the existing Damo side of the scene for only a fraction of a second, then make one fast, physically plausible handheld whip-pan to camera-right across the existing crowd. The pan itself should contain natural directional motion blur and imperfect phone-camera movement. Land on the woman who is ALREADY elevated at camera-right with both arms up, together with the man ALREADY beneath/carrying her. Hold on that existing pair briefly after the pan settles while they simply continue the action already present in the source frame.

The room must continue independently during the move: people sing, jostle, talk, raise hands and look in different directions. Nobody notices the camera. Nobody reorganises around Damo or around the woman. Do not make either of them performers or heroes. Preserve competing foreground obstruction and ugly late-night pub exposure.

This is a camera observation of one continuous event, not a new scene. Do not invent a new pub, do not replace or add principal people, do not change Damo's olive/grey-green shirt, black cap, cue, pool-table position or the existing woman/man pair at camera-right. No cuts, no camera teleport, no slow motion, no staged audience semicircle, no tattoos, no jewellery added to Damo, no halo, no text. AUDIO WILL BE ADDED IN POST; generated audio is irrelevant."""


def scene_lineage(seed: Path, scene_key: str) -> dict:
    """Refuse anything that is not coverage of this scene's approved master."""
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--scene", default="pub-1105")
    args = parser.parse_args()

    seed = Path(args.seed).resolve()
    if not seed.is_file():
        raise SystemExit(f"missing seed: {seed}")

    data = seed.read_bytes()
    actual_sha = hashlib.sha256(data).hexdigest()
    if actual_sha != args.expected_sha256:
        raise SystemExit(f"seed SHA mismatch: expected {args.expected_sha256}, got {actual_sha}")

    lineage = scene_lineage(seed, args.scene)

    with Image.open(seed) as image:
        source_dimensions = list(image.size)
        source_format = image.format

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

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "var/renderer-validation" / args.scene / f"{stamp}-veo-whip-pan"
    out.mkdir(parents=True, exist_ok=True)

    result = client.generate(
        GoogleVideoRequest(
            prompt=PROMPT,
            first_frame=data,
            first_frame_mime=mime,
            aspect_ratio="9:16",
            resolution=DEV_RESOLUTION,
        )
    )

    raw = out / "video-generated.mp4"
    raw.write_bytes(result.data)
    final = out / "video-1.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw), "-map", "0:v:0", "-c:v", "copy", "-an", str(final)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    raw.unlink()

    final_data = final.read_bytes()
    manifest = {
        **lineage,
        "shot": "1C-whip-pan-damo-to-emma-brock",
        "experiment": "wide-master-spatial-whip-pan-silent-veo",
        "generated_at": stamp,
        "model": result.model,
        "aspect_ratio": "9:16",
        "resolution": DEV_RESOLUTION,
        "seed_path": str(seed),
        "seed_sha256": actual_sha,
        "source_dimensions": source_dimensions,
        "source_format": source_format,
        "camera_move": "fast_handheld_whip_pan_right_then_settle",
        "target": "existing_camera_right_woman_and_man_beneath_her",
        "video_sha256": hashlib.sha256(final_data).hexdigest(),
        "audio": "stripped_for_post",
        "manual_gate": "inspect_motion_and_landing_then_harvest_usable_fragment",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "motion-prompt.txt").write_text(PROMPT)
    print(f"RESULT_DIR={out}")


if __name__ == "__main__":
    main()
