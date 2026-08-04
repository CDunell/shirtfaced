"""generation attempts and image assets

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-05

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

ATTEMPT_STATE = sa.Enum(
    "planned",
    "prompt_ready",
    "generating",
    "generated",
    "reviewing",
    "awaiting_decision",
    "approved",
    "rejected",
    "failed",
    name="attempt_state",
)
FAILURE_CODE = sa.Enum(
    "planning_failed",
    "provider_error",
    "provider_timeout",
    "provider_refused",
    "invalid_image",
    "storage_failed",
    "configuration",
    "internal",
    name="failure_code",
)
ASSET_KIND = sa.Enum("original", "thumbnail", "reference", name="asset_kind")

# An attempt in one of these states occupies its world; the partial unique index
# below permits only one at a time.
ACTIVE_STATES_PREDICATE = (
    "state IN ('planned', 'prompt_ready', 'generating', 'generated', "
    "'reviewing', 'awaiting_decision')"
)

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "generation_attempts",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("world_id", sa.UUID(), nullable=False),
        sa.Column("shot_id", sa.UUID(), nullable=False),
        sa.Column("parent_attempt_id", sa.UUID(), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column(
            "state",
            sa.Enum(
                "planned",
                "prompt_ready",
                "generating",
                "generated",
                "reviewing",
                "awaiting_decision",
                "approved",
                "rejected",
                "failed",
                name="attempt_state",
            ),
            server_default="planned",
            nullable=False,
        ),
        sa.Column("selection_reason", sa.Text(), nullable=True),
        sa.Column("production_prompt", sa.Text(), nullable=True),
        sa.Column("prompt_plan_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("image_model", sa.String(length=120), nullable=True),
        sa.Column("image_size", sa.String(length=32), nullable=True),
        sa.Column("image_quality", sa.String(length=32), nullable=True),
        sa.Column("image_format", sa.String(length=16), nullable=True),
        sa.Column("provider_request_id", sa.String(length=120), nullable=True),
        sa.Column("hero_product", sa.String(length=120), nullable=True),
        sa.Column("camera_position", sa.String(length=120), nullable=True),
        sa.Column("world_document_hash", sa.String(length=64), nullable=True),
        sa.Column("continuity_document_hash", sa.String(length=64), nullable=True),
        sa.Column("shotlist_document_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "failure_code",
            sa.Enum(
                "planning_failed",
                "provider_error",
                "provider_timeout",
                "provider_refused",
                "invalid_image",
                "storage_failed",
                "configuration",
                "internal",
                name="failure_code",
            ),
            nullable=True,
        ),
        sa.Column("failure_message", sa.Text(), nullable=True),
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
            ["parent_attempt_id"],
            ["generation_attempts.id"],
            name=op.f("fk_generation_attempts_parent_attempt_id_generation_attempts"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["shot_id"],
            ["shots.id"],
            name=op.f("fk_generation_attempts_shot_id_shots"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worlds.id"],
            name=op.f("fk_generation_attempts_world_id_worlds"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generation_attempts")),
        sa.UniqueConstraint(
            "shot_id", "attempt_number", name="uq_generation_attempts_shot_id_attempt_number"
        ),
    )
    op.create_index(
        "ix_generation_attempts_world_id_created_at",
        "generation_attempts",
        ["world_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "uq_generation_attempts_one_active_per_world",
        "generation_attempts",
        ["world_id"],
        unique=True,
        postgresql_where=sa.text(ACTIVE_STATES_PREDICATE),
    )
    op.create_table(
        "image_assets",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("attempt_id", sa.UUID(), nullable=False),
        sa.Column(
            "kind", sa.Enum("original", "thumbnail", "reference", name="asset_kind"), nullable=False
        ),
        sa.Column("relative_path", sa.String(length=512), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["generation_attempts.id"],
            name=op.f("fk_image_assets_attempt_id_generation_attempts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_image_assets")),
        sa.UniqueConstraint("attempt_id", "kind", name="uq_image_assets_attempt_id_kind"),
    )


def downgrade() -> None:
    op.drop_table("image_assets")
    op.drop_index(
        "uq_generation_attempts_one_active_per_world",
        table_name="generation_attempts",
        postgresql_where=sa.text(ACTIVE_STATES_PREDICATE),
    )
    op.drop_index("ix_generation_attempts_world_id_created_at", table_name="generation_attempts")
    op.drop_table("generation_attempts")
    # drop_table does not remove enum types, so they are dropped explicitly.
    for enum in (ASSET_KIND, FAILURE_CODE, ATTEMPT_STATE):
        enum.drop(op.get_bind(), checkfirst=True)
