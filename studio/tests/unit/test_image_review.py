"""The review schema, the acceptance set and the review adapter.

The real OpenAI client is never constructed.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from pydantic import ValidationError

from app.adapters.factory import build_review_client, review_client_is_live
from app.adapters.review import (
    IMAGE_REVIEW_JSON_SCHEMA,
    FakeImageReviewClient,
    ImageReviewRequest,
    OpenAIImageReviewClient,
    ReviewError,
)
from app.config import Settings
from app.domain.enums import GateName, GateStatus, ReviewRecommendation, ReviewVerdict
from app.domain.schemas import ImageReview
from app.services.review_service import _recommended_action
from tests.fixtures.reviews import ACCEPTANCE_SET, build_review, gate

PNG = b"\x89PNG\r\n\x1a\nfake"

REQUEST = ImageReviewRequest(
    attempt_id="attempt-1",
    image_data=PNG,
    image_mime_type="image/png",
    shot_external_id="W01-011",
    scene="Car interior transition",
    required_hero_product="Tote bag",
    required_camera_position="Rear seat",
    production_prompt="Documentary 35mm photograph of friends reorganising a car.",
)


# --- schema ------------------------------------------------------------------------


def test_a_complete_review_validates() -> None:
    review = build_review()

    assert review.recommendation is ReviewRecommendation.APPROVE
    assert len(review.gates) == len(GateName)


def test_every_gate_is_required() -> None:
    payload = build_review().model_dump(mode="json")
    del payload["gates"]["story"]

    with pytest.raises(ValidationError, match="missing gates: story"):
        ImageReview.model_validate(payload)


@pytest.mark.parametrize("score", ["mood_score", "story_score", "product_visibility_score"])
@pytest.mark.parametrize("value", [0, 6, -1])
def test_scores_are_constrained_to_one_through_five(score: str, value: int) -> None:
    payload = build_review().model_dump(mode="json")
    payload[score] = value

    with pytest.raises(ValidationError):
        ImageReview.model_validate(payload)


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_confidence_is_constrained(confidence: float) -> None:
    payload = build_review().model_dump(mode="json")
    payload["gates"]["mood"]["confidence"] = confidence

    with pytest.raises(ValidationError):
        ImageReview.model_validate(payload)


def test_blank_evidence_is_rejected() -> None:
    """A gate without an observation is not evidence."""
    payload = build_review().model_dump(mode="json")
    payload["gates"]["mood"]["evidence"] = "   "

    with pytest.raises(ValidationError):
        ImageReview.model_validate(payload)


def test_unexpected_fields_are_rejected() -> None:
    payload = build_review().model_dump(mode="json")
    payload["surprise"] = True

    with pytest.raises(ValidationError):
        ImageReview.model_validate(payload)


@pytest.mark.parametrize(
    ("recommendation", "verdict"),
    [
        (ReviewRecommendation.APPROVE, ReviewVerdict.APPROVED),
        (ReviewRecommendation.APPROVE_WITH_NOTE, ReviewVerdict.APPROVED_WITH_NOTE),
        (ReviewRecommendation.REJECT, ReviewVerdict.REJECTED),
        (ReviewRecommendation.UNCERTAIN, ReviewVerdict.UNCERTAIN),
    ],
)
def test_the_verdict_follows_the_recommendation(
    recommendation: ReviewRecommendation, verdict: ReviewVerdict
) -> None:
    assert build_review(recommendation=recommendation).verdict is verdict


def test_uncertainty_alone_never_blocks() -> None:
    """Low confidence can ask for human inspection; it cannot fail a gate."""
    review = build_review(
        overrides={
            GateName.THIRD_PARTY_BRANDING: gate(
                "A mark is below readable resolution.",
                GateStatus.UNCERTAIN,
                confidence=0.2,
                material=True,
            )
        }
    )

    assert review.blocking_gates == []
    assert GateName.THIRD_PARTY_BRANDING in review.uncertain_gates


def test_an_immaterial_failure_does_not_block() -> None:
    review = build_review(
        overrides={GateName.STORY: gate("Minor.", GateStatus.FAIL, material=False)}
    )

    assert review.blocking_gates == []


def test_not_applicable_is_not_a_failure() -> None:
    review = build_review(
        overrides={
            GateName.VEHICLE_CONTINUITY: gate("No vehicle visible.", GateStatus.NOT_APPLICABLE)
        }
    )

    assert review.blocking_gates == []


# --- the acceptance set ------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(ACCEPTANCE_SET))
def test_every_acceptance_fixture_is_a_valid_review(name: str) -> None:
    assert len(ACCEPTANCE_SET[name].gates) == len(GateName)


@pytest.mark.parametrize(
    ("name", "expected_gate"),
    [
        ("branded_chip_packet", GateName.THIRD_PARTY_BRANDING),
        ("american_pickup", GateName.VEHICLE_CONTINUITY),
        ("invented_back_graphic", GateName.PRODUCT_VISIBILITY),
        ("miserable_hangover", GateName.MOOD),
        ("car_with_no_seats", GateName.STRUCTURAL_PLAUSIBILITY),
        ("van_with_no_rear_end", GateName.STRUCTURAL_PLAUSIBILITY),
        ("camera_inside_the_cabin", GateName.VEHICLE_CONTINUITY),
    ],
)
def test_material_failures_block_the_expected_gate(name: str, expected_gate: GateName) -> None:
    review = ACCEPTANCE_SET[name]

    assert expected_gate in review.blocking_gates


# --- the tenth gate ----------------------------------------------------------------
#
# Every case here is a real live review that the original nine gates passed. They are
# not hypotheticals: a seatless car scored documentary credibility 4/5 and a van with
# no rear end scored 5/5 and vehicle_compliant true.


@pytest.mark.parametrize("name", ["car_with_no_seats", "van_with_no_rear_end"])
def test_a_structural_failure_is_recorded_as_not_sound(name: str) -> None:
    assert ACCEPTANCE_SET[name].structurally_sound is False


def test_a_frame_can_pass_every_creative_gate_and_still_be_impossible() -> None:
    """The reason this gate exists, stated as an assertion.

    The van frame was genuinely well composed, genuinely Australian and genuinely
    documentary. It also had no back end. Nothing in the first nine gates is wrong
    about it, which is why a tenth was needed rather than a stricter ninth.
    """
    review = ACCEPTANCE_SET["van_with_no_rear_end"]

    creative = [name for name in GateName if name is not GateName.STRUCTURAL_PLAUSIBILITY]
    assert all(review.gates[name].status is not GateStatus.FAIL for name in creative)
    assert review.blocking_gates == [GateName.STRUCTURAL_PLAUSIBILITY]


def test_an_unbranded_object_is_not_a_branding_failure() -> None:
    """A live review failed a frame over an "unbranded drink can in the foreground"."""
    review = ACCEPTANCE_SET["unbranded_can_is_not_branding"]

    assert review.branding_compliant is True
    assert GateName.THIRD_PARTY_BRANDING not in review.blocking_gates


def test_a_structural_failure_is_reported_even_when_the_gate_is_not_marked_material() -> None:
    """The summary cannot let an impossible frame read as a clean pass.

    A model that sets structurally_sound false but leaves the gate non-material would
    otherwise produce a recommended_action mentioning nothing at all. Something that
    could not exist is material whatever the gate says.
    """
    review = build_review(
        overrides={
            GateName.STRUCTURAL_PLAUSIBILITY: gate(
                "The rear wheel is not attached to the vehicle.",
                GateStatus.FAIL,
                material=False,
            )
        },
        structurally_sound=False,
    )
    assert review.blocking_gates == []

    # The model even recommended approval here, which is exactly the case that has to
    # not read as clean.
    assert review.recommendation is ReviewRecommendation.APPROVE
    assert "structurally implausible" in _recommended_action(review)


@pytest.mark.parametrize(
    "name", ["correct_car_interior", "correct_apartment_lift", "blank_back_surface"]
)
def test_correct_fixtures_have_no_blocking_gates(name: str) -> None:
    assert ACCEPTANCE_SET[name].blocking_gates == []


def test_the_posed_lineup_fails_two_gates() -> None:
    review = ACCEPTANCE_SET["posed_lift_lineup"]

    assert set(review.blocking_gates) == {
        GateName.DOCUMENTARY_CREDIBILITY,
        GateName.COMPOSITION,
    }


def test_an_ambiguous_mark_is_uncertain_rather_than_a_guess() -> None:
    review = ACCEPTANCE_SET["ambiguous_environmental_mark"]

    assert review.recommendation is ReviewRecommendation.UNCERTAIN
    assert review.blocking_gates == []
    assert GateName.THIRD_PARTY_BRANDING in review.uncertain_gates


def test_a_quiet_scene_can_still_pass() -> None:
    """Quiet is allowed; resignation is not."""
    review = ACCEPTANCE_SET["quiet_optimistic_sunrise"]

    assert review.recommendation is ReviewRecommendation.APPROVE_WITH_NOTE
    assert review.blocking_gates == []


def test_a_rejection_can_carry_a_proposed_rule() -> None:
    review = ACCEPTANCE_SET["american_pickup"]

    assert review.new_rule_proposal
    assert "alloy tray" in review.new_rule_proposal


# --- the fake ----------------------------------------------------------------------


def test_the_fake_returns_a_valid_review() -> None:
    result = FakeImageReviewClient().review(REQUEST)

    assert len(result.review.gates) == len(GateName)
    assert result.model == "fake-review-model"


def test_the_fake_reflects_the_request() -> None:
    result = FakeImageReviewClient().review(REQUEST)

    assert "Tote bag" in result.review.gates[GateName.PRODUCT_VISIBILITY].evidence


def test_the_fake_can_be_scripted() -> None:
    scripted = ACCEPTANCE_SET["branded_chip_packet"]

    result = FakeImageReviewClient(result=scripted).review(REQUEST)

    assert result.review.recommends_rejection


def test_the_fake_records_what_it_was_asked() -> None:
    client = FakeImageReviewClient()

    client.review(REQUEST)

    assert client.requests[0].shot_external_id == "W01-011"


def test_a_review_failure_is_surfaced() -> None:
    with pytest.raises(ReviewError, match="unavailable"):
        FakeImageReviewClient(fail_with="the reviewer was unavailable").review(REQUEST)


# --- the OpenAI adapter ------------------------------------------------------------


class StubResponses:
    def __init__(self, *, text: str | None = None, error: Exception | None = None) -> None:
        self._text = text
        self._error = error
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self._error is not None:
            raise self._error

        class Response:
            id = "resp_review"
            output_text = self._text

        return Response()


class StubClient:
    def __init__(self, responses: StubResponses) -> None:
        self.responses = responses


def _client(**kwargs: Any) -> tuple[OpenAIImageReviewClient, StubResponses]:
    responses = StubResponses(**kwargs)
    return (
        OpenAIImageReviewClient(StubClient(responses), model="a-review-model", timeout_seconds=30),
        responses,
    )


def test_parses_structured_output() -> None:
    payload = json.dumps(build_review().model_dump(mode="json"))
    client, _ = _client(text=payload)

    result = client.review(REQUEST)

    assert result.review.recommendation is ReviewRecommendation.APPROVE
    assert result.provider_request_id == "resp_review"


def test_the_actual_image_is_sent_not_only_the_prompt() -> None:
    """A prompt saying "blank garments" proves nothing about what was drawn."""
    payload = json.dumps(build_review().model_dump(mode="json"))
    client, responses = _client(text=payload)

    client.review(REQUEST)

    content = responses.calls[0]["input"][0]["content"]
    kinds = [part["type"] for part in content]
    assert "input_image" in kinds
    image_part = next(part for part in content if part["type"] == "input_image")
    assert image_part["image_url"].startswith("data:image/png;base64,")


def test_the_request_carries_what_was_asked_for() -> None:
    payload = json.dumps(build_review().model_dump(mode="json"))
    client, responses = _client(text=payload)

    client.review(REQUEST)

    text = responses.calls[0]["input"][0]["content"][0]["text"]
    assert "Required hero product: Tote bag" in text
    assert "W01-011" in text


def test_the_schema_requires_all_nine_gates() -> None:
    assert set(IMAGE_REVIEW_JSON_SCHEMA["properties"]["gates"]["required"]) == {
        gate_name.value for gate_name in GateName
    }


def test_an_unset_model_is_refused_before_any_request() -> None:
    with pytest.raises(ReviewError, match="OPENAI_REVIEW_MODEL"):
        OpenAIImageReviewClient(StubClient(StubResponses()), model="", timeout_seconds=30)


def test_a_provider_error_becomes_a_review_error() -> None:
    client, _ = _client(error=RuntimeError("upstream exploded"))

    with pytest.raises(ReviewError, match="upstream exploded"):
        client.review(REQUEST)


def test_invalid_json_is_reported_clearly() -> None:
    client, _ = _client(text="not json")

    with pytest.raises(ReviewError, match="not valid JSON"):
        client.review(REQUEST)


def test_a_response_missing_a_gate_is_rejected() -> None:
    payload = build_review().model_dump(mode="json")
    del payload["gates"]["mood"]
    client, _ = _client(text=json.dumps(payload))

    with pytest.raises(ReviewError, match="did not match the schema"):
        client.review(REQUEST)


# --- the factory -------------------------------------------------------------------

VALID_URL = "postgresql+psycopg://app:secret@db.example:5432/shirtfaced_studio"


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {"database_url": VALID_URL}
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


def test_the_fake_reviewer_is_used_without_a_key() -> None:
    settings = _settings(openai_review_model="a-review-model")

    assert review_client_is_live(settings) is False
    assert isinstance(build_review_client(settings), FakeImageReviewClient)


def test_the_fake_reviewer_is_used_without_a_model() -> None:
    settings = _settings(openai_api_key="sk-test")

    assert review_client_is_live(settings) is False
    assert isinstance(build_review_client(settings), FakeImageReviewClient)


def test_a_live_reviewer_needs_both() -> None:
    settings = _settings(openai_api_key="sk-test", openai_review_model="a-review-model")

    assert review_client_is_live(settings) is True
