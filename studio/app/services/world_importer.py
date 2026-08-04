"""Importing a validated world into PostgreSQL.

The Markdown files are the human-readable creative record; PostgreSQL is the
operational source of truth. Import reconciles the two.

It is idempotent: running it twice produces the same state. Shots are matched on
``(world_id, external_id)``, so re-importing an edited shotlist updates rows rather
than duplicating them.

Import never overwrites operational state that the workflow owns. A shot that the
application has already moved on from — approved, rejected or abandoned — keeps its
status even if the Markdown still shows it as planned, because the database records
what actually happened. Where the two disagree, that is reported rather than
silently resolved.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.markdown_store import MarkdownStore
from app.db.models import Shot, World
from app.domain.enums import ShotStatus, WorldStatus
from app.domain.schemas import LoadedWorld, ParsedShot
from app.services.world_loader import load_world

# Statuses the workflow owns. Once a shot reaches one of these, the database is
# authoritative and the Markdown status is advisory.
WORKFLOW_OWNED_STATUSES = frozenset(
    {ShotStatus.APPROVED, ShotStatus.REJECTED, ShotStatus.ABANDONED}
)


@dataclass
class ImportReport:
    """What an import changed."""

    slug: str
    world_created: bool = False
    shots_created: int = 0
    shots_updated: int = 0
    shots_unchanged: int = 0
    documents_changed: list[str] = field(default_factory=list)
    status_conflicts: list[str] = field(default_factory=list)

    @property
    def shots_total(self) -> int:
        return self.shots_created + self.shots_updated + self.shots_unchanged

    def summary(self) -> str:
        parts = [
            f"world {self.slug}: {'created' if self.world_created else 'updated'}",
            f"{self.shots_total} shots "
            f"({self.shots_created} new, {self.shots_updated} changed, "
            f"{self.shots_unchanged} unchanged)",
        ]
        if self.documents_changed:
            parts.append("documents changed: " + ", ".join(self.documents_changed))
        return "; ".join(parts)


def import_world(session: Session, store: MarkdownStore, slug: str) -> ImportReport:
    """Load, validate and import one world. Raises on validation failure."""
    loaded = load_world(store, slug)
    return import_loaded_world(session, loaded)


def import_loaded_world(session: Session, loaded: LoadedWorld) -> ImportReport:
    """Import an already-validated world."""
    report = ImportReport(slug=loaded.slug)

    world = session.execute(select(World).where(World.slug == loaded.slug)).scalar_one_or_none()
    if world is None:
        world = World(
            slug=loaded.slug,
            name=loaded.name,
            directory_path=loaded.directory_path,
            status=WorldStatus.ACTIVE,
        )
        session.add(world)
        session.flush()
        report.world_created = True

    world.name = loaded.name
    world.directory_path = loaded.directory_path

    _record_hashes(world, loaded, report)
    _import_shots(session, world, loaded, report)

    session.flush()
    return report


def _record_hashes(world: World, loaded: LoadedWorld, report: ImportReport) -> None:
    documents = (
        ("WORLD.md", "world_document_hash", loaded.world_document.sha256),
        ("CONTINUITY.md", "continuity_document_hash", loaded.continuity_document.sha256),
        ("SHOTLIST.md", "shotlist_document_hash", loaded.shotlist_document.sha256),
    )
    for name, attribute, digest in documents:
        if getattr(world, attribute) != digest:
            if getattr(world, attribute) is not None:
                report.documents_changed.append(name)
            setattr(world, attribute, digest)


def _import_shots(
    session: Session, world: World, loaded: LoadedWorld, report: ImportReport
) -> None:
    existing = {
        shot.external_id: shot
        for shot in session.execute(select(Shot).where(Shot.world_id == world.id)).scalars()
    }

    for parsed in loaded.shots:
        shot = existing.get(parsed.external_id)
        if shot is None:
            session.add(_new_shot(world, parsed))
            report.shots_created += 1
            continue

        if _update_shot(shot, parsed, report):
            report.shots_updated += 1
        else:
            report.shots_unchanged += 1


def _new_shot(world: World, parsed: ParsedShot) -> Shot:
    return Shot(
        world_id=world.id,
        external_id=parsed.external_id,
        sequence=parsed.sequence,
        priority=parsed.priority,
        title=parsed.title,
        hero_product=parsed.hero_product,
        camera_position=parsed.camera_position,
        lighting_source=parsed.lighting_source,
        status=parsed.status,
        source_line=parsed.source_line,
    )


def _update_shot(shot: Shot, parsed: ParsedShot, report: ImportReport) -> bool:
    """Apply the parsed row, protecting statuses the workflow owns."""
    changed = False

    for attribute in (
        "sequence",
        "priority",
        "title",
        "hero_product",
        "camera_position",
        "lighting_source",
        "source_line",
    ):
        new_value = getattr(parsed, attribute)
        if getattr(shot, attribute) != new_value:
            setattr(shot, attribute, new_value)
            changed = True

    if shot.status is not parsed.status:
        if shot.status in WORKFLOW_OWNED_STATUSES:
            report.status_conflicts.append(
                f"{shot.external_id}: the database says {shot.status.value}, "
                f"the shotlist says {parsed.status.value}. The database was kept."
            )
        else:
            shot.status = parsed.status
            changed = True

    return changed
