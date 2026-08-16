from __future__ import annotations

from app.services.renderer_validation import harness_manifest


def test_validation_defaults_to_manual_billing_gate() -> None:
    manifest = harness_manifest(
        google_enabled=False,
        image_model="gemini-3.1-flash-image",
        video_model="veo-3.1-fast-generate-preview",
    )
    assert manifest["mode"] == "planning-only"
    assert "seed still approval" in manifest["manual_gates"]
