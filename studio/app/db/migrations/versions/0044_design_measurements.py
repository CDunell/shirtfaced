"""machine measurements over the corpus live in the database

The advisor and the scoring thresholds used to read JSON files under
var/design_corpus/ that existed only on whichever machine last ran a mining
script -- for the advisor's whole life, no machine at all. A table cannot be
absent from the box. Identity columns match design_observations so measured
and observed join without sharing a column, per that schema's own rule.

Revision ID: 0044
Revises: 0043
Create Date: 2026-08-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0044"
down_revision: str | None = "0043"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "design_measurements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("corpus", sa.String(32), nullable=False),
        sa.Column("brand_slug", sa.String(64), nullable=False),
        sa.Column("product_slug", sa.String(128), nullable=False),
        sa.Column("image_path", sa.Text(), nullable=False),
        sa.Column("product_name", sa.Text(), nullable=False, server_default=""),
        sa.Column("tradition", sa.String(48), nullable=False, server_default=""),
        sa.Column("refusal_reason", sa.String(64), nullable=True),
        sa.Column("print_coverage", sa.Float(), nullable=True),
        sa.Column("ink_colours", sa.Integer(), nullable=True),
        sa.Column("placement_band", sa.String(16), nullable=True),
        sa.Column("light_on_dark", sa.Boolean(), nullable=True),
        sa.Column("phrase_words", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("analyser_version", sa.String(64), nullable=False),
        sa.Column(
            "measured_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "corpus",
            "brand_slug",
            "product_slug",
            "image_path",
            name="uq_design_measurements_frame",
        ),
    )
    op.create_index("ix_design_measurements_tradition", "design_measurements", ["tradition"])


def downgrade() -> None:
    op.drop_index("ix_design_measurements_tradition", table_name="design_measurements")
    op.drop_table("design_measurements")
