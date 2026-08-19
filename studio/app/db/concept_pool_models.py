"""ORM model for batch-generated design concepts.

The gap this closes: ``render_generation_prompt()`` can only phrase what
``advise()`` already decided from corpus statistics -- coverage, ink count,
placement, and (since the structure fix) the real measured composition shape
for a tradition. None of that is a *design idea*. Given the same idea twice
it produces the same prompt twice, because it has no idea of its own to
contribute -- by design, per ``design_advisor.py``'s own docstring.

This table holds ideas, written once in a batch (a Claude Code session, not
a live per-request API call -- see the batch generation script under
``scripts/``) and served randomly per tradition at zero request-time cost.
Hit and miss by nature: a person is not curating each row, so ``active``
exists to retire ones that read badly without deleting the audit trail.
"""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import Boolean, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DesignConceptPoolEntry(Base):
    """One batch-written design idea, for one tradition."""

    __tablename__ = "design_concept_pool"
    __table_args__ = (
        Index("ix_design_concept_pool_tradition_active", "tradition", "active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tradition: Mapped[str] = mapped_column(String(48), nullable=False)
    concept_text: Mapped[str] = mapped_column(Text, nullable=False)
    structural_shape: Mapped[str | None] = mapped_column(String(96), nullable=True)
    batch: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
