from __future__ import annotations

from app.config import PROJECT_ROOT
from app.services.nano_pipeline import panel_plan_from_prompt, scene_prompt_path

WORLDS = PROJECT_ROOT / "worlds"
PRIMARY = "W01-P28.nano-banana-coverage.txt"
NON_DAMO = "W01-P28Z-non-damo.nano-banana-coverage.txt"


def test_w01_p28_default_prompt_remains_the_full_scene_prompt() -> None:
    prompt = scene_prompt_path(WORLDS, "W01-P28")

    assert prompt is not None
    assert prompt.name == PRIMARY


def test_w01_p28_non_damo_prompt_is_explicitly_selectable() -> None:
    prompt = scene_prompt_path(WORLDS, "W01-P28", NON_DAMO)

    assert prompt is not None
    assert prompt.name == NON_DAMO
    text = prompt.read_text(encoding="utf-8")
    assert len(panel_plan_from_prompt(text)) == 9
    assert "Do not require or supply a Damo identity reference" in text
    assert "remain outside every one of these nine phone frames" in text
