"""element archive

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-08

The parts a design is assembled from, and the rules for using them. Geometry is
stored apart from aesthetics: an authored element carries a recipe and its
parameters, an ingested one carries path data and a licence trail, and neither
carries a finished design. Renders store the tuple that produced them so the
artwork stays disposable.

Requires the pgvector extension, which is created here. Similarity between
elements is a query rather than a pass over the archive in Python.

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ELEMENT_FEATURE_DIMENSIONS = 32

ELEMENT_FAMILIES = (
    "frame",
    "type_layout",
    "wordmark",
    "badge",
    "texture",
    "print_effect",
    "patch_label",
    "placement",
    "composition_template",
    "colour_system",
    "illustration_part",
    "symbol",
    "ornament",
    "pattern",
)

LICENCE_STATUSES = ("verified", "unverified", "refused")


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    element_family = postgresql.ENUM(*ELEMENT_FAMILIES, name="element_family")
    element_family.create(op.get_bind(), checkfirst=True)
    licence_status = postgresql.ENUM(*LICENCE_STATUSES, name="licence_status")
    licence_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "archive_elements",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("element_key", sa.String(length=120), nullable=False),
        sa.Column(
            "family",
            postgresql.ENUM(*ELEMENT_FAMILIES, name="element_family", create_type=False),
            nullable=False,
        ),
        sa.Column("subtype", sa.String(length=80), nullable=False),
        # Authored elements name a recipe; ingested elements carry path data.
        sa.Column("recipe", sa.String(length=120), nullable=False),
        sa.Column("geometry", sa.Text(), nullable=False),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        # Where supplied content goes. No slots means placeable but not fillable.
        sa.Column("slots", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("symmetry", sa.String(length=24), nullable=False),
        sa.Column("ink_min", sa.Integer(), nullable=False),
        sa.Column("ink_max", sa.Integer(), nullable=False),
        sa.Column("complexity", sa.Float(), nullable=False),
        sa.Column(
            "style_tags",
            postgresql.ARRAY(sa.String(length=40)),
            server_default=sa.text("'{}'::varchar[]"),
            nullable=False,
        ),
        sa.Column(
            "compatible_treatments",
            postgresql.ARRAY(sa.String(length=40)),
            server_default=sa.text("'{}'::varchar[]"),
            nullable=False,
        ),
        sa.Column(
            "exclusions",
            postgresql.ARRAY(sa.String(length=40)),
            server_default=sa.text("'{}'::varchar[]"),
            nullable=False,
        ),
        sa.Column(
            "licence_status",
            postgresql.ENUM(*LICENCE_STATUSES, name="licence_status", create_type=False),
            server_default=sa.text("'unverified'"),
            nullable=False,
        ),
        sa.Column("licence_terms", sa.String(length=80), nullable=False),
        sa.Column("licence_source", sa.String(length=80), nullable=False),
        sa.Column("licence_source_id", sa.String(length=200), nullable=False),
        sa.Column("licence_source_url", sa.Text(), nullable=False),
        sa.Column("licence_checked_at", sa.Date(), nullable=True),
        sa.Column(
            "licence_commercial_use",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("licence_note", sa.Text(), nullable=False),
        sa.Column("feature", sa.dialects.postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_archive_elements"),
        sa.UniqueConstraint("element_key", name="uq_archive_elements_element_key"),
        # The licence gate, in the database. Not a duplicated validation -- it is
        # the one that survives a bulk import written in a hurry, and these
        # elements go on garments that are sold.
        sa.CheckConstraint(
            "licence_status <> 'verified' OR ("
            " licence_commercial_use"
            " AND licence_terms <> ''"
            " AND licence_source <> ''"
            " AND licence_checked_at IS NOT NULL)",
            name="ck_archive_elements_verified_licence_complete",
        ),
        sa.CheckConstraint("ink_min >= 1 AND ink_max >= ink_min", name="ck_archive_elements_inks"),
        sa.CheckConstraint(
            "complexity >= 0 AND complexity <= 1", name="ck_archive_elements_complexity"
        ),
        # Authored or ingested, never both and never neither.
        sa.CheckConstraint(
            "(recipe <> '') <> (geometry <> '')",
            name="ck_archive_elements_recipe_xor_geometry",
        ),
    )

    # The ARRAY placeholder above is replaced by a real vector column. Declaring
    # it through alembic's type system would need pgvector imported into every
    # migration environment; the extension is a better place for that knowledge.
    op.execute(
        f"ALTER TABLE archive_elements ALTER COLUMN feature "
        f"TYPE vector({ELEMENT_FEATURE_DIMENSIONS}) USING NULL"
    )

    op.create_index("ix_archive_elements_family", "archive_elements", ["family"])
    # Partial: the composer never queries anything but verified elements.
    op.create_index(
        "ix_archive_elements_usable",
        "archive_elements",
        ["family", "subtype"],
        postgresql_where=sa.text("licence_status = 'verified'"),
    )
    # HNSW over cosine distance. Cosine because the feature vector mixes counts
    # and shares, so direction carries the meaning and magnitude mostly carries
    # how many components happened to be populated.
    op.execute(
        "CREATE INDEX ix_archive_elements_feature ON archive_elements "
        "USING hnsw (feature vector_cosine_ops)"
    )

    op.create_table(
        "element_renders",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("element_id", sa.UUID(), nullable=False),
        # The inputs, whole, so the output can be reproduced from this row alone.
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("palette", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("svg", sa.Text(), nullable=False),
        sa.Column("renderer_version", sa.String(length=40), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_element_renders"),
        sa.ForeignKeyConstraint(
            ["element_id"],
            ["archive_elements.id"],
            name="fk_element_renders_element_id_archive_elements",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "element_id", "content_hash", name="uq_element_renders_element_content"
        ),
    )
    op.create_index("ix_element_renders_element_id", "element_renders", ["element_id"])


def downgrade() -> None:
    op.drop_index("ix_element_renders_element_id", table_name="element_renders")
    op.drop_table("element_renders")
    op.drop_index("ix_archive_elements_feature", table_name="archive_elements")
    op.drop_index("ix_archive_elements_usable", table_name="archive_elements")
    op.drop_index("ix_archive_elements_family", table_name="archive_elements")
    op.drop_table("archive_elements")
    postgresql.ENUM(name="licence_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="element_family").drop(op.get_bind(), checkfirst=True)
    # The extension is deliberately left in place. Dropping it would break any
    # other table using vector columns, and it is harmless when unused.
