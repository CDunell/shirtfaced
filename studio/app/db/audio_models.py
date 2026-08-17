"""The soundtrack library: one song, many delivered files.

``studio/worlds/world-01/SOUNDTRACK.md`` §8 asks for eight masters, seven
cutdowns, seven stem families and SHA-256 checksums on the finals. This is the
Visual Asset Library's discipline applied to that: identity is the hash of the
bytes, measurements are immutable, approval is a decision with an audit event,
and a role says what a file is for.

A sibling table rather than a widening of ``visual_assets``. What an audio file
knows about itself — duration, sample rate, channels, bit depth — is meaningless
on an image, width and height are meaningless here, and a table named for
pictures holding a WAV would make every consumer ask which kind of row it had.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.base import NO_VALUE

from app.db.base import Base, TimestampMixin
from app.db.models import SHA256_HEX_LENGTH, _enum
from app.db.visual_models import AssetIsImmutable
from app.domain.enums import AudioAssetStatus, AudioSourceType, LicenceStatus


class AudioAsset(Base, TimestampMixin):
    """One immutable audio file, its identity and what it sounds like.

    ``duration_ms`` and the rest are null where the format could not be read
    without a decoder this application does not carry. Absent is honest; a
    guessed duration would be worse than none, because an edit would trust it.
    """

    __tablename__ = "audio_assets"
    __table_args__ = (
        UniqueConstraint("sha256", name="uq_audio_assets_sha256"),
        Index("ix_audio_assets_role_status", "role", "status"),
        CheckConstraint("byte_size > 0", name="byte_size_positive"),
        CheckConstraint("duration_ms IS NULL OR duration_ms > 0", name="duration_positive"),
        CheckConstraint("channels IS NULL OR channels > 0", name="channels_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    role: Mapped[str | None] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(SHA256_HEX_LENGTH), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    sample_rate_hz: Mapped[int | None] = mapped_column(Integer)
    channels: Mapped[int | None] = mapped_column(Integer)
    bit_depth: Mapped[int | None] = mapped_column(Integer)
    source_type: Mapped[AudioSourceType] = mapped_column(
        _enum(AudioSourceType, "audio_source_type"), nullable=False
    )
    provider: Mapped[str | None] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[AudioAssetStatus] = mapped_column(
        _enum(AudioAssetStatus, "audio_asset_status"),
        nullable=False,
        default=AudioAssetStatus.PENDING,
        server_default=AudioAssetStatus.PENDING.value,
    )
    # Verified by default, like the visual library and for the same reason.
    rights_status: Mapped[LicenceStatus] = mapped_column(
        _enum(LicenceStatus, "licence_status"),
        nullable=False,
        default=LicenceStatus.VERIFIED,
        server_default=LicenceStatus.VERIFIED.value,
    )
    rights_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata_json", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    description: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[str | None] = mapped_column(String(64))

    @property
    def duration_seconds(self) -> float | None:
        """Derived, never stored: it cannot disagree with the milliseconds."""
        return None if self.duration_ms is None else self.duration_ms / 1000

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<AudioAsset {self.role!r} {self.sha256[:12]}>"


class SoundtrackTrack(Base, TimestampMixin):
    """A song, and the facts every one of its files has to agree with.

    §1 fixes 132 BPM, 4/4 and D major with a B-minor shadow. They live on the
    track because they are true of the work rather than of any one delivery.
    """

    __tablename__ = "soundtrack_tracks"
    __table_args__ = (
        UniqueConstraint("world_id", "slug", name="uq_soundtrack_tracks_world_id_slug"),
        CheckConstraint("status IN ('active','deprecated')", name="status_known"),
        CheckConstraint("bpm IS NULL OR bpm > 0", name="bpm_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    world_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE")
    )
    slug: Mapped[str] = mapped_column(String(96), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="active")
    bpm: Mapped[int | None] = mapped_column(Integer)
    musical_key: Mapped[str | None] = mapped_column(String(32))
    time_signature: Mapped[str | None] = mapped_column(String(16))
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata_json", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    assets: Mapped[list[SoundtrackTrackAsset]] = relationship(
        back_populates="track",
        cascade="all, delete-orphan",
        order_by="SoundtrackTrackAsset.sort_order",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<SoundtrackTrack {self.slug!r}>"


class SoundtrackTrackAsset(Base, TimestampMixin):
    """One delivered file, in one role, for one track.

    The role carries the job — ``canonical_12s5``, ``stem_drums``, ``tv_mix`` —
    and the primary badge says which file answers to it. One primary per role,
    so "the 12.5" resolves to one thing rather than to whichever an edit reached
    for first.
    """

    __tablename__ = "soundtrack_track_assets"
    __table_args__ = (
        UniqueConstraint(
            "track_id", "audio_asset_id", name="uq_soundtrack_track_assets_track_id_audio_asset_id"
        ),
        Index(
            "uq_soundtrack_track_assets_primary_per_role",
            "track_id",
            "role",
            unique=True,
            postgresql_where=text("is_primary"),
        ),
        Index("ix_soundtrack_track_assets_audio_asset_id", "audio_asset_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("soundtrack_tracks.id", ondelete="CASCADE"), nullable=False
    )
    audio_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audio_assets.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    notes: Mapped[str | None] = mapped_column(Text)

    track: Mapped[SoundtrackTrack] = relationship(back_populates="assets")
    asset: Mapped[AudioAsset] = relationship(lazy="joined")


# Same rule as the visual library: the hash, the size and the measurements are
# what the bytes are. A different mix is a different asset, never an edit.
IMMUTABLE_AUDIO_FIELDS = ("sha256", "byte_size", "storage_key", "mime_type", "duration_ms")


def _refuse_mutation(target: AudioAsset, value: Any, old: Any, _initiator: Any) -> Any:
    if old is NO_VALUE or old is None or old == value:
        return value
    raise AssetIsImmutable(
        f"Audio asset {target.sha256[:12]}: bytes and their measurements cannot be edited. "
        "Ingest the new mix as its own asset."
    )


for _field in IMMUTABLE_AUDIO_FIELDS:
    event.listen(getattr(AudioAsset, _field), "set", _refuse_mutation, retval=True)
