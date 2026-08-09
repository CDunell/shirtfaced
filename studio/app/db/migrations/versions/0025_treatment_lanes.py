"""treatment lanes from the creative brain

Revision ID: 0025
Revises: 0024
Create Date: 2026-08-10

SHIRTFACED_CREATIVE_BRAIN.md §11 names the treatment lanes the brand works in:
tonal grey on black, tiny incidental marks, oversized back statements,
integrated type crossing imagery, caption above or beneath photography, type
embedded in the composition, and so on.

The Constitution's §8 archetypes say what a design *is* -- emblem, typographic
hero, all-over field. The lanes say how it was *handled*, which is the language
a brief is written in. Recording both means precedent can be retrieved either
way rather than needing a translation table.

An array, because a design can occupy more than one lane at once.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0025"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "design_observations",
        sa.Column(
            "treatment_lanes",
            postgresql.ARRAY(sa.Text()),
            server_default="{}",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("design_observations", "treatment_lanes")
