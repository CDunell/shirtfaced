#!/usr/bin/env python3
"""Generate one expression-matched Damo identity bridge from the canonical headshot."""

from __future__ import annotations

import io
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.adapters.asset_store import FilesystemAssetStore
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.adapters.reference_images import ReferenceImage
from app.config import get_settings
from app.db.session import get_session_factory
from app.services.reference_resolution import resolve_cast_reference

PROMPT = """IMAGE 1 is canonical DAMO. Generate the SAME PERSON ONLY, as an identity/expression bridge reference for a later edit.

Preserve Damo's identity exactly: same skull shape, forehead, brow, eye spacing, nose, cheekbones, jaw, ears, hairline, hair texture, stubble pattern, skin texture and age. Do not beautify, stylize, age, de-age or change ethnicity/body identity.

Change ONLY expression and head pose: tilt his head back approximately 20-25 degrees, eyes fully shut, mouth wide open mid-shout / roaring a song chorus. This is not pain, fear or aggression; it is exuberant singing/yelling along. Show enough neck and upper shoulders to make the head angle anatomically clear.

Keep the same faded olive t-shirt. Neutral mid-grey studio background, soft even light, no dramatic grading. Head and shoulders only, 4:5 portrait crop. No tattoos, jewellery, scars or added marks.

The result exists solely to give a later image editor a canonical Damo reference in the same extreme expression as the pub master. Identity fidelity is more important than attractiveness."""


def main():
    settings = get_settings()
    # Resolved by identity, not by path: the frames were renamed on 17 August 2026
    # and this script read the old name until the Phase 5 cutover.
    with get_session_factory()() as session:
        canonical = resolve_cast_reference(
            session,
            FilesystemAssetStore(settings.assets_root_resolved),
            slug="damo",
            role="head_shoulders_neutral",
        )
    raw = canonical.data
    with Image.open(io.BytesIO(raw)) as im:
        im.load()
        dims = im.size
        im = ImageOps.exif_transpose(im).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=98, subsampling=0)
        data = buf.getvalue()
    ref = ReferenceImage(name="damo-canonical-head", data=data, mime_type="image/jpeg", locked=True)
    if not settings.google_media_live or settings.gemini_api_key is None:
        raise SystemExit("Google media not live; no provider call made")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "var/renderer-validation/identity-bridges/damo" / stamp
    out.mkdir(parents=True, exist_ok=True)
    model = "gemini-3-pro-image"
    client = GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(), model=model)
    result = client.generate(
        GoogleImageRequest(prompt=PROMPT, references=(ref,), aspect_ratio="4:5", image_size="2K")
    )
    suffix = ".png" if result.mime_type == "image/png" else ".jpg"
    output = out / ("bridge-1" + suffix)
    output.write_bytes(result.data)
    manifest = {
        "character": "damo",
        "experiment": "expression-bridge-roaring-chorus",
        "generated_at": stamp,
        "model": model,
        "aspect_ratio": "4:5",
        "image_size": "2K",
        "canonical": canonical.as_manifest(),
        "canonical_sha256": canonical.sha256,
        "canonical_dimensions": list(dims),
        "change": ["head_pose", "expression"],
        "preserve": ["identity", "hair", "stubble", "age", "skin", "wardrobe"],
        "candidate_count": 1,
        "manual_gate": "identity_bridge_review",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "prompt.txt").write_text(PROMPT)
    print(f"RESULT_DIR={out}")


if __name__ == "__main__":
    main()
