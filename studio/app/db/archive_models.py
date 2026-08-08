"""ORM models for the element archive.

Kept apart from ``models.py`` because they belong to a different thing. Those
tables describe worlds, shots and the photographs made from them; these describe
the parts a design is assembled from and the rules for using them.

The archive's premise is that geometry is stored apart from aesthetics and that
finished artwork is a disposable output. An authored element stores a recipe
name and its parameters; an ingested one stores path data and a licence trail; a
render stores the tuple that produced it, so the artwork can be thrown away and
rebuilt.

``ComposedDesign`` follows the same rule and is the reason this file now stores
something that looks like a design. It keeps the *brief* -- seed, garment,
placement, words, palette -- because that is what regenerates the artwork. The
SVG alongside it is a convenience, not the record. Until this existed the
composer could only be run from a Python prompt: nothing could be stored, so
nothing could reach ``awaiting_decision``, so nothing could be approved.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.models import SHA256_HEX_LENGTH, _enum
from app.domain.enums import AttemptState, ElementFamily, LicenceStatus

__all__ = [
    "ELEMENT_FEATURE_DIMENSIONS",
    "ArchiveElement",
    "ComposedDesign",
    "ElementRender",
]

# Width of an element's feature vector. Deliberately small and deliberately
# hand-derived: every component is computed from a declared parameter, so a
# similarity result can be explained by pointing at the field that caused it.
# A learned embedding would be neither reproducible across runs nor auditable,
# and this archive's premise is that its outputs can always be regenerated.
ELEMENT_FEATURE_DIMENSIONS = 32

EMPTY_ARRAY = text("'{}'::varchar[]")


class ArchiveElement(Base, TimestampMixin):
    """One part in the archive: geometry plus the rules for using it."""

    __tablename__ = "archive_elements"
    __table_args__ = (
        UniqueConstraint("element_key", name="uq_archive_elements_element_key"),
        # The licence gate lives in the database, not only in Python. An element
        # marked verified must carry what verification means: terms, a source, a
        # date, and permission for commercial use. This is not a duplicated
        # validation -- it is the one that survives a bulk import written in a
        # hurry, and these elements go on garments that are sold.
        CheckConstraint(
            "licence_status <> 'verified' OR ("
            " licence_commercial_use"
            " AND licence_terms <> ''"
            " AND licence_source <> ''"
            " AND licence_checked_at IS NOT NULL)",
            name="verified_licence_complete",
        ),
        CheckConstraint(
            "ink_min >= 1 AND ink_max >= ink_min",
            name="inks",
        ),
        CheckConstraint(
            "complexity >= 0 AND complexity <= 1",
            name="complexity",
        ),
        # An element may be authored from a recipe or carry its own geometry,
        # but not both -- that would be ambiguous about which one draws it.
        #
        # Neither is allowed. A raster arrives with no vector geometry and is
        # still worth holding; the earlier version refused it, which made the
        # sourcing list's invitation to send a photograph untrue.
        CheckConstraint(
            "NOT (recipe <> '' AND geometry <> '')",
            name="recipe_or_geometry_not_both",
        ),
        Index("ix_archive_elements_family", "family"),
        # Partial index over what the composer actually queries. It never looks
        # at anything but verified elements, so the index need not either.
        Index(
            "ix_archive_elements_usable",
            "family",
            "subtype",
            postgresql_where=text("licence_status = 'verified'"),
        ),
        # HNSW over cosine distance. Cosine because the feature vector mixes
        # counts and shares, so direction carries the meaning while magnitude
        # mostly carries how many components happened to be populated.
        Index(
            "ix_archive_elements_feature",
            "feature",
            postgresql_using="hnsw",
            postgresql_ops={"feature": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    # Stable human-readable identity, e.g. "badge_shield_0142". Renders refer to
    # it, so it must not change once anything has been produced from it.
    element_key: Mapped[str] = mapped_column(String(120), nullable=False)
    family: Mapped[ElementFamily] = mapped_column(
        _enum(ElementFamily, "element_family"), nullable=False
    )
    subtype: Mapped[str] = mapped_column(String(80), nullable=False, default="")

    # Authored elements name a recipe and supply parameters; ingested elements
    # carry path data. Never a rendered picture, in either case.
    recipe: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    geometry: Mapped[str] = mapped_column(Text, nullable=False, default="")
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Where supplied content goes. An element with no slots can be placed but
    # never filled, which is the difference between a recipe and a picture.
    slots: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)

    symmetry: Mapped[str] = mapped_column(String(24), nullable=False, default="none")
    ink_min: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    ink_max: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    complexity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    style_tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(40)), nullable=False, server_default=EMPTY_ARRAY
    )
    compatible_treatments: Mapped[list[str]] = mapped_column(
        ARRAY(String(40)), nullable=False, server_default=EMPTY_ARRAY
    )
    # What the element refuses. Cheaper and more honest than enumerating what it
    # permits, and it is what makes the grammar tractable.
    exclusions: Mapped[list[str]] = mapped_column(
        ARRAY(String(40)), nullable=False, server_default=EMPTY_ARRAY
    )

    # --- Licence, as a recorded fact with a source rather than a flag. ---
    licence_status: Mapped[LicenceStatus] = mapped_column(
        _enum(LicenceStatus, "licence_status"),
        nullable=False,
        server_default=text("'unverified'"),
    )
    licence_terms: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    licence_source: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    licence_source_id: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    licence_source_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    licence_checked_at: Mapped[dt.date | None] = mapped_column(Date)
    licence_commercial_use: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    # For the awkward majority of the hard cases: an out-of-copyright work whose
    # scan carries its own claim, or terms that differ between the jurisdictions
    # the brand sells into.
    licence_note: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Similarity is computed in the database rather than by pulling the archive
    # into Python, so "find me elements like this one" stays one query as the
    # archive grows past a few thousand parts. Null until the vector is built,
    # which keeps ingestion and feature derivation independently runnable.
    feature: Mapped[list[float] | None] = mapped_column(Vector(ELEMENT_FEATURE_DIMENSIONS))

    @property
    def licence_usable(self) -> bool:
        """Whether the composer may reach this element at all.

        Mirrors the database constraint deliberately. The constraint is what
        holds under bulk import; this is what lets a caller ask without a round
        trip. They must agree, and the test suite asserts that they do.
        """
        return (
            self.licence_status is LicenceStatus.VERIFIED
            and self.licence_commercial_use
            and bool(self.licence_terms)
            and bool(self.licence_source)
            and self.licence_checked_at is not None
        )


class ElementRender(Base):
    """A rendered output, stored as the tuple that produced it.

    The artwork is disposable; this row is not. Given the same element, content,
    palette and seed the renderer must emit the same bytes, so the hash here is
    both a cache key and a standing assertion that determinism holds. A mismatch
    on re-render is a regression, and it should be found by a test rather than
    by a reprint that does not match the original.
    """

    __tablename__ = "element_renders"
    __table_args__ = (
        UniqueConstraint("element_id", "content_hash", name="uq_element_renders_element_content"),
        Index("ix_element_renders_element_id", "element_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    element_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("archive_elements.id", ondelete="CASCADE"),
        nullable=False,
    )
    # The inputs, kept whole, so the output can be reproduced from this row alone.
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    palette: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    # sha256 of the emitted SVG. Determinism is asserted against this.
    content_hash: Mapped[str] = mapped_column(String(SHA256_HEX_LENGTH), nullable=False)
    svg: Mapped[str] = mapped_column(Text, nullable=False)
    # Which renderer produced it. A renderer change that alters output is
    # legitimate; silently attributing new output to an old row is not.
    renderer_version: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ComposedDesign(Base, TimestampMixin):
    """One design the composer produced, and everything needed to rebuild it.

    A stored design is not an approved design. It arrives at
    ``awaiting_decision`` and stays there until a person settles it, which is
    the same rule the photography pipeline follows and the reason that state
    exists in the data rather than only in someone's head.

    The brief columns are the record. Given the same seed, garment, placement,
    words and palette the composer must produce the same bytes, so
    ``content_hash`` is both a cache key and a standing assertion that
    determinism survives a restart -- not merely that it holds within one
    process, which is all an in-memory test can show.
    """

    __tablename__ = "composed_designs"
    __table_args__ = (
        # The same brief composed twice is the same design. Re-running a seed
        # should find the existing row rather than fill the table with
        # duplicates that a reviewer then has to tell apart.
        UniqueConstraint("content_hash", name="uq_composed_designs_content_hash"),
        Index("ix_composed_designs_state", "state"),
        # Partial: the review queue only ever asks for the undecided ones, and
        # that set stays small while the decided set grows without bound.
        Index(
            "ix_composed_designs_awaiting",
            "created_at",
            postgresql_where=text("state = 'awaiting_decision'"),
        ),
        CheckConstraint("seed >= 0", name="seed_not_negative"),
        # A design that has been settled must say who settled it. Without this
        # an approval is an assertion nobody signed.
        CheckConstraint(
            "state NOT IN ('approved', 'rejected') OR decided_by <> ''",
            name="decision_has_an_author",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # --- The brief: everything the composer was given. -----------------------
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    garment_key: Mapped[str] = mapped_column(String(80), nullable=False)
    placement_key: Mapped[str] = mapped_column(String(40), nullable=False)
    fit: Mapped[str] = mapped_column(String(20), nullable=False, server_default="adult")
    # The owner's words. Never invented here, and never edited: the engine
    # decides how supplied text is set, not what it says.
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    palette: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    treatment: Mapped[str] = mapped_column(String(20), nullable=False, server_default="clean")

    # --- What came back. -----------------------------------------------------
    grammar_key: Mapped[str] = mapped_column(String(40), nullable=False)
    # role -> element key. Which parts of the archive this design is made of,
    # so an element can be traced to everything it appears in.
    parts: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    width_mm: Mapped[float] = mapped_column(Float, nullable=False)
    height_mm: Mapped[float] = mapped_column(Float, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(SHA256_HEX_LENGTH), nullable=False)
    svg: Mapped[str] = mapped_column(Text, nullable=False)
    # Which assembler produced it. Attributing new output to an old row is how a
    # reprint quietly stops matching the sample that was approved.
    assembler_version: Mapped[str] = mapped_column(String(40), nullable=False)

    # --- The decision. -------------------------------------------------------
    state: Mapped[str] = mapped_column(
        _enum(AttemptState, "attempt_state"),
        nullable=False,
        server_default=AttemptState.AWAITING_DECISION.value,
    )
    decided_by: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    decided_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    decision_note: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
