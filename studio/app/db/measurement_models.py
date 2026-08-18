"""ORM model for machine measurements over the design corpus.

The other half of ``observation_models.py``'s rule: **measured and observed
never share a column**. A ``DesignObservation`` is a model looking at a
picture and is not reproducible; a ``DesignMeasurement`` is code reading the
same frame and is -- same corpus in, same numbers out. They share an identity
vocabulary (``corpus``, ``brand_slug``, ``product_slug``, ``image_path``) so
the two can be joined, and nothing else.

These rows are what the design advisor and the scoring thresholds learn from.
They used to be JSON files under ``var/design_corpus/`` that existed only on
whichever machine last ran a mining script -- which for the advisor's whole
life was no machine at all. A table cannot be absent from the box, and an
empty one is loudly visible; see ``DESIGN_SYSTEM_AUDIT_2026-08-18.md``.

A refused frame is a row too, with ``refusal_reason`` set and the measured
columns null. Refusals are evidence about the corpus -- worn full-body
photography the analyser will not guess at -- and dropping them would make
"measured 60% of the corpus" indistinguishable from "measured all of it".
"""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DesignMeasurement(Base):
    """One frame of the corpus, measured by code."""

    __tablename__ = "design_measurements"
    __table_args__ = (
        # One measurement per frame. A re-run replaces, never accumulates --
        # the analyser is deterministic, so two rows for one frame could only
        # mean two analyser versions, and that is what analyser_version is for.
        UniqueConstraint(
            "corpus", "brand_slug", "product_slug", "image_path",
            name="uq_design_measurements_frame",
        ),
        # The advisor and the thresholds both slice by tradition before they
        # take a median; this is the read path.
        Index("ix_design_measurements_tradition", "tradition"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # --- Identity: observation_models.py's vocabulary, so the two join. ------
    corpus: Mapped[str] = mapped_column(String(32), nullable=False)
    brand_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    product_slug: Mapped[str] = mapped_column(String(128), nullable=False)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    product_name: Mapped[str] = mapped_column(Text, default="", server_default="")
    tradition: Mapped[str] = mapped_column(String(48), default="", server_default="")

    # --- What the analyser said. ---------------------------------------------
    # Null measurements with a reason, or measurements with no reason. Never both.
    refusal_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    print_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    ink_colours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    placement_band: Mapped[str | None] = mapped_column(String(16), nullable=True)
    light_on_dark: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # How many words the product's name carries -- the advisor buckets by this.
    phrase_words: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Provenance. ---------------------------------------------------------
    analyser_version: Mapped[str] = mapped_column(String(64), nullable=False)
    measured_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
