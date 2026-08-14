"""design briefs — the constitution's steps 1-4 and 6

Revision ID: 0028
Revises: 0027
Create Date: 2026-08-14

Phase 4 of ``studio/docs/DESIGN_FLOW_PLAN.md``. The 14 August audit found six of
the constitution's ten governing steps absent or unwired, and that the first
four are the ones that decide *what a product is* before any artwork exists:
define the product, define its role in the range, select the garment
architecture, select the graphic architecture. None had any representation in
software. The audit's words for the consequence: the research bench produces a
graphic idea and jumps straight to artwork, "which is why output arrives as
competent generic work with no collection role and no declared archetype".

One row per concept. §3's required fields -- blank, fit, weight, colour, wash,
method -- describe the long-lived product idea rather than one execution of it,
and ``create_attempt`` already snapshots the concept into ``brief_snapshot`` so
an attempt stays explicable after the brief changes.

**Two of the scorecard's thirteen hard gates get a source of truth for the first
time.** ``product_blank_defined`` and ``collection_role_defined`` were being
answered ``pass`` by a person with nothing in the software holding the answer --
recorded as the known limit of Phase 1, and closed here.

Three enums, all from the constitution rather than from ``domain.ts``:

* ``collection_role`` is §4's five — anchor, core, expression, hero,
  collaboration. ``domain.ts`` carried six, with ``staple`` and ``capsule`` and
  no ``anchor``. The constitution governs; see ADR-018.
* ``layout_archetype`` is §6's A1-A8.
* ``graphic_archetype`` is §8's nine dominant families.

Zones (§5) and typography (§10) are JSONB rather than columns: the zones a
garment has depend on the blank -- a cap has three panels, a hoodie has a
pocket -- and a column per zone is a table that changes shape every time a
blank is added.

Nothing exotic: uuid, jsonb, timestamptz and three enums, all on the supported
list in ORACLE_CLOUD_DEPLOYMENT.md for PostgreSQL 15. No CREATE EXTENSION --
the application role is not superuser.

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

collection_role = postgresql.ENUM(
    "anchor",
    "core",
    "expression",
    "hero",
    "collaboration",
    name="collection_role",
    create_type=False,
)
layout_archetype = postgresql.ENUM(
    "a1_small_front_large_back",
    "a2_front_hero_rear_signature",
    "a3_front_hero_clean_back",
    "a4_micro_front_back_hero",
    "a5_unequal_front_and_back",
    "a6_image_language_split",
    "a7_multi_zone",
    "a8_jumbo_field",
    name="layout_archetype",
    create_type=False,
)
graphic_archetype = postgresql.ENUM(
    "image_led_hero",
    "typographic_hero",
    "emblem_or_badge",
    "image_and_title_lockup",
    "poster_or_editorial",
    "symbolic_icon_system",
    "collage_controlled_frame",
    "character_or_object_portrait",
    "all_over_or_jumbo_field",
    name="graphic_archetype",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    collection_role.create(bind, checkfirst=True)
    layout_archetype.create(bind, checkfirst=True)
    graphic_archetype.create(bind, checkfirst=True)

    op.create_table(
        "design_briefs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Step 1 — define the product (§3).
        sa.Column("garment_category", sa.String(length=60), server_default="", nullable=False),
        sa.Column("canonical_blank", sa.String(length=120), server_default="", nullable=False),
        sa.Column("fit_block", sa.String(length=60), server_default="", nullable=False),
        sa.Column("fabric_weight", sa.String(length=60), server_default="", nullable=False),
        sa.Column("garment_colour", sa.String(length=60), server_default="", nullable=False),
        sa.Column("wash", sa.String(length=60), server_default="", nullable=False),
        sa.Column("production_method", sa.String(length=60), server_default="", nullable=False),
        sa.Column("intended_use", sa.Text(), server_default="", nullable=False),
        sa.Column("commercial_tier", sa.String(length=60), server_default="", nullable=False),
        sa.Column("target_release", sa.String(length=120), server_default="", nullable=False),
        # Steps 2 and 4 — nullable, because a brief is filled in over time. The
        # gate is that an attempt cannot open until both are set, not that a
        # draft brief cannot exist.
        sa.Column("collection_role", collection_role, nullable=True),
        sa.Column("graphic_archetype", graphic_archetype, nullable=True),
        sa.Column("layout_archetype", layout_archetype, nullable=True),
        sa.Column("archetype_departure_reason", sa.Text(), server_default="", nullable=False),
        # Step 3 — garment architecture (§5), zone key -> state.
        sa.Column(
            "zones",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        # Step 6 — typography by function (§10).
        sa.Column(
            "typography",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "advisor_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), server_default="", nullable=False),
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
        sa.ForeignKeyConstraint(
            ["concept_id"],
            ["design_concepts.id"],
            name="fk_design_briefs_concept_id_design_concepts",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_design_briefs"),
        sa.UniqueConstraint("concept_id", name="uq_design_briefs_concept_id"),
    )


def downgrade() -> None:
    op.drop_table("design_briefs")
    bind = op.get_bind()
    graphic_archetype.drop(bind, checkfirst=True)
    layout_archetype.drop(bind, checkfirst=True)
    collection_role.drop(bind, checkfirst=True)
