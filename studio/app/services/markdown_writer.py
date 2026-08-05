"""Constructing canonical Markdown from validated fields.

Models never write these files. Application code builds the text from typed data, and
every value that came from a human or a model is sanitised first, so a reason
containing ``### Purpose`` cannot invent a heading or break a table.

This module only builds strings. Reading, validating, replacing and committing is the
decision service's job, which is what makes the update atomic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.markdown_sections import split_sections

REJECTED_DRIFT_HEADING = "Rejected Drift"
APPROVED_REFERENCES_HEADING = "Approved Reference Frames"
HERO_PRODUCT_ROTATION_HEADING = "Hero Product Rotation"
CAMERA_POSITION_ROTATION_HEADING = "Camera Position Rotation"

# Long enough for a reason and its lesson; short enough that the entry stays inside the
# 600 characters the planner reads.
MAX_REASON_CHARACTERS = 400
MAX_LABEL_CHARACTERS = 60

APPROVED_MARKER = "✅"
REJECTED_MARKER = "❌"
PLANNED_MARKER = "⬜"
IN_PROGRESS_MARKER = "🟡"


class MarkdownWriteError(Exception):
    """The document could not be updated safely."""


def sanitise_inline(text: str, limit: int = MAX_REASON_CHARACTERS) -> str:
    """Make arbitrary text safe to place inside a Markdown paragraph or table cell.

    Removes anything that would change the document's structure rather than its
    content: newlines that could start a new block, leading hashes that would become a
    heading, pipes that would split a table cell, and backticks that could open a code
    fence.
    """
    collapsed = " ".join(text.split())
    collapsed = collapsed.replace("|", "/").replace("`", "'")
    # A leading marker would turn the value into a heading, list item or quote.
    collapsed = re.sub(r"^[#>\-*+\s]+", "", collapsed)
    collapsed = collapsed.replace("\\", "/")

    if not collapsed:
        raise MarkdownWriteError("The text is empty once sanitised.")

    if len(collapsed) > limit:
        collapsed = collapsed[: limit - 1].rstrip() + "…"
    return collapsed


def _short_label(text: str) -> str:
    label = sanitise_inline(text, MAX_LABEL_CHARACTERS)
    return label.rstrip(".")


@dataclass(frozen=True)
class DriftEntry:
    """One rejected-drift record, built from validated fields."""

    shot_external_id: str
    label: str
    reason: str
    lesson: str | None = None

    def render(self) -> str:
        lesson = self.lesson.strip() if self.lesson else ""
        lesson_text = sanitise_inline(lesson) if lesson else "No new permanent lesson."

        return "\n".join(
            [
                f"### {_short_label(self.shot_external_id)} — {_short_label(self.label)}",
                "",
                "**Status:** REJECTED",
                "",
                f"**Reason:** {sanitise_inline(self.reason)}",
                "",
                f"**Permanent lesson:** {lesson_text}",
            ]
        )


@dataclass(frozen=True)
class ApprovedEntry:
    """One approved reference record."""

    shot_external_id: str
    scene: str
    hero_product: str | None
    camera_position: str | None
    strongest_success: str | None
    note: str | None
    is_reference: bool

    def render(self) -> str:
        lines = [
            f"## {_short_label(self.shot_external_id)} — {_short_label(self.scene)}",
            "",
            "**Status:** APPROVED",
            "",
            f"**Hero product:** {sanitise_inline(self.hero_product or 'unset')}",
            "",
            f"**Camera position:** {sanitise_inline(self.camera_position or 'unset')}",
        ]

        # The owner's words are the reason a frame works. The reviewer's are recorded
        # under its own name or not at all: it is a model whose branding, vehicle and
        # structural verdicts have all been measured wrong, and "Why it works" on an
        # owner-approved frame is a load-bearing line. It is also fed back into every
        # planning request once a frame becomes a reference, so an unreliable
        # sentence here does not stay here.
        if self.note:
            lines += ["", f"**Why it works:** {sanitise_inline(self.note)}"]
            if self.strongest_success:
                lines += ["", f"**Reviewer said:** {sanitise_inline(self.strongest_success)}"]
        elif self.strongest_success:
            lines += ["", f"**Reviewer said:** {sanitise_inline(self.strongest_success)}"]
        if self.is_reference:
            lines += ["", "**Reference:** promoted to an approved reference frame."]

        return "\n".join(lines)


def _section_bounds(text: str, heading: str) -> tuple[int, int, int]:
    """``(heading_line_index, body_start, body_end)`` as 0-based line offsets."""
    lines = text.splitlines()
    sections = split_sections(text)

    for position, section in enumerate(sections):
        if section.heading.casefold() != heading.casefold():
            continue

        start = section.line  # 0-based index of the first line after the heading
        end = len(lines)
        for candidate in sections[position + 1 :]:
            if candidate.level <= section.level:
                end = candidate.line - 1
                break
        return section.line - 1, start, end

    raise MarkdownWriteError(f"{heading!r} is missing from the document.")


def insert_drift_entry(continuity_text: str, entry: DriftEntry) -> str:
    """Put a new drift entry at the top of ``# Rejected Drift``.

    Newest first, because the planner reads the first three subsections. Older entries
    stay below as history and are never deleted.
    """
    _, body_start, _ = _section_bounds(continuity_text, REJECTED_DRIFT_HEADING)
    lines = continuity_text.splitlines()

    # Skip blank lines directly under the heading so the entry sits flush.
    insert_at = body_start
    while insert_at < len(lines) and not lines[insert_at].strip():
        insert_at += 1

    block = [*entry.render().splitlines(), ""]
    updated = lines[:insert_at] + block + lines[insert_at:]
    return "\n".join(updated) + ("\n" if continuity_text.endswith("\n") else "")


def append_approved_entry(continuity_text: str, entry: ApprovedEntry) -> str:
    """Add an approved record to the end of ``# Approved Reference Frames``."""
    _, _, body_end = _section_bounds(continuity_text, APPROVED_REFERENCES_HEADING)
    lines = continuity_text.splitlines()

    # Trim trailing blank lines inside the section so spacing stays even.
    insert_at = body_end
    while insert_at > 0 and not lines[insert_at - 1].strip():
        insert_at -= 1

    block = ["", *entry.render().splitlines(), ""]
    updated = lines[:insert_at] + block + lines[insert_at:]
    return "\n".join(updated) + ("\n" if continuity_text.endswith("\n") else "")


def append_rotation_row(continuity_text: str, heading: str, cells: list[str]) -> str:
    """Append one row to a pipe table under ``heading``.

    The table's headings and format are left exactly as they are; only a row is added.
    """
    _, body_start, body_end = _section_bounds(continuity_text, heading)
    lines = continuity_text.splitlines()

    last_row = None
    for index in range(body_start, body_end):
        if lines[index].strip().startswith("|"):
            last_row = index

    if last_row is None:
        raise MarkdownWriteError(f"No table found under {heading!r}.")

    row = "| " + " | ".join(sanitise_inline(cell, 80) for cell in cells) + " |"
    updated = [*lines[: last_row + 1], row, *lines[last_row + 1 :]]
    return "\n".join(updated) + ("\n" if continuity_text.endswith("\n") else "")


def set_shot_status_marker(shotlist_text: str, external_id: str, marker: str) -> str:
    """Change one shot's status cell, leaving the rest of the line untouched.

    The status is the last column, so only the trailing token is replaced. Column
    alignment is not rebuilt: the parser splits on runs of two or more spaces, so a
    marker of a different width does not break the table.
    """
    if marker not in {APPROVED_MARKER, REJECTED_MARKER, PLANNED_MARKER, IN_PROGRESS_MARKER}:
        raise MarkdownWriteError(f"{marker!r} is not a known status marker.")

    lines = shotlist_text.splitlines()
    target = external_id.strip()
    changed = False

    for index, line in enumerate(lines):
        cells = [cell for cell in re.split(r"\s{2,}|\s*\|\s*", line.strip()) if cell]
        if not cells or cells[0] != target:
            continue

        stripped = line.rstrip()
        if stripped.endswith("|"):
            # A pipe table: replace the final populated cell.
            head, _, _ = stripped.rstrip("|").rstrip().rpartition("|")
            lines[index] = f"{head}| {marker} |"
        else:
            # Replace the trailing marker itself, never "everything after the last
            # run of two spaces". A camera value wide enough to fill its column
            # leaves a single space before the status, and rpartition then took the
            # separator between the previous two columns and wrote the camera value
            # away along with the status.
            for known in (APPROVED_MARKER, REJECTED_MARKER, PLANNED_MARKER, IN_PROGRESS_MARKER):
                if stripped.endswith(known):
                    lines[index] = stripped[: -len(known)] + marker
                    break
            else:
                raise MarkdownWriteError(
                    f"The row for {external_id} does not end in a status marker."
                )
        changed = True
        break

    if not changed:
        raise MarkdownWriteError(f"No shotlist row for {external_id}.")

    return "\n".join(lines) + ("\n" if shotlist_text.endswith("\n") else "")


def append_canon_rule(world_text: str, heading: str, rule: str) -> str:
    """Add one approved rule to the end of a ``WORLD.md`` section.

    Appended as a sentence in the section's own voice rather than a new subsection,
    so the document keeps the shape the loader validates and the planner reads. The
    caller has already checked that the heading is one the planner sees.
    """
    _, _, body_end = _section_bounds(world_text, heading)
    lines = world_text.splitlines()

    # Step back over the blank lines and horizontal rules that separate sections, so
    # the rule sits with the prose it belongs to rather than orphaned above the next
    # heading. The section bounds would include it either way; a reader would not.
    insert_at = body_end
    while insert_at > 0 and _is_separator(lines[insert_at - 1]):
        insert_at -= 1

    block = ["", sanitise_inline(rule)]
    updated = [*lines[:insert_at], *block, *lines[insert_at:]]
    return "\n".join(updated) + ("\n" if world_text.endswith("\n") else "")


def _is_separator(line: str) -> bool:
    """A blank line or a horizontal rule, both of which divide rather than contain."""
    stripped = line.strip()
    return not stripped or (set(stripped) <= {"-", "*", "_"} and len(stripped) >= 3)
