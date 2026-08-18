#!/usr/bin/env python3
# ruff: noqa: I001
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
from app.adapters.asset_store import FilesystemAssetStore
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.adapters.reference_images import ReferenceImage
from app.config import get_settings
from app.db.session import get_session_factory
from app.services.reference_resolution import ReferenceUnavailable, resolve_cast_reference

PUB_PROMPT = """Create a photorealistic 9:16 vertical phone photograph, an accidental instant inside a packed ordinary Australian pub back room at 11:05pm Friday. This is not a hero portrait and not an arranged crowd scene. It must feel physically chaotic, obstructed, asymmetrical and caught half a second before or after a cleaner photographer would have pressed the shutter.

Images 1 and 2 are DAMO: image 1 controls his build/proportions and image 2 his face. Images 3/4 are BROCK, images 5/6 EMMA. Preserve identities. Damo has NO tattoos, jewellery, piercings or invented marks.

Damo is an AUDIENCE MEMBER, never a performer. A separate four-piece band is visibly performing on a low stage deeper in the room. Damo is on top of the pool table because the night has got out of hand. Both boots contact the playing surface, but his stance must NOT be symmetrical, planted, heroic or posed. His weight is displaced and unstable: one knee bent, torso twisted, hips off-axis, one foot turned differently from the other. Another mate may be grabbing his waist/leg to steady him. Damo holds a pool cue horizontally above his head in both fists, head thrown back, eyes shut, roaring along with the chorus TOWARD the real singer on the distant stage. He faces away from the camera/stage relationship established naturally by the room, never performing to camera.

A plain wooden pub stool stands on the pool table with one full beer. Preserve them, but allow bodies to partially obscure their edges. Brock and Emma are secondary crowd members reacting independently, not arranged beside Damo.

CROWD PHYSICS ARE CRITICAL: foreground heads, shoulders and arms block significant parts of the frame. People collide, lean, duck, shout, grab friends, turn away, squeeze past and react independently. No evenly spaced faces. No semicircle around Damo. No clean sightlines. No duplicated gestures. Some faces are completely hidden; some are cropped by frame edges; one or two nearby people may be motion-blurred. Build at least four overlapping depth planes: obstructing foreground bodies, pool table/Damo, dense surrounding crowd, distant stage/bar. The photographer is physically trapped inside this crowd and cannot compose cleanly.

LIGHTING: genuinely dark late-night pub. General house lights OFF. Black ceiling and deep room shadows. Tight pool-table pendant light catches parts of Damo/table, localized red/coloured stage spill deeper behind, sparse warm practical glints. Background patrons mostly silhouettes or partial faces. Do not lift shadows to show everyone. Windows nearly black except reflections/condensation. Phone auto-exposure struggles; clipped practical highlights and crushed blacks are desirable. Absolutely no HDR, venue-promo lighting, community-hall brightness or studio fill.

CAMERA: one-handed phone held by a friend in the crowd at chest/head height, 24mm-equivalent, native portrait 9:16. Damo/cue/table/stool remain within the central 4:5-safe region but DO NOT protect them from foreground occlusion. Cue can approach or clip a frame edge. Nearby bodies can fill corners. Slight motion imperfection, close-range distortion and awkward framing are desirable. Nobody notices the camera.

Wardrobe: Damo bare-headed, faded olive tee, dark denim, ordinary worn trainers. No logos. The final image should communicate instantly: some dickhead climbed onto the pool table and his mates are dealing with the consequences — not 'man poses enthusiastically on pool table'. Preserve exact identity and required props while prioritising physical spontaneity, crowd entropy, occlusion, depth and accidental-camera realism."""
# Cast slots, by identity. These were six hard-coded paths until the Phase 5
# cutover; the frames were then renamed on disk and every one of them broke.
# A slot now says which member and which role, and the library says which bytes.
REFERENCE_SLOTS = {
    "W01-P28": (
        ("damo-full", "damo", "full_body_neutral"),
        ("damo-head", "damo", "head_shoulders_neutral"),
        ("brock-full", "brock", "full_body_neutral"),
        ("brock-head", "brock", "head_shoulders_neutral"),
        ("emma-head", "emma", "head_shoulders_neutral"),
        ("emma-full", "emma", "full_body_neutral"),
    )
}
DERIVATIVE_ROOT = PROJECT_ROOT / "var" / "cast-derivatives" / "jpeg-v1"
MAX_SOURCE_BYTES = 50 * 1024 * 1024
MAX_SIDE = 2048


def prepare_reference(name, resolved):
    source_bytes = resolved.data
    source_sha256 = resolved.sha256
    if not source_bytes or len(source_bytes) > MAX_SOURCE_BYTES:
        raise ValueError(f"invalid canonical reference: {resolved.label}")
    with Image.open(io.BytesIO(source_bytes)) as opened:
        opened.load()
        source_format = opened.format
        source_dimensions = tuple(opened.size)
        image = ImageOps.exif_transpose(opened)
        if image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info):
            rgba = image.convert("RGBA")
            bg = Image.new("RGB", rgba.size, "white")
            bg.paste(rgba, mask=rgba.getchannel("A"))
            image = bg
        else:
            image = image.convert("RGB")
        if max(image.size) > MAX_SIDE:
            image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
        derivative_dimensions = tuple(image.size)
        derivative_path = DERIVATIVE_ROOT / source_sha256[:2] / f"{source_sha256}.jpg"
        if not derivative_path.is_file():
            derivative_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(derivative_path, format="JPEG", quality=92, optimize=True, progressive=False)
    data = derivative_path.read_bytes()
    meta = {
        "name": name,
        **resolved.as_manifest(),
        "canonical_bytes": len(source_bytes),
        "canonical_sha256": source_sha256,
        "canonical_format": source_format,
        "canonical_dimensions": list(source_dimensions),
        "derivative_path": str(derivative_path.relative_to(PROJECT_ROOT)),
        "derivative_bytes": len(data),
        "derivative_sha256": hashlib.sha256(data).hexdigest(),
        "derivative_dimensions": list(derivative_dimensions),
        "derivative_mime": "image/jpeg",
    }
    return ReferenceImage(name=name, data=data, mime_type="image/jpeg", locked=True), meta


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scene", default="W01-P28")
    p.add_argument("--candidates", type=int, default=1)
    p.add_argument("--model", default=None)
    p.add_argument("--image-size", default="2K")
    args = p.parse_args()
    if args.candidates < 1 or args.candidates > 3:
        raise SystemExit("--candidates must be 1..3")
    settings = get_settings()
    try:
        with get_session_factory()() as session:
            store = FilesystemAssetStore(settings.assets_root_resolved)
            resolved = [
                (name, resolve_cast_reference(session, store, slug=slug, role=role))
                for name, slug, role in REFERENCE_SLOTS[args.scene]
            ]
    except ReferenceUnavailable as error:
        raise SystemExit(f"{error} No provider call made.") from error
    prepared = tuple(prepare_reference(name, reference) for name, reference in resolved)
    refs = tuple(x[0] for x in prepared)
    metadata = [x[1] for x in prepared]
    model = args.model or settings.google_image_model
    if not settings.google_media_live or settings.gemini_api_key is None:
        raise SystemExit("Google media not live; no provider call made")
    client = GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(), model=model)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = PROJECT_ROOT / "var" / "renderer-validation" / args.scene / stamp
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "scene": args.scene,
        "generated_at": stamp,
        "model": model,
        "aspect_ratio": "9:16",
        "channel_master": "vertical-social",
        "safe_crop": "central-4:5",
        "image_size": args.image_size,
        "references": metadata,
        "candidate_count": args.candidates,
        "quality_benchmark": "gpt-chaotic-pub-reference",
        "manual_gate": "seed_review_required_before_video",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "prompt.txt").write_text(PUB_PROMPT)
    for i in range(1, args.candidates + 1):
        result = client.generate(
            GoogleImageRequest(
                prompt=PUB_PROMPT, references=refs, aspect_ratio="9:16", image_size=args.image_size
            )
        )
        suffix = ".png" if result.mime_type == "image/png" else ".jpg"
        path = out / f"seed-{i}{suffix}"
        path.write_bytes(result.data)
        print(f"generated {args.scene} candidate {i}: {path}")
    print(f"RESULT_DIR={out}")


if __name__ == "__main__":
    main()
