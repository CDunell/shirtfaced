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

__all__ = ["BriefPackage", "EvidenceImage", "compose_brief"]


@dataclass(frozen=True)
class EvidenceImage:
    """One reference image, as the screen and the brief both need it."""

    url: str
    listing_id: str
    filename: str

    def to_dict(self) -> dict[str, str]:
        return {"url": self.url, "listing_id": self.listing_id, "filename": self.filename}


@dataclass(frozen=True)
class BriefPackage:
    """The brief as text, plus the evidence it refers to."""

    text: str
    evidence_images: list[EvidenceImage]
    evidence_listing_ids: list[str]
    research_run_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "evidence_images": [image.to_dict() for image in self.evidence_images],
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

    images = _evidence(references.get("evidence_images"))
    listings = [str(item) for item in references.get("evidence_listing_ids") or []]
    if not images:
        research = concept.preferred_execution or {}
        images = _evidence(research.get("evidence_images"))
        listings = [str(item) for item in research.get("evidence_listing_ids") or []]

    if images:
        lines += [
            "",
            "EVIDENCE",
            # One sentence, and no URLs. The first version printed each entry's
            # dict repr; the second replaced that with one line per URL, which
            # is a shorter wall of the same noise -- and the paths are relative,
            # so pasted into ChatGPT or Gemini they are not merely ugly but
            # meaningless. The images are shown beside this brief in Studio and
            # attached as files from there, which is how a person actually gets
            # them to a generation interface.
            (
                f"{len(images)} reference image{'s' if len(images) != 1 else ''} from the "
                "vintage corpus are shown with this brief in Studio. Attach them alongside "
                "it — they are what the era is read from."
            ),
        ]

    return BriefPackage(
        text="\n".join(lines),
        evidence_images=images,
        evidence_listing_ids=listings,
        research_run_id=str(references.get("vintage_research_run_id") or ""),
    )


def _evidence(stored: Any) -> list[EvidenceImage]:
    """Read the stored evidence, whatever shape it is in.

    The research run records each image as a dict -- ``image_url``, ``filename``,
    ``listing_id``, ``sha256``, ``byte_size``, ``mime_type``. The first version
    of this module assumed a list of strings and called ``str()`` on each entry,
    which printed the whole dict's repr into the brief: a wall of sha256 hashes
    and byte counts where the URLs should have been, and no image anywhere.

    Plain strings are still accepted, because an older run may hold them and a
    brief that drops its evidence is worse than one that shows a bare path.
    """
    found: list[EvidenceImage] = []
    for item in stored or []:
        if isinstance(item, dict):
            url = str(item.get("image_url") or item.get("url") or "").strip()
            if not url:
                continue
            found.append(
                EvidenceImage(
                    url=url,
                    listing_id=str(item.get("listing_id") or ""),
                    filename=str(item.get("filename") or url.rsplit("/", 1)[-1]),
                )
            )
        elif isinstance(item, str) and item.strip():
            found.append(
                EvidenceImage(
                    url=item.strip(),
                    listing_id="",
                    filename=item.strip().rsplit("/", 1)[-1],
                )
            )
    return found
