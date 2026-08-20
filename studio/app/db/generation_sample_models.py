"""ORM model for tested concept-pool renders.

``design_concept_pool`` holds ideas; this holds proof one was actually
rendered -- the image and the exact prompt that produced it -- so a batch's
real output survives past the scratch files a session wrote it to. Every
future batch-eval run should insert here directly instead of leaving the
record in a local manifest.json nobody else can see.
"""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DesignGenerationSample(Base):
    """One rendered test image for one batch-pool concept, kept or dropped."""

    __tablename__ = "design_generation_samples"
    __table_args__ = (
        Index("ix_design_generation_samples_batch", "batch"),
        Index("ix_design_generation_samples_tradition_status", "tradition", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    concept_pool_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    tradition: Mapped[str] = mapped_column(String(48), nullable=False)
    concept_text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    image_relative_path: Mapped[str] = mapped_column(String(512), nullable=False)
    thumb_relative_path: Mapped[str] = mapped_column(String(512), nullable=False)
    # "kept" | "dropped" -- a plain string, not an enum, so a new status never
    # needs a migration to introduce.
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    drop_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    batch: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
