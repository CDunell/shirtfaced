"""Splitting a document into its sections.

Used to send only the relevant canon to a model rather than an entire document.
Ordering and unknown sections are preserved: this reads, it never rewrites.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


@dataclass(frozen=True)
class Section:
    """One heading and the text beneath it, up to the next heading of any level."""

    heading: str
    level: int
    body: str
    line: int

    @property
    def is_empty(self) -> bool:
        return not self.body.strip()


def split_sections(text: str) -> list[Section]:
    """Every section of the document, in order."""
    lines = text.splitlines()
    starts: list[tuple[int, int, str]] = []

    for index, line in enumerate(lines):
        match = HEADING.match(line)
        if match:
            starts.append((index, len(match.group(1)), match.group(2).strip()))

    sections: list[Section] = []
    for position, (index, level, heading) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        body = "\n".join(lines[index + 1 : end]).strip()
        sections.append(Section(heading=heading, level=level, body=body, line=index + 1))

    return sections


def section_map(text: str) -> dict[str, Section]:
    """Sections keyed by case-folded heading. The first of a repeated heading wins."""
    mapped: dict[str, Section] = {}
    for section in split_sections(text):
        mapped.setdefault(section.heading.casefold(), section)
    return mapped


def find_section(text: str, heading: str) -> Section | None:
    """One section by heading, ignoring case."""
    return section_map(text).get(heading.casefold())


def subsections_of(text: str, heading: str) -> list[Section]:
    """Sections nested under ``heading``, down to the next heading of the same level."""
    sections = split_sections(text)
    for position, section in enumerate(sections):
        if section.heading.casefold() != heading.casefold():
            continue
        nested: list[Section] = []
        for candidate in sections[position + 1 :]:
            if candidate.level <= section.level:
                break
            nested.append(candidate)
        return nested
    return []


BULLET = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+(.*\S)\s*$")


def bullets_of(body: str) -> list[str]:
    """List items in a section body, with their markers and emphasis removed."""
    items: list[str] = []
    for line in body.splitlines():
        match = BULLET.match(line)
        if match:
            items.append(match.group(1).replace("**", "").strip())
    return items
