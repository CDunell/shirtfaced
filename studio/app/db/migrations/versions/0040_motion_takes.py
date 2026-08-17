"""video assets, and the takes a shot accumulates

Revision ID: 0040
Revises: 0039
Create Date: 2026-08-18

The last leg of the pipeline. §5 of the Nano contract: an approved standalone
shot becomes the first frame of a motion generation, and the keeper range is
chosen afterwards by a person.

``video_assets`` is a third sibling beside images and audio, for the same reason
audio got its own: a clip knows its duration, its frame rate and whether it
still carries generated sound, and none of that means anything on a still.

``motion_takes`` is the part that matters for how this is actually used.
SHOTLIST.md's package asks for roughly six to eight seconds per shot and expects
a usable slice of one and a half to four -- so a shot gets *takes*, plural, and
most of them are wrong. A take therefore records its own outcome, and a rejected
one stays: it is the cheapest evidence there is about what the motion prompt
does, and the next attempt is a new row rather than an overwrite.

``keeper_from_ms``/``keeper_to_ms`` hold the range worth cutting once somebody
has watched it. Null until then, because nothing can compute which two seconds
of a take are the good ones.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0040"
down_revision: str | None = "0039"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())
UUID = postgresql.UUID(as_uuid=True)

video_asset_status = postgresql.ENUM(
    "pending",
    "approved",
    "deprecated",
    "rejected",
    name="video_asset_status",
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
    video_asset_status.create(op.get_bind(), checkfirst=True)
    for event in ("motion_take_generated", "motion_take_approved", "motion_take_rejected"):
        op.execute(f"ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS '{event}'")

    op.create_table(
        "video_assets",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("frame_rate", sa.Numeric(6, 3), nullable=True),
        # Veo returns sound the world does not use; the scripts strip it. Which
        # of the two a file is cannot be told apart by looking at the name.
        sa.Column("has_audio", sa.Boolean(), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("status", video_asset_status, server_default="pending", nullable=False),
        sa.Column("rights_status", licence_status, server_default="verified", nullable=False),
        sa.Column("metadata_json", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(length=64), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_video_assets"),
        sa.UniqueConstraint("sha256", name="uq_video_assets_sha256"),
        sa.CheckConstraint("byte_size > 0", name="byte_size_positive"),
        sa.CheckConstraint("duration_ms IS NULL OR duration_ms > 0", name="duration_positive"),
    )

    op.create_table(
        "motion_takes",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("coverage_frame_id", UUID, nullable=False),
        sa.Column("video_asset_id", UUID, nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("prompt_sha256", sa.String(length=64), nullable=True),
        sa.Column("first_frame_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        # The slice worth cutting, once a person has watched it. Not computable.
        sa.Column("keeper_from_ms", sa.Integer(), nullable=True),
        sa.Column("keeper_to_ms", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", sa.String(length=64), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_motion_takes"),
        sa.ForeignKeyConstraint(
            ["coverage_frame_id"],
            ["coverage_frames.id"],
            name="fk_motion_takes_coverage_frame_id_coverage_frames",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["video_asset_id"],
            ["video_assets.id"],
            name="fk_motion_takes_video_asset_id_video_assets",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("video_asset_id", name="uq_motion_takes_video_asset_id"),
        sa.UniqueConstraint(
            "coverage_frame_id", "attempt", name="uq_motion_takes_coverage_frame_id_attempt"
        ),
        sa.CheckConstraint("attempt > 0", name="attempt_positive"),
        sa.CheckConstraint("status IN ('pending','keeper','rejected')", name="status_known"),
        sa.CheckConstraint(
            "keeper_from_ms IS NULL OR keeper_to_ms IS NULL OR keeper_to_ms > keeper_from_ms",
            name="keeper_range_ordered",
        ),
    )
    op.create_index(
        "ix_motion_takes_coverage_frame_id_attempt",
        "motion_takes",
        ["coverage_frame_id", "attempt"],
    )
    # One keeper per shot: the edit needs one answer, the same rule as one
    # approved master per scene.
    op.create_index(
        "uq_motion_takes_one_keeper_per_frame",
        "motion_takes",
        ["coverage_frame_id"],
        unique=True,
        postgresql_where=sa.text("status = 'keeper'"),
    )


def downgrade() -> None:
    op.drop_index("uq_motion_takes_one_keeper_per_frame", table_name="motion_takes")
    op.drop_index("ix_motion_takes_coverage_frame_id_attempt", table_name="motion_takes")
    op.drop_table("motion_takes")
    op.drop_table("video_assets")
    video_asset_status.drop(op.get_bind(), checkfirst=True)
