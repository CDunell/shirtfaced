"""observations classified in the Constitution's own terms

Revision ID: 0023
Revises: 0022
Create Date: 2026-08-09

0022 shipped with an invented vocabulary. A dry run refused every row, which is
the validation doing its job: the rows were classified against
SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md and the table was not.

Three corrections.

A zone's *state* and its *content* were sharing one column. They are different
facts. §5 gives every zone one of three states -- active graphic zone, permanent
identity zone, intentional negative space -- which is a decision about what the
zone is for. A blank chest chosen deliberately and a woven neck label are both
unprinted by the design and are not remotely the same thing. What is actually on
the zone is separate, and now lives in `content`.

Scale role (§7, S0-S4) and hierarchy (§9.3, H1-H3) had nowhere to go. Both are
per-zone: a mark can be small and subordinate, or small and the entire design.

`construction` was a parallel archetype vocabulary invented before the research
was read. §8 already names the graphic archetypes and §6 the layout archetypes,
and two prior research passes had already collided on exactly this -- there is a
reconciliation note in the repo warning about it. Replaced by
`graphic_archetype` and `layout_archetype`.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("design_observations", "construction")
    op.add_column(
        "design_observations",
        sa.Column("graphic_archetype", sa.String(48), server_default=""),
    )
    op.add_column(
        "design_observations",
        sa.Column("layout_archetype", sa.String(16), server_default=""),
    )

    op.drop_constraint("zone_state_known", "observation_zones", type_="check")
    op.alter_column(
        "observation_zones",
        "state",
        existing_type=sa.String(16),
        type_=sa.String(32),
    )
    op.add_column(
        "observation_zones",
        sa.Column("content", sa.String(16), nullable=False, server_default="bare"),
    )
    op.add_column("observation_zones", sa.Column("scale_role", sa.String(4), server_default=""))
    op.add_column("observation_zones", sa.Column("hierarchy", sa.String(4), server_default=""))

    op.create_check_constraint(
        "zone_state_known",
        "observation_zones",
        "state IN ('active graphic zone','permanent identity zone','intentional negative space')",
    )
    op.create_check_constraint(
        "zone_content_known",
        "observation_zones",
        "content IN ('bare','image_only','text_only','image_and_text')",
    )
    op.create_check_constraint(
        "scale_role_known",
        "observation_zones",
        "scale_role = '' OR scale_role IN ('S0','S1','S2','S3','S4')",
    )
    op.create_check_constraint(
        "hierarchy_known",
        "observation_zones",
        "hierarchy = '' OR hierarchy IN ('H1','H2','H3')",
    )


def downgrade() -> None:
    op.drop_constraint("hierarchy_known", "observation_zones", type_="check")
    op.drop_constraint("scale_role_known", "observation_zones", type_="check")
    op.drop_constraint("zone_content_known", "observation_zones", type_="check")
    op.drop_constraint("zone_state_known", "observation_zones", type_="check")
    op.drop_column("observation_zones", "hierarchy")
    op.drop_column("observation_zones", "scale_role")
    op.drop_column("observation_zones", "content")
    op.alter_column(
        "observation_zones",
        "state",
        existing_type=sa.String(32),
        type_=sa.String(16),
    )
    op.create_check_constraint(
        "zone_state_known",
        "observation_zones",
        "state IN ('bare','image_only','text_only','image_and_text')",
    )
    op.drop_column("design_observations", "layout_archetype")
    op.drop_column("design_observations", "graphic_archetype")
    op.add_column(
        "design_observations", sa.Column("construction", sa.String(32), server_default="")
    )
