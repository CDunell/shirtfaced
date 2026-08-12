"""Importing concept libraries into PostgreSQL.

The rules under test are the ones that keep the backlog honest: numbers are
permanent, re-import is idempotent, wording follows the Markdown, statuses the
workflow set are kept, and every disagreement is reported with both sides
named rather than silently resolved.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.concept_models import DesignConcept
from app.domain.enums import ConceptLibrary, ConceptStatus
from app.services.concept_importer import import_concepts
from app.services.concept_loader import parse_concept_library
from tests.fixtures.concepts import VALID_LIBRARY, entry, library

pytestmark = pytest.mark.integration

SOURCE = "docs/design/FIXTURE.md"


def _load(content: str = VALID_LIBRARY):
    return parse_concept_library(content, source_path=SOURCE)


def _concepts(session: Session) -> dict[int, DesignConcept]:
    rows = (
        session.execute(select(DesignConcept).where(DesignConcept.library == ConceptLibrary.TSHIRT))
        .scalars()
        .all()
    )
    return {concept.external_number: concept for concept in rows}


def test_the_first_import_creates_every_concept(session: Session) -> None:
    report = import_concepts(session, _load())

    assert report.created == 8
    assert report.updated == 0
    assert report.document_changed is False

    concepts = _concepts(session)
    assert len(concepts) == 8
    assert concepts[1].slug == "001-absolute-weapon"
    assert concepts[2].status is ConceptStatus.RETIRED
    assert concepts[3].status is ConceptStatus.RETIRED
    assert concepts[5].status is ConceptStatus.HELD
    assert concepts[5].parsed_json["salvage"].startswith("Retire as currently framed")
    assert concepts[6].garments == ["crop"]


def test_import_is_idempotent(session: Session) -> None:
    import_concepts(session, _load())
    session.flush()

    second = import_concepts(session, _load())

    assert second.created == 0
    assert second.updated == 0
    assert second.unchanged == 8
    assert second.document_changed is False
    assert len(_concepts(session)) == 8


def test_edited_wording_updates_the_row_and_reports_the_document_change(
    session: Session,
) -> None:
    import_concepts(session, _load())
    session.flush()

    edited = VALID_LIBRARY.replace("a pedestal fan", "an oscillating pedestal fan")
    report = import_concepts(session, _load(edited))

    assert report.updated == 1
    assert report.unchanged == 7
    assert report.document_changed is True
    assert "oscillating" in _concepts(session)[1].concept_text


def test_a_new_retirement_applies_to_an_untouched_concept(session: Session) -> None:
    """The workflow never moved #1, so the source's decision lands."""
    import_concepts(session, _load())
    session.flush()

    edited = VALID_LIBRARY.replace("1. **ABSOLUTE WEAPON** —", "1. **ABSOLUTE WEAPON** — Retired.")
    report = import_concepts(session, _load(edited))

    assert report.status_conflicts == []
    concept = _concepts(session)[1]
    assert concept.status is ConceptStatus.RETIRED
    assert concept.retirement == "unconditional"


def test_a_workflow_owned_status_is_kept_and_the_conflict_named(session: Session) -> None:
    import_concepts(session, _load())
    session.flush()

    _concepts(session)[1].status = ConceptStatus.APPROVED
    session.flush()

    edited = VALID_LIBRARY.replace("1. **ABSOLUTE WEAPON** —", "1. **ABSOLUTE WEAPON** — Retired.")
    report = import_concepts(session, _load(edited))

    concept = _concepts(session)[1]
    assert concept.status is ConceptStatus.APPROVED
    # The authored fact still lands even though the status was kept.
    assert concept.retirement == "unconditional"
    assert report.status_conflicts == [
        "concept 1: the database says approved, the library now says retired. "
        "The database was kept."
    ]


def test_workflow_progress_past_an_unchanged_entry_is_not_a_conflict(
    session: Session,
) -> None:
    """A concept being explored still reads as backlog in the source. Normal work."""
    import_concepts(session, _load())
    session.flush()

    _concepts(session)[1].status = ConceptStatus.EXPLORING
    session.flush()

    report = import_concepts(session, _load())

    assert report.status_conflicts == []
    assert _concepts(session)[1].status is ConceptStatus.EXPLORING


def test_a_ready_concept_is_not_demoted_by_reimport(session: Session) -> None:
    """READY is the owner queueing work. The importer must not undo it."""
    import_concepts(session, _load())
    session.flush()

    _concepts(session)[4].status = ConceptStatus.READY
    session.flush()

    report = import_concepts(session, _load())

    assert report.status_conflicts == []
    assert _concepts(session)[4].status is ConceptStatus.READY


def test_a_number_missing_from_the_source_is_reported_and_kept(session: Session) -> None:
    import_concepts(session, _load())
    session.flush()

    shorter = library(
        entry(1, "ABSOLUTE WEAPON", "Museum-quality portrait treatment of a pedestal fan."),
    )
    report = import_concepts(session, _load(shorter))

    assert len(report.missing_from_source) == 7
    assert report.missing_from_source[0].startswith("concept 2 is in the database")
    assert len(_concepts(session)) == 8


def test_workflow_fields_survive_reimport(session: Session) -> None:
    """priority, tags and notes belong to the owner; the importer never touches them."""
    import_concepts(session, _load())
    session.flush()

    concept = _concepts(session)[1]
    concept.priority = -5
    concept.tags = ["favourite"]
    concept.notes = "Do this one first."
    session.flush()

    import_concepts(session, _load())

    concept = _concepts(session)[1]
    assert concept.priority == -5
    assert concept.tags == ["favourite"]
    assert concept.notes == "Do this one first."
