#!/usr/bin/env python3
"""Run one explicitly-approved paid renderer seed on the production box.

This is intentionally a CLI rather than an always-open HTTP endpoint. A paid run must
be initiated deliberately (currently by the validation workflow), and reference
preflight happens before the provider call.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.adapters.google_media import GoogleImageClient, GoogleImageRequest  # noqa: E402
from app.adapters.reference_images import ReferenceImage, SUFFIX_MIME  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.services.renderer_validation import scene_package  # noqa: E402


PUB_PROMPT = """Photorealistic accidental phone photograph in the packed back room of an ordinary Australian pub at 11:05pm on a Friday night. A four-piece band is playing loudly on a low stage at the far wall. The room is packed solid, hot and humid, with condensation on the windows, sticky worn surfaces, ordinary pub furniture, glasses, taps, posters and incidental beer/brewery signage. Signage is realistic background texture only: nothing is centred, heroed, unusually sharp or visually competitive with the people.

REFERENCE ASSIGNMENTS — LOCKED:
Image 1 and image 2 are the same man: DAMO. Image 1 controls his build and proportions; image 2 controls his face. Image 3 is BROCK. Image 4 is EMMA. Match these people closely and do not invent identity-changing traits. Damo has no tattoos, no jewellery, no piercings and no invented scars. Do not add tattoos to any referenced character unless visible in the supplied reference.

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
        ("emma-full", Path("var/cast/emma/a-full-length.png")),
    )
}


def load_reference(name: str, relative_path: Path) -> ReferenceImage:
    path = PROJECT_ROOT / relative_path
    if not path.is_file():
        raise FileNotFoundError(str(path))
    mime = SUFFIX_MIME.get(path.suffix.lower())
    if not mime:
        raise ValueError(f"unsupported reference format: {path}")
    return ReferenceImage(name=name, data=path.read_bytes(), mime_type=mime, locked=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default="pub-1105")
    parser.add_argument("--candidates", type=int, default=1)
    args = parser.parse_args()

    if args.candidates < 1 or args.candidates > 3:
        raise SystemExit("--candidates must be 1..3")
    if args.scene not in REFERENCE_PATHS:
        raise SystemExit(f"paid seed runner is not enabled for {args.scene!r}")

    # Resolve the package first so a stale/unknown benchmark cannot call a provider.
    scene_package(args.scene)

    missing = [str(PROJECT_ROOT / p) for _, p in REFERENCE_PATHS[args.scene] if not (PROJECT_ROOT / p).is_file()]
    if missing:
        raise SystemExit("Missing canonical cast reference(s); no provider call made:\n" + "\n".join(missing))

    settings = get_settings()
    if not settings.google_media_live or settings.gemini_api_key is None:
        raise SystemExit("Google media is not live; no provider call made")

    references = tuple(load_reference(name, path) for name, path in REFERENCE_PATHS[args.scene])
    prompt = PUB_PROMPT
    client = GoogleImageClient(
        api_key=settings.gemini_api_key.get_secret_value(),
        model=settings.google_image_model,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = PROJECT_ROOT / "var" / "renderer-validation" / args.scene / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "scene": args.scene,
        "generated_at": stamp,
        "model": settings.google_image_model,
        "aspect_ratio": "16:9",
        "image_size": settings.google_image_size,
        "references": [str(path) for _, path in REFERENCE_PATHS[args.scene]],
        "candidate_count": args.candidates,
        "manual_gate": "seed_review_required_before_video",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    for index in range(1, args.candidates + 1):
        result = client.generate(
            GoogleImageRequest(
                prompt=prompt,
                references=references,
                aspect_ratio="16:9",
                image_size=settings.google_image_size,
            )
        )
        suffix = ".png" if result.mime_type == "image/png" else ".jpg"
        (out_dir / f"seed-{index}{suffix}").write_bytes(result.data)
        print(f"generated {args.scene} candidate {index}: {out_dir / f'seed-{index}{suffix}'}")

    print(f"RESULT_DIR={out_dir}")


if __name__ == "__main__":
    main()
