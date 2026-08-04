"""ORM models.

Phase 0 introduces the ``World`` aggregate only. Shots, generation attempts, image
assets, reviews, decisions, canon proposals, usage records and audit events are added
by the phases that first need them, each with its own Alembic migration.
"""

from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import Enum, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

SHA256_HEX_LENGTH = 64


class WorldStatus(StrEnum):
    """Lifecycle of a world.

    Version 1 runs a single active world. ``archived`` exists so a finished world can
    be retained for its history without appearing as a production target.
    """

    ACTIVE = "active"
    ARCHIVED = "archived"


class World(Base, TimestampMixin):
    """A creative world backed by ``WORLD.md``, ``CONTINUITY.md`` and ``SHOTLIST.md``."""

    __tablename__ = "worlds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Relative to WORLDS_ROOT. Stored relative so the same database works on a
    # developer machine and on the Oracle host.
    directory_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[WorldStatus] = mapped_column(
        Enum(WorldStatus, name="world_status", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=WorldStatus.ACTIVE,
        server_default=WorldStatus.ACTIVE.value,
    )
    # SHA-256 of each canonical document as last loaded; null until the first load.
    world_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))
    continuity_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))
    shotlist_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<World slug={self.slug!r} status={self.status.value!r}>"
