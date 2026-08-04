"""Simple tables survive hand edits that break column alignment.

The shotlist is edited by a person in a text editor. Changing a scene name changes
its width, and everything after it shifts. Reading the row by column position alone
would silently drop the status.
"""

from __future__ import annotations

from app.services.markdown_tables import find_table

COLUMNS = ["ID", "Scene", "Hero Product", "Camera", "Status"]

MISALIGNED = """\
  ID        Scene                     Hero Product   Camera              Status
  --------- ------------------------- -------------- ------------------- --------
  W01-011   Car interior handover   Tote bag   Rear seat   ⬜
"""

WIDER_THAN_THE_RULE = """\
  ID        Scene                     Hero Product   Camera              Status
  --------- ------------------------- -------------- ------------------- --------
  W01-011   A considerably longer scene name than the rule allows   Tote bag   Rear seat   ⬜
"""

EMPTY_MIDDLE_CELL = """\
  ID        Scene                     Hero Product   Camera              Status
  --------- ------------------------- -------------- ------------------- --------
  W01-011   Car interior transition                  Rear seat           ⬜
"""


def test_a_shortened_cell_does_not_lose_the_status() -> None:
    table = find_table(MISALIGNED, COLUMNS)

    assert table is not None
    assert table.rows[0].cells["scene"] == "Car interior handover"
    assert table.rows[0].cells["status"] == "⬜"


def test_a_cell_wider_than_the_rule_is_read_whole() -> None:
    table = find_table(WIDER_THAN_THE_RULE, COLUMNS)

    assert table is not None
    assert table.rows[0].cells["scene"] == "A considerably longer scene name than the rule allows"
    assert table.rows[0].cells["status"] == "⬜"


def test_an_empty_middle_cell_falls_back_to_column_positions() -> None:
    table = find_table(EMPTY_MIDDLE_CELL, COLUMNS)

    assert table is not None
    assert table.rows[0].cells["hero product"] == ""
    assert table.rows[0].cells["camera"] == "Rear seat"
    assert table.rows[0].cells["status"] == "⬜"
