"""every provider call, as the attempt record the contract asks for

Revision ID: 0038
Revises: 0037
Create Date: 2026-08-18

§6 of ``NANO_BANANA_CONTACT_SHEET_PIPELINE.md`` requires each stage to be
persisted as a distinct attempt carrying the prompt version, the resolved
prompt, the model and settings, the exact input manifest and the parent
lineage. The assets record their own half of that; this records the call.

Failures are kept as well as successes, and that is the part that pays off: a
prompt that Nano refuses is a fact about the prompt, and losing it means
learning the same thing twice.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0038"
down_revision: str | None = "0037"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())
UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "generation_calls",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        # coverage_sheet / panel_extraction / motion.
        sa.Column("operation", sa.String(length=48), nullable=False),
        sa.Column("scene_key", sa.String(length=96), nullable=True),
        sa.Column("subject", sa.String(length=96), nullable=True),
        sa.Column("prompt_sha256", sa.String(length=64), nullable=True),
        # The exact references sent -- §6's input manifest, queryable.
        sa.Column("input_asset_ids", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("output_asset_id", UUID, nullable=True),
        sa.Column("succeeded", sa.Boolean(), nullable=False),
        sa.Column("failure", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("actor", sa.String(length=64), server_default="owner", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_generation_calls"),
    )
    op.create_index(
        "ix_generation_calls_scene_key_created_at",
        "generation_calls",
        ["scene_key", sa.text("created_at DESC")],
    )
    op.create_index("ix_generation_calls_operation", "generation_calls", ["operation"])


def downgrade() -> None:
    op.drop_index("ix_generation_calls_operation", table_name="generation_calls")
    op.drop_index("ix_generation_calls_scene_key_created_at", table_name="generation_calls")
    op.drop_table("generation_calls")
