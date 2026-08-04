"""ORM models.

``World`` and ``Shot`` are present. Generation attempts, image assets, reviews,
decisions, canon proposals, usage records and audit events are added by the phases
that first need them, each with its own Alembic migration.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.domain.enums import ShotStatus, WorldStatus

__all__ = ["SHA256_HEX_LENGTH", "Shot", "ShotStatus", "World", "WorldStatus"]

SHA256_HEX_LENGTH = 64


def _enum(enum_type: type[WorldStatus] | type[ShotStatus], name: str) -> Enum:
    """A native PostgreSQL enum storing the member values, not their Python names."""
    return Enum(enum_type, name=name, values_callable=lambda e: [member.value for member in e])


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
        _enum(WorldStatus, "world_status"),
        nullable=False,
        default=WorldStatus.ACTIVE,
        server_default=WorldStatus.ACTIVE.value,
    )
    # SHA-256 of each canonical document as last loaded; null until the first load.
    world_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))
    continuity_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))
    shotlist_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))

    shots: Mapped[list[Shot]] = relationship(
        back_populates="world",
        cascade="all, delete-orphan",
        order_by="Shot.sequence",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<World slug={self.slug!r} status={self.status.value!r}>"


class Shot(Base, TimestampMixin):
    """One planned photograph, imported from ``SHOTLIST.md``."""

    __tablename__ = "shots"
    __table_args__ = (
        UniqueConstraint("world_id", "external_id", name="uq_shots_world_id_external_id"),
        # Supports the deterministic selector: eligible shots for a world, in
        # priority then sequence order.
        Index(
            "ix_shots_world_id_status_priority_sequence",
            "world_id",
            "status",
            "priority",
            "sequence",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
    )
    # The human-facing identifier from the shotlist, such as W01-011.
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("100"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    hero_product: Mapped[str | None] = mapped_column(String(120))
    camera_position: Mapped[str | None] = mapped_column(String(120))
    lighting_source: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[ShotStatus] = mapped_column(
        _enum(ShotStatus, "shot_status"),
        nullable=False,
        default=ShotStatus.PLANNED,
        server_default=ShotStatus.PLANNED.value,
    )
    disabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    # Line in SHOTLIST.md this shot came from, so a problem can be pointed at.
    source_line: Mapped[int | None] = mapped_column(Integer)

    world: Mapped[World] = relationship(back_populates="shots")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Shot {self.external_id!r} status={self.status.value!r}>"
