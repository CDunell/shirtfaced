"""social publishing

Revision ID: 0018
Revises: 0017
Create Date: 2026-08-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

social_post_state = postgresql.ENUM(
    "review_required", "approved", "rejected", "queued", "live", name="social_post_state"
)
publication_state = postgresql.ENUM(
    "queued", "scheduled", "held", "publishing", "published", "failed", "cancelled",
    name="publication_state",
)
social_channel = postgresql.ENUM(
    "instagram_feed", "instagram_story", "instagram_reel", "tiktok", name="social_channel"
)


def upgrade() -> None:
    bind = op.get_bind()
    social_post_state.create(bind, checkfirst=True)
    publication_state.create(bind, checkfirst=True)
    social_channel.create(bind, checkfirst=True)

    op.create_table(
        "social_posts",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("source_photo_id", sa.UUID(), nullable=False),
        sa.Column("theme", sa.String(length=32), nullable=False),
        sa.Column("branding", sa.String(length=32), nullable=False),
        sa.Column("caption", sa.Text(), server_default="", nullable=False),
        sa.Column("campaign_id", sa.UUID(), nullable=True),
        sa.Column("state", social_post_state, server_default="review_required", nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_photo_id"], ["photos.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_social_posts_state_created_at", "social_posts", ["state", sa.text("created_at DESC")])

    op.create_table(
        "social_derivatives",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("social_post_id", sa.UUID(), nullable=False),
        sa.Column("output_key", sa.String(length=64), nullable=False),
        sa.Column("channel", social_channel, nullable=False),
        sa.Column("relative_path", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=240), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["social_post_id"], ["social_posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("relative_path"),
    )
    op.create_index("ix_social_derivatives_post_id", "social_derivatives", ["social_post_id"])
    op.create_index("ix_social_derivatives_sha256", "social_derivatives", ["sha256"])

    op.create_table(
        "cadence_policies",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("minimum_spacing_minutes", sa.Integer(), server_default="1440", nullable=False),
        sa.Column("preferred_hour_local", sa.Integer(), server_default="19", nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "publication_jobs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("social_post_id", sa.UUID(), nullable=False),
        sa.Column("derivative_id", sa.UUID(), nullable=False),
        sa.Column("channel", social_channel, nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_timezone", sa.String(length=80), server_default="Australia/Brisbane", nullable=False),
        sa.Column("recommended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cadence_policy_id", sa.UUID(), nullable=True),
        sa.Column("locked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("state", publication_state, server_default="queued", nullable=False),
        sa.Column("external_post_id", sa.String(length=200), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["cadence_policy_id"], ["cadence_policies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["derivative_id"], ["social_derivatives.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["social_post_id"], ["social_posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_post_id"),
    )
    op.create_index("ix_publication_jobs_post_id", "publication_jobs", ["social_post_id"])
    op.create_index("ix_publication_jobs_state_scheduled_at", "publication_jobs", ["state", "scheduled_at"])

    op.execute(
        "INSERT INTO cadence_policies "
        "(name, minimum_spacing_minutes, preferred_hour_local, active) "
        "VALUES ('Default social cadence', 1440, 19, true)"
    )


def downgrade() -> None:
    op.drop_index("ix_publication_jobs_state_scheduled_at", table_name="publication_jobs")
    op.drop_index("ix_publication_jobs_post_id", table_name="publication_jobs")
    op.drop_table("publication_jobs")
    op.drop_table("cadence_policies")
    op.drop_index("ix_social_derivatives_sha256", table_name="social_derivatives")
    op.drop_index("ix_social_derivatives_post_id", table_name="social_derivatives")
    op.drop_table("social_derivatives")
    op.drop_index("ix_social_posts_state_created_at", table_name="social_posts")
    op.drop_table("social_posts")
    bind = op.get_bind()
    social_channel.drop(bind, checkfirst=True)
    publication_state.drop(bind, checkfirst=True)
    social_post_state.drop(bind, checkfirst=True)
