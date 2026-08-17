"""visual asset library and canonical cast

Revision ID: 0031
Revises: 0030
Create Date: 2026-08-17

Phase 1 of ``studio/docs/VISUAL_ASSET_LIBRARY.md`` §14: the asset substrate and
the cast domain that sits on it. Locations, scene masters and coverage frames
are later phases and are deliberately not created here -- an empty table is a
claim that something is built.

Two departures from the document, both because it proposes a table that already
exists:

* ``characters`` was added by 0029 and is campaign-scoped, cascading away with
  the campaign. Canonical cast outlives campaigns, so this revision adds
  ``cast_members`` (world-scoped, world nullable for reusable cast) and gives
  ``characters`` a nullable ``cast_member_id`` saying which real person a story
  role is cast as. The alternative -- making ``characters.campaign_id``
  nullable -- would have silently disabled the composite foreign keys that
  0029's appearance and scene tables depend on.
* ``rights_status`` reuses the existing ``licence_status`` type rather than
  introducing a second three-state rights vocabulary.

``image_assets`` is untouched. Its ``attempt_id`` is NOT NULL and means "a
provider produced this", which an uploaded photograph did not.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0031"
down_revision: str | None = "0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())
UUID = postgresql.UUID(as_uuid=True)

visual_asset_kind = postgresql.ENUM(
    "cast",
    "location",
    "scene_master",
    "coverage",
    "prop",
    "reference",
    "other",
    name="visual_asset_kind",
    create_type=False,
)
visual_asset_source_type = postgresql.ENUM(
    "upload",
    "generated",
    "edited",
    "imported",
    "commissioned",
    "licensed_stock",
    name="visual_asset_source_type",
    create_type=False,
)
visual_asset_status = postgresql.ENUM(
    "pending",
    "approved",
    "deprecated",
    "rejected",
    name="visual_asset_status",
    create_type=False,
)
# Created by 0014 for archive elements. Referenced, never recreated.
licence_status = postgresql.ENUM(name="licence_status", create_type=False)


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
    bind = op.get_bind()
    visual_asset_kind.create(bind, checkfirst=True)
    visual_asset_source_type.create(bind, checkfirst=True)
    visual_asset_status.create(bind, checkfirst=True)

    # Adding a member to a Python enum does nothing to the database.
    for event in (
        "visual_asset_ingested",
        "visual_asset_approved",
        "visual_asset_deprecated",
        "visual_asset_rejected",
        "cast_asset_linked",
    ):
        op.execute(f"ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS '{event}'")

    op.create_table(
        "visual_assets",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("kind", visual_asset_kind, nullable=False),
        sa.Column("role", sa.String(length=64), nullable=True),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("source_type", visual_asset_source_type, nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("provider_request_id", sa.String(length=128), nullable=True),
        sa.Column("prompt_hash", sa.String(length=64), nullable=True),
        sa.Column("status", visual_asset_status, server_default="pending", nullable=False),
        sa.Column("rights_status", licence_status, server_default="unverified", nullable=False),
        sa.Column("rights_metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("metadata_json", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(length=64), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_visual_assets"),
        # Exact-byte dedupe, §9. Ingesting the same file twice must resolve to
        # one identity, or two scene masters can cite "different" references
        # that are the same photograph.
        sa.UniqueConstraint("sha256", name="uq_visual_assets_sha256"),
        sa.CheckConstraint("width > 0 AND height > 0", name="dimensions_positive"),
        sa.CheckConstraint("byte_size > 0", name="byte_size_positive"),
    )
    op.create_index("ix_visual_assets_kind_status", "visual_assets", ["kind", "status"])
    op.create_index("ix_visual_assets_source_type", "visual_assets", ["source_type"])
    op.create_index("ix_visual_assets_rights_status", "visual_assets", ["rights_status"])

    op.create_table(
        "asset_lineage",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("parent_asset_id", UUID, nullable=False),
        sa.Column("child_asset_id", UUID, nullable=False),
        sa.Column("relationship", sa.String(length=48), nullable=False),
        sa.Column(
            "operation_metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_asset_lineage"),
        # RESTRICT on the parent: a master whose coverage frames exist cannot be
        # deleted out from under them, §12.
        sa.ForeignKeyConstraint(
            ["parent_asset_id"],
            ["visual_assets.id"],
            name="fk_asset_lineage_parent_asset_id_visual_assets",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["child_asset_id"],
            ["visual_assets.id"],
            name="fk_asset_lineage_child_asset_id_visual_assets",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "parent_asset_id",
            "child_asset_id",
            "relationship",
            name="uq_asset_lineage_parent_asset_id_child_asset_id_relationship",
        ),
        sa.CheckConstraint(
            "parent_asset_id <> child_asset_id", name="no_self_lineage"
        ),
    )
    op.create_index("ix_asset_lineage_child_asset_id", "asset_lineage", ["child_asset_id"])

    op.create_table(
        "cast_members",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        # Nullable: cast reusable across worlds, §5.1.
        sa.Column("world_id", UUID, nullable=True),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "canonical_metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_cast_members"),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worlds.id"],
            name="fk_cast_members_world_id_worlds",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("world_id", "slug", name="uq_cast_members_world_id_slug"),
        sa.CheckConstraint(
            "status IN ('active','deprecated')", name="status_known"
        ),
    )
    op.create_index("ix_cast_members_status", "cast_members", ["status"])

    op.create_table(
        "cast_member_assets",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cast_member_id", UUID, nullable=False),
        sa.Column("visual_asset_id", UUID, nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_cast_member_assets"),
        sa.ForeignKeyConstraint(
            ["cast_member_id"],
            ["cast_members.id"],
            name="fk_cast_member_assets_cast_member_id_cast_members",
            ondelete="CASCADE",
        ),
        # RESTRICT: detaching a reference must not be a way to destroy an asset
        # a scene master already cites.
        sa.ForeignKeyConstraint(
            ["visual_asset_id"],
            ["visual_assets.id"],
            name="fk_cast_member_assets_visual_asset_id_visual_assets",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "cast_member_id",
            "visual_asset_id",
            name="uq_cast_member_assets_cast_member_id_visual_asset_id",
        ),
    )
    # One primary per role per member: "the neutral head shot" must resolve to
    # exactly one asset, or the renderer picks by accident.
    op.create_index(
        "uq_cast_member_assets_primary_per_role",
        "cast_member_assets",
        ["cast_member_id", "role"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )
    op.create_index(
        "ix_cast_member_assets_visual_asset_id", "cast_member_assets", ["visual_asset_id"]
    )

    op.create_table(
        "tags",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tags"),
        sa.UniqueConstraint("slug", name="uq_tags_slug"),
    )

    op.create_table(
        "visual_asset_tags",
        sa.Column("visual_asset_id", UUID, nullable=False),
        sa.Column("tag_id", UUID, nullable=False),
        sa.PrimaryKeyConstraint("visual_asset_id", "tag_id", name="pk_visual_asset_tags"),
        sa.ForeignKeyConstraint(
            ["visual_asset_id"],
            ["visual_assets.id"],
            name="fk_visual_asset_tags_visual_asset_id_visual_assets",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"], ["tags.id"], name="fk_visual_asset_tags_tag_id_tags", ondelete="CASCADE"
        ),
    )

    # A campaign story role can now say which canonical person plays it. Left
    # null everywhere until someone casts it; nothing infers it from a handle.
    op.add_column("characters", sa.Column("cast_member_id", UUID, nullable=True))
    op.create_foreign_key(
        "fk_characters_cast_member_id_cast_members",
        "characters",
        "cast_members",
        ["cast_member_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_characters_cast_member_id", "characters", ["cast_member_id"])


def downgrade() -> None:
    op.drop_index("ix_characters_cast_member_id", table_name="characters")
    op.drop_constraint(
        "fk_characters_cast_member_id_cast_members", "characters", type_="foreignkey"
    )
    op.drop_column("characters", "cast_member_id")

    op.drop_table("visual_asset_tags")
    op.drop_table("tags")
    op.drop_index("ix_cast_member_assets_visual_asset_id", table_name="cast_member_assets")
    op.drop_index("uq_cast_member_assets_primary_per_role", table_name="cast_member_assets")
    op.drop_table("cast_member_assets")
    op.drop_index("ix_cast_members_status", table_name="cast_members")
    op.drop_table("cast_members")
    op.drop_index("ix_asset_lineage_child_asset_id", table_name="asset_lineage")
    op.drop_table("asset_lineage")
    op.drop_index("ix_visual_assets_rights_status", table_name="visual_assets")
    op.drop_index("ix_visual_assets_source_type", table_name="visual_assets")
    op.drop_index("ix_visual_assets_kind_status", table_name="visual_assets")
    op.drop_table("visual_assets")

    bind = op.get_bind()
    visual_asset_status.drop(bind, checkfirst=True)
    visual_asset_source_type.drop(bind, checkfirst=True)
    visual_asset_kind.drop(bind, checkfirst=True)
    # audit_event_type keeps its new members: PostgreSQL cannot remove enum
    # values, and rows recording what happened are not rewritten by a downgrade.
