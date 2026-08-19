"""persist editable motion prompt per direct scene shot master

Revision ID: 0046
Revises: 0045
Create Date: 2026-08-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0046"
down_revision: str | None = "0045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("scene_shot_masters", sa.Column("motion_prompt", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("scene_shot_masters", "motion_prompt")
