"""reference frames

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-05

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

REFERENCE_STATE = sa.Enum("active", "archived", "pinned", name="reference_state")

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Alembic does not detect new members of an existing enum. Both reference audit
    # events are added explicitly. PostgreSQL cannot remove an enum value, so the
    # downgrade leaves them; an unused member is harmless.
    for value in ("reference_archived", "reference_pinned"):
        op.execute(f"ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS '{value}'")

    op.create_table(
        "reference_frames",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("world_id", sa.UUID(), nullable=False),
        sa.Column("attempt_id", sa.UUID(), nullable=False),
        sa.Column("asset_id", sa.UUID(), nullable=False),
        sa.Column(
            "state",
            sa.Enum("active", "archived", "pinned", name="reference_state"),
            server_default="active",
            nullable=False,
        ),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("why_it_works", sa.Text(), nullable=True),
        sa.Column("hero_product", sa.String(length=120), nullable=True),
        sa.Column("camera_position", sa.String(length=120), nullable=True),
        sa.Column("strength", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["asset_id"],
            ["image_assets.id"],
            name=op.f("fk_reference_frames_asset_id_image_assets"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["generation_attempts.id"],
            name=op.f("fk_reference_frames_attempt_id_generation_attempts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worlds.id"],
            name=op.f("fk_reference_frames_world_id_worlds"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reference_frames")),
        sa.UniqueConstraint("attempt_id", name="uq_reference_frames_attempt_id"),
    )
    op.create_index(
        "ix_reference_frames_world_id_state",
        "reference_frames",
        ["world_id", "state"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_reference_frames_world_id_state", table_name="reference_frames")
    op.drop_table("reference_frames")
    # drop_table does not remove the enum type, so it is dropped explicitly.
    REFERENCE_STATE.drop(op.get_bind(), checkfirst=True)
