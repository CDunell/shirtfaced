"""social derivative review state

Revision ID: 0019
Revises: 0018
Create Date: 2026-08-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "social_derivatives",
        sa.Column(
            "review_state",
            sa.String(length=32),
            server_default="review_required",
            nullable=False,
        ),
    )
    op.add_column(
        "social_derivatives",
        sa.Column("rejection_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "social_derivatives",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_social_derivatives_post_review_state",
        "social_derivatives",
        ["social_post_id", "review_state"],
    )

    # Existing package approvals pre-date per-output review. Preserve their intent.
    op.execute(
        "UPDATE social_derivatives d SET review_state = 'approved', reviewed_at = p.approved_at "
        "FROM social_posts p WHERE d.social_post_id = p.id "
        "AND p.state IN ('approved', 'queued', 'live')"
    )
    op.execute(
        "UPDATE social_derivatives d SET review_state = 'rejected', reviewed_at = p.rejected_at "
        "FROM social_posts p WHERE d.social_post_id = p.id AND p.state = 'rejected'"
    )


def downgrade() -> None:
    op.drop_index("ix_social_derivatives_post_review_state", table_name="social_derivatives")
    op.drop_column("social_derivatives", "reviewed_at")
    op.drop_column("social_derivatives", "rejection_reason")
    op.drop_column("social_derivatives", "review_state")
