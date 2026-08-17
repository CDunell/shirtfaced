"""the soundtrack, held to the same discipline as the pictures

Revision ID: 0037
Revises: 0036
Create Date: 2026-08-18

``studio/worlds/world-01/SOUNDTRACK.md`` specifies one song delivered as many
files: eight required masters, seven cutdowns from a six-second sting to a
sixty-second bed, seven stem families, and a rule that "WAV is authoritative"
with SHA-256 checksums for the finals. That is a library, and the repository
already has one -- it is simply the wrong shape for audio.

So this is the visual library's discipline, in a sibling. Identity is the SHA of
the bytes, measurements are immutable, approval is an explicit decision with an
audit event, and a role says what the file is for. What differs is what an audio
file knows about itself: duration, sample rate, channels, bit depth. Those have
no meaning on an image, and width and height have none here.

``audio_assets`` rather than widening ``visual_assets``: a table named for
pictures holding a WAV would be a name that lies, and every consumer of that
table would have to start asking which kind of thing a row is.

Roles are free text with ``SOUNDTRACK_ASSET_ROLES`` as the offered vocabulary,
the same call as cast roles and for the same reason -- a mix nobody anticipated
must still be filable.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0037"
down_revision: str | None = "0036"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())
UUID = postgresql.UUID(as_uuid=True)

audio_source_type = postgresql.ENUM(
    "upload",
    "generated",
    "edited",
    "imported",
    "commissioned",
    "licensed_stock",
    name="audio_source_type",
    create_type=False,
)
audio_asset_status = postgresql.ENUM(
    "pending",
    "approved",
    "deprecated",
    "rejected",
    name="audio_asset_status",
    create_type=False,
)
licence_status = postgresql.ENUM(name="licence_status", create_type=False)


def _timestamps() -> tuple[sa.Column[Any], sa.Column[Any]]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def upgrade() -> None:
    bind = op.get_bind()
    audio_source_type.create(bind, checkfirst=True)
    audio_asset_status.create(bind, checkfirst=True)

    for event in (
        "audio_asset_ingested",
        "audio_asset_approved",
        "audio_asset_deprecated",
        "soundtrack_asset_linked",
    ):
        op.execute(f"ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS '{event}'")

    op.create_table(
        "audio_assets",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=True),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        # Null where the format could not be read without a decoder. Absent is
        # honest; a guessed duration would be worse than none.
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("sample_rate_hz", sa.Integer(), nullable=True),
        sa.Column("channels", sa.Integer(), nullable=True),
        sa.Column("bit_depth", sa.Integer(), nullable=True),
        sa.Column("source_type", audio_source_type, nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("status", audio_asset_status, server_default="pending", nullable=False),
        sa.Column("rights_status", licence_status, server_default="verified", nullable=False),
        sa.Column("rights_metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("metadata_json", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(length=64), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_audio_assets"),
        # Exact-byte dedupe. Delivering the same WAV twice is one file.
        sa.UniqueConstraint("sha256", name="uq_audio_assets_sha256"),
        sa.CheckConstraint("byte_size > 0", name="byte_size_positive"),
        sa.CheckConstraint("duration_ms IS NULL OR duration_ms > 0", name="duration_positive"),
        sa.CheckConstraint("channels IS NULL OR channels > 0", name="channels_positive"),
    )
    op.create_index("ix_audio_assets_role_status", "audio_assets", ["role", "status"])

    op.create_table(
        "soundtrack_tracks",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("world_id", UUID, nullable=True),
        sa.Column("slug", sa.String(length=96), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        # The facts §1 fixes: 132 BPM, 4/4, D major with a B-minor shadow.
        sa.Column("bpm", sa.Integer(), nullable=True),
        sa.Column("musical_key", sa.String(length=32), nullable=True),
        sa.Column("time_signature", sa.String(length=16), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_soundtrack_tracks"),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worlds.id"],
            name="fk_soundtrack_tracks_world_id_worlds",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("world_id", "slug", name="uq_soundtrack_tracks_world_id_slug"),
        sa.CheckConstraint("status IN ('active','deprecated')", name="status_known"),
        sa.CheckConstraint("bpm IS NULL OR bpm > 0", name="bpm_positive"),
    )

    op.create_table(
        "soundtrack_track_assets",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("track_id", UUID, nullable=False),
        sa.Column("audio_asset_id", UUID, nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_soundtrack_track_assets"),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["soundtrack_tracks.id"],
            name="fk_soundtrack_track_assets_track_id_soundtrack_tracks",
            ondelete="CASCADE",
        ),
        # RESTRICT: unlinking a mix must not be a way to destroy the file an
        # edit is cut against.
        sa.ForeignKeyConstraint(
            ["audio_asset_id"],
            ["audio_assets.id"],
            name="fk_soundtrack_track_assets_audio_asset_id_audio_assets",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "track_id", "audio_asset_id", name="uq_soundtrack_track_assets_track_id_audio_asset_id"
        ),
    )
    # One primary per role: "the 12.5" has to resolve to one file, or an edit
    # picks by accident.
    op.create_index(
        "uq_soundtrack_track_assets_primary_per_role",
        "soundtrack_track_assets",
        ["track_id", "role"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )
    op.create_index(
        "ix_soundtrack_track_assets_audio_asset_id",
        "soundtrack_track_assets",
        ["audio_asset_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_soundtrack_track_assets_audio_asset_id", table_name="soundtrack_track_assets")
    op.drop_index(
        "uq_soundtrack_track_assets_primary_per_role", table_name="soundtrack_track_assets"
    )
    op.drop_table("soundtrack_track_assets")
    op.drop_table("soundtrack_tracks")
    op.drop_index("ix_audio_assets_role_status", table_name="audio_assets")
    op.drop_table("audio_assets")

    bind = op.get_bind()
    audio_asset_status.drop(bind, checkfirst=True)
    audio_source_type.drop(bind, checkfirst=True)
