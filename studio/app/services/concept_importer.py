"""Importing a validated concept library into PostgreSQL.

The Markdown file is the authored creative source; PostgreSQL is the
operational queue. Import reconciles the two, exactly as the world importer
reconciles ``SHOTLIST.md`` with ``shots``.

It is idempotent: running it twice produces the same state. Concepts are
matched on ``(library, external_number)``, so re-importing an edited document
updates rows rather than duplicating them, and a number missing from the file
is reported and kept -- never deleted, never renumbered.

Status needs more care here than it does for shots, because the library has no
status column: the only workflow signal the prose carries is retirement. So the
importer compares against what the row's own stored retirement classification
derives. If the current status is exactly that, the workflow never touched the
concept and the new derivation applies -- including a fresh retirement. If the
owner has moved it anywhere else (ready, exploring, a decision, a manual hold),
the database is authoritative; and when the source *changes its mind* about
such a concept, that is a conflict to report, not to resolve.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.concept_models import DesignConcept
from app.services.concept_loader import (
    RETIREMENT_STATUSES,
    LoadedConceptLibrary,
    ParsedConcept,
)

__all__ = ["ConceptImportReport", "import_concepts"]

# Authored fields: what the Markdown owns, copied straight across on every
# import. Everything else on the row belongs to the owner or the workflow.
_AUTHORED_ATTRIBUTES = (
    "slug",
    "title",
    "concept_text",
    "retirement",
    "round",
    "round_label",
    "source_line",
)


@dataclass
class ConceptImportReport:
    """What an import changed."""

    library: str
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    document_changed: bool = False
    status_conflicts: list[str] = field(default_factory=list)
    missing_from_source: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.created + self.updated + self.unchanged

    def summary(self) -> str:
        parts = [
            f"library {self.library}: {self.total} concepts "
            f"({self.created} new, {self.updated} changed, {self.unchanged} unchanged)",
        ]
        if self.document_changed:
            parts.append("document changed")
        return "; ".join(parts)


def import_concepts(session: Session, loaded: LoadedConceptLibrary) -> ConceptImportReport:
    """Import an already-validated library. The caller commits."""
    report = ConceptImportReport(library=loaded.library.value)

    existing = {
        concept.external_number: concept
        for concept in session.execute(
            select(DesignConcept).where(DesignConcept.library == loaded.library)
        ).scalars()
    }

    # Reported only when a previously recorded hash differs: the first import
    # of a document is not a change to it.
    report.document_changed = any(
        concept.source_document_hash != loaded.document_hash for concept in existing.values()
    )

    seen: set[int] = set()
    for parsed in loaded.concepts:
        seen.add(parsed.external_number)
        concept = existing.get(parsed.external_number)
        if concept is None:
            session.add(_new_concept(loaded, parsed))
            report.created += 1
            continue
        if _update_concept(concept, loaded, parsed, report):
            report.updated += 1
        else:
            report.unchanged += 1

    for number in sorted(set(existing) - seen):
        report.missing_from_source.append(
            f"concept {number} is in the database but no longer in the document. "
            "The row was kept: numbers are permanent and are never reused."
        )

    session.flush()
    return report


def _new_concept(loaded: LoadedConceptLibrary, parsed: ParsedConcept) -> DesignConcept:
    return DesignConcept(
        library=loaded.library,
        external_number=parsed.external_number,
        slug=parsed.slug,
        title=parsed.title,
        concept_text=parsed.concept_text,
        retirement=parsed.retirement,
        garments=list(parsed.garments),
        round=parsed.round,
        round_label=parsed.round_label,
        source_path=loaded.source_path,
        source_line=parsed.source_line,
        source_document_hash=loaded.document_hash,
        parsed_json=_parsed_json(parsed),
        status=parsed.status,
        # The one derivable kind. The rest is the owner's classification to
        # make, after insert, and the importer never revisits it.
        concept_kind=parsed.kind,
    )


def _update_concept(
    concept: DesignConcept,
    loaded: LoadedConceptLibrary,
    parsed: ParsedConcept,
    report: ConceptImportReport,
) -> bool:
    """Apply the parsed entry, protecting everything the workflow owns."""
    # What the row's stored retirement derived when it was last written. If the
    # status is still exactly that, the workflow never intervened.
    previously_derived = RETIREMENT_STATUSES[concept.retirement]

    changed = False
    for attribute in _AUTHORED_ATTRIBUTES:
        new_value = getattr(parsed, attribute)
        if getattr(concept, attribute) != new_value:
            setattr(concept, attribute, new_value)
            changed = True
    if concept.garments != list(parsed.garments):
        concept.garments = list(parsed.garments)
        changed = True
    if concept.source_path != loaded.source_path:
        concept.source_path = loaded.source_path
        changed = True
    new_parsed_json = _parsed_json(parsed)
    if concept.parsed_json != new_parsed_json:
        concept.parsed_json = new_parsed_json
        changed = True

    if concept.status is not parsed.status:
        if concept.status is previously_derived:
            concept.status = parsed.status
            changed = True
        elif parsed.status is not previously_derived:
            report.status_conflicts.append(
                f"concept {parsed.external_number}: the database says "
                f"{concept.status.value}, the library now says {parsed.status.value}. "
                "The database was kept."
            )
        # Otherwise the workflow simply moved on from an unchanged source
        # entry, which is the normal course of work, not a conflict.

    if concept.source_document_hash != loaded.document_hash:
        concept.source_document_hash = loaded.document_hash

    return changed


def _parsed_json(parsed: ParsedConcept) -> dict[str, str]:
    """What the parser saw but the columns do not hold. Empties are omitted."""
    values = {
        "title_raw": parsed.title_raw if parsed.title_raw != parsed.title else "",
        "garment_prefix": parsed.garment_prefix,
        "salvage": parsed.salvage,
    }
    return {key: value for key, value in values.items() if value}
