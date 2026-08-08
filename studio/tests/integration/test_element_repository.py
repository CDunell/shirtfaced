"""The archive in Postgres: record integrity, and similarity as a query.

Two things can only be tested against a real database.

A check constraint keeps the provenance record honest -- an element marked
verified must actually carry terms, a source and a date, so "verified" cannot
mean "somebody ticked a box". It constrains what the record may claim; it does
not stop anything being designed with. Rights are reviewed once, before
release.

And similarity runs as a pgvector query, so "does it return sensible
neighbours" is a question about SQL rather than about a list comprehension.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.archive import authored
from app.archive.repository import ElementRepository, verified_licence
from app.domain.element import Licence
from app.domain.enums import ElementFamily, LicenceStatus

pytestmark = pytest.mark.integration


def test_syncing_the_authored_archive_stores_every_element(session: Session) -> None:
    repository = ElementRepository(session)
    result = repository.sync(authored.ALL)
    assert result.total == len(authored.ALL)
    assert len(result.added) == len(authored.ALL)
    assert len(repository.usable()) == len(authored.ALL)


def test_syncing_twice_changes_nothing(session: Session) -> None:
    """A sync that reports work it did not do makes the report useless."""
    repository = ElementRepository(session)
    repository.sync(authored.ALL)
    again = repository.sync(authored.ALL)
    assert again.added == []
    assert again.updated == []
    assert len(again.unchanged) == len(authored.ALL)


def test_an_edited_element_reports_as_updated(session: Session) -> None:
    repository = ElementRepository(session)
    repository.sync(authored.ALL)
    changed = replace(authored.element("frame_rect_0001"), complexity=0.99)
    assert repository.upsert(changed) == "updated"


def test_a_stored_element_round_trips(session: Session) -> None:
    repository = ElementRepository(session)
    repository.sync(authored.ALL)
    original = authored.element("badge_shield_0001")
    loaded = repository.get("badge_shield_0001")
    assert loaded is not None
    assert loaded.id == original.id
    assert loaded.subtype == original.subtype
    assert loaded.recipe == original.recipe
    assert loaded.complexity == pytest.approx(original.complexity)
    assert [slot.name for slot in loaded.slots] == [slot.name for slot in original.slots]
    assert loaded.licence.usable


def test_a_round_tripped_element_still_renders_identically(session: Session) -> None:
    """Storage must not change the artwork, or the archive is not reproducible."""
    from app.archive.render import Palette, render

    repository = ElementRepository(session)
    repository.sync(authored.ALL)
    content = {"primary_text": "SHIRTFACED", "secondary_text": "EST 2026"}
    palette = Palette(inks=("#C6FF00", "#F2F0EA"))

    for element in authored.ALL:
        stored = repository.get(element.id)
        assert stored is not None
        direct = render(element, content, palette, seed=8374)
        from_database = render(stored, content, palette, seed=8374)
        assert direct.content_hash == from_database.content_hash, element.id


# --- Record integrity, enforced by the database ------------------------------


def test_the_database_refuses_a_verified_licence_with_no_source(session: Session) -> None:
    """The constraint is what survives an import nobody reviewed."""
    repository = ElementRepository(session)
    element = replace(
        authored.element("frame_rect_0001"),
        licence=Licence(
            status=LicenceStatus.VERIFIED,
            terms="CC0",
            source="",
            checked_at=date(2026, 8, 8),
            commercial_use=True,
        ),
    )
    repository.upsert(element)
    with pytest.raises(IntegrityError):
        session.flush()


def test_the_database_refuses_a_verified_licence_with_no_date(session: Session) -> None:
    repository = ElementRepository(session)
    element = replace(
        authored.element("frame_rect_0001"),
        licence=Licence(
            status=LicenceStatus.VERIFIED,
            terms="CC0",
            source="smithsonian",
            checked_at=None,
            commercial_use=True,
        ),
    )
    repository.upsert(element)
    with pytest.raises(IntegrityError):
        session.flush()


def test_an_element_whose_terms_are_unknown_is_still_reachable(session: Session) -> None:
    """Unknown terms are a worklist item for the release review, not a block.
    Designing with something and selling it are different acts."""
    repository = ElementRepository(session)
    element = replace(
        authored.element("frame_rect_0001"),
        id="ingested_unchecked_0001",
        licence=Licence(status=LicenceStatus.UNVERIFIED, source="internet-archive"),
    )
    repository.upsert(element)
    session.flush()

    assert "ingested_unchecked_0001" in {found.id for found in repository.usable()}
    assert ("ingested_unchecked_0001", "internet-archive", "unverified") in repository.unverified()


def test_terms_that_forbid_sale_are_recorded_against_the_element(session: Session) -> None:
    """Recorded so the pre-release review reads it off a line instead of
    working it out again. The element stays available to design with."""
    repository = ElementRepository(session)
    element = replace(
        authored.element("frame_rect_0001"),
        id="ingested_refused_0001",
        licence=Licence(
            status=LicenceStatus.REFUSED,
            terms="CC BY-NC",
            source="internet-archive",
            note="Non-commercial only. Flag before release.",
        ),
    )
    repository.upsert(element)
    session.flush()

    stored = repository.get("ingested_refused_0001")
    assert stored is not None
    assert stored.licence.terms == "CC BY-NC"
    assert "Flag before release" in stored.licence.note


def test_the_licence_audit_is_one_query(session: Session) -> None:
    repository = ElementRepository(session)
    repository.sync(authored.ALL)
    repository.upsert(
        replace(
            authored.element("frame_rect_0001"),
            id="ingested_pending_0001",
            licence=Licence(status=LicenceStatus.UNVERIFIED, source="smithsonian"),
        )
    )
    session.flush()
    audit = repository.licence_audit()
    assert audit["verified"] == len(authored.ALL)
    assert audit["unverified"] == 1
    # The audit is the release review's worklist, not a gate: everything in it
    # is reachable by the composer regardless of status.
    assert len(repository.usable()) == len(authored.ALL) + 1


def test_the_helper_builds_a_complete_provenance_record(session: Session) -> None:
    repository = ElementRepository(session)
    element = replace(
        authored.element("symbol_star_0001"),
        id="ingested_star_0001",
        licence=verified_licence(
            terms="CC0",
            source="smithsonian",
            source_id="SI-1234",
            source_url="https://example.invalid/SI-1234",
            checked_at=date(2026, 8, 8),
        ),
    )
    repository.upsert(element)
    session.flush()
    assert "ingested_star_0001" in {found.id for found in repository.usable()}


# --- Similarity, computed by pgvector ---------------------------------------


def test_similarity_returns_neighbours_from_the_same_family(session: Session) -> None:
    repository = ElementRepository(session)
    repository.sync(authored.ALL)
    session.flush()

    neighbours = repository.similar_to("symbol_star_0001", limit=4)
    assert neighbours
    keys = [element.id for element, _ in neighbours]
    assert "symbol_star_0001" not in keys, "an element is always its own neighbour"
    assert any(key.startswith("symbol_") for key in keys)


def test_neighbours_come_back_nearest_first(session: Session) -> None:
    repository = ElementRepository(session)
    repository.sync(authored.ALL)
    session.flush()
    distances = [distance for _, distance in repository.similar_to("badge_shield_0001", limit=6)]
    assert distances == sorted(distances)


def test_similarity_searches_the_whole_archive(session: Session) -> None:
    """Neighbours are for finding what else is like this. Hiding an element
    because nobody has looked up its terms hides it from the search that would
    have found it useful."""
    repository = ElementRepository(session)
    repository.sync(authored.ALL)
    repository.upsert(
        replace(
            authored.element("symbol_star_0001"),
            id="ingested_unchecked_star",
            licence=Licence(status=LicenceStatus.UNVERIFIED, source="somewhere"),
        )
    )
    session.flush()
    keys = {element.id for element, _ in repository.similar_to("symbol_star_0002", limit=25)}
    assert "ingested_unchecked_star" in keys


def test_the_vector_index_exists_and_is_hnsw(session: Session) -> None:
    """Sequential similarity is fine at 25 elements and not at 3,000."""
    definition = session.execute(
        text("SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_archive_elements_feature'")
    ).scalar()
    assert definition is not None
    assert "hnsw" in definition.lower()


def test_every_stored_element_carries_a_feature_vector(session: Session) -> None:
    repository = ElementRepository(session)
    repository.sync(authored.ALL)
    session.flush()
    missing = session.execute(
        text("SELECT count(*) FROM archive_elements WHERE feature IS NULL")
    ).scalar()
    assert missing == 0


def test_family_is_derived_from_the_recipe(session: Session) -> None:
    """A row whose family and recipe disagree returns nonsense and nothing checks it."""
    repository = ElementRepository(session)
    repository.sync(authored.ALL)
    session.flush()
    badges = repository.usable(family=ElementFamily.SYMBOL)
    assert badges
    assert all(element.recipe.startswith("symbol.") for element in badges)
