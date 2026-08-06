"""prompt variations

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-06

Writing a prompt recorded nothing, so asking again replaced what came before and a
variation could not be compared against the one it varies from.

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prompt_variations",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("shot_id", sa.UUID(), nullable=False),
        sa.Column("variation", sa.Integer(), nullable=False),
        sa.Column("image_prompt", sa.Text(), nullable=False),
        sa.Column("video_prompt", sa.Text(), nullable=False),
        sa.Column("selection_reason", sa.Text(), nullable=False),
        sa.Column("live", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["shot_id"], ["shots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # Numbering is per shot. A race that produced two number 3s should fail
        # here rather than quietly renumber a shot's history.
        sa.UniqueConstraint("shot_id", "variation", name="uq_prompt_variations_shot_variation"),
    )
    op.create_index(
        "ix_prompt_variations_shot_id_variation",
        "prompt_variations",
        ["shot_id", "variation"],
    )


def downgrade() -> None:
    op.drop_index("ix_prompt_variations_shot_id_variation", table_name="prompt_variations")
    op.drop_table("prompt_variations")
