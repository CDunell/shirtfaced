#!/usr/bin/env python3
# ruff: noqa: E501, I001
"""Run one explicitly-approved paid renderer seed on the production box.

Canonical cast originals live only in persistent Studio storage under ``var/cast``.
The renderer validates those originals strictly, then creates one SHA-addressed JPEG
derivative when Gemini needs JPEG input. Canonical originals are never rewritten.
"""

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


PUB_PROMPT = """Photorealistic accidental phone photograph in the packed back room of an ordinary Australian pub at 11:05pm on a Friday night. A four-piece band is playing loudly on a low stage at the far wall. The room is packed solid, hot and humid, with condensation on the windows, sticky worn surfaces, ordinary pub furniture, glasses, taps, posters and incidental beer/brewery signage. Signage is realistic background texture only: nothing is centred, heroed, unusually sharp or visually competitive with the people.

REFERENCE ASSIGNMENTS — LOCKED:
Images 1 and 2 are the same man: DAMO. Image 1 controls his build and proportions; image 2 controls his face. Images 3 and 4 are BROCK: full-length then head/shoulders. Images 5 and 6 are EMMA: head/shoulders then full-length. Match these people closely and do not invent identity-changing traits. Damo has no tattoos, no jewellery, no piercings and no invented scars. Do not add tattoos to any referenced character unless visible in the supplied reference.

EXACT FROZEN INSTANT — LOCKED:
Damo is physically STANDING ON TOP OF THE POOL TABLE, not beside it and not merely with his feet on a rail. Both boots are planted on the pool-table playing surface. He holds a pool cue HORIZONTAL ABOVE HIS HEAD in both fists, arms raised. His head is tipped back, eyes shut, mouth open, roaring the chorus. He faces away from the stage. This position is already achieved; do not depict him raising the cue or climbing onto the table.

A plain wooden pub stool is also standing on top of the pool table beside Damo with one full beer on it. Keep the stool and beer physically plausible. Brock and Emma are in the surrounding crowd and retain their supplied identities; they are secondary, naturally occupied by the room, and do not pose or look at the camera. Anonymous patrons may partially obstruct people naturally.

Damo wears a black cap, a faded olive t-shirt, dark denim and ordinary worn trainers. Keep his underlying body shape consistent with the supplied full-length reference. No tattoos. Brock and Emma wear plausible understated Friday-night clothing; do not copy their grey studio backdrop or studio posing.

CAMERA — LOCKED:
A friend inside the crowd takes the image on a phone while being jostled, from roughly chest height and close to the pool table, equivalent to a wide 24mm phone lens. The photographer is physically in the crowd. Imperfect framing, slight close-range perspective distortion, believable motion imperfection and mixed pub lighting are desirable. No cinematic crane view, no clean commercial composition, no fashion posing, no HDR polish.

The result must feel like a real Australian pub photograph somebody found in their camera roll the next morning, not an AI advertising image. Preserve character identity first, then exact hero geometry, then believable pub detail."""


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
            opened.load()  # strict decode: never salvage truncated canonical originals
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
                image.save(
                    temp_path,
                    format="JPEG",
                    quality=92,
                    optimize=True,
                    progressive=False,
                )
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
    return (
        ReferenceImage(name=name, data=derivative_bytes, mime_type="image/jpeg", locked=True),
        metadata,
    )


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

    missing = [
        str(PROJECT_ROOT / path)
        for _, path in REFERENCE_PATHS[args.scene]
        if not (PROJECT_ROOT / path).is_file()
    ]
    if missing:
        raise SystemExit(
            "Missing persistent canonical cast reference(s); no provider call made:\n"
            + "\n".join(missing)
        )

    prepared = tuple(prepare_reference(name, path) for name, path in REFERENCE_PATHS[args.scene])
    references = tuple(item[0] for item in prepared)
    reference_metadata = [item[1] for item in prepared]

    settings = get_settings()
    if not settings.google_media_live or settings.gemini_api_key is None:
        raise SystemExit("Google media is not live; no provider call made")

    client = GoogleImageClient(
        api_key=settings.gemini_api_key.get_secret_value(),
        model=settings.google_image_model,
    )

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = PROJECT_ROOT / "var" / "renderer-validation" / args.scene / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "scene": args.scene,
        "generated_at": stamp,
        "model": settings.google_image_model,
        "aspect_ratio": "16:9",
        "image_size": settings.google_image_size,
        "references": reference_metadata,
        "candidate_count": args.candidates,
        "manual_gate": "seed_review_required_before_video",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out_dir / "prompt.txt").write_text(PUB_PROMPT, encoding="utf-8")

    for index in range(1, args.candidates + 1):
        result = client.generate(
            GoogleImageRequest(
                prompt=PUB_PROMPT,
                references=references,
                aspect_ratio="16:9",
                image_size=settings.google_image_size,
            )
        )
        suffix = ".png" if result.mime_type == "image/png" else ".jpg"
        output_path = out_dir / f"seed-{index}{suffix}"
        output_path.write_bytes(result.data)
        print(f"generated {args.scene} candidate {index}: {output_path}")

    print(f"RESULT_DIR={out_dir}")


if __name__ == "__main__":
    main()
