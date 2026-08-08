"""allow elements without geometry

Revision ID: 0016
Revises: 0015
Create Date: 2026-08-08

An element had to carry either a recipe or path data, exactly one. That refused
anything with neither -- a raster, a photograph of a printed shirt -- which is
material worth holding even though nothing can draw it yet.

The half of the rule that was doing real work is kept: a row claiming both a
recipe and its own geometry is ambiguous about which one draws it.

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_archive_elements_recipe_xor_geometry", "archive_elements", type_="check")
    op.create_check_constraint(
        "recipe_or_geometry_not_both",
        "archive_elements",
        "NOT (recipe <> '' AND geometry <> '')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_archive_elements_recipe_or_geometry_not_both", "archive_elements", type_="check"
    )
    op.create_check_constraint(
        "recipe_xor_geometry",
        "archive_elements",
        "(recipe <> '') <> (geometry <> '')",
    )
