"""photo lineage

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-07

Which prompt produced a photograph. The frames are generated elsewhere from a
prompt written here and then uploaded, so without this the join exists only in
somebody's memory.

Nullable, and cleared rather than cascading: a photograph outlives the prompt that
made it, and losing the lineage is not a reason to lose the photograph.

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("photos", sa.Column("prompt_variation_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_photos_prompt_variation_id",
        "photos",
        "prompt_variations",
        ["prompt_variation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_photos_prompt_variation_id", "photos", ["prompt_variation_id"])


def downgrade() -> None:
    op.drop_index("ix_photos_prompt_variation_id", table_name="photos")
    op.drop_constraint("fk_photos_prompt_variation_id", "photos", type_="foreignkey")
    op.drop_column("photos", "prompt_variation_id")
