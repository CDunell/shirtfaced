"""direct shot masters: up to five approved first frames per scene

Revision ID: 0045
Revises: 0044
Create Date: 2026-08-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0045"
down_revision: str | None = "0044"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scene_shot_masters",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("scene_key", sa.String(96), nullable=False),
        sa.Column("name", sa.String(96), nullable=False),
        sa.Column(
            "visual_asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("visual_assets.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="candidate"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(64), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.UniqueConstraint("scene_key", "name", name="uq_scene_shot_masters_scene_name"),
        sa.UniqueConstraint("visual_asset_id", name="uq_scene_shot_masters_visual_asset_id"),
        sa.CheckConstraint(
            "status IN ('candidate','approved','rejected','deprecated')",
            name="ck_scene_shot_masters_status_known",
        ),
    )
    op.create_index(
        "ix_scene_shot_masters_scene_status",
        "scene_shot_masters",
        ["scene_key", "status"],
    )
    op.create_index(
        "ix_scene_shot_masters_scene_order",
        "scene_shot_masters",
        ["scene_key", "sort_order"],
    )


def downgrade() -> None:
    op.drop_index("ix_scene_shot_masters_scene_order", table_name="scene_shot_masters")
    op.drop_index("ix_scene_shot_masters_scene_status", table_name="scene_shot_masters")
    op.drop_table("scene_shot_masters")
