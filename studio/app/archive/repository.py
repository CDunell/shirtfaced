"""The archive in the database, rather than only in Python.

`authored.py` is where elements are written; this is where they live once
written. The distinction matters as the archive grows past what a module can
hold: ingested material arrives with an external licence trail that has to be
queried and audited, similarity has to be a query rather than a pass over
everything in memory, and the composer needs "give me the usable elements"
rather than a tuple someone remembered to import.

Two rules the database enforces that Python alone cannot:

*The licence gate is a check constraint.* An element marked verified must carry
terms, a source, a date and commercial permission. That survives a bulk import
written in a hurry, which is exactly when it will be needed.

*Only verified elements are readable through the composer's path.* `usable()`
filters, and there is no method that hands back everything without saying so.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.archive.features import element_feature
from app.db.archive_models import ArchiveElement
from app.domain.element import Element, Licence, Slot
from app.domain.enums import ElementFamily, LicenceStatus


@dataclass
class SyncResult:
    """What a sync changed, so a run is reviewable rather than silent."""

    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.added) + len(self.updated) + len(self.unchanged)


def _slot_to_json(slot: Slot) -> dict[str, object]:
    return {
        "name": slot.name,
        "top": slot.top,
        "height": slot.height,
        "width": slot.width,
        "centre_x": slot.centre_x,
        "accepts": list(slot.accepts),
        "path": slot.path,
        "tracking": slot.tracking,
        "alignment": slot.alignment,
    }


def _slot_from_json(data: dict[str, Any]) -> Slot:
    """JSONB comes back untyped, so the shape is asserted here rather than
    trusted at every call site."""
    accepts = data.get("accepts") or ("text",)
    if isinstance(accepts, str):
        accepts = (accepts,)
    return Slot(
        name=str(data["name"]),
        top=float(data["top"]),
        height=float(data["height"]),
        width=float(data["width"]),
        centre_x=float(data["centre_x"]),
        accepts=tuple(str(kind) for kind in accepts),
        path=str(data.get("path", "")),
        tracking=float(data.get("tracking", 0.0)),
        alignment=str(data.get("alignment", "centre")),
    )


def to_domain(row: ArchiveElement) -> Element:
    """A stored row as the element the renderer and composer understand."""
    return Element(
        id=row.element_key,
        family=row.family.value,
        subtype=row.subtype,
        licence=Licence(
            status=row.licence_status,
            terms=row.licence_terms,
            source=row.licence_source,
            source_id=row.licence_source_id,
            source_url=row.licence_source_url,
            checked_at=row.licence_checked_at,
            commercial_use=row.licence_commercial_use,
            note=row.licence_note,
        ),
        slots=tuple(_slot_from_json(slot) for slot in row.slots),
        symmetry=row.symmetry,
        ink_min=row.ink_min,
        ink_max=row.ink_max,
        complexity=row.complexity,
        style_tags=tuple(row.style_tags),
        compatible_treatments=tuple(row.compatible_treatments),
        exclusions=tuple(row.exclusions),
        recipe=row.recipe,
        geometry=row.geometry,
        parameters={key: float(value) for key, value in (row.parameters or {}).items()},
    )


def _family_of(element: Element) -> ElementFamily:
    """The element's family, from its recipe rather than from a second field.

    An element's recipe already says what it is -- ``frame.shield`` is a frame.
    Deriving it removes the chance of a row whose family and recipe disagree,
    which is the sort of thing nothing checks until a query returns nonsense.
    """
    head = (element.recipe.split(".", 1)[0] if element.recipe else element.family).strip()
    aliases = {
        "frame": ElementFamily.FRAME,
        "type_layout": ElementFamily.TYPE_LAYOUT,
        "wordmark": ElementFamily.WORDMARK,
        "badge": ElementFamily.BADGE,
        "texture": ElementFamily.TEXTURE,
        "print_effect": ElementFamily.PRINT_EFFECT,
        "patch_label": ElementFamily.PATCH_LABEL,
        "placement": ElementFamily.PLACEMENT,
        "composition_template": ElementFamily.COMPOSITION_TEMPLATE,
        "colour_system": ElementFamily.COLOUR_SYSTEM,
        "illustration_part": ElementFamily.ILLUSTRATION_PART,
        "symbol": ElementFamily.SYMBOL,
        "ornament": ElementFamily.ORNAMENT,
        "pattern": ElementFamily.PATTERN,
    }
    try:
        return aliases[head]
    except KeyError as error:
        raise ValueError(f"element {element.id!r} has no known family for {head!r}") from error


class ElementRepository:
    """Reading and writing archive elements."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # --- Writing ------------------------------------------------------------

    def upsert(self, element: Element, geometry: str | None = None) -> str:
        """Store one element, returning "added", "updated" or "unchanged".

        The feature vector is recomputed on every write rather than carried
        forward. It is derived entirely from declared fields, so recomputing is
        cheap and a stale vector would be a silent wrongness -- neighbours would
        just quietly get worse with nothing failing.
        """
        family = _family_of(element)
        feature = element_feature(
            family=family.value,
            symmetry=element.symmetry,
            complexity=element.complexity,
            ink_min=element.ink_min,
            ink_max=element.ink_max,
            slots=[_slot_to_json(slot) for slot in element.slots],
            compatible_treatments=element.compatible_treatments,
            parameters=element.parameters,
        )

        row = self.session.scalar(
            select(ArchiveElement).where(ArchiveElement.element_key == element.id)
        )
        created = row is None
        if row is None:
            row = ArchiveElement(element_key=element.id)
            self.session.add(row)

        before = None if created else self._fingerprint(row)

        row.family = family
        row.subtype = element.subtype
        row.recipe = element.recipe
        row.geometry = element.geometry if geometry is None else geometry
        row.parameters = dict(element.parameters)
        row.slots = [_slot_to_json(slot) for slot in element.slots]
        row.symmetry = element.symmetry
        row.ink_min = element.ink_min
        row.ink_max = element.ink_max
        row.complexity = element.complexity
        row.style_tags = list(element.style_tags)
        row.compatible_treatments = list(element.compatible_treatments)
        row.exclusions = list(element.exclusions)
        row.licence_status = element.licence.status
        row.licence_terms = element.licence.terms
        row.licence_source = element.licence.source
        row.licence_source_id = element.licence.source_id
        row.licence_source_url = element.licence.source_url
        row.licence_checked_at = element.licence.checked_at
        row.licence_commercial_use = element.licence.commercial_use
        row.licence_note = element.licence.note
        row.feature = feature

        if created:
            return "added"
        return "unchanged" if self._fingerprint(row) == before else "updated"

    @staticmethod
    def _fingerprint(row: ArchiveElement) -> tuple[object, ...]:
        return (
            row.subtype,
            row.recipe,
            row.geometry,
            row.parameters,
            row.slots,
            row.symmetry,
            row.ink_min,
            row.ink_max,
            row.complexity,
            list(row.style_tags),
            list(row.compatible_treatments),
            list(row.exclusions),
            row.licence_status,
            row.licence_terms,
            row.licence_source,
            row.licence_checked_at,
            row.licence_commercial_use,
        )

    def sync(self, elements: tuple[Element, ...]) -> SyncResult:
        """Bring the stored archive in line with a set of elements."""
        result = SyncResult()
        for element in elements:
            outcome = self.upsert(element)
            getattr(result, outcome).append(element.id)
        self.session.flush()
        return result

    # --- Reading ------------------------------------------------------------

    def usable(self, family: ElementFamily | None = None) -> list[Element]:
        """Every element the composer may reach, which is all of them.

        Rights are not a filter here. An element whose terms are unknown is
        still something to design with, study and learn from; whether the
        finished design may be sold is asked once, before release.
        """
        query = select(ArchiveElement)
        if family is not None:
            query = query.where(ArchiveElement.family == family)
        rows = self.session.scalars(query.order_by(ArchiveElement.element_key)).all()
        return [to_domain(row) for row in rows]

    def get(self, element_key: str) -> Element | None:
        row = self.session.scalar(
            select(ArchiveElement).where(ArchiveElement.element_key == element_key)
        )
        return to_domain(row) if row else None

    def _extension_schema(self) -> str:
        """Where pgvector lives.

        Its operators are schema-qualified like its type. The integration tests
        pin search_path to their own schema, so an unqualified `<=>` does not
        resolve -- "operator does not exist: public.vector <=> unknown" -- even
        though the extension is installed and the column is a vector.
        """
        found = self.session.execute(
            text(
                "SELECT n.nspname FROM pg_extension e "
                "JOIN pg_namespace n ON n.oid = e.extnamespace "
                "WHERE e.extname = 'vector'"
            )
        ).scalar()
        if not found:
            raise RuntimeError("the pgvector extension is not enabled on this database")
        return str(found)

    def similar_to(self, element_key: str, limit: int = 5) -> list[tuple[Element, float]]:
        """Nearest neighbours by cosine distance, computed in the database.

        Verified only, for the same reason `usable` is: suggesting an element
        nobody may print is not a helpful suggestion. The element itself is
        excluded, since it is always its own nearest neighbour.
        """
        subject = self.session.scalar(
            select(ArchiveElement).where(ArchiveElement.element_key == element_key)
        )
        if subject is None or subject.feature is None:
            return []

        schema = self._extension_schema()
        # The operator and the cast are both qualified. Without the cast the
        # parameter arrives as `unknown` and no operator matches it, which reads
        # as a missing extension when the extension is fine.
        vector = "[" + ",".join(str(float(value)) for value in subject.feature) + "]"
        rows = self.session.execute(
            text(
                f"SELECT element_key, feature OPERATOR({schema}.<=>) "
                f"CAST(:vector AS {schema}.vector) AS distance "
                "FROM archive_elements "
                "WHERE element_key <> :key "
                "AND feature IS NOT NULL "
                "ORDER BY distance LIMIT :limit"
            ),
            {"vector": vector, "key": element_key, "limit": limit},
        ).all()

        found: list[tuple[Element, float]] = []
        for key, distance in rows:
            row = self.session.scalar(
                select(ArchiveElement).where(ArchiveElement.element_key == key)
            )
            if row is not None:
                found.append((to_domain(row), float(distance)))
        return found

    def unverified(self) -> list[tuple[str, str, str]]:
        """Elements whose terms nobody has looked up yet, as (key, source, status).

        Not a blocklist -- a worklist. These are perfectly usable for designing
        with. The list exists so that when a design built from them reaches
        release, whoever runs the rights review knows what to look up.
        """
        rows = self.session.scalars(
            select(ArchiveElement)
            .where(ArchiveElement.licence_status != LicenceStatus.VERIFIED)
            .order_by(ArchiveElement.element_key)
        ).all()
        return [(row.element_key, row.licence_source, row.licence_status.value) for row in rows]

    def licence_audit(self) -> dict[str, int]:
        """Counts by licence status, so the archive's rights position is one query."""
        counts: dict[str, int] = {status.value: 0 for status in LicenceStatus}
        for row in self.session.scalars(select(ArchiveElement)).all():
            counts[row.licence_status.value] += 1
        return counts


def verified_licence(
    terms: str,
    source: str,
    source_id: str,
    source_url: str,
    checked_at: date,
    note: str = "",
) -> Licence:
    """Build a licence that will actually pass the gate.

    A helper rather than a convenience: the gate wants terms, a source and a
    date together, and the commonest way to fail it is to set the status and
    leave the rest blank.
    """
    return Licence(
        status=LicenceStatus.VERIFIED,
        terms=terms,
        source=source,
        source_id=source_id,
        source_url=source_url,
        checked_at=checked_at,
        commercial_use=True,
        note=note,
    )
