"""observation columns are not nullable

Revision ID: 0024
Revises: 0023
Create Date: 2026-08-09

SQLAlchemy 2.0 reads a `Mapped[str]` annotation as NOT NULL; 0022 and 0023
created those columns nullable because that is alembic's default. Every column
carrying a server_default therefore drifted, and the migration-versus-model test
failed on all thirty-eight of them.

The model is right: these columns always have a value, either supplied or from
their default. The database is brought into line rather than the annotations
loosened, because a nullable column with a default invites rows that are neither.

Safe on a table with no rows, and every column has a server_default, so there is
nothing to backfill.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OBSERVATION_COLUMNS = (
    "product_name",
    "tradition",
    "category",
    "price",
    "source_url",
    "presentation",
    "garment",
    "garment_colour",
    "backdrop",
    "description",
    "text_content",
    "subject_primary",
    "subject_terms",
    "depicts_people",
    "references_property",
    "property_name",
    "graphic_archetype",
    "layout_archetype",
    "integration",
    "element_shapes",
    "type_styles",
    "type_case",
    "type_effects",
    "type_lines",
    "palette_terms",
    "print_effect",
    "stroke",
    "detail_density",
    "bare_zones",
    "described_at",
    "confidence",
    "notes",
    "raw",
    "created_at",
    "updated_at",
)

ZONE_COLUMNS = (
    "scale_role",
    "hierarchy",
    "description",
)


def upgrade() -> None:
    for column in OBSERVATION_COLUMNS:
        op.alter_column("design_observations", column, nullable=False)
    for column in ZONE_COLUMNS:
        op.alter_column("observation_zones", column, nullable=False)


def downgrade() -> None:
    for column in OBSERVATION_COLUMNS:
        op.alter_column("design_observations", column, nullable=True)
    for column in ZONE_COLUMNS:
        op.alter_column("observation_zones", column, nullable=True)
