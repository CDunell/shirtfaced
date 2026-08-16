from __future__ import annotations

from app.adapters.google_media import GoogleImageRequest, GoogleVideoRequest
from app.adapters.reference_images import ReferenceImage


def test_google_image_request_carries_reference_bytes() -> None:
    ref = ReferenceImage(name="damo.png", data=b"abc", mime_type="image/png", locked=True)
    request = GoogleImageRequest(prompt="scene", references=(ref,), aspect_ratio="16:9")
    assert request.references[0].name == "damo.png"
    assert request.aspect_ratio == "16:9"


def test_google_video_request_requires_explicit_first_frame() -> None:
    request = GoogleVideoRequest(prompt="motion only", first_frame=b"png", resolution="1080p")
    assert request.first_frame == b"png"
    assert request.resolution == "1080p"
