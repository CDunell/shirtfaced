from __future__ import annotations

from app.services.veo_prompt import (
    bounded_subject_motion,
    build_motion_prompt,
    finish_state,
    observational_camera,
    temporal_window,
    world_independence,
)


def test_prompt_functions_define_a_state_not_an_action_arc() -> None:
    text = build_motion_prompt("Damo is rocking out. The stool and pint remain stable.")

    assert "begins mid-event and ends mid-event" in text
    assert "short reversible micro-movements" in text
    assert "Each movement returns toward the starting pose" in text
    assert "No intentional pan" in text
    assert "independent overlapping behaviour" in text
    assert "same ongoing moment" in text
    assert "Damo is rocking out" in text


def test_functions_are_generic_and_scene_direction_is_injected_once() -> None:
    direction = "The band is the event source and the room stays packed."
    text = build_motion_prompt(direction)

    assert text.count(direction) == 1
    assert "Damo" not in temporal_window()
    assert "Damo" not in bounded_subject_motion()
    assert "Damo" not in observational_camera()
    assert "Damo" not in world_independence()
    assert "Damo" not in finish_state()


def test_empty_scene_direction_is_refused() -> None:
    try:
        build_motion_prompt("   ")
    except ValueError as error:
        assert "empty" in str(error)
    else:  # pragma: no cover
        raise AssertionError("empty scene direction was accepted")
