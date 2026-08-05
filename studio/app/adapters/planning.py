"""Prompt planning adapters.

Services depend on the :class:`PromptPlanningClient` protocol, never on the OpenAI
SDK. That keeps domain logic testable and survives the provider changing its API.

Two implementations:

* :class:`FakePromptPlanningClient` — deterministic, used by every automated test and
  by local development without a key. It costs nothing and never leaves the process.
* :class:`OpenAIPromptPlanningClient` — the real thing, using the Responses API with
  structured output.

Tests must never construct the OpenAI client.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Protocol, runtime_checkable

from app.domain.errors import StudioError
from app.domain.schemas import PromptPlan, PromptPlanRequest

logger = logging.getLogger(__name__)


class PlanningError(StudioError):
    """The planning model failed or returned something unusable."""


@runtime_checkable
class PromptPlanningClient(Protocol):
    """Turns a bounded request into a structured production plan."""

    def create_plan(self, request: PromptPlanRequest) -> PromptPlan: ...


class FakePromptPlanningClient:
    """A deterministic planner.

    It composes a plan from the request itself, so a test asserting on the output is
    asserting on the context the service assembled. The same request always produces
    the same plan.
    """

    def __init__(self, *, fail_with: str | None = None) -> None:
        self._fail_with = fail_with
        self.requests: list[PromptPlanRequest] = []

    def create_plan(self, request: PromptPlanRequest) -> PromptPlan:
        self.requests.append(request)

        if self._fail_with is not None:
            raise PlanningError(self._fail_with)

        shot = request.shot
        hero = shot.hero_product or "Black heavyweight t-shirt"
        camera = shot.camera_position or "Across the street, slightly behind"
        lighting = shot.lighting_source or "Streetlight spill and venue light"

        return PromptPlan(
            scene_summary=shot.title,
            emotional_beat="Renewed momentum; the night is continuing.",
            hero_product=hero,
            product_visibility_instruction=(
                f"The {hero.lower()} is visible because of what the subject is doing, "
                "never because they are displaying it."
            ),
            camera_position=camera,
            lighting_source=lighting,
            documentary_imperfection="A foreground element crops part of the frame.",
            australian_authenticity_anchors=[
                "Australian street signage and suburban architecture",
                "Generic unbranded packaging",
            ],
            negative_constraints=[
                "No visible branding or commercial logos",
                "No American pickup trucks",
                "No studio lighting",
                "No posing or acknowledgement of the camera",
            ],
            mood_words=["Hopeful", "Loose", "Possible"],
            selection_rationale=(
                request.selection_reason or f"{shot.external_id} is the next planned shot."
            ),
            production_prompt=(
                f"Documentary 35mm photograph, high ISO, natural grain. {shot.title}. "
                f"Hero product: {hero}, naturally visible. Camera: {camera}. "
                f"Lighting: {lighting}. Australian night-out setting. "
                "All clothing and packaging completely blank and unbranded."
            ),
        )


# The schema the model must satisfy. Kept beside the adapter because it describes the
# wire format, not the domain type.
PROMPT_PLAN_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "scene_summary",
        "emotional_beat",
        "hero_product",
        "product_visibility_instruction",
        "camera_position",
        "lighting_source",
        "documentary_imperfection",
        "australian_authenticity_anchors",
        "negative_constraints",
        "mood_words",
        "selection_rationale",
        "production_prompt",
    ],
    "properties": {
        "scene_summary": {"type": "string"},
        "emotional_beat": {"type": "string"},
        "hero_product": {"type": "string"},
        "product_visibility_instruction": {"type": "string"},
        "camera_position": {"type": "string"},
        "lighting_source": {"type": "string"},
        "documentary_imperfection": {"type": "string"},
        "australian_authenticity_anchors": {"type": "array", "items": {"type": "string"}},
        "negative_constraints": {"type": "array", "items": {"type": "string"}},
        "mood_words": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 4,
        },
        "selection_rationale": {"type": "string"},
        "production_prompt": {"type": "string"},
    },
}

SYSTEM_INSTRUCTIONS = """\
You are the World Architect for a private photographic production tool.

Write one production prompt for the supplied shot.

The canon includes a Locked Reference Prompt: the prompt that produced this world's
benchmark photograph. Write yours in that form. Not a summary of it, not a variation
on its theme — the same kind of document, for the shot you have been given. It is the
specification. Everything else in the canon is context for filling it.

Match its shape, its rhythm and its length. One short declarative per line. Nobody
named. The atmosphere stated in bare words. What nobody is doing, about the night
rather than about the camera. Background that keeps moving. Garments last. It closes
on what the photograph would mean to somebody in it.

Describe the scene; do not choreograph it. The reference says "one bloke sits
casually on the edge of a white Australian tray-back ute" and leaves the rest to the
picture. Assigning every person a separate precise action, and every object a precise
position, produces a frame the model has to contort to satisfy — that is where cars
lose their seats and rooms lose their walls. Fewer, looser, more natural placements
survive generation better than exact ones.

Two things are not yours to change, because the shotlist depends on them:

- The nominated hero product is the one supplied. Elaborate it if you like — "plain
  black tote bag" for "tote bag" — but do not substitute it.
- The camera position is the one supplied.

Obey the canon you have been given. Where it and this instruction disagree, the canon
wins.

Use Australian English. Return only the structured fields requested."""


class OpenAIPromptPlanningClient:
    """Planning through the OpenAI Responses API with structured output."""

    def __init__(self, client: Any, model: str, timeout_seconds: float) -> None:
        if not model:
            raise PlanningError(
                "OPENAI_TEXT_MODEL is not set. Configure it explicitly: guessing a "
                "model name can cause unexpected cost."
            )
        self._client = client
        self._model = model
        self._timeout = timeout_seconds

    def create_plan(self, request: PromptPlanRequest) -> PromptPlan:
        try:
            response = self._client.responses.create(
                model=self._model,
                timeout=self._timeout,
                instructions=SYSTEM_INSTRUCTIONS,
                input=[{"role": "user", "content": _render_request(request)}],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "prompt_plan",
                        "strict": True,
                        "schema": PROMPT_PLAN_JSON_SCHEMA,
                    }
                },
            )
        except Exception as error:
            raise PlanningError(f"The planning request failed: {error}") from error

        request_id = getattr(response, "id", None)
        if request_id:
            # Provider request IDs are logged for support; payloads are not.
            logger.info("Planning response %s from %s", request_id, self._model)

        return _parse_plan(_output_text(response))


def _output_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text
    raise PlanningError("The planning response contained no text output.")


def _parse_plan(text: str) -> PromptPlan:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise PlanningError("The planning response was not valid JSON.") from error

    try:
        return PromptPlan.model_validate(payload)
    except Exception as error:
        raise PlanningError(f"The planning response did not match the schema: {error}") from error


def _render_request(request: PromptPlanRequest) -> str:
    """The user message: only the canon and history relevant to this shot."""
    parts: list[str] = [
        f"World: {request.world_name} ({request.world_slug})",
        "",
        "## Shot",
        f"ID: {request.shot.external_id}",
        f"Scene: {request.shot.title}",
        f"Required hero product: {request.shot.hero_product or 'unset'}",
        f"Required camera position: {request.shot.camera_position or 'unset'}",
    ]

    if request.selection_reason:
        parts += ["", "## Why this shot", request.selection_reason]

    for excerpt in request.canon_excerpts:
        parts += ["", f"## Canon — {excerpt.heading}", excerpt.body]

    parts += _bullet_block("Approved reference frames", request.reference_frames)
    parts += _bullet_block("Recent continuity", request.recent_continuity)
    parts += _bullet_block("Rejected drift to avoid", request.rejected_drift)
    parts += _bullet_block("Current canon notes", request.canon_notes)
    parts += _bullet_block("Recently used hero products", request.recent_hero_products)
    parts += _bullet_block("Recently used camera positions", request.recent_camera_positions)
    parts += _bullet_block("Preferred next hero products", request.next_product_priority)
    parts += _bullet_block("Preferred next camera positions", request.next_camera_priority)

    return "\n".join(parts)


def _bullet_block(heading: str, items: list[str]) -> list[str]:
    if not items:
        return []
    return ["", f"## {heading}", *(f"- {item}" for item in items)]
