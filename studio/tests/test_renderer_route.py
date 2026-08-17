from __future__ import annotations

from app.services.renderer_validation import scene_package


def test_pub_package_is_motion_ready_without_reopening_canon() -> None:
    package = scene_package("W01-P28")
    assert package["video_mode"] == "first-frame-image-to-video"
    assert package["manual_stop_after_seed"] is True
    assert "cue horizontal overhead" in str(package["exact_instant"]).lower()
    assert "raises the cue" not in str(package["motion"]).lower()
