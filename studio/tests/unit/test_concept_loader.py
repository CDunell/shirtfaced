"""The parser must read the library the owner actually wrote.

The stakes are all in the retirement handling: a substring match fabricates
retirements out of prose, a missed title prefix resurrects a decided one, and
mapping a conditional "Retire ... if ..." to retired invents a ruling the
source does not contain. Each of those is a fixture here.
"""

from __future__ import annotations

import pytest

from app.domain.enums import ConceptKind, ConceptLibrary, ConceptStatus
from app.services.concept_loader import (
    ConceptLibraryError,
    parse_concept_library,
)
from tests.fixtures.concepts import VALID_LIBRARY, entry, library


def _parse(content: str):
    return parse_concept_library(content, source_path="docs/design/FIXTURE.md")


# --- The rules the module exists to hold ------------------------------------


def test_a_valid_library_parses_every_entry() -> None:
    loaded = _parse(VALID_LIBRARY)
    assert loaded.library is ConceptLibrary.TSHIRT
    assert [concept.external_number for concept in loaded.concepts] == list(range(1, 9))


def test_a_hard_retirement_is_read_from_the_title_and_cleaned() -> None:
    concept = _parse(VALID_LIBRARY).concepts[1]
    assert concept.retirement == "hard"
    assert concept.status is ConceptStatus.RETIRED
    assert concept.title == "SEND IT (technical treatment)"
    assert concept.title_raw == "RETIRED — SEND IT (technical treatment)"


def test_an_unconditional_retirement_is_read_from_the_body() -> None:
    concept = _parse(VALID_LIBRARY).concepts[2]
    assert concept.retirement == "unconditional"
    assert concept.status is ConceptStatus.RETIRED


def test_a_conditional_retirement_is_held_not_retired() -> None:
    """ "Retire ... if ..." is a decision not yet made. Retiring it would fabricate one."""
    concept = _parse(VALID_LIBRARY).concepts[4]
    assert concept.retirement == "conditional"
    assert concept.status is ConceptStatus.HELD
    assert concept.salvage.startswith("Retire as currently framed")


def test_retired_in_prose_does_not_retire_the_concept() -> None:
    """Entry 54 in the real library describes "retired blokes" and is live."""
    concept = _parse(VALID_LIBRARY).concepts[3]
    assert concept.retirement == ""
    assert concept.status is ConceptStatus.BACKLOG


# --- Garment prefixes -------------------------------------------------------


def test_a_garment_prefix_is_parsed_and_the_body_stays_verbatim() -> None:
    concept = _parse(VALID_LIBRARY).concepts[5]
    assert concept.garments == ("crop",)
    assert concept.garment_prefix == "Crop"
    assert concept.kind is ConceptKind.GARMENT_LED
    assert concept.concept_text.startswith("Crop. Clean tiny front type")


def test_a_compound_garment_prefix_lists_every_garment_in_order() -> None:
    concept = _parse(VALID_LIBRARY).concepts[6]
    assert concept.garments == ("crop", "tee", "crew", "hoodie")


def test_a_pair_prefix_is_one_garment() -> None:
    concept = _parse(VALID_LIBRARY).concepts[7]
    assert concept.garments == ("tee",)
    assert concept.garment_prefix == "Tee pair"


def test_an_entry_without_a_prefix_has_no_garments() -> None:
    concept = _parse(VALID_LIBRARY).concepts[0]
    assert concept.garments == ()
    assert concept.kind is ConceptKind.OTHER


# --- Rounds and slugs -------------------------------------------------------


def test_the_round_and_its_label_come_from_the_heading() -> None:
    loaded = _parse(VALID_LIBRARY)
    assert loaded.concepts[0].round == 1
    assert loaded.concepts[0].round_label == "Round 01"
    assert loaded.concepts[5].round == 2
    assert loaded.concepts[5].round_label == "Round 02 — garment-led"


def test_prose_sections_are_not_concepts() -> None:
    """Hard guardrails and Selection rule surround the rounds and produce nothing."""
    loaded = _parse(VALID_LIBRARY)
    assert len(loaded.concepts) == 8


def test_slugs_carry_the_number_so_repeated_titles_stay_unique() -> None:
    first = library(entry(1, "shirtfaced", "The word."), entry(2, "shirtfaced", "The word again."))
    slugs = [concept.slug for concept in _parse(first).concepts]
    assert slugs == ["001-shirtfaced", "002-shirtfaced"]


def test_a_slug_reduces_punctuation_to_hyphens() -> None:
    loaded = _parse(library(entry(1, "SHE'LL BE RIGHT", "The phrase.")))
    assert loaded.concepts[0].slug == "001-she-ll-be-right"


# --- Validation: everything reported together -------------------------------


def test_every_problem_is_reported_in_one_raise() -> None:
    content = library(
        "1. no bold title here",
        entry(3, "SKIPPED AHEAD", "Number two is missing."),
    )
    with pytest.raises(ConceptLibraryError) as excinfo:
        _parse(content)
    message = str(excinfo.value)
    assert "not a concept entry" in message
    assert "breaks the sequence" in message


def test_numbers_must_be_contiguous_from_one() -> None:
    with pytest.raises(ConceptLibraryError, match="breaks the sequence"):
        _parse(library(entry(2, "STARTS AT TWO", "The first number is missing.")))


def test_an_empty_document_is_a_fault_not_an_empty_import() -> None:
    with pytest.raises(ConceptLibraryError, match="no concept entries"):
        _parse("# Empty\n\n## Round 01\n")


def test_the_hash_is_over_decoded_text_so_line_endings_do_not_matter(tmp_path) -> None:
    """A CRLF checkout must not read as a content change. This matters on Windows."""
    from app.services.concept_loader import load_concept_library

    unix_file = tmp_path / "unix.md"
    unix_file.write_bytes(VALID_LIBRARY.encode("utf-8"))
    windows_file = tmp_path / "windows.md"
    windows_file.write_bytes(VALID_LIBRARY.replace("\n", "\r\n").encode("utf-8"))

    unix = load_concept_library(unix_file)
    windows = load_concept_library(windows_file)
    assert unix.document_hash == windows.document_hash
