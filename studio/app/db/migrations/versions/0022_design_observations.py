"""design observations from the visual pass over the corpus

Revision ID: 0022
Revises: 0021
Create Date: 2026-08-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "design_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("image_path", sa.Text(), nullable=False),
        sa.Column("corpus", sa.String(32), nullable=False),
        sa.Column("brand_slug", sa.String(64), nullable=False),
        sa.Column("product_slug", sa.String(128), nullable=False),
        sa.Column("product_name", sa.Text(), server_default=""),
        sa.Column("tradition", sa.String(48), server_default=""),
        sa.Column("category", sa.String(48), server_default=""),
        sa.Column("price", sa.String(32), server_default=""),
        sa.Column("source_url", sa.Text(), server_default=""),
        sa.Column("presentation", sa.String(32), server_default=""),
        sa.Column("garment", sa.Text(), server_default=""),
        sa.Column("garment_colour", sa.String(64), server_default=""),
        sa.Column("backdrop", sa.String(64), server_default=""),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("text_content", sa.Text(), server_default=""),
        sa.Column("subject_primary", sa.String(32), server_default=""),
        sa.Column("subject_terms", postgresql.ARRAY(sa.Text()), server_default="{}"),
        sa.Column("depicts_people", sa.Boolean(), server_default=sa.false()),
        sa.Column("references_property", sa.Boolean(), server_default=sa.false()),
        sa.Column("property_name", sa.Text(), server_default=""),
        sa.Column("construction", sa.String(32), server_default=""),
        sa.Column("integration", sa.String(32), server_default=""),
        sa.Column("element_shapes", postgresql.ARRAY(sa.Text()), server_default="{}"),
        sa.Column("type_styles", postgresql.ARRAY(sa.Text()), server_default="{}"),
        sa.Column("type_case", sa.String(16), server_default=""),
        sa.Column("type_effects", postgresql.ARRAY(sa.Text()), server_default="{}"),
        sa.Column("type_lines", sa.Integer(), server_default="0"),
        sa.Column("palette_terms", postgresql.ARRAY(sa.Text()), server_default="{}"),
        sa.Column("print_effect", sa.String(32), server_default=""),
        sa.Column("stroke", sa.String(16), server_default=""),
        sa.Column("detail_density", sa.String(16), server_default=""),
        sa.Column("bare_zones", postgresql.ARRAY(sa.Text()), server_default="{}"),
        sa.Column("symmetry", sa.Float(), nullable=True),
        sa.Column("containment", sa.Float(), nullable=True),
        sa.Column("ink_count", sa.Integer(), nullable=True),
        sa.Column("aspect", sa.Float(), nullable=True),
        sa.Column("described_by", sa.String(64), nullable=False),
        sa.Column("described_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("confidence", sa.String(8), server_default="medium"),
        sa.Column("notes", sa.Text(), server_default=""),
        sa.Column("raw", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "image_path", "described_by", name="uq_design_observations_image_model"
        ),
        sa.CheckConstraint(
            "confidence <> 'high' OR (subject_primary <> '' AND description <> '')",
            name="confident_rows_are_complete",
        ),
        sa.CheckConstraint("confidence IN ('high', 'medium', 'low')", name="confidence_known"),
    )
    op.create_index("ix_design_observations_brand", "design_observations", ["brand_slug"])
    op.create_index("ix_design_observations_tradition", "design_observations", ["tradition"])

    op.create_table(
        "observation_zones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "observation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("design_observations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("zone", sa.String(32), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("fill", sa.String(16), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.UniqueConstraint("observation_id", "zone", name="uq_observation_zones_zone"),
        sa.CheckConstraint(
            "zone IN ('full_front','full_back','centre_chest','centre_back','left_chest',"
            "'upper_back_yoke','outer_back_neck','inner_neck_label','short_sleeve',"
            "'long_sleeve','pocket','cap_front','cap_side','cap_back')",
            name="zone_known",
        ),
        sa.CheckConstraint(
            "state IN ('bare','image_only','text_only','image_and_text')",
            name="zone_state_known",
        ),
        sa.CheckConstraint(
            "fill IN ('trace','quarter','half','most','full','bleeds')",
            name="zone_fill_known",
        ),
    )
    op.create_index("ix_observation_zones_zone", "observation_zones", ["zone"])


def downgrade() -> None:
    op.drop_index("ix_observation_zones_zone", table_name="observation_zones")
    op.drop_table("observation_zones")
    op.drop_index("ix_design_observations_tradition", table_name="design_observations")
    op.drop_index("ix_design_observations_brand", table_name="design_observations")
    op.drop_table("design_observations")
