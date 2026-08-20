"""design_generation_samples: durable store for tested concept-pool renders

Revision ID: 0050
Revises: 0049
Create Date: 2026-08-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0050"
down_revision: str | None = "0049"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "design_generation_samples",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Nullable and unconstrained: a concept can be retired or deleted from
        # the pool and the sample -- the proof a batch was actually tested --
        # must outlive it.
        sa.Column("concept_pool_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tradition", sa.String(48), nullable=False),
        sa.Column("concept_text", sa.Text(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        # Both relative to ASSETS_ROOT, via FilesystemAssetStore -- same
        # convention as ImageAsset.relative_path.
        sa.Column("image_relative_path", sa.String(512), nullable=False),
        sa.Column("thumb_relative_path", sa.String(512), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("drop_reason", sa.Text(), nullable=True),
        sa.Column("batch", sa.String(64), nullable=False),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.create_index(
        "ix_design_generation_samples_batch",
        "design_generation_samples",
        ["batch"],
    )
    op.create_index(
        "ix_design_generation_samples_tradition_status",
        "design_generation_samples",
        ["tradition", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_design_generation_samples_tradition_status", table_name="design_generation_samples"
    )
    op.drop_index("ix_design_generation_samples_batch", table_name="design_generation_samples")
    op.drop_table("design_generation_samples")
