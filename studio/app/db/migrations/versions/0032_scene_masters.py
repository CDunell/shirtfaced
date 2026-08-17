"""one approved scene master per scene

Revision ID: 0032
Revises: 0031
Create Date: 2026-08-17

Phase 3 of ``studio/docs/VISUAL_ASSET_LIBRARY.md``, reduced to what the Veo
pipeline actually needs today: which image is the approved master for a scene.

Before this, the coverage tool answered that by trying ``composition-gpt.png``,
then ``.jpg``, then ``.jpeg`` in the scene's directory and taking the first hit,
and the rich-pub script took whichever matching file had the newest mtime. On
the production box both a ``.png`` and a ``.jpg`` are present, so the choice was
being made by list order over two different images, with no approval anywhere in
it -- and the four coverage frames already cut for pub-1105 cite a parent SHA
that matches neither of them.

``scene_key`` is a string rather than a foreign key to ``scenes``. Migration
0029 added that table for campaign-native production and nothing populates it;
a join to an empty table would not make this resolution more correct. The key
is what the coverage tool, the renderer scripts and the Veo manifests already
agree on.

The partial unique index carries the rule: at most one approved master per
scene. A second approval is a database error rather than a silent tie-break.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0032"
down_revision: str | None = "0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    for event in ("scene_master_registered", "scene_master_approved"):
        op.execute(f"ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS '{event}'")

    op.create_table(
        "scene_masters",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("scene_key", sa.String(length=96), nullable=False),
        sa.Column("visual_asset_id", UUID, nullable=False),
        sa.Column("status", sa.String(length=32), server_default="candidate", nullable=False),
        sa.Column("parent_master_id", UUID, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(length=64), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_scene_masters"),
        # RESTRICT: the image a master points at cannot be deleted while any
        # coverage frame or finished clip depends on it.
        sa.ForeignKeyConstraint(
            ["visual_asset_id"],
            ["visual_assets.id"],
            name="fk_scene_masters_visual_asset_id_visual_assets",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["parent_master_id"],
            ["scene_masters.id"],
            name="fk_scene_masters_parent_master_id_scene_masters",
            ondelete="SET NULL",
        ),
        # One image is one master. Registering the same bytes for two scenes is
        # a mistake worth catching, not a feature.
        sa.UniqueConstraint("visual_asset_id", name="uq_scene_masters_visual_asset_id"),
        sa.CheckConstraint(
            "status IN ('candidate','approved','superseded','rejected','deprecated')",
            name="status_known",
        ),
    )
    op.create_index(
        "uq_scene_masters_one_approved_per_scene",
        "scene_masters",
        ["scene_key"],
        unique=True,
        postgresql_where=sa.text("status = 'approved'"),
    )
    op.create_index("ix_scene_masters_scene_key_status", "scene_masters", ["scene_key", "status"])


def downgrade() -> None:
    op.drop_index("ix_scene_masters_scene_key_status", table_name="scene_masters")
    op.drop_index("uq_scene_masters_one_approved_per_scene", table_name="scene_masters")
    op.drop_table("scene_masters")
