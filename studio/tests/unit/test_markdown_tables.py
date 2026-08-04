"""Table parsing.

The world documents contain both table styles, so both are covered.
"""

from __future__ import annotations

from app.services.markdown_tables import find_table

SIMPLE_TABLE = """\
# Shotlist

  ID        Scene                     Hero Product   Camera              Status
  --------- ------------------------- -------------- ------------------- --------
  W01-001   Walking between venues    T-shirt        Across street       ✅
  W01-011   Car interior transition   Tote bag       Rear seat           ⬜

## After
"""

PIPE_TABLE = """\
| ID | Scene | Hero Product | Camera | Status |
|---|---|---|---|---|
| W01-001 | Walking between venues | T-shirt | Across street | ✅ |
| W01-011 | Car interior transition | Tote bag | Rear seat | ⬜ |
"""


def test_parses_a_pandoc_simple_table() -> None:
    table = find_table(SIMPLE_TABLE, ["ID", "Scene", "Hero Product", "Camera", "Status"])

    assert table is not None
    assert len(table.rows) == 2
    assert table.rows[0].cells["id"] == "W01-001"
    assert table.rows[0].cells["scene"] == "Walking between venues"
    assert table.rows[0].cells["hero product"] == "T-shirt"
    assert table.rows[0].cells["status"] == "✅"


def test_parses_a_pipe_table() -> None:
    table = find_table(PIPE_TABLE, ["ID", "Scene", "Hero Product", "Camera", "Status"])

    assert table is not None
    assert len(table.rows) == 2
    assert table.rows[1].cells["id"] == "W01-011"
    assert table.rows[1].cells["camera"] == "Rear seat"
    assert table.rows[1].cells["status"] == "⬜"


def test_records_the_source_line_of_each_row() -> None:
    """A validation message has to be able to point at the offending line."""
    table = find_table(SIMPLE_TABLE, ["ID", "Scene", "Status"])

    assert table is not None
    assert [row.line for row in table.rows] == [5, 6]


def test_stops_at_the_end_of_the_table() -> None:
    table = find_table(SIMPLE_TABLE, ["ID", "Scene", "Status"])

    assert table is not None
    assert all("After" not in row.cells["scene"] for row in table.rows)


def test_returns_none_when_no_table_has_the_required_columns() -> None:
    assert find_table(SIMPLE_TABLE, ["ID", "Lighting"]) is None


def test_column_matching_ignores_case() -> None:
    assert find_table(PIPE_TABLE, ["id", "SCENE", "status"]) is not None


def test_short_rows_do_not_raise() -> None:
    """A hand-edited file may leave a trailing cell off."""
    text = "| ID | Scene | Status |\n|---|---|---|\n| W01-001 | Walking |\n"

    table = find_table(text, ["ID", "Scene", "Status"])

    assert table is not None
    assert table.rows[0].cells["status"] == ""
