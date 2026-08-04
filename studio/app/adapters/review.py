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

REVIEW_SCHEMA_VERSION = 1


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

For each of the nine gates report what is actually visible.

- Evidence is one concise observation of something visible. Not aesthetic commentary.
- Confidence is evidentiary. Return UNCERTAIN rather than guessing about tiny labels,
  fabric construction, obscured vehicle bodies or ambiguous marks.
- Low confidence cannot by itself support a material failure. It can ask for human
  inspection.
- Return NOT_APPLICABLE where a gate does not apply, such as vehicle continuity when
  no vehicle is visible.
- Mark a finding material only if it could change the recommendation.

Recommend rejection for a clearly evidenced foundational failure: the wrong or
materially inaccurate nominated product; any garment graphic, logo, text, embroidery
or visible label; readable third-party branding; posed or fashion-campaign behaviour;
an American pickup or enclosed tub where a ute is visible; resignation or
drunken-comedy drift; no independent documentary value; or a severe artefact.

Incidental Shirtfaced environmental marks are permitted. Third-party branding is not,
and garments and packaging stay blank and generic regardless.

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
            },
            "mood_score": 4,
            "australian_authenticity_score": 4,
            "product_visibility_score": 4,
            "documentary_credibility_score": 4,
            "story_score": 4,
            "branding_compliant": True,
            "vehicle_compliant": True,
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
