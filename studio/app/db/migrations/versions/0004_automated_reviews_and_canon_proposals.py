"""automated reviews and canon proposals

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-05

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

ENUMS = (
    sa.Enum("pending", "approved", "rejected", "applied", "failed", name="canon_proposal_status"),
    sa.Enum("approved", "approved_with_note", "rejected", "uncertain", name="review_verdict"),
    sa.Enum(
        "APPROVE_RECOMMENDED",
        "APPROVE_WITH_NOTE_RECOMMENDED",
        "REJECT_RECOMMENDED",
        "REVIEW_UNCERTAIN",
        name="review_recommendation",
    ),
)

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Adding a member to the Python enum does not change the PostgreSQL type, so the
    # review failure code is added explicitly. PostgreSQL cannot remove an enum value,
    # so the downgrade leaves it in place; an unused member is harmless.
    op.execute("ALTER TYPE failure_code ADD VALUE IF NOT EXISTS 'review_failed'")

    op.create_table(
        "automated_reviews",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("attempt_id", sa.UUID(), nullable=False),
        sa.Column("review_model", sa.String(length=120), nullable=False),
        sa.Column("schema_version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("provider_request_id", sa.String(length=120), nullable=True),
        sa.Column(
            "recommendation",
            sa.Enum(
                "APPROVE_RECOMMENDED",
                "APPROVE_WITH_NOTE_RECOMMENDED",
                "REJECT_RECOMMENDED",
                "REVIEW_UNCERTAIN",
                name="review_recommendation",
            ),
            nullable=False,
        ),
        sa.Column(
            "verdict",
            sa.Enum(
                "approved", "approved_with_note", "rejected", "uncertain", name="review_verdict"
            ),
            nullable=False,
        ),
        sa.Column("mood_score", sa.Integer(), nullable=False),
        sa.Column("australian_authenticity_score", sa.Integer(), nullable=False),
        sa.Column("product_visibility_score", sa.Integer(), nullable=False),
        sa.Column("documentary_credibility_score", sa.Integer(), nullable=False),
        sa.Column("story_score", sa.Integer(), nullable=False),
        sa.Column("branding_compliant", sa.Boolean(), nullable=False),
        sa.Column("vehicle_compliant", sa.Boolean(), nullable=False),
        sa.Column("strongest_success", sa.Text(), nullable=False),
        sa.Column("material_drift", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("next_hero_product", sa.String(length=120), nullable=True),
        sa.Column("next_camera", sa.String(length=120), nullable=True),
        sa.Column("raw_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("world_document_hash", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["generation_attempts.id"],
            name=op.f("fk_automated_reviews_attempt_id_generation_attempts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_automated_reviews")),
    )
    op.create_index(
        "ix_automated_reviews_attempt_id", "automated_reviews", ["attempt_id"], unique=False
    )
    op.create_table(
        "canon_proposals",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("world_id", sa.UUID(), nullable=False),
        sa.Column("attempt_id", sa.UUID(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "approved", "rejected", "applied", "failed", name="canon_proposal_status"
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("proposed_heading", sa.String(length=200), nullable=True),
        sa.Column("proposed_text", sa.Text(), nullable=False),
        sa.Column("insertion_anchor", sa.String(length=200), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("human_note", sa.Text(), nullable=True),
        sa.Column("git_commit", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["generation_attempts.id"],
            name=op.f("fk_canon_proposals_attempt_id_generation_attempts"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worlds.id"],
            name=op.f("fk_canon_proposals_world_id_worlds"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_canon_proposals")),
    )
    op.create_index(
        "ix_canon_proposals_world_id_status",
        "canon_proposals",
        ["world_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_canon_proposals_world_id_status", table_name="canon_proposals")
    op.drop_table("canon_proposals")
    op.drop_index("ix_automated_reviews_attempt_id", table_name="automated_reviews")
    op.drop_table("automated_reviews")
    # drop_table does not remove enum types, so they are dropped explicitly.
    for enum in ENUMS:
        enum.drop(op.get_bind(), checkfirst=True)
