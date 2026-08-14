"""What leaves the building with one attempt.

Phase 6, restated: the evidence reaches the brief, because since decision 0.1
the brief is the thing that leaves and there is no generator here to reach.
"""

from __future__ import annotations

from app.db.concept_models import DesignAttempt, DesignBrief, DesignConcept
from app.domain.enums import (
    CollectionRole,
    ConceptLibrary,
    DesignAttemptMethod,
    GraphicArchetype,
    LayoutArchetype,
)
from app.services.brief_package import compose_brief


def concept(brief: DesignBrief | None = None, preferred: dict[str, object] | None = None):
    row = DesignConcept(
        library=ConceptLibrary.VINTAGE_RESEARCH,
        external_number=1,
        slug="0001-second-breakfast",
        title="SECOND BREAKFAST",
        concept_text="A type-led chest lockup treating a second breakfast as an institution.",
        round=0,
        source_path="x",
        source_document_hash="0" * 64,
        parsed_json={},
        preferred_execution=preferred or {},
    )
    row.brief = brief
    return row


def attempt(concept_row: DesignConcept, prompt: str = "", references: dict | None = None):
    row = DesignAttempt(
        attempt_number=1,
        method=DesignAttemptMethod.IMAGE_GENERATION,
        production_prompt=prompt,
        reference_inputs=references or {},
    )
    row.concept = concept_row
    return row


def full_brief() -> DesignBrief:
    return DesignBrief(
        garment_category="tee",
        canonical_blank="AS Colour 5026",
        fit_block="regular",
        fabric_weight="220gsm",
        garment_colour="black",
        wash="none",
        production_method="screen print",
        collection_role=CollectionRole.CORE,
        graphic_archetype=GraphicArchetype.TYPOGRAPHIC_HERO,
        layout_archetype=LayoutArchetype.A3_FRONT_HERO_CLEAN_BACK,
        notes="Keep the counters open at 180mm.",
    )


def test_the_brief_leads_with_the_owners_words() -> None:
    package = compose_brief(attempt(concept()))

    assert package.text.startswith("SECOND BREAKFAST — Shirtfaced concept #1")
    assert "second breakfast as an institution" in package.text


def test_the_product_and_the_architecture_travel_with_it() -> None:
    package = compose_brief(attempt(concept(full_brief())))

    assert "THE PRODUCT" in package.text
    assert "Blank: AS Colour 5026" in package.text
    assert "Method: screen print" in package.text
    assert "THE ARCHITECTURE" in package.text
    assert "Role in the range: core" in package.text
    assert "Graphic archetype: typographic hero" in package.text
    assert "NOTES" in package.text


def test_a_documented_departure_is_carried_instead_of_a_layout() -> None:
    brief = full_brief()
    brief.layout_archetype = None
    brief.archetype_departure_reason = "The joke needs the back and the sleeve at once."

    package = compose_brief(attempt(concept(brief)))

    assert "Departs from the layout library: The joke needs the back" in package.text
    assert "Layout archetype:" not in package.text


def test_the_evidence_travels_and_says_why() -> None:
    """The whole point of the restatement: it goes with the brief, because the
    brief is what a person carries to a paid interface."""
    package = compose_brief(
        attempt(
            concept(full_brief()),
            prompt="heavy condensed sans lockup",
            references={
                "evidence_images": ["listing-1/0.jpg", "listing-1/2.jpg"],
                "evidence_listing_ids": ["listing-1"],
                "vintage_research_run_id": "run-9",
            },
        )
    )

    assert "EVIDENCE" in package.text
    assert "2 reference image(s)" in package.text
    assert "Attach them alongside this brief" in package.text
    assert "listing-1/0.jpg" in package.text
    assert package.evidence_images == ["listing-1/0.jpg", "listing-1/2.jpg"]
    assert package.research_run_id == "run-9"


def test_the_researched_prompt_survives_a_concept_with_no_attempt_prompt() -> None:
    """Phase 4 stopped creating an attempt before a brief exists, and kept the
    researched prompt against the concept. It must not be lost on the way."""
    package = compose_brief(
        attempt(
            concept(
                full_brief(),
                preferred={
                    "production_prompt": "kept against the concept",
                    "evidence_images": ["listing-7/1.jpg"],
                },
            )
        )
    )

    assert "kept against the concept" in package.text
    assert package.evidence_images == ["listing-7/1.jpg"]


def test_a_brief_with_no_evidence_says_nothing_about_evidence() -> None:
    package = compose_brief(attempt(concept(full_brief())))

    assert "EVIDENCE" not in package.text
    assert package.evidence_images == []


def test_an_unbriefed_concept_still_produces_something_usable() -> None:
    """A brief is filled in over time; the words are worth carrying before the
    rest of it exists."""
    package = compose_brief(attempt(concept()))

    assert "SECOND BREAKFAST" in package.text
    assert "THE PRODUCT" not in package.text
