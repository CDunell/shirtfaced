#!/usr/bin/env python3
# ruff: noqa: E501, I001
"""Run one explicitly-approved paid renderer seed on the production box."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image, ImageOps

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.adapters.google_media import GoogleImageClient, GoogleImageRequest  # noqa: E402
from app.adapters.reference_images import ReferenceImage  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.services.renderer_validation import scene_package  # noqa: E402


PUB_PROMPT = """Photorealistic accidental VERTICAL phone photograph in the packed back room of an ordinary Australian pub at 11:05pm on a Friday night. Native 9:16 portrait composition for Instagram Reels and TikTok, not a landscape photograph and not a landscape crop. Keep Damo, the cue, pool table, stool and beer inside the central 4:5-safe region so a feed crop remains usable. A four-piece band plays loudly on a low stage deeper behind him. The crowd wraps around foreground and midground vertically instead of spreading into a wide horizontal composition.

REFERENCE ASSIGNMENTS — LOCKED:
Images 1 and 2 are DAMO. Image 1 controls build/proportions; image 2 controls face. Images 3 and 4 are BROCK: full-length then head/shoulders. Images 5 and 6 are EMMA: head/shoulders then full-length. Match them closely. Damo has no tattoos, jewellery, piercings or invented scars.

EXACT FROZEN INSTANT — LOCKED:
Damo is physically STANDING ON TOP OF THE POOL TABLE. BOTH BOOTS are planted on the playing surface. He holds a pool cue HORIZONTAL ABOVE HIS HEAD in BOTH FISTS, arms raised. Head back, eyes shut, mouth open, roaring the chorus. He faces AWAY FROM THE STAGE. A plain wooden pub stool also stands on the pool table beside him with one FULL BEER on it. Brock and Emma remain secondary people in the surrounding crowd, naturally occupied and never posing.

Damo wears a black cap, faded olive t-shirt, dark denim and ordinary worn trainers. Preserve his supplied body shape and face. No tattoos.

LIGHTING — ABSOLUTELY LOCKED:
This is a DARK late-night pub back room. ALL GENERAL HOUSE LIGHTS ARE OFF. NO ceiling-wide illumination, NO bright ambient fill, NO evenly illuminated walls, NO bright room exposure. The ceiling and upper room are predominantly black. Background patrons are mostly silhouettes or fragments of faces appearing only where stray practical light catches them. The pool-table pendant lamp is the dominant local light and creates a tight pool of light on Damo and the green table with rapid falloff into darkness. The band has LOCALIZED coloured stage lights behind him; that light does not fill the whole room. A few tiny warm practical glints may hit glasses or faces. Windows are nearly black with only reflections and condensation visible. Deep shadows are expected and desirable. Do not brighten shadows to make every face readable. Expose like a real phone struggling in a dark crowded pub, not a venue promo, community hall, bingo night, commercial photograph or HDR image.

CAMERA — LOCKED:
A friend inside the crowd takes the image one-handed on a phone while being jostled, portrait orientation, roughly chest height, close to the pool table, equivalent to a 24mm phone lens. Damo and the pool table dominate the vertical frame; band remains visible deeper behind him. Imperfect framing, close-range distortion, slight motion imperfection, blocked edges from nearby patrons and clipped practical highlights are desirable. Nobody acknowledges the camera.

The result must feel like a real vertical Australian pub phone photo somebody found in their camera roll the next morning. Preserve identity first, exact hero geometry second, darkness and native vertical social composition third."""

REFERENCE_PATHS = {
    "pub-1105": (
        ("damo-full", Path("var/cast/damo/a-full-length.png")),
        ("damo-head", Path("var/cast/damo/b-head-shoulders.png")),
        ("brock-full", Path("var/cast/brock/a-full-length.png")),
        ("brock-head", Path("var/cast/brock/b-head-shoulders.png")),
        ("emma-head", Path("var/cast/emma/b-head-shoulders.png")),
        ("emma-full", Path("var/cast/emma/a-full-length.png")),
    )
}

DERIVATIVE_ROOT = PROJECT_ROOT / "var" / "cast-derivatives" / "jpeg-v1"
MAX_SOURCE_BYTES = 50 * 1024 * 1024
MAX_SIDE = 2048


def prepare_reference(name: str, relative_path: Path) -> tuple[ReferenceImage, dict[str, object]]:
    source_path = PROJECT_ROOT / relative_path
    if not source_path.is_file():
        raise FileNotFoundError(str(source_path))
    source_bytes = source_path.read_bytes()
    source_size = len(source_bytes)
    if source_size == 0 or source_size > MAX_SOURCE_BYTES:
        raise ValueError(f"invalid canonical reference size: {source_path} ({source_size} bytes)")
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    try:
        with Image.open(io.BytesIO(source_bytes)) as opened:
            opened.load()
            source_format = opened.format
            source_dimensions = tuple(opened.size)
            image = ImageOps.exif_transpose(opened)
            if image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info):
                rgba = image.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")
            if max(image.size) > MAX_SIDE:
                image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
            derivative_dimensions = tuple(image.size)
            derivative_path = DERIVATIVE_ROOT / source_sha256[:2] / f"{source_sha256}.jpg"
            if not derivative_path.is_file():
                derivative_path.parent.mkdir(parents=True, exist_ok=True)
                temp_path = derivative_path.with_suffix(".tmp")
                image.save(temp_path, format="JPEG", quality=92, optimize=True, progressive=False)
                temp_path.replace(derivative_path)
    except Exception as exc:
        raise ValueError(f"canonical reference cannot be strictly decoded: {source_path}") from exc
    derivative_bytes = derivative_path.read_bytes()
    derivative_sha256 = hashlib.sha256(derivative_bytes).hexdigest()
    metadata: dict[str, object] = {
        "name": name,
        "canonical_path": str(relative_path),
        "canonical_bytes": source_size,
        "canonical_sha256": source_sha256,
        "canonical_format": source_format,
        "canonical_dimensions": list(source_dimensions),
        "derivative_path": str(derivative_path.relative_to(PROJECT_ROOT)),
        "derivative_bytes": len(derivative_bytes),
        "derivative_sha256": derivative_sha256,
        "derivative_dimensions": list(derivative_dimensions),
        "derivative_mime": "image/jpeg",
    }
    return ReferenceImage(name=name, data=derivative_bytes, mime_type="image/jpeg", locked=True), metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default="pub-1105")
    parser.add_argument("--candidates", type=int, default=1)
    args = parser.parse_args()
    if args.candidates < 1 or args.candidates > 3:
        raise SystemExit("--candidates must be 1..3")
    if args.scene not in REFERENCE_PATHS:
        raise SystemExit(f"paid seed runner is not enabled for {args.scene!r}")
    scene_package(args.scene)
    missing = [str(PROJECT_ROOT / path) for _, path in REFERENCE_PATHS[args.scene] if not (PROJECT_ROOT / path).is_file()]
    if missing:
        raise SystemExit("Missing persistent canonical cast reference(s); no provider call made:\n" + "\n".join(missing))
    prepared = tuple(prepare_reference(name, path) for name, path in REFERENCE_PATHS[args.scene])
    references = tuple(item[0] for item in prepared)
    reference_metadata = [item[1] for item in prepared]
    settings = get_settings()
    if not settings.google_media_live or settings.gemini_api_key is None:
        raise SystemExit("Google media is not live; no provider call made")
    client = GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(), model=settings.google_image_model)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = PROJECT_ROOT / "var" / "renderer-validation" / args.scene / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "scene": args.scene,
        "generated_at": stamp,
        "model": settings.google_image_model,
        "aspect_ratio": "9:16",
        "channel_master": "vertical-social",
        "safe_crop": "central-4:5",
        "image_size": settings.google_image_size,
        "references": reference_metadata,
        "candidate_count": args.candidates,
        "manual_gate": "seed_review_required_before_video",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out_dir / "prompt.txt").write_text(PUB_PROMPT, encoding="utf-8")
    for index in range(1, args.candidates + 1):
        result = client.generate(GoogleImageRequest(prompt=PUB_PROMPT, references=references, aspect_ratio="9:16", image_size=settings.google_image_size))
        suffix = ".png" if result.mime_type == "image/png" else ".jpg"
        output_path = out_dir / f"seed-{index}{suffix}"
        output_path.write_bytes(result.data)
        print(f"generated {args.scene} candidate {index}: {output_path}")
    print(f"RESULT_DIR={out_dir}")


if __name__ == "__main__":
    main()
