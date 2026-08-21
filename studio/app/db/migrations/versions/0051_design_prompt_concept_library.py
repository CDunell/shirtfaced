"""concept_library: add 'design_prompt' for the quick-prompt screen

Revision ID: 0051
Revises: 0050
Create Date: 2026-08-21
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0051"
down_revision: str | None = "0050"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Postgres enum values cannot be dropped, only added -- same shape as
    # 0026's audit_event_type additions.
    op.execute("ALTER TYPE concept_library ADD VALUE IF NOT EXISTS 'design_prompt'")


def downgrade() -> None:
    # Enum values cannot be removed in Postgres without rebuilding the type.
    # Any 'design_prompt' concept created in the meantime would have to move
    # libraries first -- not attempted here, same as every other enum-add
    # migration in this history.
    pass
