"""Loading and validating the canonical world documents.

Validation runs before anything is spent. Every problem found is reported together,
because an operator fixing a hand-edited Markdown file wants the whole list, not one
fault per run.

Unknown sections are preserved: the loader reads what it needs and never rewrites the
documents, so an author can keep their own structure alongside the required headings.
"""

from __future__ import annotations

import re

from app.adapters.markdown_store import (
    CONTINUITY_DOCUMENT,
    SHOTLIST_DOCUMENT,
    WORLD_DOCUMENT,
    Document,
    MarkdownStore,
)
from app.domain.enums import parse_shot_status
from app.domain.errors import ValidationProblem, WorldValidationError
from app.domain.schemas import DocumentSummary, LoadedWorld, ParsedShot
from app.services.markdown_tables import Table, find_table

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")

# The Markdown contract lists these as required. The title heading is matched as a
# prefix because the real document is "# SHIRTFACED --- WORLD 01"; the rest must match
# in full.
WORLD_TITLE_PREFIX = "SHIRTFACED"
REQUIRED_WORLD_HEADINGS = (
    "Purpose",
    "Emotional Tone",
    "Lighting",
    "Colour Palette",
    "Photography Language",
    "Locations",
    "People",
    "Wardrobe",
    "Composition",
    "Success Test",
)

REQUIRED_CONTINUITY_HEADINGS = (
    "Status Key",
    "Hero Product Rotation",
    "Camera Position Rotation",
    "Approved Reference Frames",
    "Rejected Drift",
    "Current Canon Notes",
    "Next Prompt Brief",
)

SHOTLIST_COLUMNS = ("ID", "Scene", "Hero Product", "Camera", "Status")
OPTIONAL_SHOTLIST_COLUMNS = ("Priority", "Time", "Location", "Notes")

DEFAULT_PRIORITY = 100


def headings_of(text: str) -> list[str]:
    """Every ATX heading in the document, in order, without its hashes."""
    found: list[str] = []
    for line in text.splitlines():
        match = HEADING.match(line)
        if match:
            found.append(match.group(2).strip())
    return found


def _missing_headings(headings: list[str], required: tuple[str, ...]) -> list[str]:
    present = {heading.casefold() for heading in headings}
    return [heading for heading in required if heading.casefold() not in present]


def _validate_world_document(document: Document, problems: list[ValidationProblem]) -> list[str]:
    headings = headings_of(document.text)

    if not any(heading.upper().startswith(WORLD_TITLE_PREFIX) for heading in headings):
        problems.append(
            ValidationProblem(
                document=document.name,
                message=f"No title heading beginning with {WORLD_TITLE_PREFIX!r}.",
            )
        )

    for missing in _missing_headings(headings, REQUIRED_WORLD_HEADINGS):
        problems.append(
            ValidationProblem(document=document.name, message=f"Missing heading {missing!r}.")
        )

    return headings


def _validate_continuity_document(
    document: Document, problems: list[ValidationProblem]
) -> list[str]:
    headings = headings_of(document.text)

    for missing in _missing_headings(headings, REQUIRED_CONTINUITY_HEADINGS):
        problems.append(
            ValidationProblem(document=document.name, message=f"Missing heading {missing!r}.")
        )

    return headings


def _parse_shotlist(
    document: Document, problems: list[ValidationProblem]
) -> tuple[list[str], list[ParsedShot]]:
    headings = headings_of(document.text)
    table = find_table(document.text, list(SHOTLIST_COLUMNS))

    if table is None:
        problems.append(
            ValidationProblem(
                document=document.name,
                message=(f"No shot table with the required columns {', '.join(SHOTLIST_COLUMNS)}."),
            )
        )
        return headings, []

    return headings, _rows_to_shots(document.name, table, problems)


def _rows_to_shots(
    document_name: str, table: Table, problems: list[ValidationProblem]
) -> list[ParsedShot]:
    shots: list[ParsedShot] = []
    seen: dict[str, int] = {}

    for position, row in enumerate(table.rows, start=1):
        cells = row.cells
        external_id = cells.get("id", "").strip()
        title = cells.get("scene", "").strip()

        if not external_id:
            problems.append(
                ValidationProblem(document=document_name, message="Row has no ID.", line=row.line)
            )
            continue

        if not title:
            problems.append(
                ValidationProblem(
                    document=document_name,
                    message=f"Shot {external_id} has no scene.",
                    line=row.line,
                )
            )
            continue

        if external_id in seen:
            problems.append(
                ValidationProblem(
                    document=document_name,
                    message=(
                        f"Duplicate shot ID {external_id}, first seen on line {seen[external_id]}."
                    ),
                    line=row.line,
                )
            )
            continue
        seen[external_id] = row.line

        raw_status = cells.get("status", "").strip()
        status = parse_shot_status(raw_status)
        if status is None:
            problems.append(
                ValidationProblem(
                    document=document_name,
                    message=(
                        f"Shot {external_id} has an unrecognised status {raw_status!r}. "
                        "Use one of ⬜ 🟡 ✅ ❌, or planned, in progress, approved, "
                        "rejected, abandoned."
                    ),
                    line=row.line,
                )
            )
            continue

        priority = _parse_priority(document_name, external_id, cells, row.line, problems)
        if priority is None:
            continue

        shots.append(
            ParsedShot(
                external_id=external_id,
                sequence=position,
                priority=priority,
                title=title,
                hero_product=_optional(cells.get("hero product")),
                camera_position=_optional(cells.get("camera")),
                lighting_source=_optional(cells.get("lighting")),
                status=status,
                source_line=row.line,
            )
        )

    if not shots and not problems:
        problems.append(
            ValidationProblem(document=document_name, message="The shot table has no rows.")
        )

    return shots


def _parse_priority(
    document_name: str,
    external_id: str,
    cells: dict[str, str],
    line: int,
    problems: list[ValidationProblem],
) -> int | None:
    """Priority is optional; the shotlist may omit the column entirely."""
    raw = (cells.get("priority") or "").strip()
    if not raw:
        return DEFAULT_PRIORITY
    try:
        return int(raw)
    except ValueError:
        problems.append(
            ValidationProblem(
                document=document_name,
                message=f"Shot {external_id} has a non-numeric priority {raw!r}.",
                line=line,
            )
        )
        return None


def _optional(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None


def _world_name(headings: list[str], slug: str) -> str:
    """Human name for the world, taken from its title heading."""
    for heading in headings:
        if heading.upper().startswith(WORLD_TITLE_PREFIX):
            # "SHIRTFACED --- WORLD 01" reads better as "Shirtfaced — World 01".
            return heading.replace("---", "—").replace("  ", " ").strip()
    return slug


def load_world(store: MarkdownStore, slug: str) -> LoadedWorld:
    """Load and validate one world.

    Raises :class:`WorldValidationError` listing every problem found.
    """
    documents = store.read_world_documents(slug)
    problems: list[ValidationProblem] = []

    world_headings = _validate_world_document(documents[WORLD_DOCUMENT], problems)
    continuity_headings = _validate_continuity_document(documents[CONTINUITY_DOCUMENT], problems)
    shotlist_headings, shots = _parse_shotlist(documents[SHOTLIST_DOCUMENT], problems)

    if problems:
        raise WorldValidationError(problems=problems)

    directory = store.world_directory(slug)
    return LoadedWorld(
        slug=slug,
        name=_world_name(world_headings, slug),
        directory_path=directory.relative_to(store.root).as_posix(),
        world_document=_summary(documents[WORLD_DOCUMENT], world_headings),
        continuity_document=_summary(documents[CONTINUITY_DOCUMENT], continuity_headings),
        shotlist_document=_summary(documents[SHOTLIST_DOCUMENT], shotlist_headings),
        shots=shots,
    )


def _summary(document: Document, headings: list[str]) -> DocumentSummary:
    return DocumentSummary(name=document.name, sha256=document.sha256, headings=headings)
