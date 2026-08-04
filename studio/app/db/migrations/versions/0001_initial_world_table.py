"""initial world table

Revision ID: 0001
Revises:
Create Date: 2026-08-04

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

WORLD_STATUS = sa.Enum("active", "archived", name="world_status")


def upgrade() -> None:
    op.create_table(
        "worlds",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("directory_path", sa.String(length=512), nullable=False),
        sa.Column("status", WORLD_STATUS, server_default="active", nullable=False),
        sa.Column("world_document_hash", sa.String(length=64), nullable=True),
        sa.Column("continuity_document_hash", sa.String(length=64), nullable=True),
        sa.Column("shotlist_document_hash", sa.String(length=64), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_worlds")),
        sa.UniqueConstraint("slug", name=op.f("uq_worlds_slug")),
    )


def downgrade() -> None:
    op.drop_table("worlds")
    # drop_table does not remove the enum type, so it is dropped explicitly.
    WORLD_STATUS.drop(op.get_bind(), checkfirst=True)
