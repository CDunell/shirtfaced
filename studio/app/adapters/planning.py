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
        "selection_rationale": {"type": "string"},
        "production_prompt": {"type": "string"},
    },
}

SYSTEM_INSTRUCTIONS = """\
You are the World Architect for a private photographic production tool.

Build one production prompt for the supplied shot, obeying the supplied canon exactly.

Rules you must not break:
- The photograph must work as a documentary image without any product in it.
- The nominated hero product must be the one supplied. Do not substitute it.
- The camera position must be the one supplied.
- Every garment in frame is blank: no logos, graphics, printed text, embroidery or
  labels. This holds wherever in the frame it sits.
- Everything the brand does not sell may carry real branding, as background only.
  Servo boards, shopfronts, packaging, transport. Never centred, never the reason
  the frame exists, never held up or displayed.
- Use Australian English.

WRITING THE PRODUCTION PROMPT

One short declarative sentence per line. No paragraphs. A dense block of prose
produces a posed group portrait with documentary styling applied over it; the line
break is what forces each detail to be specified rather than gestured at.

Cover these, in this order:

1. "Photorealistic documentary photograph." Then country, night, and a specific
   clock time such as 12:07am. Not "at night".
2. The location in one line, then what it is NOT. "Not the destination. Just a stop
   on the way to whatever happens next."
3. The cast as a count and a split: "Six ordinary Australians in their mid-twenties
   to mid-thirties. Three men. Three women." Six to ten people. Four reads as
   arranged.
4. "Nobody is posing. Nobody acknowledges the camera."
5. One line per person, each doing a specific ordinary thing, none of it about the
   camera and none of it about the product. Someone washing a windscreen that
   barely needs it. Someone stealing a chip before anyone notices. Someone laughing
   so hard they have to stop walking. This is the section that decides whether the
   photograph is alive.
6. "Nobody is rushing. Nobody looks like a model. Nobody is performing."
7. The light, itemised one source per line, all of it practical and available.
8. The clutter: what is on the bench, in the boot, on the ground. Then background
   life — strangers, passing cars, someone out of focus in a doorway. An empty
   background is the clearest sign of a set.
9. "Everything feels completely ordinary." "Everything feels unmistakably
   Australian."
10. Who took it and from where, as a person: "Photographed from across the forecourt
    by another friend waiting beside their own car."
11. The camera block, one per line: 35mm documentary photography. 50mm lens. Kodak
    Portra 400. Available light only. Natural film grain. No HDR. No cinematic
    colour grading. Slight motion blur. Slightly underexposed. Imperfect framing.
12. A named crop and a named obstruction: which person the edge cuts, and what sits
    in front of the lens.
13. "The photograph feels accidental rather than composed."
14. The garments, one line each, all plain and blank, the hero product among them
    and never presented.
15. "The photograph should be good enough that someone would post it on Instagram
    even if everyone was wearing plain black clothing."

No HDR and no cinematic colour grading are not stylistic preferences. Warm, even,
flattering light is the single most common failure, and it has to be refused
explicitly or it arrives by default.

Return only the structured fields requested."""


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
