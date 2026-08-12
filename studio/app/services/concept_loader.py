"""Parsing a concept library document into validated concepts.

Pure: no database, no filesystem writes. Validation runs before anything is
touched, and every problem found is reported together -- an operator fixing a
library should see the whole list in one go, not discover faults one run at a
time.

The grammar is the one the tee library actually uses, not an aspiration:

    ## Round 04 — Full noise
    121. **THE BOUNCER** — Retire kangaroo-specific version. ...

Retirement appears in the source in three distinct forms, and telling them
apart is the point of this module:

* Hard: the title itself reads ``RETIRED — TITLE (lane)``. A decision, made.
* Unconditional: the body opens ``Retired.``. Also a decision, made.
* Conditional: the body opens ``Retire ... if ...`` (or "as named", "unless").
  A decision the owner has *not* made -- these become ``held``, never
  ``retired``, because mapping them to retired would fabricate a ruling the
  source does not contain.

All three are anchored on prefixes, never substrings: entry 54 describes
"three retired blokes sitting outside a hardware store" and is a live concept.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from app.adapters.markdown_store import sha256_hex
from app.domain.enums import ConceptKind, ConceptLibrary, ConceptStatus
from app.domain.errors import StudioError, ValidationProblem

__all__ = [
    "ConceptLibraryError",
    "LoadedConceptLibrary",
    "ParsedConcept",
    "load_concept_library",
    "parse_concept_library",
]

EM_DASH = "—"

# ``N. **TITLE** — body``, one line, em-dash required. Anything inside a Round
# section that is not blank and not this is a fault, reported by line number.
_ENTRY = re.compile(r"^(\d+)\.\s+\*\*(.+?)\*\*\s+" + EM_DASH + r"\s+(\S.*?)\s*$")

# ``## Round 04 — Full noise``. The suffix is optional; the number is not.
_ROUND_HEADING = re.compile(r"^##\s+Round\s+(\d+)(?:\s+" + EM_DASH + r"\s+(.+?))?\s*$")

_ANY_HEADING = re.compile(r"^##\s+")

# A hard retirement lives in the title field itself.
_RETIRED_TITLE_PREFIX = f"RETIRED {EM_DASH} "

# The garment prefix rounds 05-06 open their bodies with: ``Tee.``, ``Crop.``,
# ``Tee/crop.``, ``Crop/tee/crew/hoodie.``, ``Tee pair.``.
_GARMENT_WORD = r"(?:[Tt]ee|[Cc]rop|[Hh]oodie|[Cc]rew|[Tt]ank)"
_GARMENT_PREFIX = re.compile(
    r"^(" + _GARMENT_WORD + r"(?:/" + _GARMENT_WORD + r")*(?:\s+pair)?)\.\s+"
)

_SLUG_CLEANER = re.compile(r"[^a-z0-9]+")

# What each retirement classification derives. Shared with the importer, which
# uses it to recognise a status it set itself as distinct from one the owner
# moved -- see ``concept_importer``.
RETIREMENT_STATUSES: dict[str, ConceptStatus] = {
    "": ConceptStatus.BACKLOG,
    "hard": ConceptStatus.RETIRED,
    "unconditional": ConceptStatus.RETIRED,
    "conditional": ConceptStatus.HELD,
}


@dataclass
class ConceptLibraryError(StudioError):
    """The library document failed validation."""

    problems: list[ValidationProblem] = field(default_factory=list)

    def __str__(self) -> str:
        if not self.problems:
            return "The concept library failed validation."
        lines = "\n".join(f"  - {problem}" for problem in self.problems)
        count = len(self.problems)
        noun = "problem" if count == 1 else "problems"
        return f"The concept library failed validation ({count} {noun}):\n{lines}"


@dataclass(frozen=True)
class ParsedConcept:
    """One entry, as the parser understood it."""

    external_number: int
    slug: str
    title: str
    title_raw: str
    # Verbatim from the em-dash to the end of the line, garment prefix and all.
    concept_text: str
    retirement: str
    status: ConceptStatus
    kind: ConceptKind
    garments: tuple[str, ...]
    garment_prefix: str
    # A conditional retirement's full body, kept so the salvage clause -- what
    # of the idea may return -- is not lost in a status value.
    salvage: str
    round: int
    round_label: str
    source_line: int


@dataclass(frozen=True)
class LoadedConceptLibrary:
    """A parsed, validated library document."""

    library: ConceptLibrary
    source_path: str
    document_hash: str
    concepts: tuple[ParsedConcept, ...]


def load_concept_library(
    path: Path,
    library: ConceptLibrary = ConceptLibrary.TSHIRT,
    *,
    source_path: str | None = None,
) -> LoadedConceptLibrary:
    """Read, parse and validate one library document. Raises on any fault.

    ``source_path`` overrides what is recorded as the document's location, so a
    caller can store the repo-relative form no matter where it ran from.
    """
    # Text mode normalises line endings, and the hash is taken over the decoded
    # text, so a CRLF checkout does not read as a content change on Windows.
    content = path.read_text(encoding="utf-8")
    return parse_concept_library(
        content, source_path=source_path or path.as_posix(), library=library
    )


def parse_concept_library(
    content: str, *, source_path: str, library: ConceptLibrary = ConceptLibrary.TSHIRT
) -> LoadedConceptLibrary:
    """Parse library text. Split from the file read so tests need no disk."""
    document = source_path.rsplit("/", 1)[-1]
    problems: list[ValidationProblem] = []
    concepts: list[ParsedConcept] = []

    round_number: int | None = None
    round_label = ""

    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.rstrip()

        heading = _ROUND_HEADING.match(line)
        if heading:
            round_number = int(heading.group(1))
            round_label = line.removeprefix("##").strip()
            continue
        if _ANY_HEADING.match(line):
            # Hard guardrails, Selection rule: prose sections, not concepts.
            round_number = None
            continue
        if round_number is None or not line.strip():
            continue

        entry = _ENTRY.match(line)
        if entry is None:
            problems.append(
                ValidationProblem(
                    document=document,
                    line=line_number,
                    message=("not a concept entry; expected 'N. **TITLE** " + EM_DASH + " text'"),
                )
            )
            continue

        concepts.append(
            _parse_entry(
                number=int(entry.group(1)),
                title_raw=entry.group(2).strip(),
                body=entry.group(3).strip(),
                round_number=round_number,
                round_label=round_label,
                source_line=line_number,
            )
        )

    _validate(document, concepts, problems)
    if problems:
        raise ConceptLibraryError(problems=problems)

    return LoadedConceptLibrary(
        library=library,
        source_path=source_path,
        document_hash=sha256_hex(content),
        concepts=tuple(concepts),
    )


def _parse_entry(
    *,
    number: int,
    title_raw: str,
    body: str,
    round_number: int,
    round_label: str,
    source_line: int,
) -> ParsedConcept:
    retirement = ""
    title = title_raw
    if title_raw.startswith(_RETIRED_TITLE_PREFIX):
        retirement = "hard"
        title = title_raw.removeprefix(_RETIRED_TITLE_PREFIX).strip()

    garments: tuple[str, ...] = ()
    garment_prefix = ""
    classified_body = body
    prefix_match = _GARMENT_PREFIX.match(body)
    if prefix_match:
        garment_prefix = prefix_match.group(1)
        garments = _garments(garment_prefix)
        # Stripped for classification only; ``concept_text`` stays verbatim.
        classified_body = body[prefix_match.end() :]

    salvage = ""
    if not retirement:
        # Prefix-anchored on the body, never a substring: "retired blokes" in
        # the middle of entry 54 must not retire it.
        if classified_body.startswith("Retired."):
            retirement = "unconditional"
        elif classified_body.startswith("Retire "):
            retirement = "conditional"
            salvage = classified_body

    status = RETIREMENT_STATUSES[retirement]
    kind = ConceptKind.GARMENT_LED if garments else ConceptKind.OTHER

    return ParsedConcept(
        external_number=number,
        slug=_slug(number, title),
        title=title,
        title_raw=title_raw,
        concept_text=body,
        retirement=retirement,
        status=status,
        kind=kind,
        garments=garments,
        garment_prefix=garment_prefix,
        salvage=salvage,
        round=round_number,
        round_label=round_label,
        source_line=source_line,
    )


def _garments(prefix: str) -> tuple[str, ...]:
    """``Crop/tee/crew/hoodie`` -> (crop, tee, crew, hoodie); ``Tee pair`` -> (tee,)."""
    seen: list[str] = []
    for token in prefix.removesuffix(" pair").split("/"):
        cleaned = token.strip().casefold()
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return tuple(seen)


def _slug(number: int, title: str) -> str:
    """``005-absolute-weapon``. The number leads because titles repeat."""
    cleaned = _SLUG_CLEANER.sub("-", title.casefold()).strip("-")
    return f"{number:03d}-{cleaned}"[:160]


def _validate(
    document: str, concepts: list[ParsedConcept], problems: list[ValidationProblem]
) -> None:
    if not concepts and not problems:
        problems.append(
            ValidationProblem(document=document, message="no concept entries were found")
        )

    expected = 1
    for concept in concepts:
        if concept.external_number != expected:
            problems.append(
                ValidationProblem(
                    document=document,
                    line=concept.source_line,
                    message=(
                        f"entry number {concept.external_number} breaks the sequence; "
                        f"expected {expected}. Numbers are permanent identity and must "
                        "be contiguous from 1 -- never renumber, never reuse."
                    ),
                )
            )
        expected = concept.external_number + 1

        if not concept.title:
            problems.append(
                ValidationProblem(
                    document=document, line=concept.source_line, message="entry has no title"
                )
            )
        if not concept.concept_text:
            problems.append(
                ValidationProblem(
                    document=document, line=concept.source_line, message="entry has no body"
                )
            )
