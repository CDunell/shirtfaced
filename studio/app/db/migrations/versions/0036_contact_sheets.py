"""contact sheets, and coverage that is extracted rather than cropped

Revision ID: 0036
Revises: 0035
Create Date: 2026-08-18

``docs/stage-2/social-ai-production/NANO_BANANA_CONTACT_SHEET_PIPELINE.md`` is
an ACTIVE production contract, and its §8 retires the route 0033 modelled:

    approved 16:9 master + focus -> deterministic 9:16 crop -> Veo

becomes

    approved master + approved character refs -> Nano 3x3 coverage contact
    sheet -> selected-panel extraction at target aspect ratio -> review -> Veo

The difference is not cosmetic. An extraction is generated, not cut: it has no
crop box, its bytes are its own, and its parent is the contact sheet rather than
the master. Coordinates cannot identify it and cannot reproduce it. A panel
number can, which is why one is stored.

So this revision:

* adds ``scene_contact_sheets`` -- the 3x3 sheet as a first-class persisted
  artefact, not a disposable preview (§6 is explicit about that), carrying the
  prompt template version and the resolved scene prompt it was made from;
* makes ``coverage_frames``' crop box nullable and adds ``contact_sheet_id`` and
  ``panel``, so one row covers both a literal crop and a Nano extraction, with
  ``operation`` saying which;
* keeps the crop path intact. §8 supersedes it for the Nano route, not
  everywhere, and a deterministic crop is still the cheapest way to get an exact
  observation out of an image nobody needs to regenerate.

Character contact sheets need no schema: a cast reference role is free text, so
one files as ``contact_sheet`` against the member today. Per the owner's
ruling of 18 August 2026 they are per character, not per character-and-
appearance-state.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0036"
down_revision: str | None = "0035"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())
UUID = postgresql.UUID(as_uuid=True)


def _timestamps() -> tuple[sa.Column[Any], sa.Column[Any]]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def upgrade() -> None:
    for event in ("contact_sheet_registered", "contact_sheet_approved"):
        op.execute(f"ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS '{event}'")

    op.create_table(
        "scene_contact_sheets",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("scene_master_id", UUID, nullable=False),
        sa.Column("visual_asset_id", UUID, nullable=False),
        sa.Column("label", sa.String(length=96), nullable=False),
        sa.Column("rows", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.Column("columns", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="candidate", nullable=False),
        # §6: the prompt that produced it, and the exact reference manifest. The
        # manifest is also asset_lineage edges; this is the human-readable copy
        # that survives a reader who has only the sheet in front of them.
        sa.Column("prompt_template", sa.String(length=200), nullable=True),
        sa.Column("resolved_prompt_sha256", sa.String(length=64), nullable=True),
        sa.Column("panel_plan", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(length=64), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_scene_contact_sheets"),
        sa.ForeignKeyConstraint(
            ["scene_master_id"],
            ["scene_masters.id"],
            name="fk_scene_contact_sheets_scene_master_id_scene_masters",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["visual_asset_id"],
            ["visual_assets.id"],
            name="fk_scene_contact_sheets_visual_asset_id_visual_assets",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("visual_asset_id", name="uq_scene_contact_sheets_visual_asset_id"),
        sa.CheckConstraint(
            "status IN ('candidate','approved','superseded','rejected')", name="status_known"
        ),
        sa.CheckConstraint("rows > 0 AND columns > 0", name="grid_positive"),
    )
    # One approved sheet per master: the selected observation has one authority,
    # the same rule as one approved master per scene.
    op.create_index(
        "uq_scene_contact_sheets_one_approved_per_master",
        "scene_contact_sheets",
        ["scene_master_id"],
        unique=True,
        postgresql_where=sa.text("status = 'approved'"),
    )

    # A crop has coordinates; an extraction has a panel. Neither is universal.
    for column in ("x", "y", "width", "height"):
        op.alter_column("coverage_frames", column, nullable=True)

    op.add_column("coverage_frames", sa.Column("contact_sheet_id", UUID, nullable=True))
    op.add_column("coverage_frames", sa.Column("panel", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_coverage_frames_contact_sheet_id_scene_contact_sheets",
        "coverage_frames",
        "scene_contact_sheets",
        ["contact_sheet_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    # One panel is one shot. Two rows claiming panel 4 would put the choice of
    # "which panel 4" back on a person at the moment of spending money.
    op.create_index(
        "uq_coverage_frames_contact_sheet_id_panel",
        "coverage_frames",
        ["contact_sheet_id", "panel"],
        unique=True,
        postgresql_where=sa.text("contact_sheet_id IS NOT NULL"),
    )
    op.create_check_constraint(
        "crop_or_panel",
        "coverage_frames",
        # A crop needs its whole box. An extraction needs a sheet and a panel.
        "(x IS NOT NULL AND y IS NOT NULL AND width IS NOT NULL AND height IS NOT NULL)"
        " OR (contact_sheet_id IS NOT NULL AND panel IS NOT NULL)",
    )
    op.create_check_constraint("panel_positive", "coverage_frames", "panel IS NULL OR panel > 0")


def downgrade() -> None:
    op.drop_constraint("panel_positive", "coverage_frames", type_="check")
    op.drop_constraint("crop_or_panel", "coverage_frames", type_="check")
    op.drop_index("uq_coverage_frames_contact_sheet_id_panel", table_name="coverage_frames")
    op.drop_constraint(
        "fk_coverage_frames_contact_sheet_id_scene_contact_sheets",
        "coverage_frames",
        type_="foreignkey",
    )
    op.drop_column("coverage_frames", "panel")
    op.drop_column("coverage_frames", "contact_sheet_id")

    # Extractions have no crop box, so the columns cannot go back to NOT NULL
    # while any exist. Refuse rather than invent coordinates for them.
    op.execute(
        sa.text(
            "DELETE FROM coverage_frames WHERE x IS NULL OR y IS NULL "
            "OR width IS NULL OR height IS NULL"
        )
    )
    for column in ("x", "y", "width", "height"):
        op.alter_column("coverage_frames", column, nullable=False)

    op.drop_index(
        "uq_scene_contact_sheets_one_approved_per_master", table_name="scene_contact_sheets"
    )
    op.drop_table("scene_contact_sheets")
