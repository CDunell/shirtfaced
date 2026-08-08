"""social delivery attempts and receipts

Revision ID: 0020
Revises: 0019
Create Date: 2026-08-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "publication_jobs",
        sa.Column("max_attempts", sa.Integer(), server_default="5", nullable=False),
    )
    op.add_column(
        "publication_jobs", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "publication_jobs", sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("publication_jobs", sa.Column("adapter", sa.String(length=120), nullable=True))
    op.add_column(
        "publication_jobs",
        sa.Column("publish_receipt", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index(
        "ix_publication_jobs_retry_due", "publication_jobs", ["state", "next_attempt_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_publication_jobs_retry_due", table_name="publication_jobs")
    op.drop_column("publication_jobs", "publish_receipt")
    op.drop_column("publication_jobs", "adapter")
    op.drop_column("publication_jobs", "last_attempt_at")
    op.drop_column("publication_jobs", "next_attempt_at")
    op.drop_column("publication_jobs", "max_attempts")
