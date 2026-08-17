#!/usr/bin/env python3
"""Run one silent Veo candidate from an explicitly supplied approved master."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.adapters.google_media import GoogleVideoClient, GoogleVideoRequest
from app.config import get_settings

PROMPT = """Continue this exact first frame as accidental handheld vertical phone footage inside a packed Australian pub. The room is already going off independently. Every person continues their own pre-existing action: talking, singing toward the band, moving through the crowd, bumping friends, looking in different directions. Nobody reorganises around the man on the pool table and nobody treats him as a performer. He remains a punter inside the event, both boots planted on the pool table, cue held horizontally overhead in both fists, head back, eyes shut, roaring along with the chorus. The band remains the performance source. Preserve the stool and full beer on the table. Small natural movement only. The phone is physically inside the crowd and gets one minor bump/reframe. Preserve ugly late-night exposure, foreground obstruction, crowd density, competing focal activity and accidental framing. No cuts, no camera teleport, no slow motion, no added people, no audience formation around him, no tattoos, no hero lighting, no halo, no text. AUDIO WILL BE ADDED IN POST; do not rely on generated audio for storytelling."""


def scene_lineage(seed: Path, scene_key: str) -> dict:
    """Refuse anything that is not coverage of this scene's approved master."""
    from app.adapters.asset_store import FilesystemAssetStore
    from app.db.session import get_session_factory
    from app.services.reference_resolution import ReferenceUnavailable, verify_coverage_seed

    store = FilesystemAssetStore(get_settings().assets_root_resolved)
    try:
        with get_session_factory()() as session:
            return verify_coverage_seed(session, store, seed=seed, scene_key=scene_key)
    except ReferenceUnavailable as error:
        raise SystemExit(f"{error} No provider call made.") from error


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", required=True)
    p.add_argument("--arm", default="approved-master")
    p.add_argument("--scene", default="pub-1105")
    a = p.parse_args()
    seed = Path(a.seed).resolve()
    if not seed.is_file():
        raise SystemExit(f"missing seed: {seed}")
    lineage = scene_lineage(seed, a.scene)
    data = seed.read_bytes()
    s = get_settings()
    if not s.google_media_live or s.gemini_api_key is None:
        raise SystemExit("Google media not live")
    mime = "image/png" if seed.suffix.lower() == ".png" else "image/jpeg"
    client = GoogleVideoClient(
        api_key=s.gemini_api_key.get_secret_value(),
        model=s.google_video_model,
        poll_seconds=s.google_video_poll_seconds,
        timeout_seconds=s.google_video_timeout_seconds,
    )
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "var/renderer-validation" / a.scene / (stamp + "-veo-" + a.arm)
    out.mkdir(parents=True, exist_ok=True)
    r = client.generate(
        GoogleVideoRequest(
            prompt=PROMPT,
            first_frame=data,
            first_frame_mime=mime,
            aspect_ratio="9:16",
            resolution=s.google_video_resolution,
        )
    )
    raw = out / "video-generated.mp4"
    raw.write_bytes(r.data)
    final = out / "video-1.mp4"
    # Strip generated audio deterministically; World 01 sound is authored in post.
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw), "-map", "0:v:0", "-c:v", "copy", "-an", str(final)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    raw.unlink()
    final_data = final.read_bytes()
    m = {
        **lineage,
        "experiment": "approved-master-direct-silent-veo",
        "arm": a.arm,
        "generated_at": stamp,
        "model": r.model,
        "aspect_ratio": "9:16",
        "resolution": s.google_video_resolution,
        "seed_path": str(seed),
        "seed_sha256": hashlib.sha256(data).hexdigest(),
        "video_sha256": hashlib.sha256(final_data).hexdigest(),
        "audio": "stripped_for_post",
        "manual_gate": "keeper_segment_review",
    }
    (out / "manifest.json").write_text(json.dumps(m, indent=2))
    (out / "motion-prompt.txt").write_text(PROMPT)
    print(f"RESULT_DIR={out}")


if __name__ == "__main__":
    main()
