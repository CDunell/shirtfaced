"""The concept library actually shipped in the repository.

The fixtures elsewhere are simplified. This is the real thing: if the tee
library stops parsing -- or an edit quietly changes what retirement means --
this fails, with the counts the source held on the day the pipeline landed.
"""

from __future__ import annotations

import pytest

from app.config import PROJECT_ROOT
from app.domain.enums import ConceptStatus
from app.services.concept_loader import load_concept_library

LIBRARY_PATH = PROJECT_ROOT.parent / "docs" / "design" / "TSHIRT_CONCEPT_LIBRARY.md"

pytestmark = pytest.mark.skipif(
    not LIBRARY_PATH.is_file(),
    reason="The tee concept library is not present.",
)


@pytest.fixture
def loaded():  # type: ignore[no-untyped-def]
    return load_concept_library(LIBRARY_PATH)


def test_all_two_hundred_and_sixty_concepts_are_read(loaded) -> None:  # type: ignore[no-untyped-def]
    numbers = [concept.external_number for concept in loaded.concepts]
    assert numbers == list(range(1, 261))


def test_the_retirement_counts_match_the_source(loaded) -> None:  # type: ignore[no-untyped-def]
    """12 hard, 1 unconditional, 17 conditional. A drift here is an edit to review."""
    by_retirement = {
        kind: [c.external_number for c in loaded.concepts if c.retirement == kind]
        for kind in ("hard", "unconditional", "conditional")
    }
    assert by_retirement["hard"] == [8, 14, 18, 21, 23, 31, 33, 41, 53, 55, 56, 59]
    assert by_retirement["unconditional"] == [102]
    assert len(by_retirement["conditional"]) == 17


def test_the_statuses_add_up(loaded) -> None:  # type: ignore[no-untyped-def]
    statuses = [concept.status for concept in loaded.concepts]
    assert statuses.count(ConceptStatus.RETIRED) == 13
    assert statuses.count(ConceptStatus.HELD) == 17
    assert statuses.count(ConceptStatus.BACKLOG) == 230


def test_the_decoy_stays_live(loaded) -> None:  # type: ignore[no-untyped-def]
    """Entry 54 says "retired blokes" in prose. It is a live concept."""
    concept = loaded.concepts[53]
    assert concept.title == "SENIOR MANAGEMENT"
    assert concept.status is ConceptStatus.BACKLOG


def test_the_garment_led_rounds_all_declare_garments(loaded) -> None:  # type: ignore[no-untyped-def]
    for concept in loaded.concepts:
        if concept.round >= 5:
            assert concept.garments, f"#{concept.external_number} has no garment prefix"
        else:
            assert not concept.garments, f"#{concept.external_number} has a surprise prefix"


def test_the_repeated_titles_get_distinct_slugs(loaded) -> None:  # type: ignore[no-untyped-def]
    slugs = [concept.slug for concept in loaded.concepts]
    assert len(set(slugs)) == len(slugs)
    assert slugs[119] == "120-shirtfaced"
    assert slugs[179] == "180-shirtfaced"
    assert slugs[259] == "260-shirtfaced"
