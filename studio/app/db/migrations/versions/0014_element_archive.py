"""element archive

Revision ID: 0014
Revises: 0013
Create Date: 2026-08-08

The parts a design is assembled from, and the rules for using them. Geometry is
stored apart from aesthetics: an authored element carries a recipe and its
parameters, an ingested one carries path data and a licence trail, and neither
carries a finished design. Renders store the tuple that produced them so the
artwork stays disposable.

Requires the pgvector extension, which the deploy script installs and enables
because CREATE EXTENSION needs superuser and the application role is not one.
This migration checks for it and stops with a readable message if it is absent.
Similarity between elements is a query rather than a pass over the archive in
Python.

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
    # The extension is enabled by the deploy script, as postgres, because
    # CREATE EXTENSION requires superuser and the application role deliberately
    # is not one. Checked rather than created here so the failure names the
    # missing prerequisite instead of surfacing as a permission error, or as
    # "could not open extension control file" inside an alembic traceback --
    # which is how this first went wrong.
    #
    # The query returns where the extension lives, not just whether it does.
    # The integration tests pin search_path to their own
    # schema and only that, so an unqualified `vector` does not resolve even
    # when the extension is installed. Qualifying is better than widening their
    # search_path, which would let alembic find the application's own version
    # table instead of the test schema's empty one.
    extension_schema = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT n.nspname FROM pg_extension e "
                "JOIN pg_namespace n ON n.oid = e.extnamespace "
                "WHERE e.extname = 'vector'"
            )
        )
        .scalar()
    )
    if not extension_schema:
        raise RuntimeError(
            "The pgvector extension is not enabled on this database. "
            "deploy-studio.sh installs the package and enables it; run that, "
            "or enable it by hand with: "
            "sudo -u postgres psql -d <database> -c "
            "'CREATE EXTENSION IF NOT EXISTS vector'"
        )

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
        f"TYPE {extension_schema}.vector({ELEMENT_FEATURE_DIMENSIONS}) USING NULL"
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
    # Declared on the model too, so the schema-drift check sees it on both
    # sides. The operator class is schema-qualified for the same reason the
    # column type is: the integration tests run without public on the path.
    op.create_index(
        "ix_archive_elements_feature",
        "archive_elements",
        ["feature"],
        postgresql_using="hnsw",
        postgresql_ops={"feature": f"{extension_schema}.vector_cosine_ops"},
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
