"""coverage frames as rows, with their parent master

Revision ID: 0033
Revises: 0032
Create Date: 2026-08-17

Phase 4 of ``studio/docs/VISUAL_ASSET_LIBRARY.md`` and §8. A coverage frame is a
named 9:16 observation of one scene master: original pixels, exact crop box, and
the parent it came from.

Until now a frame was a directory -- ``var/scene-references/<scene>/coverage/
<shot>/{frame.png,manifest.json}`` -- and the manifest was the only record of
which master it was cut from. Nothing could ask "which frames does this master
have", nothing stopped a master being replaced under frames that cite it, and a
Veo run could be handed any file at all.

``source_master_sha256`` is stored beside the foreign key on purpose. The key
says which master; the hash says which bytes that master had when the crop was
taken, so a superseded master and a re-approved one can never be confused for
each other.

One row per (scene master, name): re-cutting a shot from the same master
replaces the row rather than accumulating near-duplicates that a person then has
to choose between.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0033"
down_revision: str | None = "0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())
UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    for event in ("coverage_frame_derived", "coverage_frame_approved"):
        op.execute(f"ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS '{event}'")

    op.create_table(
        "coverage_frames",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("scene_master_id", UUID, nullable=False),
        sa.Column("visual_asset_id", UUID, nullable=False),
        sa.Column("name", sa.String(length=96), nullable=False),
        sa.Column("aspect_ratio", sa.String(length=16), server_default="9:16", nullable=False),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("y", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        # The master's hash at the moment of the crop. Not derivable from the
        # foreign key: an approved master can be superseded later.
        sa.Column("source_master_sha256", sa.String(length=64), nullable=False),
        sa.Column("frame_sha256", sa.String(length=64), nullable=False),
        sa.Column("operation", sa.String(length=32), server_default="crop_only", nullable=False),
        sa.Column(
            "approved_for_veo", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name="pk_coverage_frames"),
        # RESTRICT both ways: a master with frames cannot be deleted, and neither
        # can the image a frame is. Finished clips cite these.
        sa.ForeignKeyConstraint(
            ["scene_master_id"],
            ["scene_masters.id"],
            name="fk_coverage_frames_scene_master_id_scene_masters",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["visual_asset_id"],
            ["visual_assets.id"],
            name="fk_coverage_frames_visual_asset_id_visual_assets",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("visual_asset_id", name="uq_coverage_frames_visual_asset_id"),
        sa.UniqueConstraint(
            "scene_master_id", "name", name="uq_coverage_frames_scene_master_id_name"
        ),
        sa.CheckConstraint("width > 0 AND height > 0", name="dimensions_positive"),
        sa.CheckConstraint("x >= 0 AND y >= 0", name="origin_not_negative"),
    )
    op.create_index(
        "ix_coverage_frames_scene_master_id_name", "coverage_frames", ["scene_master_id", "name"]
    )
    op.create_index("ix_coverage_frames_approved_for_veo", "coverage_frames", ["approved_for_veo"])


def downgrade() -> None:
    op.drop_index("ix_coverage_frames_approved_for_veo", table_name="coverage_frames")
    op.drop_index("ix_coverage_frames_scene_master_id_name", table_name="coverage_frames")
    op.drop_table("coverage_frames")
