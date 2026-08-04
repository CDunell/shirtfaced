"""shots

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-05

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SHOT_STATUS = sa.Enum(
    "planned", "in_progress", "approved", "rejected", "abandoned", name="shot_status"
)


def upgrade() -> None:
    op.create_table(
        "shots",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("world_id", sa.UUID(), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), server_default=sa.text("100"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("hero_product", sa.String(length=120), nullable=True),
        sa.Column("camera_position", sa.String(length=120), nullable=True),
        sa.Column("lighting_source", sa.String(length=120), nullable=True),
        sa.Column("status", SHOT_STATUS, server_default="planned", nullable=False),
        sa.Column("disabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("blocked_reason", sa.Text(), nullable=True),
        sa.Column("source_line", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worlds.id"],
            name=op.f("fk_shots_world_id_worlds"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shots")),
        sa.UniqueConstraint("world_id", "external_id", name="uq_shots_world_id_external_id"),
    )
    # Supports the deterministic selector: eligible shots for a world, ordered by
    # priority then sequence.
    op.create_index(
        "ix_shots_world_id_status_priority_sequence",
        "shots",
        ["world_id", "status", "priority", "sequence"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_shots_world_id_status_priority_sequence", table_name="shots")
    op.drop_table("shots")
    # drop_table does not remove the enum type, so it is dropped explicitly.
    SHOT_STATUS.drop(op.get_bind(), checkfirst=True)
