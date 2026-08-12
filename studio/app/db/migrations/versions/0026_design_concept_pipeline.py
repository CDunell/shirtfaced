"""design concept pipeline

Revision ID: 0026
Revises: 0025
Create Date: 2026-08-12

The concept library in ``docs/design/TSHIRT_CONCEPT_LIBRARY.md`` holds 260
numbered ideas and no memory. Markdown cannot record that #4 has three attempts
and a rejection, "next" means whatever the last conversation remembered, and a
retired entry either lingers ambiguously or is deleted and renumbers everything
after it. The library stays -- it is the authored creative source -- but it
becomes the seed, and PostgreSQL becomes the queue. The same split the world
pipeline made between ``SHOTLIST.md`` and ``shots``.

Six tables carry the lineage the audit called missing: concept -> attempt ->
asset -> decision -> approved version -> product link. The concept is the
long-lived idea and its ``external_number`` is permanent: #1 stays #1, retired
entries remain rows rather than gaps. The attempt is one execution. The asset
is one set of bytes. The approved design is the frozen production milestone,
and the only thing allowed downstream -- which is what stops "we made an image"
being read as "that design is finished". ``product_links`` is a soft reference
into the shop's separate database: an identifier and a sync state, never a
cross-database foreign key.

``design_attempt_state`` is a fresh type rather than a reuse of
``attempt_state``. Migration 0017 taught ``composed_designs`` to share the
photography enum, which means any value added for designs would silently widen
the photography pipeline's vocabulary too -- and a design attempt has no
``prompt_ready`` or ``reviewing`` in any case. ``design_decision_kind`` is
separate from ``human_decision_kind`` for the same reason, even though the
values are identical today.

``composed_designs`` gains a nullable ``design_attempt_id`` so the
deterministic composer becomes a producer feeding attempts rather than a
parallel universe. Null stays legitimate: every design composed before this
migration is standalone, and remains so.

Nothing exotic: uuid, jsonb, timestamptz, arrays and partial indexes, all on
the supported list in ORACLE_CLOUD_DEPLOYMENT.md for PostgreSQL 15. No
CREATE EXTENSION -- the application role is not superuser.

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

concept_library = postgresql.ENUM(
    "tshirt",
    "headwear",
    "brand_garment",
    name="concept_library",
    create_type=False,
)
concept_status = postgresql.ENUM(
    "backlog",
    "ready",
    "exploring",
    "approved",
    "rejected",
    "held",
    "retired",
    "superseded",
    name="concept_status",
    create_type=False,
)
concept_kind = postgresql.ENUM(
    "image",
    "typography",
    "mixed",
    "garment_led",
    "other",
    name="concept_kind",
    create_type=False,
)
design_attempt_method = postgresql.ENUM(
    "image_generation",
    "deterministic_composition",
    "manual_import",
    "hybrid",
    name="design_attempt_method",
    create_type=False,
)
design_attempt_state = postgresql.ENUM(
    "planned",
    "generating",
    "generated",
    "awaiting_decision",
    "approved",
    "rejected",
    "variation_requested",
    "failed",
    name="design_attempt_state",
    create_type=False,
)
design_decision_kind = postgresql.ENUM(
    "approved",
    "rejected",
    "variation_requested",
    name="design_decision_kind",
    create_type=False,
)
design_asset_kind = postgresql.ENUM(
    "artwork",
    "preview",
    "print_master",
    "separation",
    "source",
    "mockup",
    name="design_asset_kind",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    concept_library.create(bind, checkfirst=True)
    concept_status.create(bind, checkfirst=True)
    concept_kind.create(bind, checkfirst=True)
    design_attempt_method.create(bind, checkfirst=True)
    design_attempt_state.create(bind, checkfirst=True)
    design_decision_kind.create(bind, checkfirst=True)
    design_asset_kind.create(bind, checkfirst=True)

    # Design events go into the existing audit trail rather than a new outbox
    # table: an outbox with no consumer is speculative. Adding an enum member
    # in Python does nothing to the database -- both 0004 and 0005 learned
    # this -- so the type is widened here explicitly.
    op.execute("ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'design_decision_recorded'")
    op.execute("ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'design_approved'")

    op.create_table(
        "design_concepts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("library", concept_library, nullable=False),
        # The number in the source document. Permanent: #1 stays #1 forever.
        sa.Column("external_number", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        # Authored fields: the importer owns these.
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("concept_text", sa.Text(), nullable=False),
        sa.Column("retirement", sa.String(length=16), nullable=False, server_default=""),
        sa.Column(
            "garments",
            postgresql.ARRAY(sa.String(length=16)),
            nullable=False,
            server_default=sa.text("'{}'::varchar[]"),
        ),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("round_label", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("source_path", sa.String(length=512), nullable=False),
        sa.Column("source_line", sa.Integer(), nullable=True),
        sa.Column("source_document_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "parsed_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        # Workflow fields: the owner owns these, and import never touches them.
        sa.Column("status", concept_status, nullable=False, server_default="backlog"),
        sa.Column("concept_kind", concept_kind, nullable=False, server_default="other"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column(
            "treatment_lanes",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column(
            "preferred_execution",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "integral_text",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "constraints",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "library", "external_number", name="uq_design_concepts_library_external_number"
        ),
        sa.UniqueConstraint("slug", name="uq_design_concepts_slug"),
        sa.CheckConstraint("external_number >= 1", name="external_number_positive"),
        sa.CheckConstraint(
            "retirement IN ('', 'hard', 'unconditional', 'conditional')",
            name="retirement_known",
        ),
    )
    op.create_index("ix_design_concepts_status", "design_concepts", ["status"])
    # Partial: "what is next" only reads the undone end of the queue.
    op.create_index(
        "ix_design_concepts_queue",
        "design_concepts",
        ["library", "priority", "external_number"],
        postgresql_where=sa.text("status IN ('backlog', 'ready')"),
    )

    op.create_table(
        "design_attempts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_attempt_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("method", design_attempt_method, nullable=False),
        sa.Column("state", design_attempt_state, nullable=False, server_default="planned"),
        sa.Column(
            "brief_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("source_concept_hash", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("production_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("model", sa.String(length=120), nullable=False, server_default=""),
        sa.Column(
            "model_settings",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "reference_inputs",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "execution_rules",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "failure_code",
            postgresql.ENUM(name="failure_code", create_type=False),
            nullable=True,
        ),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["concept_id"], ["design_concepts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_attempt_id"], ["design_attempts.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "concept_id", "attempt_number", name="uq_design_attempts_concept_id_attempt_number"
        ),
        sa.CheckConstraint("attempt_number >= 1", name="attempt_number_positive"),
    )
    op.create_index("ix_design_attempts_concept_id", "design_attempts", ["concept_id"])
    # Partial: the review queue only asks for the undecided ones.
    op.create_index(
        "ix_design_attempts_awaiting",
        "design_attempts",
        ["created_at"],
        postgresql_where=sa.text("state = 'awaiting_decision'"),
    )

    op.create_table(
        "design_assets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("design_attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", design_asset_kind, nullable=False),
        sa.Column("relative_path", sa.String(length=512), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["design_attempt_id"], ["design_attempts.id"], ondelete="CASCADE"),
        # On the path, not the kind: separations and mockups repeat per attempt.
        sa.UniqueConstraint(
            "design_attempt_id",
            "relative_path",
            name="uq_design_assets_design_attempt_id_relative_path",
        ),
    )
    op.create_index("ix_design_assets_design_attempt_id", "design_assets", ["design_attempt_id"])

    op.create_table(
        "design_decisions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("design_attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision", design_decision_kind, nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("instruction", sa.Text(), nullable=True),
        sa.Column("actor", sa.String(length=64), nullable=False, server_default="owner"),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["design_attempt_id"], ["design_attempts.id"], ondelete="CASCADE"),
        # Exactly one decision per attempt; a retry recognises itself by the
        # idempotency key instead of writing a second row.
        sa.UniqueConstraint("design_attempt_id", name="uq_design_decisions_design_attempt_id"),
        sa.CheckConstraint("actor <> ''", name="decision_has_an_author"),
    )

    op.create_table(
        "approved_designs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("concept_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("design_attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("master_asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("approved_by", sa.String(length=64), nullable=False),
        sa.Column(
            "approved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "production_spec",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.ForeignKeyConstraint(["concept_id"], ["design_concepts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["design_attempt_id"], ["design_attempts.id"], ondelete="CASCADE"),
        # RESTRICT: deleting the bytes a production milestone points at should
        # be loud, not a cascade.
        sa.ForeignKeyConstraint(["master_asset_id"], ["design_assets.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("design_attempt_id", name="uq_approved_designs_design_attempt_id"),
        sa.UniqueConstraint("concept_id", "version", name="uq_approved_designs_concept_id_version"),
        sa.CheckConstraint("version >= 1", name="version_positive"),
        sa.CheckConstraint("approved_by <> ''", name="approval_has_an_author"),
    )
    op.create_index("ix_approved_designs_concept_id", "approved_designs", ["concept_id"])

    op.create_table(
        "design_attempt_elements",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("design_attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("element_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("render_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "settings",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["design_attempt_id"], ["design_attempts.id"], ondelete="CASCADE"),
        # RESTRICT: provenance must not vanish because the archive was tidied.
        sa.ForeignKeyConstraint(["element_id"], ["archive_elements.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["render_id"], ["element_renders.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "design_attempt_id", "role", name="uq_design_attempt_elements_design_attempt_id_role"
        ),
    )
    op.create_index(
        "ix_design_attempt_elements_element_id", "design_attempt_elements", ["element_id"]
    )

    op.create_table(
        "product_links",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("approved_design_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "external_system",
            sa.String(length=40),
            nullable=False,
            server_default="shirtfaced_shop",
        ),
        sa.Column("external_product_id", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("external_slug", sa.String(length=200), nullable=False, server_default=""),
        sa.Column(
            "sync_state",
            postgresql.ENUM(name="sync_state", create_type=False),
            nullable=False,
            server_default="not_attempted",
        ),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["approved_design_id"], ["approved_designs.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "approved_design_id",
            "external_system",
            name="uq_product_links_approved_design_id_external_system",
        ),
        sa.CheckConstraint(
            "sync_state <> 'succeeded' OR external_product_id <> ''",
            name="synced_links_name_a_product",
        ),
    )

    # The deterministic composer becomes a producer feeding attempts. Nullable,
    # because every design composed before this migration is standalone and
    # remains legitimate.
    op.add_column(
        "composed_designs",
        sa.Column("design_attempt_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_composed_designs_design_attempt_id_design_attempts",
        "composed_designs",
        "design_attempts",
        ["design_attempt_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # Partial unique: an attempt owns at most one composed design, and the
    # pre-pipeline nulls must not collide.
    op.create_index(
        "uq_composed_designs_design_attempt_id",
        "composed_designs",
        ["design_attempt_id"],
        unique=True,
        postgresql_where=sa.text("design_attempt_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_composed_designs_design_attempt_id", table_name="composed_designs")
    op.drop_constraint(
        "fk_composed_designs_design_attempt_id_design_attempts",
        "composed_designs",
        type_="foreignkey",
    )
    op.drop_column("composed_designs", "design_attempt_id")

    op.drop_table("product_links")
    op.drop_index("ix_design_attempt_elements_element_id", table_name="design_attempt_elements")
    op.drop_table("design_attempt_elements")
    op.drop_index("ix_approved_designs_concept_id", table_name="approved_designs")
    op.drop_table("approved_designs")
    op.drop_table("design_decisions")
    op.drop_index("ix_design_assets_design_attempt_id", table_name="design_assets")
    op.drop_table("design_assets")
    op.drop_index("ix_design_attempts_awaiting", table_name="design_attempts")
    op.drop_index("ix_design_attempts_concept_id", table_name="design_attempts")
    op.drop_table("design_attempts")
    op.drop_index("ix_design_concepts_queue", table_name="design_concepts")
    op.drop_index("ix_design_concepts_status", table_name="design_concepts")
    op.drop_table("design_concepts")

    bind = op.get_bind()
    design_asset_kind.drop(bind, checkfirst=True)
    design_decision_kind.drop(bind, checkfirst=True)
    design_attempt_state.drop(bind, checkfirst=True)
    design_attempt_method.drop(bind, checkfirst=True)
    concept_kind.drop(bind, checkfirst=True)
    concept_status.drop(bind, checkfirst=True)
    concept_library.drop(bind, checkfirst=True)

    # PostgreSQL cannot remove a value from an enum type, so the two audit
    # event kinds stay in ``audit_event_type``. That is only unsafe while a row
    # carries them -- reading such a row after this downgrade would raise -- so
    # the rows go, and the lingering labels are harmless.
    op.execute(
        "DELETE FROM audit_events "
        "WHERE event_type::text IN ('design_decision_recorded', 'design_approved')"
    )
