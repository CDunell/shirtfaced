"""design reviews, and a library for research-born concepts

Revision ID: 0027
Revises: 0026
Create Date: 2026-08-14

Two changes, both from Phase 1 of ``studio/docs/DESIGN_FLOW_PLAN.md``.

**``design_reviews``** closes what the 14 August audit called the blocking gap.
``design_extraction`` measures one category honestly and leaves the rest
untested, which correctly blocks release -- but nothing could answer the
scorecard's human questions, so a complete review could never be assembled and
no design could pass. Not one, ever, by construction. This is where those
answers live: thirteen gates, nine categories, the measurement they sit beside,
and the verdict the scorecard's own arithmetic reaches on them.

One row per attempt, enforced by a unique constraint rather than by convention.
A review is a working document while the attempt is undecided -- answering
three more gates updates it -- and ``design_scoring.score_design`` freezes it
the moment a ``design_decisions`` row exists, because what justified a decision
has to stay readable exactly as it was.

``evaluation`` keeps the computed verdict beside the raw answers deliberately.
The arithmetic is deterministic and could be recomputed at read time, but the
thresholds are explicitly calibratable (``DESIGN_REVIEW_SCORECARD.md`` §12), so
recomputing next year would silently re-judge this year's decisions against
numbers nobody applied at the time.

**``concept_library`` gains ``vintage_research``.** Phase 1 lets a research
concept become a numbered design concept, and those numbers need somewhere to
live. Not a high band of tee numbers: ``concept_importer`` matches on
``(library, external_number)`` and updates the authored fields of whatever it
matches, so a research concept holding the next free tee number would have its
title and text silently overwritten the day the Markdown grew to that number.
Nothing imports this library, so nothing can collide with it.

Adding a value to an existing enum is not transactional on PostgreSQL before
12, and is not reversible on any version -- the downgrade leaves the value in
place and says so rather than rebuilding the type underneath live rows.

Nothing exotic: uuid, jsonb, timestamptz, double precision and one partial
index, all on the supported list in ORACLE_CLOUD_DEPLOYMENT.md for PostgreSQL
15. No CREATE EXTENSION -- the application role is not superuser.

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # IF NOT EXISTS so a re-run is a no-op rather than a failure; the deploy
    # runs migrations on every push and a half-applied revision must be safe to
    # retry.
    op.execute("ALTER TYPE concept_library ADD VALUE IF NOT EXISTS 'vintage_research'")

    op.create_table(
        "design_reviews",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("design_attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer", sa.String(length=64), nullable=False),
        sa.Column(
            "measurements",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "hard_gates",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "score_categories",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("rationale", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "requested_decision",
            sa.String(length=32),
            server_default="design_approved",
            nullable=False,
        ),
        sa.Column(
            "evaluation",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("total_score", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("percentage", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("band", sa.String(length=32), server_default="", nullable=False),
        sa.Column(
            "eligible_for_design_approval",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=True),
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
            ["design_attempt_id"],
            ["design_attempts.id"],
            name="fk_design_reviews_design_attempt_id_design_attempts",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_design_reviews"),
        sa.UniqueConstraint("design_attempt_id", name="uq_design_reviews_design_attempt_id"),
        # A review nobody signed is an assertion, not a review -- the same rule
        # design_decisions applies to its actor.
        sa.CheckConstraint("reviewer <> ''", name="review_has_a_reviewer"),
        sa.CheckConstraint(
            "percentage >= 0 AND percentage <= 100", name="percentage_is_a_percentage"
        ),
    )
    op.create_index(
        "ix_design_reviews_eligible",
        "design_reviews",
        ["updated_at"],
        unique=False,
        postgresql_where=sa.text("eligible_for_design_approval"),
    )


def downgrade() -> None:
    op.drop_index("ix_design_reviews_eligible", table_name="design_reviews")
    op.drop_table("design_reviews")
    # 'vintage_research' is left in concept_library. Removing an enum value
    # means rebuilding the type and rewriting every column that uses it, which
    # would take a lock over design_concepts to undo an addition that breaks
    # nothing by remaining. An unused enum value is inert.
