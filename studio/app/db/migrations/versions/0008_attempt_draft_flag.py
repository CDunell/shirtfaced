"""attempt draft flag

Drafts run on the cheap image model to check framing and composition. Their review
scores are not comparable with a full frame's, and reference strength is the sum of
those scores, so a draft must be distinguishable to be kept out of the library.

Existing attempts all predate drafting and so default to false, which is correct:
every one of them ran on the full model.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-05

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "generation_attempts",
        sa.Column("is_draft", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("generation_attempts", "is_draft")
