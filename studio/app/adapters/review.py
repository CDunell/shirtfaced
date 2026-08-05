"""Image review adapters.

Review is a separate model operation from generation, with its own adapter, so a
stored image is never mistaken for an approved one.

The model looks at the actual stored image, not just the prompt. That is the whole
point: a prompt that says "blank garments" proves nothing about what was drawn.

Tests must never construct the OpenAI client.
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from app.domain.enums import GateName, GateStatus, ReviewRecommendation
from app.domain.errors import StudioError
from app.domain.schemas import CanonExcerpt, ImageReview

logger = logging.getLogger(__name__)

# 2 added the structural_plausibility gate and the structurally_sound field. A
# version 1 review has neither, and its silence about structure is absence of
# assessment rather than a pass.
REVIEW_SCHEMA_VERSION = 2


class ReviewError(StudioError):
    """The review model failed or returned something unusable."""


@dataclass(frozen=True)
class ImageReviewRequest:
    """Everything the reviewer is allowed to see.

    The image itself, what was asked for, and the canon to judge against. Nothing
    about earlier decisions, so the reviewer cannot simply agree with the last one.
    """

    attempt_id: str
    image_data: bytes
    image_mime_type: str
    shot_external_id: str
    scene: str
    # The exact values from the shotlist, not paraphrases.
    required_hero_product: str | None
    required_camera_position: str | None
    production_prompt: str
    selection_rationale: str = ""
    canon_excerpts: list[CanonExcerpt] = field(default_factory=list)
    canon_notes: list[str] = field(default_factory=list)
    rejected_drift: list[str] = field(default_factory=list)
    world_document_hash: str | None = None


@dataclass(frozen=True)
class ReviewResult:
    """A validated review and how it was produced."""

    review: ImageReview
    model: str
    provider_request_id: str | None = None
    schema_version: int = REVIEW_SCHEMA_VERSION


@runtime_checkable
class ImageReviewClient(Protocol):
    """Judges one generated image against canon."""

    def review(self, request: ImageReviewRequest) -> ReviewResult: ...


def _gate_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["status", "evidence", "codes", "confidence", "material"],
        "properties": {
            "status": {"type": "string", "enum": [status.value for status in GateStatus]},
            "evidence": {"type": "string"},
            "codes": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "material": {"type": "boolean"},
        },
    }


IMAGE_REVIEW_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "recommendation",
        "gates",
        "mood_score",
        "australian_authenticity_score",
        "product_visibility_score",
        "documentary_credibility_score",
        "story_score",
        "branding_compliant",
        "vehicle_compliant",
        "structurally_sound",
        "strongest_success",
        "material_drift",
        "new_rule_proposal",
        "next_hero_product",
        "next_camera",
    ],
    "properties": {
        "recommendation": {
            "type": "string",
            "enum": [value.value for value in ReviewRecommendation],
        },
        "gates": {
            "type": "object",
            "additionalProperties": False,
            "required": [gate.value for gate in GateName],
            "properties": {gate.value: _gate_schema() for gate in GateName},
        },
        "mood_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "australian_authenticity_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "product_visibility_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "documentary_credibility_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "story_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "branding_compliant": {"type": "boolean"},
        "vehicle_compliant": {"type": "boolean"},
        "structurally_sound": {"type": "boolean"},
        "strongest_success": {"type": "string"},
        "material_drift": {"type": ["string", "null"]},
        "new_rule_proposal": {"type": ["string", "null"]},
        "next_hero_product": {"type": ["string", "null"]},
        "next_camera": {"type": ["string", "null"]},
    },
}

SYSTEM_INSTRUCTIONS = """\
You are the Continuity Director for a private photographic production tool.

Judge the supplied image against the supplied canon. Assess the image, not the prompt:
what the prompt asked for is not evidence of what was drawn.

For each of the ten gates report what is actually visible.

- Evidence is one concise observation of something visible. Not aesthetic commentary.
- Confidence is evidentiary. Return UNCERTAIN rather than guessing about tiny labels,
  fabric construction, obscured vehicle bodies or ambiguous marks.
- Low confidence cannot by itself support a material failure. It can ask for human
  inspection.
- Return NOT_APPLICABLE where a gate does not apply, such as vehicle continuity when
  no vehicle is visible.
- Mark a finding material only if it could change the recommendation.

STRUCTURAL PLAUSIBILITY asks one question the other nine do not: could the thing in
this photograph exist? Judge the physical object, not the mood.

- Is anything missing that must be there? A car with no seats. A vehicle whose rear
  end is absent, showing the background through where the body should be. A room with
  no floor.
- Is every person supported by something? Weight has to rest on a surface that is
  visible or clearly implied. Someone perched where there is nothing to sit on fails,
  however natural their posture looks.
- Does the furniture match the people? A row built for two cannot seat three. A seat
  faces the way it is bolted down; a passenger squared to a side door means the seat
  has been silently rotated.
- Counts and joins: limbs, fingers, legs of chairs, wheels, doors. Reflections that
  disagree with the scene.
- Does everything being operated have the thing it operates in frame? A lift call
  button with no lift. An entry intercom being pressed by somebody already inside
  the lobby, when a buzzer is on the street side of the door and exists to get you
  in. A handle on no door, a pump with no car. This one hides well, because the
  person, the hand and the panel are each ordinary; it is the relationship between
  them that cannot exist.

A frame can be beautiful, documentary and perfectly Australian and still fail this
gate. It is a fact check, not a taste judgement, and it is the one an approving
reader is most likely to skip. Set structurally_sound false whenever this gate fails.

COMPOSITION covers where the photographer is standing. The camera observes, so it
stands outside what it is watching -- never inside the box with the subjects. Fail it
when the frame is taken from inside the enclosed space the group occupies: inside the
lift with them, inside the car with them, looking out over a door sill or past window
rubber with an occupant on the camera's side of the glass. Being in an interior is
fine. A kitchen photographed from the dining room is an observer; a lift photographed
from inside the lift is a passenger.

COMPOSITION also covers where the subjects are. They stay out of small built
enclosures — car cabins, lifts, tents, phone boxes — and are next to, in front of, or
sitting on them instead. The exception is interaction at an opening: someone already
seated in a car talking out through the window, someone at a tent entrance. A group
crowded inside a lift is the failure; the same group in the lobby is not.

VEHICLE CONTINUITY also covers what people are doing with the vehicle, not only its
body shape. Fail it when anyone is entering, leaving, climbing in, or half in and half
out. A correct body shape does not pass this gate on its own.

THIRD-PARTY BRANDING turns on what the brand sells, not on whether a mark is visible.
There are two rules and they are not the same rule.

Apparel — anything the brand sells, worn, carried, folded or on a poster behind — is
blank always. Any graphic, logo, printed text, embroidery or visible label on a
garment fails, with no background exemption and no allowance for distance or blur.

Everything else may carry its real branding, and is wanted. Servo price boards,
shopfronts, buses, street signage, food packaging, drink cans, delivery bags: the
ordinary marked clutter of a Friday night belongs in these photographs, because its
absence is what makes a frame look staged. It fails only when it stops being
background — centred, held up, presented, or so large and legible that the eye goes to
it first. A servo sign across wet asphalt is scenery; the same sign filling a third of
the frame is an advertisement for someone else.

So do not fail this gate merely because a brand is legible somewhere in the frame.
Ask what it is on and where it sits. An unbranded object is never a branding failure:
a plain can, a blank carton, an unmarked esky, a worn sticker with no readable text.
Shirtfaced's own environmental marks are permitted and are not third-party. Where a
mark is present but you cannot read it, return UNCERTAIN rather than failing.

Recommend rejection for a clearly evidenced foundational failure: the wrong or
materially inaccurate nominated product; any garment graphic, logo, text, embroidery
or visible label; third-party branding that has stopped being background; posed or
fashion-campaign behaviour;
an American pickup or enclosed tub where a ute is visible; a camera inside a vehicle
or anyone getting into or out of one; resignation or drunken-comedy drift; no
independent documentary value; a severe artefact; or anything that could not
physically exist.

Recommend approval with a note only when the image belongs in the world and the note
records a genuinely repeatable rule. Never use it to excuse a foundational failure.

Propose a new permanent rule only for a repeatable failure that canon does not already
cover. Otherwise return null.

You never approve or reject anything. You advise; the owner decides. Use Australian
English."""


class FakeImageReviewClient:
    """A deterministic reviewer.

    It judges from the request rather than from pixels, which is exactly what a test
    needs: the outcome is a function of what the service assembled. Override
    ``result`` to script a specific verdict for a fixture.
    """

    def __init__(
        self,
        *,
        result: ImageReview | None = None,
        fail_with: str | None = None,
        model: str = "fake-review-model",
    ) -> None:
        self._result = result
        self._fail_with = fail_with
        self._model = model
        self.requests: list[ImageReviewRequest] = []

    def review(self, request: ImageReviewRequest) -> ReviewResult:
        self.requests.append(request)
        if self._fail_with is not None:
            raise ReviewError(self._fail_with)

        return ReviewResult(
            review=self._result or default_fake_review(request),
            model=self._model,
            provider_request_id="fake-review-request",
        )


def default_fake_review(request: ImageReviewRequest) -> ImageReview:
    """A plausible pass, built from the request so it stays consistent with it."""
    product = request.required_hero_product or "the nominated product"
    camera = request.required_camera_position or "the nominated camera position"

    def gate(evidence: str, status: GateStatus = GateStatus.PASS) -> dict[str, Any]:
        return {
            "status": status,
            "evidence": evidence,
            "codes": [],
            "confidence": 0.8,
            "material": False,
        }

    return ImageReview.model_validate(
        {
            "recommendation": ReviewRecommendation.APPROVE,
            "gates": {
                GateName.MOOD: gate("The group is mid-action and the night is continuing."),
                GateName.AUSTRALIAN_AUTHENTICITY: gate(
                    "Suburban Australian street furniture is visible behind the group."
                ),
                GateName.PRODUCT_VISIBILITY: gate(
                    f"{product} is visible through the action rather than displayed."
                ),
                GateName.THIRD_PARTY_BRANDING: gate("No readable third-party marks are visible."),
                GateName.VEHICLE_CONTINUITY: gate(
                    "No vehicle is visible in frame.", GateStatus.NOT_APPLICABLE
                ),
                GateName.WARDROBE_BALANCE: gate(
                    "Clothing varies in colour and cut across the group."
                ),
                GateName.COMPOSITION: gate(f"The framing is consistent with {camera}."),
                GateName.DOCUMENTARY_CREDIBILITY: gate(
                    "People are engaged with each other, not the camera."
                ),
                GateName.STORY: gate("A clear social action is under way."),
                GateName.STRUCTURAL_PLAUSIBILITY: gate(
                    "Everyone is supported, and nothing is missing from the scene."
                ),
            },
            "mood_score": 4,
            "australian_authenticity_score": 4,
            "product_visibility_score": 4,
            "documentary_credibility_score": 4,
            "story_score": 4,
            "branding_compliant": True,
            "vehicle_compliant": True,
            "structurally_sound": True,
            "strongest_success": "The moment reads as taken rather than arranged.",
            "material_drift": None,
            "new_rule_proposal": None,
            "next_hero_product": None,
            "next_camera": None,
        }
    )


class OpenAIImageReviewClient:
    """Review through the OpenAI Responses API, with the image attached."""

    def __init__(self, client: Any, model: str, timeout_seconds: float) -> None:
        if not model:
            raise ReviewError(
                "OPENAI_REVIEW_MODEL is not set. Configure it explicitly: guessing a "
                "model name can cause unexpected cost."
            )
        self._client = client
        self._model = model
        self._timeout = timeout_seconds

    def review(self, request: ImageReviewRequest) -> ReviewResult:
        encoded = base64.b64encode(request.image_data).decode()

        try:
            response = self._client.responses.create(
                model=self._model,
                timeout=self._timeout,
                instructions=SYSTEM_INSTRUCTIONS,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": _render_request(request)},
                            {
                                "type": "input_image",
                                "image_url": f"data:{request.image_mime_type};base64,{encoded}",
                            },
                        ],
                    }
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "image_review",
                        "strict": True,
                        "schema": IMAGE_REVIEW_JSON_SCHEMA,
                    }
                },
            )
        except Exception as error:
            raise ReviewError(f"The review request failed: {error}") from error

        request_id = getattr(response, "id", None)
        if request_id:
            # Provider request IDs are logged for support; image payloads are not.
            logger.info("Review response %s from %s", request_id, self._model)

        return ReviewResult(
            review=_parse_review(_output_text(response)),
            model=self._model,
            provider_request_id=str(request_id) if request_id else None,
        )


def _output_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text
    raise ReviewError("The review response contained no text output.")


def _parse_review(text: str) -> ImageReview:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise ReviewError("The review response was not valid JSON.") from error

    try:
        return ImageReview.model_validate(payload)
    except Exception as error:
        raise ReviewError(f"The review response did not match the schema: {error}") from error


def _render_request(request: ImageReviewRequest) -> str:
    parts: list[str] = [
        "## What was asked for",
        f"Shot: {request.shot_external_id} — {request.scene}",
        f"Required hero product: {request.required_hero_product or 'unset'}",
        f"Required camera position: {request.required_camera_position or 'unset'}",
        "",
        "## Production prompt used",
        request.production_prompt,
    ]

    if request.selection_rationale:
        parts += ["", "## Why this shot was chosen", request.selection_rationale]

    for excerpt in request.canon_excerpts:
        parts += ["", f"## Canon — {excerpt.heading}", excerpt.body]

    if request.canon_notes:
        parts += ["", "## Current canon notes", *(f"- {note}" for note in request.canon_notes)]

    if request.rejected_drift:
        parts += [
            "",
            "## Previously rejected drift",
            *(f"- {entry}" for entry in request.rejected_drift),
        ]

    return "\n".join(parts)
