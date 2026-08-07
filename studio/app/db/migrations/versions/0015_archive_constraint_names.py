"""archive constraint names

Revision ID: 0015
Revises: 0014
Create Date: 2026-08-08

The element archive's check constraints were created with doubled names --
``ck_archive_elements_ck_archive_elements_complexity``. The metadata naming
convention for check constraints is ``ck_%(table_name)s_%(constraint_name)s``,
so passing an already-qualified name into ``create_table`` gets it prefixed a
second time. The ORM models pass short names and so produce the single-prefixed
form, which is what put the two out of step.

0014 now passes short names, so a database built from scratch is already
correct. This exists for the ones that ran the earlier version -- production
among them -- and it renames rather than drops and recreates, so no constraint
is ever briefly absent on a table that may hold rows.

Guarded on each old name existing, so it is a no-op on a fresh database and can
be applied to either.

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (doubled name as first written, corrected name)
RENAMES: tuple[tuple[str, str], ...] = (
    (
        "ck_archive_elements_ck_archive_elements_verified_licence_complete",
        "ck_archive_elements_verified_licence_complete",
    ),
    ("ck_archive_elements_ck_archive_elements_inks", "ck_archive_elements_inks"),
    ("ck_archive_elements_ck_archive_elements_complexity", "ck_archive_elements_complexity"),
    (
        "ck_archive_elements_ck_archive_elements_recipe_xor_geometry",
        "ck_archive_elements_recipe_xor_geometry",
    ),
)


def _exists(name: str) -> bool:
    return bool(
        op.get_bind()
        .execute(
            sa.text(
                "SELECT 1 FROM pg_constraint c "
                "JOIN pg_class t ON t.oid = c.conrelid "
                "WHERE t.relname = 'archive_elements' AND c.conname = :name"
            ),
            {"name": name},
        )
        .scalar()
    )


def upgrade() -> None:
    for old, new in RENAMES:
        if _exists(old):
            op.execute(f'ALTER TABLE archive_elements RENAME CONSTRAINT "{old}" TO "{new}"')


def downgrade() -> None:
    for old, new in RENAMES:
        if _exists(new):
            op.execute(f'ALTER TABLE archive_elements RENAME CONSTRAINT "{new}" TO "{old}"')
