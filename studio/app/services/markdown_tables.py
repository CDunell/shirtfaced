"""Markdown table parsing.

Two table styles appear in the world documents and both must be readable:

* pipe tables, used throughout ``CONTINUITY.md``;
* Pandoc simple tables, used for the shotlist in ``SHOTLIST.md``, where columns are
  aligned by whitespace and a row of dashes marks the column widths.

The shotlist is the human's production backlog. It is edited by hand in whichever
style the author's tools produce, so the parser accepts both rather than forcing the
file into one shape.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A pipe table separator: | --- | :--: | etc.
PIPE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
# A Pandoc simple-table rule: runs of dashes separated by spaces.
SIMPLE_RULE = re.compile(r"^\s*-{2,}(\s+-{2,})+\s*$")


@dataclass(frozen=True)
class TableRow:
    """One data row, with the source line it came from."""

    cells: dict[str, str]
    line: int


@dataclass(frozen=True)
class Table:
    """A parsed table."""

    headings: list[str]
    rows: list[TableRow]
    heading_line: int


def find_table(text: str, required_headings: list[str]) -> Table | None:
    """Return the first table containing every heading in ``required_headings``.

    Matching is case-insensitive so a hand-edited file is not rejected over
    capitalisation.
    """
    wanted = {heading.casefold() for heading in required_headings}

    for table in _all_tables(text):
        if wanted <= {heading.casefold() for heading in table.headings}:
            return table
    return None


def _all_tables(text: str) -> list[Table]:
    lines = text.splitlines()
    tables: list[Table] = []

    for index, line in enumerate(lines):
        if index == 0:
            continue
        if PIPE_SEPARATOR.match(line) and "|" in lines[index - 1]:
            tables.append(_parse_pipe_table(lines, index))
        elif SIMPLE_RULE.match(line):
            table = _parse_simple_table(lines, index)
            if table is not None:
                tables.append(table)

    return tables


def _split_pipe_row(line: str) -> list[str]:
    stripped = line.strip()
    stripped = stripped.removeprefix("|").removesuffix("|")
    return [cell.strip() for cell in stripped.split("|")]


def _parse_pipe_table(lines: list[str], separator_index: int) -> Table:
    headings = _split_pipe_row(lines[separator_index - 1])
    rows: list[TableRow] = []

    for offset, line in enumerate(lines[separator_index + 1 :], start=separator_index + 2):
        if "|" not in line or not line.strip():
            break
        cells = _split_pipe_row(line)
        rows.append(TableRow(cells=_zip_cells(headings, cells), line=offset))

    return Table(headings=headings, rows=rows, heading_line=separator_index)


def _column_spans(rule: str) -> list[tuple[int, int]]:
    """Character ranges for each column, taken from the dashed rule."""
    return [(match.start(), match.end()) for match in re.finditer(r"-+", rule)]


def _slice_columns(line: str, spans: list[tuple[int, int]]) -> list[str]:
    cells: list[str] = []
    for position, (start, end) in enumerate(spans):
        is_last = position == len(spans) - 1
        # The final column runs to the end of the line: its content is often wider
        # than the rule, and a status glyph may sit past the marked span.
        cells.append((line[start:] if is_last else line[start:end]).strip())
    return cells


def _row_cells(line: str, spans: list[tuple[int, int]], column_count: int) -> list[str]:
    """Split one data row of a simple table.

    Splitting on runs of two or more spaces is tried first, because it survives a hand
    edit that changes a cell's width and shifts everything after it. Column positions
    are the fallback, for rows where a cell is empty or itself contains a wide gap.
    """
    by_gap = [cell for cell in re.split(r"\s{2,}", line.strip()) if cell]
    if len(by_gap) == column_count:
        return by_gap
    return _slice_columns(line, spans)


def _parse_simple_table(lines: list[str], rule_index: int) -> Table | None:
    if rule_index == 0:
        return None

    spans = _column_spans(lines[rule_index])
    if len(spans) < 2:
        return None

    headings = _slice_columns(lines[rule_index - 1], spans)
    if not any(headings):
        return None

    rows: list[TableRow] = []
    for offset, line in enumerate(lines[rule_index + 1 :], start=rule_index + 2):
        if not line.strip():
            break
        # A second rule closes the table in some Pandoc dialects.
        if SIMPLE_RULE.match(line):
            break
        cells = _row_cells(line, spans, len(headings))
        if not any(cells):
            break
        rows.append(TableRow(cells=_zip_cells(headings, cells), line=offset))

    return Table(headings=headings, rows=rows, heading_line=rule_index)


def _zip_cells(headings: list[str], cells: list[str]) -> dict[str, str]:
    """Map cells onto headings, tolerating short or long rows."""
    mapped: dict[str, str] = {}
    for position, heading in enumerate(headings):
        mapped[heading.casefold()] = cells[position] if position < len(cells) else ""
    return mapped
