"""drop video_assets and motion_takes; the Veo route already existed

Revision ID: 0042
Revises: 0041
Create Date: 2026-08-18

0040 built a second way to reach Veo: a service, four endpoints and a Takes
stage on the Scenes bench. ``NANO_BANANA_VEO_SCENE_PRODUCTION_PIPELINE.md`` §17
records the first one, which was already in this repository and already proven —
a trigger under ``studio/veo-coverage-triggers/`` runs a workflow that resolves
the seed path on the Studio server, verifies its SHA-256, calls
``run_pub_coverage_veo.py``, strips the generated audio §20 requires stripping,
probes the result, checksums it and uploads it.

The owner's ruling on 18 August 2026, given both: *remove yours, the other one
is proven to work.* And it strips the audio, which mine did not.

That document was not in the repository when 0040 was written, which is the
whole of the reason a second route got built. It is in it now.

Both tables were empty in production, so nothing is lost by dropping them rather
than leaving two schemas for one job. ``video_asset_status`` goes with them.

Not dropped: the three ``motion_take_*`` values added to ``audit_event_type``.
PostgreSQL will not remove an enum value without rewriting the type, and three
unused labels are cheaper than that. Nothing writes them.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0042"
down_revision: str | None = "0041"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())
UUID = postgresql.UUID(as_uuid=True)

video_asset_status = postgresql.ENUM(
    "pending", "approved", "deprecated", "rejected", name="video_asset_status", create_type=False
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
    op.drop_index("uq_motion_takes_one_keeper_per_frame", table_name="motion_takes")
    op.drop_index("ix_motion_takes_coverage_frame_id_attempt", table_name="motion_takes")
    op.drop_table("motion_takes")
    op.drop_table("video_assets")
    video_asset_status.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    """0040's tables, rebuilt exactly, so the revert is a revert."""
    video_asset_status.create(op.get_bind(), checkfirst=True)

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
    op.create_index(
        "uq_motion_takes_one_keeper_per_frame",
        "motion_takes",
        ["coverage_frame_id"],
        unique=True,
        postgresql_where=sa.text("status = 'keeper'"),
    )
