from __future__ import annotations

import pytest

from app.services.renderer_validation import SCENES, harness_manifest, scene_package


def test_validation_harness_has_five_distinct_scenes() -> None:
    assert len(SCENES) == 5
    assert len({scene.id for scene in SCENES}) == 5


def test_pub_scene_locks_cue_overhead_and_table_position() -> None:
    pub = scene_package("W01-P28")
    instant = str(pub["exact_instant"]).lower()
    assert "stands on the pool table" in instant
    assert "cue horizontal overhead" in instant
    assert "raises the cue" not in str(pub["motion"]).lower()
    assert pub["manual_stop_after_seed"] is True


def test_manifest_exposes_manual_gates_and_planning_mode() -> None:
    manifest = harness_manifest(
        google_enabled=False,
        image_model="gemini-3.1-flash-image",
        video_model="veo-3.1-fast-generate-preview",
    )
    assert manifest["mode"] == "planning-only"
    assert "seed still approval" in manifest["manual_gates"]
    assert "final video/performance approval" in manifest["manual_gates"]


def test_unknown_scene_is_not_silently_substituted() -> None:
    with pytest.raises(KeyError):
        scene_package("does-not-exist")
