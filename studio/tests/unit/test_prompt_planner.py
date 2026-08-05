"""Prompt planning: bounded context in, validated plan out.

No test here constructs an OpenAI client.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.adapters.planning import FakePromptPlanningClient, PlanningError
from app.domain.schemas import PromptPlan, PromptPlanRequest, ShotBrief
from app.services.prompt_planner import build_request, create_plan, validate_plan
from app.services.rotation import RotationState
from tests.fixtures.worlds import VALID_WORLD
from tests.unit.test_shot_selector import make_shot

VALID_PLAN_FIELDS = {
    "scene_summary": "Car interior transition",
    "emotional_beat": "Renewed momentum",
    "hero_product": "Tote bag",
    "product_visibility_instruction": "Visible because it is being moved.",
    "camera_position": "Rear seat",
    "lighting_source": "Interior dome light",
    "documentary_imperfection": "The door frame crops the edge.",
    "australian_authenticity_anchors": ["Suburban Australian street"],
    "negative_constraints": ["No visible branding"],
    "mood_words": ["Hopeful", "Loose", "Possible"],
    "selection_rationale": "Next planned shot.",
    "production_prompt": "Documentary 35mm photograph of friends reorganising a car.",
}


def a_request(**overrides: object) -> PromptPlanRequest:
    values: dict[str, object] = {
        "world_slug": "world-01",
        "world_name": "World 01",
        "shot": ShotBrief(
            external_id="W01-011",
            title="Car interior transition",
            hero_product="Tote bag",
            camera_position="Rear seat",
        ),
    }
    values.update(overrides)
    return PromptPlanRequest.model_validate(values)


# --- context assembly --------------------------------------------------------------


def test_builds_bounded_context_from_the_canon() -> None:
    request = build_request(
        world_slug="world-01",
        world_name="World 01",
        shot=make_shot("W01-011", sequence=11),
        world_text=VALID_WORLD,
        rotation=RotationState(),
    )

    headings = [excerpt.heading for excerpt in request.canon_excerpts]
    assert "Purpose" in headings
    assert "Emotional Tone" in headings
    assert "Success Test" in headings


def test_context_excludes_sections_that_are_not_image_rules() -> None:
    """Only the relevant canon is sent, not the whole document."""
    request = build_request(
        world_slug="world-01",
        world_name="World 01",
        shot=make_shot("W01-011", sequence=11),
        world_text=VALID_WORLD,
        rotation=RotationState(),
    )

    headings = [excerpt.heading for excerpt in request.canon_excerpts]
    assert "An Unknown Section" not in headings


def test_context_carries_rotation_state_and_the_selection_reason() -> None:
    rotation = RotationState(
        last_hero_product="Cap",
        recent_hero_products=["Cap", "T-shirt"],
        recent_camera_positions=["Front gate"],
        next_product_priority=["Black tote bag"],
        next_camera_priority=["From the rear seat"],
        canon_notes=["Optimism does not require loud behaviour."],
    )

    request = build_request(
        world_slug="world-01",
        world_name="World 01",
        shot=make_shot("W01-011", sequence=11),
        world_text=VALID_WORLD,
        rotation=rotation,
        selection_reason="W01-011 chosen because the product differs.",
    )

    assert request.recent_hero_products == ["Cap", "T-shirt"]
    assert request.next_product_priority == ["Black tote bag"]
    assert request.canon_notes == ["Optimism does not require loud behaviour."]
    assert "product differs" in request.selection_reason


def test_recent_continuity_is_capped() -> None:
    request = build_request(
        world_slug="world-01",
        world_name="World 01",
        shot=make_shot("W01-011", sequence=11),
        world_text=VALID_WORLD,
        rotation=RotationState(),
        recent_continuity=["one", "two", "three", "four", "five"],
    )

    assert len(request.recent_continuity) == 3


# --- schema validation -------------------------------------------------------------


def test_a_complete_plan_validates() -> None:
    assert PromptPlan.model_validate(VALID_PLAN_FIELDS).hero_product == "Tote bag"


@pytest.mark.parametrize("field", sorted(VALID_PLAN_FIELDS))
def test_every_field_is_required(field: str) -> None:
    fields = {key: value for key, value in VALID_PLAN_FIELDS.items() if key != field}

    with pytest.raises(ValidationError):
        PromptPlan.model_validate(fields)


def test_an_empty_production_prompt_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PromptPlan.model_validate({**VALID_PLAN_FIELDS, "production_prompt": ""})


def test_a_whitespace_only_production_prompt_is_rejected() -> None:
    with pytest.raises(ValidationError):
        PromptPlan.model_validate({**VALID_PLAN_FIELDS, "production_prompt": "   \n  "})


def test_empty_constraint_lists_are_rejected() -> None:
    with pytest.raises(ValidationError):
        PromptPlan.model_validate({**VALID_PLAN_FIELDS, "negative_constraints": []})


def test_unexpected_fields_are_rejected() -> None:
    """A changed model contract should fail loudly, not be silently absorbed."""
    with pytest.raises(ValidationError):
        PromptPlan.model_validate({**VALID_PLAN_FIELDS, "extra_field": "surprise"})


# --- agreement with the brief ------------------------------------------------------


def test_a_substituted_hero_product_is_rejected() -> None:
    plan = PromptPlan.model_validate({**VALID_PLAN_FIELDS, "hero_product": "Black cap"})

    with pytest.raises(PlanningError, match="hero product"):
        validate_plan(plan, a_request())


def test_a_substituted_camera_position_is_rejected() -> None:
    plan = PromptPlan.model_validate({**VALID_PLAN_FIELDS, "camera_position": "Front gate"})

    with pytest.raises(PlanningError, match="camera position"):
        validate_plan(plan, a_request())


def test_an_elaborated_hero_product_is_accepted() -> None:
    """The shotlist says "Tote bag"; "Plain black tote bag" is the same product."""
    plan = PromptPlan.model_validate({**VALID_PLAN_FIELDS, "hero_product": "Plain black tote bag"})

    validate_plan(plan, a_request())


def _lobby_brief() -> ShotBrief:
    return ShotBrief(
        external_id="W01-012",
        title="Apartment lobby",
        hero_product="Hoodie waist",
        camera_position="From the entrance",
    )


def test_an_elaboration_that_adds_words_in_the_middle_is_accepted() -> None:
    """The shotlist column is narrow, so its values are clipped.

    "Hoodie waist" expands naturally to "Hoodie tied around waist", which contains
    neither string. Substring matching called that a substituted hero product and
    failed a live plan over it.
    """
    request = a_request(shot=_lobby_brief())

    for produced in ("Hoodie tied around waist", "Plain black hoodie tied around the waist"):
        plan = PromptPlan.model_validate(
            {**VALID_PLAN_FIELDS, "hero_product": produced, "camera_position": "From the entrance"}
        )
        validate_plan(plan, request)


def test_dropping_a_required_word_is_still_a_substitution() -> None:
    plan = PromptPlan.model_validate({**VALID_PLAN_FIELDS, "hero_product": "Cap"})

    with pytest.raises(PlanningError):
        validate_plan(plan, a_request(shot=_lobby_brief()))


def test_a_shot_without_a_required_product_accepts_any() -> None:
    plan = PromptPlan.model_validate({**VALID_PLAN_FIELDS, "hero_product": "Anything"})
    request = a_request(
        shot=ShotBrief(
            external_id="W01-011", title="Scene", hero_product=None, camera_position=None
        )
    )

    validate_plan(plan, request)


# --- the fake adapter --------------------------------------------------------------


def test_the_fake_client_produces_a_valid_plan() -> None:
    outcome = create_plan(FakePromptPlanningClient(), a_request())

    assert outcome.plan.hero_product == "Tote bag"
    assert outcome.plan.camera_position == "Rear seat"
    assert outcome.plan.production_prompt


def test_the_fake_client_is_deterministic() -> None:
    first = create_plan(FakePromptPlanningClient(), a_request()).plan
    second = create_plan(FakePromptPlanningClient(), a_request()).plan

    assert first == second


def test_the_fake_client_records_what_it_was_asked() -> None:
    client = FakePromptPlanningClient()

    create_plan(client, a_request())

    assert client.requests[0].shot.external_id == "W01-011"


def test_a_planning_failure_is_surfaced() -> None:
    client = FakePromptPlanningClient(fail_with="the model was unavailable")

    with pytest.raises(PlanningError, match="unavailable"):
        create_plan(client, a_request())
