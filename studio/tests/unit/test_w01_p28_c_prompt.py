from __future__ import annotations

from app.config import PROJECT_ROOT
from app.services.nano_pipeline import panel_plan_from_prompt, scene_prompt_path

WORLDS = PROJECT_ROOT / "worlds"
NAME = "W01-P28C-emma-brock.nano-banana-coverage.txt"


def test_w01_p28_c_prompt_is_explicit_and_shot_specific() -> None:
    prompt = scene_prompt_path(WORLDS, "W01-P28", NAME)
    assert prompt is not None
    text = prompt.read_text(encoding="utf-8")
    assert len(panel_plan_from_prompt(text)) == 9
    assert "EXACTLY THREE COLUMNS × THREE ROWS" in text
    assert "TALL PORTRAIT 9:16 PHONE PHOTOGRAPH" in text
    assert "DO NOT make wide/landscape panel images" in text
    assert "Damo and the pool-table action are outside every one of these nine phone frames" in text
    assert "Emma" in text and "Brock" in text


def test_w01_p28_primary_prompt_remains_default() -> None:
    prompt = scene_prompt_path(WORLDS, "W01-P28")
    assert prompt is not None
    assert prompt.name == "W01-P28.nano-banana-coverage.txt"
