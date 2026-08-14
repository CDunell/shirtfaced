"""Everything that leaves the building with one attempt.

Phase 6, restated. As written it was *evidence reaches the image generator*, and
decision 0.1 removed the generator: the app owns the brief, the record, the
measurement, the judgement and the decision, and the pixels are made in a paid
interface. The plan's escape hatch -- local generation -- is the branch 0.1
declined.

So the evidence reaches **the brief**, because the brief is the thing that
leaves. One action produces the words, the product definition and the evidence
image references, so a person can paste the lot into ChatGPT, Gemini or Claude
without assembling it from three screens. What went out is recorded on the
attempt, which is the half of the original exit test that survives.

Composed on the server rather than in the browser for the reason every other
sentence is: two screens phrasing the same thing separately is how they come to
disagree, and the record of what was taken has to match what was actually shown.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.db.concept_models import DesignAttempt

__all__ = ["BriefPackage", "compose_brief"]


@dataclass(frozen=True)
class BriefPackage:
    """The brief as text, plus the evidence it refers to."""

    text: str
    evidence_images: list[str]
    evidence_listing_ids: list[str]
    research_run_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "evidence_images": list(self.evidence_images),
            "evidence_listing_ids": list(self.evidence_listing_ids),
            "research_run_id": self.research_run_id,
            "evidence_count": len(self.evidence_images),
        }


def compose_brief(attempt: DesignAttempt) -> BriefPackage:
    """One attempt's brief: the idea, the product, the prompt, the evidence."""
    concept = attempt.concept
    brief = concept.brief
    references = attempt.reference_inputs or {}

    lines: list[str] = [
        f"{concept.title} — Shirtfaced concept #{concept.external_number}",
        "",
        concept.concept_text,
    ]

    if brief is not None:
        product = [
            (label, str(getattr(brief, field, "")).strip())
            for field, label in (
                ("garment_category", "Garment"),
                ("canonical_blank", "Blank"),
                ("fit_block", "Fit"),
                ("fabric_weight", "Weight"),
                ("garment_colour", "Colour"),
                ("wash", "Wash"),
                ("production_method", "Method"),
            )
        ]
        stated = [f"{label}: {value}" for label, value in product if value]
        if stated:
            lines += ["", "THE PRODUCT", *stated]

        architecture = []
        if brief.collection_role is not None:
            architecture.append(f"Role in the range: {brief.collection_role.value}")
        if brief.graphic_archetype is not None:
            architecture.append(
                f"Graphic archetype: {brief.graphic_archetype.value.replace('_', ' ')}"
            )
        if brief.layout_archetype is not None:
            architecture.append(
                f"Layout archetype: {brief.layout_archetype.value.replace('_', ' ')}"
            )
        elif brief.archetype_departure_reason.strip():
            architecture.append(
                f"Departs from the layout library: {brief.archetype_departure_reason.strip()}"
            )
        if architecture:
            lines += ["", "THE ARCHITECTURE", *architecture]

        if brief.notes.strip():
            lines += ["", "NOTES", brief.notes.strip()]

    prompt = str(attempt.production_prompt or "").strip()
    if not prompt:
        # The researched prompt is kept against the concept when the attempt
        # could not be opened yet, so it is not lost between research and brief.
        prompt = str((concept.preferred_execution or {}).get("production_prompt") or "").strip()
    if prompt:
        lines += ["", "PROMPT", prompt]

    images = [str(item) for item in references.get("evidence_images") or []]
    listings = [str(item) for item in references.get("evidence_listing_ids") or []]
    if not images:
        research = concept.preferred_execution or {}
        images = [str(item) for item in research.get("evidence_images") or []]
        listings = [str(item) for item in research.get("evidence_listing_ids") or []]

    if images:
        lines += [
            "",
            "EVIDENCE",
            (
                f"{len(images)} reference image(s) from the vintage corpus. "
                "Attach them alongside this brief; they are what the era is read from."
            ),
            *images,
        ]

    return BriefPackage(
        text="\n".join(lines),
        evidence_images=images,
        evidence_listing_ids=listings,
        research_run_id=str(references.get("vintage_research_run_id") or ""),
    )
