"""a contact sheet can be rejected, on the sheet and not only on its bytes

Revision ID: 0043
Revises: 0042
Create Date: 2026-08-18

The Scenes bench has had a Reject button on contact sheets since 0036. It
deprecated the sheet's *asset* and left ``scene_contact_sheets.status`` alone,
so a rejected candidate stayed a candidate forever, and a rejected approved
sheet stayed the one ``approved_contact_sheet`` resolves -- with deprecated
bytes behind it.

``status`` already permits ``rejected``; nothing ever wrote it. This adds the
audit event that records who said no, which is the half that needed a type
change.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0043"
down_revision: str | None = "0042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'contact_sheet_rejected'")


def downgrade() -> None:
    """Kept. PostgreSQL cannot drop an enum value without rewriting the type."""
