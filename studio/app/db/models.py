"""ORM models.

``World`` and ``Shot`` are present. Generation attempts, image assets, reviews,
decisions, canon proposals, usage records and audit events are added by the phases
that first need them, each with its own Alembic migration.
"""

from __future__ import annotations

import datetime as dt
import uuid
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.domain.enums import (
    ACTIVE_ATTEMPT_STATES,
    AssetKind,
    AttemptState,
    FailureCode,
    ShotStatus,
    WorldStatus,
)

__all__ = [
    "SHA256_HEX_LENGTH",
    "AssetKind",
    "AttemptState",
    "GenerationAttempt",
    "ImageAsset",
    "Shot",
    "ShotStatus",
    "World",
    "WorldStatus",
]

SHA256_HEX_LENGTH = 64


def _enum(enum_type: type[StrEnum], name: str) -> Enum:
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
    attempts: Mapped[list[GenerationAttempt]] = relationship(
        back_populates="shot",
        cascade="all, delete-orphan",
        order_by="GenerationAttempt.attempt_number",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Shot {self.external_id!r} status={self.status.value!r}>"


class GenerationAttempt(Base, TimestampMixin):
    """One attempt to produce an image for a shot.

    Everything needed to explain the result is recorded here: the exact prompt, the
    model settings, the shot metadata as it stood, and the hashes of the three
    canonical documents. A generated image must be traceable to its prompt, its model
    settings and the source world version, and the documents can be edited afterwards.
    """

    __tablename__ = "generation_attempts"
    __table_args__ = (
        UniqueConstraint(
            "shot_id", "attempt_number", name="uq_generation_attempts_shot_id_attempt_number"
        ),
        Index("ix_generation_attempts_world_id_created_at", "world_id", text("created_at DESC")),
        # One active attempt per world. Enforced by the database, not by a process
        # lock, because production restarts and may later run more than one worker.
        Index(
            "uq_generation_attempts_one_active_per_world",
            "world_id",
            unique=True,
            postgresql_where=text(
                "state IN ("
                + ", ".join(f"'{state.value}'" for state in sorted(ACTIVE_ATTEMPT_STATES))
                + ")"
            ),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False
    )
    shot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shots.id", ondelete="CASCADE"), nullable=False
    )
    # Set when this attempt retries or varies an earlier one, so the chain is intact.
    parent_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_attempts.id", ondelete="SET NULL")
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[AttemptState] = mapped_column(
        _enum(AttemptState, "attempt_state"),
        nullable=False,
        default=AttemptState.PLANNED,
        server_default=AttemptState.PLANNED.value,
    )

    selection_reason: Mapped[str | None] = mapped_column(Text)
    production_prompt: Mapped[str | None] = mapped_column(Text)
    prompt_plan_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    image_model: Mapped[str | None] = mapped_column(String(120))
    image_size: Mapped[str | None] = mapped_column(String(32))
    image_quality: Mapped[str | None] = mapped_column(String(32))
    image_format: Mapped[str | None] = mapped_column(String(16))
    # Logged for provider support. Never a key, never a payload.
    provider_request_id: Mapped[str | None] = mapped_column(String(120))

    # The shot as it stood when this attempt ran; the shotlist can change afterwards.
    hero_product: Mapped[str | None] = mapped_column(String(120))
    camera_position: Mapped[str | None] = mapped_column(String(120))
    world_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))
    continuity_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))
    shotlist_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))

    failure_code: Mapped[FailureCode | None] = mapped_column(_enum(FailureCode, "failure_code"))
    failure_message: Mapped[str | None] = mapped_column(Text)

    world: Mapped[World] = relationship()
    shot: Mapped[Shot] = relationship(back_populates="attempts")
    assets: Mapped[list[ImageAsset]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )

    @property
    def is_active(self) -> bool:
        return self.state in ACTIVE_ATTEMPT_STATES

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<GenerationAttempt {self.attempt_number} state={self.state.value!r}>"


class ImageAsset(Base):
    """A stored image file belonging to an attempt.

    The database holds metadata and a stable object key. Bytes live in the asset
    store, so the same rows work against a mounted volume today and object storage
    later.
    """

    __tablename__ = "image_assets"
    __table_args__ = (
        UniqueConstraint("attempt_id", "kind", name="uq_image_assets_attempt_id_kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("generation_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[AssetKind] = mapped_column(_enum(AssetKind, "asset_kind"), nullable=False)
    # Relative to ASSETS_ROOT, so the same row works on any host.
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(SHA256_HEX_LENGTH), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    attempt: Mapped[GenerationAttempt] = relationship(back_populates="assets")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<ImageAsset {self.kind.value!r} {self.relative_path!r}>"
