"""ORM models for the visual pass over the design corpus.

Kept apart from the archive models because they describe a different thing.
Those store the parts a Shirtfaced design is assembled from; these store what
other people's shipped designs look like, read one frame at a time, so the
engine can arrange supplied elements the way brands repeatedly arrange theirs.

Two rules shape the schema.

**Measured and observed never share a column.** A measurement comes from code
and is reproducible; an observation comes from a model looking at a picture and
is not. Blending them means nobody can tell which figures survive a re-run, and
this corpus has already produced one statistic that looked solid and was
measuring a t-shirt silhouette rather than a design.

**A frame is described from the original file, never a crop of it.** An earlier
pass cropped to the print first and described the crop; the crop was sometimes a
hoodie placket or a wordmark sliced mid-letter, and those were described
confidently. It also discarded exactly what a photograph uniquely carries -- the
cut, the wash, the garment colour, and which zone the print sits in.

Placement is recorded by zone and fill, not by coordinates. Which zone a design
occupies and how much of it is filled is the answer the engine needs; exact
position is the compositor's business.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

# Zone names come from design_range.py's SCALE_ROLE table rather than a parallel
# vocabulary invented here, so a description joins onto the engine's own terms.
ZONES = (
    "full_front",
    "full_back",
    "centre_chest",
    "centre_back",
    "left_chest",
    "upper_back_yoke",
    "outer_back_neck",
    "inner_neck_label",
    "short_sleeve",
    "long_sleeve",
    "pocket",
    "cap_front",
    "cap_side",
    "cap_back",
)

# Two different facts, and an earlier version had them fighting over one column.
#
# The state is the Constitution's §5 decision about what the zone is *for*: a
# blank chest chosen deliberately and a neck label are both unprinted by the
# design, and they are not the same thing at all.
ZONE_STATES = ("active graphic zone", "permanent identity zone", "intentional negative space")

# The content is simply what is on it.
ZONE_CONTENT = ("bare", "image_only", "text_only", "image_and_text")

FILLS = ("trace", "quarter", "half", "most", "full", "bleeds")


class DesignObservation(Base, TimestampMixin):
    """One frame of one product, described from the original image."""

    __tablename__ = "design_observations"
    __table_args__ = (
        # A frame described twice by the same model replaces rather than
        # duplicates. Two different models may both describe it, and both rows
        # are kept, which is why the model is part of the key.
        UniqueConstraint("image_path", "described_by", name="uq_design_observations_image_model"),
        # Confidence is a promise about the row. A confident row has to say what
        # the design is; anything less honest belongs at medium or low.
        CheckConstraint(
            "confidence <> 'high' OR (subject_primary <> '' AND description <> '')",
            name="confident_rows_are_complete",
        ),
        CheckConstraint(
            "confidence IN ('high', 'medium', 'low')",
            name="confidence_known",
        ),
        Index("ix_design_observations_brand", "brand_slug"),
        Index("ix_design_observations_tradition", "tradition"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # --- identity, from collection -------------------------------------------
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    corpus: Mapped[str] = mapped_column(String(32), nullable=False)
    brand_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    product_slug: Mapped[str] = mapped_column(String(128), nullable=False)
    product_name: Mapped[str] = mapped_column(Text, default="")
    tradition: Mapped[str] = mapped_column(String(48), default="")
    category: Mapped[str] = mapped_column(String(48), default="")
    price: Mapped[str] = mapped_column(String(32), default="")
    source_url: Mapped[str] = mapped_column(Text, default="")

    # --- what the frame is ---------------------------------------------------
    presentation: Mapped[str] = mapped_column(String(32), default="")
    garment: Mapped[str] = mapped_column(Text, default="")
    garment_colour: Mapped[str] = mapped_column(String(64), default="")
    backdrop: Mapped[str] = mapped_column(String(64), default="")

    # --- the design ----------------------------------------------------------
    description: Mapped[str] = mapped_column(Text, default="")
    text_content: Mapped[str] = mapped_column(Text, default="")
    subject_primary: Mapped[str] = mapped_column(String(32), default="")
    subject_terms: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    depicts_people: Mapped[bool] = mapped_column(Boolean, default=False)
    references_property: Mapped[bool] = mapped_column(Boolean, default=False)
    property_name: Mapped[str] = mapped_column(Text, default="")

    # Constitution §8 graphic archetype and §6 layout archetype. `construction`
    # was an invented parallel vocabulary and is gone.
    graphic_archetype: Mapped[str] = mapped_column(String(48), default="")
    layout_archetype: Mapped[str] = mapped_column(String(16), default="")
    integration: Mapped[str] = mapped_column(String(32), default="")
    element_shapes: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)

    type_styles: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    type_case: Mapped[str] = mapped_column(String(16), default="")
    type_effects: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    type_lines: Mapped[int] = mapped_column(Integer, default=0)

    palette_terms: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    print_effect: Mapped[str] = mapped_column(String(32), default="")
    stroke: Mapped[str] = mapped_column(String(16), default="")
    detail_density: Mapped[str] = mapped_column(String(16), default="")

    # Zones with nothing on them. Recorded because a bare back is how a design
    # is known to be front-only, which is evidence and not an absence of it.
    bare_zones: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)

    # --- measured, filled by code and recomputable ---------------------------
    symmetry: Mapped[float | None] = mapped_column(Float, nullable=True)
    containment: Mapped[float | None] = mapped_column(Float, nullable=True)
    ink_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    aspect: Mapped[float | None] = mapped_column(Float, nullable=True)

    # --- provenance ----------------------------------------------------------
    described_by: Mapped[str] = mapped_column(String(64), nullable=False)
    described_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    confidence: Mapped[str] = mapped_column(String(8), default="medium")
    notes: Mapped[str] = mapped_column(Text, default="")
    raw: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    zones: Mapped[list[ObservationZone]] = relationship(
        back_populates="observation", cascade="all, delete-orphan"
    )


class ObservationZone(Base):
    """What sits on one zone of one garment, and how much of it is used.

    A separate table rather than a JSON blob because the whole point is querying
    across it: what fills a left chest on a fifty dollar skate tee, how often a
    full back carries more detail than the front. A design may use any number of
    zones, so this is one row per zone rather than a front and back column.
    """

    __tablename__ = "observation_zones"
    __table_args__ = (
        UniqueConstraint("observation_id", "zone", name="uq_observation_zones_zone"),
        CheckConstraint(
            "zone IN ('full_front','full_back','centre_chest','centre_back','left_chest',"
            "'upper_back_yoke','outer_back_neck','inner_neck_label','short_sleeve',"
            "'long_sleeve','pocket','cap_front','cap_side','cap_back')",
            name="zone_known",
        ),
        CheckConstraint(
            "state IN ('active graphic zone','permanent identity zone',"
            "'intentional negative space')",
            name="zone_state_known",
        ),
        CheckConstraint(
            "content IN ('bare','image_only','text_only','image_and_text')",
            name="zone_content_known",
        ),
        CheckConstraint(
            "scale_role = '' OR scale_role IN ('S0','S1','S2','S3','S4')",
            name="scale_role_known",
        ),
        CheckConstraint(
            "hierarchy = '' OR hierarchy IN ('H1','H2','H3')",
            name="hierarchy_known",
        ),
        CheckConstraint(
            "fill IN ('trace','quarter','half','most','full','bleeds')",
            name="zone_fill_known",
        ),
        Index("ix_observation_zones_zone", "zone"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    observation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_observations.id", ondelete="CASCADE"), nullable=False
    )
    zone: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(String(16), nullable=False)
    fill: Mapped[str] = mapped_column(String(16), nullable=False)
    scale_role: Mapped[str] = mapped_column(String(4), default="")
    hierarchy: Mapped[str] = mapped_column(String(4), default="")
    description: Mapped[str] = mapped_column(Text, default="")

    observation: Mapped[DesignObservation] = relationship(back_populates="zones")
