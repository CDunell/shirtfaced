"""email contacts consent suppressions and messages

Revision ID: 0021
Revises: 0020
Create Date: 2026-08-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    email_purpose = postgresql.ENUM(
        "transactional", "marketing", name="email_purpose", create_type=False
    )
    consent_state = postgresql.ENUM(
        "subscribed", "unsubscribed", name="email_consent_state", create_type=False
    )
    suppression_scope = postgresql.ENUM(
        "global", "marketing", name="email_suppression_scope", create_type=False
    )
    suppression_reason = postgresql.ENUM(
        "unsubscribe",
        "hard_bounce",
        "complaint",
        "manual",
        "legal",
        name="email_suppression_reason",
        create_type=False,
    )
    message_state = postgresql.ENUM(
        "preview",
        "queued",
        "sending",
        "sent",
        "failed",
        "blocked",
        name="email_message_state",
        create_type=False,
    )
    for enum_type in (
        email_purpose,
        consent_state,
        suppression_scope,
        suppression_reason,
        message_state,
    ):
        enum_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "email_contacts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("customer_ref", sa.String(length=200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_email_contacts_customer_ref", "email_contacts", ["customer_ref"])

    op.create_table(
        "email_consent_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("purpose", email_purpose, nullable=False),
        sa.Column("state", consent_state, nullable=False),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("source_detail", sa.String(length=500), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["contact_id"], ["email_contacts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_consent_contact_purpose_time",
        "email_consent_events",
        ["contact_id", "purpose", sa.text("occurred_at DESC")],
    )

    op.create_table(
        "email_suppressions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scope", suppression_scope, nullable=False),
        sa.Column("reason", suppression_reason, nullable=False),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["contact_id"], ["email_contacts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_email_suppressions_contact_scope",
        "email_suppressions",
        ["contact_id", "scope"],
    )

    op.create_table(
        "email_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recipient_email", sa.String(length=320), nullable=False),
        sa.Column("purpose", email_purpose, nullable=False),
        sa.Column("template_key", sa.String(length=160), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=False),
        sa.Column("text_body", sa.Text(), nullable=False),
        sa.Column("state", message_state, server_default="preview", nullable=False),
        sa.Column("adapter", sa.String(length=120), nullable=True),
        sa.Column("external_message_id", sa.String(length=240), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column(
            "delivery_receipt",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["contact_id"], ["email_contacts.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_message_id"),
    )
    op.create_index(
        "ix_email_messages_state_created_at",
        "email_messages",
        ["state", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_email_messages_contact_created_at",
        "email_messages",
        ["contact_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_table("email_messages")
    op.drop_table("email_suppressions")
    op.drop_table("email_consent_events")
    op.drop_index("ix_email_contacts_customer_ref", table_name="email_contacts")
    op.drop_table("email_contacts")
    for name in (
        "email_message_state",
        "email_suppression_reason",
        "email_suppression_scope",
        "email_consent_state",
        "email_purpose",
    ):
        postgresql.ENUM(name=name).drop(op.get_bind(), checkfirst=True)
