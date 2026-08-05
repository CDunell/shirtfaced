"""review structural gate

The nine gates all judge taste and intent, and none of them asks whether the thing
photographed could exist. A car with no front seats was scored documentary
credibility 4/5. A van whose whole rear end was missing, background visible straight
through the opening, scored 5/5 and passed vehicle continuity. Neither score was
wrong: nothing in the rubric named physical structure, so nothing looked at it.

``structurally_sound`` is the tenth gate's verdict, promoted to a column beside
``branding_compliant`` and ``vehicle_compliant`` because it is a foundational pass or
fail rather than a matter of degree.

Existing reviews default to true. That is the honest default rather than the accurate
one: those images were never assessed for structure, and marking them false would
assert a failure nobody looked for. The raw_json of a pre-0009 review has no
structural_plausibility gate, which is how they stay distinguishable.

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-05

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "automated_reviews",
        sa.Column(
            "structurally_sound", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_column("automated_reviews", "structurally_sound")
