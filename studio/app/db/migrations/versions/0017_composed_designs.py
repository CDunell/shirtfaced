"""composed designs

Revision ID: 0017
Revises: 0016
Create Date: 2026-08-08

The archive could compose a design and had nowhere to put one. No route touched
``app.archive`` at all, so the engine was a library you could only run from a
Python prompt: nothing was stored, nothing reached ``awaiting_decision``, and
nothing could be approved.

This table keeps the brief rather than the artwork. Given the same seed,
garment, placement, words and palette the composer must emit the same bytes, so
the SVG here is a convenience and ``content_hash`` is the assertion -- one that
now survives a restart rather than only holding inside a single process.

Nothing exotic: uuid, jsonb, timestamptz and a partial index, all on the
supported list in ORACLE_CLOUD_DEPLOYMENT.md for PostgreSQL 15.

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "composed_designs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # The brief. This is the record; the artwork below is rebuildable from it.
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("garment_key", sa.String(length=80), nullable=False),
        sa.Column("placement_key", sa.String(length=40), nullable=False),
        sa.Column("fit", sa.String(length=20), nullable=False, server_default="adult"),
        sa.Column(
            "content", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column(
            "palette", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("treatment", sa.String(length=20), nullable=False, server_default="clean"),
        # What came back.
        sa.Column("grammar_key", sa.String(length=40), nullable=False),
        sa.Column(
            "parts", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("width_mm", sa.Float(), nullable=False),
        sa.Column("height_mm", sa.Float(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("svg", sa.Text(), nullable=False),
        sa.Column("assembler_version", sa.String(length=40), nullable=False),
        # The decision. A stored design is not an approved design.
        sa.Column(
            "state",
            postgresql.ENUM(name="attempt_state", create_type=False),
            nullable=False,
            server_default="awaiting_decision",
        ),
        sa.Column("decided_by", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # Short names. The metadata convention is
        # ck_%(table_name)s_%(constraint_name)s and alembic applies it here too,
        # so an already-qualified name comes out doubled.
        sa.UniqueConstraint("content_hash", name="composed_designs_content_hash"),
        sa.CheckConstraint("seed >= 0", name="seed_not_negative"),
        sa.CheckConstraint(
            "state NOT IN ('approved', 'rejected') OR decided_by <> ''",
            name="decision_has_an_author",
        ),
    )
    op.create_index("ix_composed_designs_state", "composed_designs", ["state"])
    # Partial. The review queue only asks for undecided designs, and that set
    # stays small while the decided set grows without bound.
    op.create_index(
        "ix_composed_designs_awaiting",
        "composed_designs",
        ["created_at"],
        postgresql_where=sa.text("state = 'awaiting_decision'"),
    )


def downgrade() -> None:
    op.drop_index("ix_composed_designs_awaiting", table_name="composed_designs")
    op.drop_index("ix_composed_designs_state", table_name="composed_designs")
    op.drop_table("composed_designs")
