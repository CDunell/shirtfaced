"""human decisions and audit events

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-05

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

ENUMS = (
    sa.Enum("approved", "rejected", "variation_requested", name="human_decision_kind"),
    sa.Enum("not_attempted", "succeeded", "failed", name="sync_state"),
    sa.Enum(
        "decision_recorded",
        "markdown_updated",
        "markdown_failed",
        "world_reimported",
        "import_failed",
        "git_committed",
        "git_failed",
        "reference_promoted",
        "reference_failed",
        "reconciliation_required",
        name="audit_event_type",
    ),
)

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Alembic does not detect a new member of an existing enum, so the terminal
    # variation state is added explicitly (ADR-013). It sits outside the active-attempt
    # partial index, so requesting a variation releases the world.
    # PostgreSQL cannot remove an enum value; the downgrade leaves it in place.
    op.execute("ALTER TYPE attempt_state ADD VALUE IF NOT EXISTS 'variation_requested'")

    op.create_table(
        "audit_events",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("world_id", sa.UUID(), nullable=True),
        sa.Column("attempt_id", sa.UUID(), nullable=True),
        sa.Column(
            "event_type",
            sa.Enum(
                "decision_recorded",
                "markdown_updated",
                "markdown_failed",
                "world_reimported",
                "import_failed",
                "git_committed",
                "git_failed",
                "reference_promoted",
                "reference_failed",
                "reconciliation_required",
                name="audit_event_type",
            ),
            nullable=False,
        ),
        sa.Column("actor", sa.String(length=64), server_default=sa.text("'owner'"), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["generation_attempts.id"],
            name=op.f("fk_audit_events_attempt_id_generation_attempts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worlds.id"],
            name=op.f("fk_audit_events_world_id_worlds"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index("ix_audit_events_attempt_id", "audit_events", ["attempt_id"], unique=False)
    op.create_index(
        "ix_audit_events_world_id_created_at",
        "audit_events",
        ["world_id", sa.literal_column("created_at DESC")],
        unique=False,
    )
    op.create_table(
        "human_decisions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("attempt_id", sa.UUID(), nullable=False),
        sa.Column(
            "decision",
            sa.Enum("approved", "rejected", "variation_requested", name="human_decision_kind"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("instruction", sa.Text(), nullable=True),
        sa.Column(
            "promote_to_reference", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("actor", sa.String(length=64), server_default=sa.text("'owner'"), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column(
            "markdown_sync",
            sa.Enum("not_attempted", "succeeded", "failed", name="sync_state"),
            server_default="not_attempted",
            nullable=False,
        ),
        sa.Column(
            "git_sync",
            sa.Enum("not_attempted", "succeeded", "failed", name="sync_state"),
            server_default="not_attempted",
            nullable=False,
        ),
        sa.Column(
            "reference_sync",
            sa.Enum("not_attempted", "succeeded", "failed", name="sync_state"),
            server_default="not_attempted",
            nullable=False,
        ),
        sa.Column("git_commit", sa.String(length=64), nullable=True),
        sa.Column(
            "reconciliation_required", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("reconciliation_detail", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["generation_attempts.id"],
            name=op.f("fk_human_decisions_attempt_id_generation_attempts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_human_decisions")),
        sa.UniqueConstraint("attempt_id", name="uq_human_decisions_attempt_id"),
    )


def downgrade() -> None:
    op.drop_table("human_decisions")
    op.drop_index("ix_audit_events_world_id_created_at", table_name="audit_events")
    op.drop_index("ix_audit_events_attempt_id", table_name="audit_events")
    op.drop_table("audit_events")
    # drop_table does not remove enum types, so they are dropped explicitly.
    for enum in ENUMS:
        enum.drop(op.get_bind(), checkfirst=True)
