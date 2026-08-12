"""Every Python enum member must exist in its PostgreSQL type.

Adding a member to a Python ``StrEnum`` does nothing to the database, and Alembic's
autogenerate does not detect it either. The mismatch stays invisible until the first
row carrying the new value is written — which in this project has meant a failure
surfacing four separate times, each on the path that was supposed to record the
problem rather than cause one.

This closes the gap. A missing ``ALTER TYPE ... ADD VALUE`` fails here, against the
migrated schema, instead of at the first write.
"""

from __future__ import annotations

import pytest
from sqlalchemy import Engine, Enum, text

# Imported for the side effect: the tables register themselves on Base.metadata when
# the module loads, and without it there is nothing here to compare.
import app.db.concept_models
import app.db.models  # noqa: F401
from app.db.base import Base

pytestmark = pytest.mark.integration


def _mapped_enums() -> dict[str, set[str]]:
    """Every native enum type the models declare, and the values they expect."""
    expected: dict[str, set[str]] = {}
    for table in Base.metadata.tables.values():
        for column in table.columns:
            kind = column.type
            if isinstance(kind, Enum) and kind.name:
                values = set(kind.enums)
                if not values and kind.enum_class is not None:
                    values = {member.value for member in kind.enum_class}
                expected.setdefault(kind.name, set()).update(values)
    return expected


def _database_values(engine: Engine, type_name: str) -> set[str]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT enumlabel FROM pg_enum e "
                "JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = :name"
            ),
            {"name": type_name},
        ).scalars()
        return set(rows)


def test_the_models_declare_enums_to_compare() -> None:
    """Guards the test itself: an empty comparison would pass without checking anything."""
    mapped = _mapped_enums()
    assert len(mapped) >= 8, f"Only found {len(mapped)} enum types; the reflection has broken."


def test_every_python_enum_value_exists_in_the_database(engine: Engine) -> None:
    """The direction that breaks writes."""
    missing: dict[str, set[str]] = {}

    for type_name, expected in _mapped_enums().items():
        actual = _database_values(engine, type_name)
        if not actual:
            missing[type_name] = {"<the type does not exist at all>"}
            continue
        gap = expected - actual
        if gap:
            missing[type_name] = gap

    assert not missing, (
        "These values exist in Python but not in PostgreSQL, so writing one raises "
        "InvalidTextRepresentation. A migration needs ALTER TYPE ... ADD VALUE for an "
        "existing type, or .create(bind) for a new one:\n"
        + "\n".join(f"  {name}: {', '.join(sorted(values))}" for name, values in missing.items())
    )


def test_every_database_enum_value_exists_in_python(engine: Engine) -> None:
    """The direction that breaks reads.

    PostgreSQL cannot drop an enum value, so a member retired from Python legitimately
    lingers in the type. That is only safe while no row still carries it — otherwise
    reading that row raises LookupError as SQLAlchemy tries to map the label back.
    """
    orphaned: dict[str, set[str]] = {}

    for type_name, expected in _mapped_enums().items():
        for value in _database_values(engine, type_name) - expected:
            # A retired label is fine in the type; it is only a problem in a row.
            with engine.connect() as connection:
                columns = connection.execute(
                    text(
                        "SELECT c.table_name, c.column_name FROM information_schema.columns c "
                        "WHERE c.udt_name = :name "
                        "AND c.table_schema = current_schema()"
                    ),
                    {"name": type_name},
                ).all()
                for table_name, column_name in columns:
                    # Interpolated rather than bound because identifiers cannot be
                    # parameters. Both names come from the system catalogue, not input.
                    used = connection.execute(
                        text(
                            f'SELECT 1 FROM "{table_name}" '
                            f'WHERE "{column_name}"::text = :value LIMIT 1'
                        ),
                        {"value": value},
                    ).scalar_one_or_none()
                    if used is not None:
                        orphaned.setdefault(type_name, set()).add(f"{value} (in {table_name})")

    assert not orphaned, (
        "Rows carry enum values that no Python member can represent, so reading them "
        "raises. Restore the member or migrate the rows:\n"
        + "\n".join(f"  {name}: {', '.join(sorted(values))}" for name, values in orphaned.items())
    )
