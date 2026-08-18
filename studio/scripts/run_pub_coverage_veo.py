#!/usr/bin/env python3
"""Animate one approved 9:16 coverage crop with minimal Veo motion.

The supplied crop is already the camera composition. Veo is not asked to reveal
new geography or perform a major reframing; it only animates the established shot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.adapters.google_media import GoogleVideoClient, GoogleVideoRequest
from app.config import get_settings


def resolve_seed(scene_key: str, shot: str):
    """The approved coverage frame for this shot, or a refusal.

    Phase E: a Veo run names a shot in a scene, never a file. Everything a path
    could get wrong -- an unapproved frame, one cut from a superseded master, a
    lookalike sitting in the same directory -- is checked before any spend.
    """
    from app.adapters.asset_store import FilesystemAssetStore
    from app.db.session import get_session_factory
    from app.services.coverage_library import CoverageRejected, resolve_veo_seed
    from app.services.reference_resolution import ReferenceUnavailable

    store = FilesystemAssetStore(get_settings().assets_root_resolved)
    try:
        with get_session_factory()() as session:
            return resolve_veo_seed(session, store, scene_key=scene_key, name=shot)
    except (CoverageRejected, ReferenceUnavailable) as error:
        raise SystemExit(f"{error} No provider call made.") from error


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


DEV_MODEL = "veo-3.1-lite-generate-preview"
DEV_RESOLUTION = "720p"

PROMPTS = {
    "emma-brock": """Animate this exact supplied 9:16 pub crop as a short piece of accidental handheld phone footage from the same instant. The camera composition is already correct: DO NOT pan, zoom, reframe, reveal new parts of the pub, or rebuild the environment. Keep the existing red-lit back bar, pool table edge, hanging lamp, crowd positions, wardrobe, faces and spatial relationships.

The elevated woman already in frame continues cheering and singing with natural upper-body movement. The man directly beneath/supporting her continues reacting and moving with the crowd. Nearby punters jostle, shout, laugh, raise hands and shift independently. Foreground bodies may partially obstruct the frame for moments. Movement should feel messy and physically plausible, not choreographed.

Preserve the exact people and clothing from the supplied frame. Do not replace faces, change garments, add principal people, clear space around the pair, create a performer/audience relationship, alter the bar geography, or move the pool table. Keep ugly uneven late-night pub lighting and documentary exposure. Nobody looks at or acknowledges the camera. No cuts, no slow motion, no text. Audio will be replaced in post.""",
    "damo": """Animate this exact supplied 9:16 pub crop as a short piece of accidental handheld phone footage from the same instant. The camera composition is already correct: DO NOT pan, zoom, reframe, reveal new parts of the pub, or rebuild the environment. Preserve the pool table, stool and beer, crowd, lighting, Damo's olive/grey-green shirt, his bare head, overhead cue and every visible spatial relationship.

Damo continues roaring the chorus with the cue overhead while the crowd around him moves independently: jostling, shouting, laughing, shifting and occasionally crossing the foreground. Keep his feet planted exactly on the pool table and preserve physically plausible weight and contact. Nobody reorganises around him or treats him as a performer.

Preserve the exact people and clothing from the supplied frame. No tattoos or jewellery added, no audience semicircle, no hero lighting, no cuts, no slow motion, no text. Audio will be replaced in post.""",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", help="Legacy: a file. Omit to resolve the approved frame.")
    parser.add_argument("--expected-sha256", help="Required with --seed.")
    parser.add_argument("--shot", choices=sorted(PROMPTS), required=True)
    parser.add_argument("--scene", default="W01-P28")
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
        source_format = "PNG" if seed.suffix.lower() == ".png" else "JPEG"
        with Image.open(BytesIO(data)) as image:
            source_dimensions = list(image.size)
    else:
        resolved = resolve_seed(args.scene, args.shot)
        data = resolved.data
        source_dimensions = [resolved.width, resolved.height]
        source_format = "PNG" if resolved.mime_type == "image/png" else "JPEG"
        lineage = {
            "scene": args.scene,
            "coverage_shot": args.shot,
            "coverage_frame_asset_id": str(resolved.asset_id),
            "coverage_frame_sha256": resolved.sha256,
        }

    if source_dimensions[0] * 16 != source_dimensions[1] * 9:
        raise SystemExit(f"seed must be exact 9:16, got {source_dimensions}")

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
    prompt = PROMPTS[args.shot]
    result = client.generate(
        GoogleVideoRequest(
            prompt=prompt,
            first_frame=data,
            first_frame_mime=mime,
            aspect_ratio="9:16",
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
        "experiment": "approved-9x16-coverage-crop-to-minimal-motion-veo",
        "generated_at": stamp,
        "model": result.model,
        "aspect_ratio": "9:16",
        "resolution": DEV_RESOLUTION,
        "seed_path": str(seed),
        "seed_sha256": actual_sha,
        "source_dimensions": source_dimensions,
        "source_format": source_format,
        "camera": "composition_locked_no_pan_no_reframe",
        "audio": "strip_in_post",
        "raw_video_sha256": hashlib.sha256(result.data).hexdigest(),
        "manual_gate": "inspect identity geography contact and usable seconds",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "motion-prompt.txt").write_text(prompt)
    print(f"RESULT_DIR={out}")


if __name__ == "__main__":
    main()
