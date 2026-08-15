"""drop print placements

Revision ID: 0030
Revises: 0029
Create Date: 2026-08-15

The corner-drag print is gone. A design was put on a photograph by dragging four
corners onto the garment, and this table held where they landed. The owner's
account of that path is that it never got off the ground and was replaced by
defined zones in real millimetres; the zone-based print reads an approved design
version and stores nothing here.

Dropped rather than left behind. A table no code reads is a question the next
person has to answer before they can trust anything near it, and every row in it
describes a screen that no longer exists.

The downgrade rebuilds the table exactly as 0012 left it -- the corners
themselves are not recoverable, because the feature that could interpret them is
not coming back.

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0030"
down_revision: str | None = "0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("print_placements")


def downgrade() -> None:
    op.create_table(
        "print_placements",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("photo_id", sa.UUID(), nullable=False),
        sa.Column("corners", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("design", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["photo_id"], ["photos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("photo_id", name="uq_print_placements_photo_id"),
    )
