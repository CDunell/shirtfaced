"""batch-generated design concepts, served randomly per tradition

Revision ID: 0049
Revises: 0048
Create Date: 2026-08-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0049"
down_revision: str | None = "0048"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "design_concept_pool",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tradition", sa.String(48), nullable=False),
        sa.Column("concept_text", sa.Text(), nullable=False),
        # Which structural shape (mine_design_structure.py's vocabulary) this
        # concept was written against, if any -- lets the picker prefer a
        # concept whose composition matches what render_generation_prompt()
        # is about to say for this tradition, instead of a random mismatch.
        sa.Column("structural_shape", sa.String(96), nullable=True),
        # Which batch produced this row. Batches are session-generated, not a
        # live API call -- this is provenance for "how was this written and
        # by what", not a foreign key to anything running.
        sa.Column("batch", sa.String(64), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
    )
    op.create_index(
        "ix_design_concept_pool_tradition_active",
        "design_concept_pool",
        ["tradition", "active"],
    )


def downgrade() -> None:
    op.drop_index("ix_design_concept_pool_tradition_active", table_name="design_concept_pool")
    op.drop_table("design_concept_pool")
