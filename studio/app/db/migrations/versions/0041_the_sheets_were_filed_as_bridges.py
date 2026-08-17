"""the cast 3x3 sheets were filed as expression bridges

Revision ID: 0041
Revises: 0040
Create Date: 2026-08-18

Eleven cast references carry the role ``expression_bridge``. Looking at one
settles what they are: nine cells — full length front, three-quarter, front
torso, full length, head and shoulders, tight face, profile, three-quarter face
and an eye macro. That is the Nano 3x3 identity sheet, which
``CAST_ASSET_ROLES`` already names ``contact_sheet``.

The role is what the reference picker shows, so the wrong label is not cosmetic:
it reads as "one more expression photograph", which is an argument for sending
the standing full-length and the head-and-shoulders alongside it. Those are
cells 1 and 5 of the same sheet. The label was talking somebody into sending two
views twice.

An expression bridge is a real and different thing — a single frame closing the
gap between a neutral reference and a performance, which is what
``run_damo_expression_bridge.py`` generates. The role stays in the vocabulary
for when one is actually filed.

Scoped to assets that are attached to a cast member, on both the link and the
asset, because ingest copies the role onto the asset row.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0041"
down_revision: str | None = "0040"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD = "expression_bridge"
NEW = "contact_sheet"


def _rename(old: str, new: str) -> None:
    op.execute(
        sa.text(
            "UPDATE visual_assets SET role = :new WHERE role = :old AND id IN "
            "(SELECT visual_asset_id FROM cast_member_assets WHERE role = :old)"
        ).bindparams(new=new, old=old)
    )
    op.execute(
        sa.text("UPDATE cast_member_assets SET role = :new WHERE role = :old").bindparams(
            new=new, old=old
        )
    )


def upgrade() -> None:
    _rename(OLD, NEW)


def downgrade() -> None:
    _rename(NEW, OLD)
