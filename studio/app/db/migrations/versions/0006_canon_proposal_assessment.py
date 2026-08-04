"""canon proposal assessment

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-05

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

PROPOSAL_CLASSIFICATION = sa.Enum(
    "already_covered",
    "genuine_addition",
    "refinement",
    "contradiction",
    "too_specific",
    name="proposal_classification",
)

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # add_column does not create an enum type the way create_table does, so it is
    # created explicitly. Third enum gotcha in this project; each was caught by a
    # migration run rather than by review.
    PROPOSAL_CLASSIFICATION.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "canon_proposals",
        sa.Column(
            "classification",
            sa.Enum(
                "already_covered",
                "genuine_addition",
                "refinement",
                "contradiction",
                "too_specific",
                name="proposal_classification",
            ),
            nullable=True,
        ),
    )
    op.add_column("canon_proposals", sa.Column("classification_reason", sa.Text(), nullable=True))
    op.add_column(
        "canon_proposals", sa.Column("classified_by", sa.String(length=120), nullable=True)
    )
    op.add_column(
        "canon_proposals", sa.Column("target_heading", sa.String(length=200), nullable=True)
    )
    op.add_column(
        "canon_proposals", sa.Column("reviewer_model", sa.String(length=120), nullable=True)
    )
    op.add_column("canon_proposals", sa.Column("applied_wording", sa.Text(), nullable=True))
    op.add_column(
        "canon_proposals", sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("canon_proposals", sa.Column("failure_detail", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("canon_proposals", "failure_detail")
    op.drop_column("canon_proposals", "applied_at")
    op.drop_column("canon_proposals", "applied_wording")
    op.drop_column("canon_proposals", "reviewer_model")
    op.drop_column("canon_proposals", "target_heading")
    op.drop_column("canon_proposals", "classified_by")
    op.drop_column("canon_proposals", "classification_reason")
    op.drop_column("canon_proposals", "classification")
    # drop_column does not remove the enum type, so it is dropped explicitly.
    PROPOSAL_CLASSIFICATION.drop(op.get_bind(), checkfirst=True)
