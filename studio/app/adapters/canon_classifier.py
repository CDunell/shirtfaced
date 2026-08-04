"""Classifying a proposed rule against existing canon.

The classification is **advisory**. It orders the queue and explains a recommendation;
the owner decides. Both live rulings on 5 August 2026 went against what a naive reading
would have said, which is precisely why this never decides anything.

Tests must never construct the OpenAI client.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from app.domain.enums import ProposalClassification
from app.domain.errors import StudioError
from app.domain.schemas import CanonExcerpt

logger = logging.getLogger(__name__)


class ClassificationError(StudioError):
    """The classifier failed or returned something unusable."""


@dataclass(frozen=True)
class ClassificationRequest:
    """The proposed rule, and the canon to weigh it against."""

    proposed_text: str
    # Only sections the planner reads: a rule can only usefully join one of these.
    canon_excerpts: list[CanonExcerpt]
    source_shot: str | None = None
    source_reason: str | None = None


@dataclass(frozen=True)
class Classification:
    """An advisory reading of a proposal."""

    classification: ProposalClassification
    reason: str
    # The heading the rule would join, when there is an obvious one.
    target_heading: str | None = None
    model: str = "fake-classifier"


@runtime_checkable
class CanonClassifier(Protocol):
    """Weighs a proposed rule against existing canon."""

    def classify(self, request: ClassificationRequest) -> Classification: ...


CLASSIFICATION_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["classification", "reason", "target_heading"],
    "properties": {
        "classification": {
            "type": "string",
            "enum": [value.value for value in ProposalClassification],
        },
        "reason": {"type": "string"},
        "target_heading": {"type": ["string", "null"]},
    },
}

SYSTEM_INSTRUCTIONS = """\
You assess whether a proposed permanent rule belongs in a creative world's canon.

You are advising, not deciding. The owner decides.

Classify the proposal as exactly one of:

- already_covered — an existing rule already implies this. A restatement of something
  canon already says is not a new rule, however true it is.
- genuine_addition — a repeatable rule with no existing home in the canon supplied.
- refinement — an existing rule should be tightened or clarified rather than a new one
  added. Name the section it refines.
- contradiction — it conflicts with a rule already in canon. Say which.
- too_specific — a scene-level observation, not a permanent rule. A one-off failure
  does not become canon; recurrence does, not severity.

Prefer already_covered and too_specific. A canon that grows on every rejection stops
being canon. Only classify something a genuine_addition when no supplied section
implies it.

For genuine_addition and refinement, set target_heading to the exact heading of the
supplied section the rule belongs under. Otherwise set it to null.

Give one sentence of reason, naming the section you compared against.

Use Australian English."""


class FakeCanonClassifier:
    """A deterministic classifier.

    It compares by keyword overlap rather than meaning, which is deliberately crude:
    it makes the queue usable without a key, and it makes tests deterministic. The
    fake defaults to caution — it prefers ``already_covered`` — because the cost of a
    wrongly added rule is permanent and the cost of a wrongly skipped one is that the
    owner reads it in the queue.
    """

    def __init__(
        self, *, result: Classification | None = None, fail_with: str | None = None
    ) -> None:
        self._result = result
        self._fail_with = fail_with
        self.requests: list[ClassificationRequest] = []

    def classify(self, request: ClassificationRequest) -> Classification:
        self.requests.append(request)
        if self._fail_with is not None:
            raise ClassificationError(self._fail_with)
        if self._result is not None:
            return self._result

        proposed = _significant_words(request.proposed_text)
        if not proposed:
            return Classification(
                classification=ProposalClassification.TOO_SPECIFIC,
                reason="The proposal contains nothing substantive to compare.",
            )

        best_heading: str | None = None
        best_overlap = 0.0
        for excerpt in request.canon_excerpts:
            overlap = len(proposed & _significant_words(excerpt.body)) / len(proposed)
            if overlap > best_overlap:
                best_overlap, best_heading = overlap, excerpt.heading

        if best_overlap >= 0.6:
            return Classification(
                classification=ProposalClassification.ALREADY_COVERED,
                reason=f"Most of this wording already appears under {best_heading!r}.",
                target_heading=best_heading,
            )
        if best_overlap >= 0.3:
            return Classification(
                classification=ProposalClassification.REFINEMENT,
                reason=f"This overlaps {best_heading!r} and reads as a tightening of it.",
                target_heading=best_heading,
            )
        return Classification(
            classification=ProposalClassification.GENUINE_ADDITION,
            reason="No supplied section covers this wording.",
            target_heading=best_heading,
        )


def _significant_words(text: str) -> set[str]:
    stopwords = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "in",
        "on",
        "to",
        "is",
        "are",
        "be",
        "must",
        "shall",
        "not",
        "no",
        "any",
        "every",
        "with",
        "for",
        "that",
        "this",
        "it",
        "as",
        "at",
        "by",
        "from",
        "was",
        "were",
        "has",
        "have",
    }
    words = {word.strip(".,;:!?()'\"").casefold() for word in text.split()}
    return {word for word in words if len(word) > 3 and word not in stopwords}


class OpenAICanonClassifier:
    """Classification through the OpenAI Responses API with structured output."""

    def __init__(self, client: Any, model: str, timeout_seconds: float) -> None:
        if not model:
            raise ClassificationError(
                "OPENAI_TEXT_MODEL is not set. Configure it explicitly: guessing a "
                "model name can cause unexpected cost."
            )
        self._client = client
        self._model = model
        self._timeout = timeout_seconds

    def classify(self, request: ClassificationRequest) -> Classification:
        try:
            response = self._client.responses.create(
                model=self._model,
                timeout=self._timeout,
                instructions=SYSTEM_INSTRUCTIONS,
                input=[{"role": "user", "content": _render(request)}],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "canon_classification",
                        "strict": True,
                        "schema": CLASSIFICATION_JSON_SCHEMA,
                    }
                },
            )
        except Exception as error:
            raise ClassificationError(f"The classification request failed: {error}") from error

        text = getattr(response, "output_text", None)
        if not isinstance(text, str) or not text.strip():
            raise ClassificationError("The classification response contained no text output.")

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise ClassificationError("The classification response was not valid JSON.") from error

        try:
            classification = ProposalClassification(payload["classification"])
            reason = str(payload["reason"]).strip()
        except (KeyError, ValueError) as error:
            raise ClassificationError(
                f"The classification response did not match the schema: {error}"
            ) from error

        if not reason:
            raise ClassificationError("The classification response gave no reason.")

        target = payload.get("target_heading")
        return Classification(
            classification=classification,
            reason=reason,
            target_heading=str(target) if target else None,
            model=self._model,
        )


def _render(request: ClassificationRequest) -> str:
    parts = ["## Proposed permanent rule", request.proposed_text]

    if request.source_shot:
        parts += ["", f"Proposed after shot {request.source_shot}."]
    if request.source_reason:
        parts += ["", "## Why that image was rejected", request.source_reason]

    parts += ["", "## Existing canon, section by section"]
    for excerpt in request.canon_excerpts:
        parts += ["", f"### {excerpt.heading}", excerpt.body]

    return "\n".join(parts)
