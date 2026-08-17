#!/usr/bin/env python3
"""Derive immutable 9:16 coverage frames from an approved scene master.

No generation occurs here. Every coverage frame is an original-pixel crop of the
master, locked by source SHA256 and recorded in a manifest.

Which image is the master is a database question, per scene, as of the Phase 5
cutover. ``--source`` used to be a path typed into a workflow trigger with its
hash beside it: self-consistent, and unable to say whether that file was the
scene's approved master or something sitting next to it. The four frames already
cut for pub-1105 cite a parent SHA that matches no file now on the box, which is
what that gap looks like once it has happened.

``--plan`` cuts a whole shot list from one resolution, which is what the
pub-1105 five-shot package in SHOTLIST.md needs: five windows onto one image,
resolved once, so a master cannot change halfway through a set of clips that are
meant to be simultaneous observations of the same moment.

``--source`` still works for cutting from an image that is deliberately not the
registered master. The frame is then marked ``explicit_source_off_master`` so
nothing downstream mistakes it for approved coverage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_master(scene_key: str) -> Any:
    """The scene's one approved master, or a refusal naming what is missing."""
    from app.adapters.asset_store import FilesystemAssetStore
    from app.config import get_settings
    from app.db.session import get_session_factory
    from app.services.reference_resolution import ReferenceUnavailable, resolve_scene_master

    store = FilesystemAssetStore(get_settings().assets_root_resolved)
    try:
        with get_session_factory()() as session:
            return resolve_scene_master(session, store, scene_key=scene_key)
    except ReferenceUnavailable as error:
        raise SystemExit(f"{error} Nothing cut.") from error


def cut_one(
    *,
    data: bytes,
    source_sha: str,
    source_label: str,
    master_asset_id: str | None,
    origin: str,
    scene: str,
    shot: str,
    x: int,
    y: int,
    height: int,
    out_root: str,
) -> Path:
    """One original-pixel 9:16 crop, and the manifest that makes it traceable."""
    with Image.open(BytesIO(data)) as image:
        image.load()
        sw, sh = image.size
        crop_h = height or sh
        crop_w = round(crop_h * 9 / 16)
        if crop_w * 16 != crop_h * 9:
            # Preserve exact pixels and exact 9:16 by reducing height to the nearest
            # multiple that gives an integer width. Never resize the master.
            crop_h = (crop_h // 16) * 16
            crop_w = crop_h * 9 // 16
        x0, y0 = x, y
        x1, y1 = x0 + crop_w, y0 + crop_h
        if x0 < 0 or y0 < 0 or x1 > sw or y1 > sh:
            raise SystemExit(f"crop outside source: source={sw}x{sh}, crop=({x0},{y0})-({x1},{y1})")
        crop = image.crop((x0, y0, x1, y1))
        if crop.size != (crop_w, crop_h):
            raise SystemExit("unexpected crop dimensions")

        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        out_dir = Path(out_root).resolve() / scene / "coverage" / shot
        out_dir.mkdir(parents=True, exist_ok=True)
        frame = out_dir / "frame.png"
        crop.save(frame, format="PNG")

    manifest = {
        "scene": scene,
        "shot": shot,
        "generated_at": stamp,
        "operation": "original_pixels_crop_only",
        "origin": origin,
        # The durable half of the lineage. A path can be renamed or overwritten;
        # this says which master these pixels came from, permanently.
        "source_master_asset_id": master_asset_id,
        "source_path": source_label,
        "source_sha256": source_sha,
        "source_dimensions": [sw, sh],
        "crop_box": [x0, y0, x1, y1],
        "crop_dimensions": [crop_w, crop_h],
        "aspect_ratio": "9:16",
        "frame_sha256": sha256(frame),
        "resized": False,
        "provider_called": False,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"FRAME={frame}")
    print(f"MANIFEST={out_dir / 'manifest.json'}")
    return frame


def cut_plan(plan_path: Path, out_root: str) -> None:
    """Cut every shot in a trigger, from one resolution of the scene's master."""
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    scene = plan["scene"]
    shots = plan.get("shots")
    if not shots:
        raise SystemExit(
            f"{plan_path.name}: no 'shots' list. Crop offsets belong to one master -- the "
            "offsets in earlier triggers were measured against a 1535px-wide image that is "
            "not the master any more, so they are not carried forward."
        )

    resolved = resolve_master(scene)
    print(f"MASTER={resolved.asset_id} SHA={resolved.sha256} {resolved.width}x{resolved.height}")
    for shot in shots:
        cut_one(
            data=resolved.data,
            source_sha=resolved.sha256,
            source_label=f"visual-asset:{resolved.asset_id}",
            master_asset_id=str(resolved.asset_id),
            origin="approved_scene_master",
            scene=scene,
            shot=str(shot["shot"]),
            x=int(shot["x"]),
            y=int(shot.get("y", 0)),
            height=int(shot.get("height", 0)),
            out_root=out_root,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", help="Trigger JSON with a shots list. Cuts all of them.")
    parser.add_argument("--scene", help="Required unless --plan names one.")
    parser.add_argument("--shot")
    parser.add_argument("--x", type=int)
    parser.add_argument("--y", type=int, default=0)
    parser.add_argument("--height", type=int, default=0, help="0 = full source height")
    parser.add_argument("--source", help="Cut from this file instead of the registered master.")
    parser.add_argument("--expected-sha256", help="Required with --source.")
    parser.add_argument("--out-root", required=True)
    args = parser.parse_args()

    if args.plan:
        cut_plan(Path(args.plan).resolve(), args.out_root)
        return

    if not args.scene or not args.shot or args.x is None:
        raise SystemExit("--scene, --shot and --x are required without --plan")

    if args.source:
        if not args.expected_sha256:
            raise SystemExit("--source requires --expected-sha256")
        source = Path(args.source).resolve()
        if not source.is_file():
            raise SystemExit(f"missing source: {source}")
        actual = sha256(source)
        if actual != args.expected_sha256:
            raise SystemExit(f"source SHA mismatch: expected {args.expected_sha256}, got {actual}")
        data, label, master_asset_id = source.read_bytes(), str(source), None
        origin = "explicit_source_off_master"
    else:
        resolved = resolve_master(args.scene)
        data, actual = resolved.data, resolved.sha256
        master_asset_id = str(resolved.asset_id)
        label = f"visual-asset:{master_asset_id}"
        origin = "approved_scene_master"

    cut_one(
        data=data,
        source_sha=actual,
        source_label=label,
        master_asset_id=master_asset_id,
        origin=origin,
        scene=args.scene,
        shot=args.shot,
        x=args.x,
        y=args.y,
        height=args.height,
        out_root=args.out_root,
    )


if __name__ == "__main__":
    main()
