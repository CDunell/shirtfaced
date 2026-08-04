"""The OpenAI planning adapter, exercised against a stub transport.

The real SDK is never constructed. What is checked is that the adapter sends a bounded
request, parses structured output and turns every provider failure into a
``PlanningError`` rather than leaking an SDK exception into domain code.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from app.adapters.factory import build_planning_client, planning_client_is_live
from app.adapters.planning import (
    PROMPT_PLAN_JSON_SCHEMA,
    FakePromptPlanningClient,
    OpenAIPromptPlanningClient,
    PlanningError,
)
from app.config import Settings
from tests.unit.test_prompt_planner import VALID_PLAN_FIELDS, a_request


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
            id = "resp_stub"
            output_text = self._text

        return Response()


class StubClient:
    def __init__(self, responses: StubResponses) -> None:
        self.responses = responses


def _client(**kwargs: Any) -> tuple[OpenAIPromptPlanningClient, StubResponses]:
    responses = StubResponses(**kwargs)
    return (
        OpenAIPromptPlanningClient(StubClient(responses), model="a-text-model", timeout_seconds=30),
        responses,
    )


def test_parses_structured_output() -> None:
    client, _ = _client(text=json.dumps(VALID_PLAN_FIELDS))

    plan = client.create_plan(a_request())

    assert plan.hero_product == "Tote bag"
    assert plan.production_prompt.startswith("Documentary")


def test_sends_the_configured_model_timeout_and_schema() -> None:
    client, responses = _client(text=json.dumps(VALID_PLAN_FIELDS))

    client.create_plan(a_request())

    call = responses.calls[0]
    assert call["model"] == "a-text-model"
    assert call["timeout"] == 30
    assert call["text"]["format"]["schema"] == PROMPT_PLAN_JSON_SCHEMA
    assert call["text"]["format"]["strict"] is True


def test_sends_the_shot_and_canon_but_not_the_whole_document() -> None:
    client, responses = _client(text=json.dumps(VALID_PLAN_FIELDS))

    client.create_plan(a_request())

    content = responses.calls[0]["input"][0]["content"]
    assert "W01-011" in content
    assert "Required hero product: Tote bag" in content


def test_an_unset_model_is_refused_before_any_request() -> None:
    """Guessing a model name can cost money."""
    with pytest.raises(PlanningError, match="OPENAI_TEXT_MODEL"):
        OpenAIPromptPlanningClient(StubClient(StubResponses()), model="", timeout_seconds=30)


def test_a_provider_error_becomes_a_planning_error() -> None:
    client, _ = _client(error=RuntimeError("upstream exploded"))

    with pytest.raises(PlanningError, match="upstream exploded"):
        client.create_plan(a_request())


def test_invalid_json_is_reported_clearly() -> None:
    client, _ = _client(text="not json at all")

    with pytest.raises(PlanningError, match="not valid JSON"):
        client.create_plan(a_request())


def test_a_response_missing_fields_is_rejected() -> None:
    incomplete = {key: value for key, value in VALID_PLAN_FIELDS.items() if key != "hero_product"}
    client, _ = _client(text=json.dumps(incomplete))

    with pytest.raises(PlanningError, match="did not match the schema"):
        client.create_plan(a_request())


def test_an_empty_response_is_rejected() -> None:
    client, _ = _client(text=None)

    with pytest.raises(PlanningError, match="no text output"):
        client.create_plan(a_request())


# --- the factory -------------------------------------------------------------------

VALID_URL = "postgresql+psycopg://app:secret@db.example:5432/shirtfaced_studio"


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {"database_url": VALID_URL}
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


def test_the_fake_client_is_used_without_a_key() -> None:
    settings = _settings(openai_text_model="a-text-model")

    assert planning_client_is_live(settings) is False
    assert isinstance(build_planning_client(settings), FakePromptPlanningClient)


def test_the_fake_client_is_used_without_a_model() -> None:
    settings = _settings(openai_api_key="sk-test")

    assert planning_client_is_live(settings) is False
    assert isinstance(build_planning_client(settings), FakePromptPlanningClient)


def test_a_live_client_needs_both_a_key_and_a_model() -> None:
    settings = _settings(openai_api_key="sk-test", openai_text_model="a-text-model")

    assert planning_client_is_live(settings) is True
