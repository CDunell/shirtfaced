"""Phase 2: the cast on disk becomes the cast in the database.

``studio/docs/VISUAL_ASSET_LIBRARY.md`` §14. ``var/cast/<slug>/`` holds two
fixed frames per person and a ``reference.json`` recording how they were made.
This reads both, keeps every hash exactly as it is, and produces cast members
whose references are rows rather than filenames.

Idempotent, like the world and concept importers. Running it twice re-links the
same assets to the same members and creates nothing new: identity is the SHA of
the bytes, and the bytes have not changed.

What it will not do:

* infer approval from a timestamp -- ``reference.json`` describes frames the
  owner approved and the CHARACTERS.md table calls "approved A/B files", so the
  two primaries are ingested approved and everything else arrives pending;
* invent provenance -- what the JSON says is carried across verbatim, and the
  fields it does not have are left empty rather than guessed;
* delete or rewrite anything under ``var/cast``. The directory stays as it is
  until the renderer is cut over, and after that it is regenerated from here.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore
from app.db.visual_models import CastMember
from app.domain.enums import VisualAssetKind, VisualAssetSourceType
from app.services import visual_library

logger = logging.getLogger(__name__)

# The two frames the fixed-slot era could express, and the role each becomes.
#
# Keyed by the ``frames`` letter in ``reference.json``, not by filename. The
# files were called ``a-full-length.png`` and ``b-head-shoulders.png`` until 17
# August 2026 and are now ``<slug>-full-length.png``; the manifest was updated
# with them, the letters were not. Anything that keyed on the name broke, which
# is the argument for this library stated as an incident.
FRAME_ROLES = {
    "a": "full_body_neutral",
    "b": "head_shoulders_neutral",
}

# Used only when a directory has no manifest to ask. Matched on the suffix, so
# both the old and the current naming resolve.
FRAME_SUFFIXES = {
    "full-length.png": "full_body_neutral",
    "head-shoulders.png": "head_shoulders_neutral",
}

# Slugs whose display name is not simply the slug capitalised.
DISPLAY_NAME_OVERRIDES = {"sk": "SK"}


@dataclass
class IngestReport:
    """What the run did, in terms a person can check against the filesystem."""

    members_created: list[str] = field(default_factory=list)
    members_seen: list[str] = field(default_factory=list)
    assets_created: list[str] = field(default_factory=list)
    assets_already_held: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    # Held already, but under a different filename than last time.
    renamed: list[str] = field(default_factory=list)

    def summary(self) -> str:
        renamed = f", {len(self.renamed)} renamed on disk" if self.renamed else ""
        return (
            f"{len(set(self.members_seen))} cast members "
            f"({len(self.members_created)} new), "
            f"{len(self.assets_created)} assets ingested, "
            f"{len(self.assets_already_held)} already held, "
            f"{len(self.links)} references linked{renamed}"
        )


def display_name_for(slug: str) -> str:
    return DISPLAY_NAME_OVERRIDES.get(slug, slug.replace("-", " ").title())


def _load_reference_json(directory: Path) -> dict[str, Any]:
    manifest = directory / "reference.json"
    if not manifest.is_file():
        return {}
    try:
        loaded: dict[str, Any] = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("unreadable reference.json in %s; provenance left empty", directory)
        return {}
    return loaded


def _canonical_metadata(manifest: dict[str, Any]) -> dict[str, Any]:
    """Continuity facts about the person, as opposed to about one photograph."""
    return {
        key: manifest[key]
        for key in ("age_at_reference", "resemblance_reference", "notes", "supersedes")
        if key in manifest
    }


def _asset_metadata(manifest: dict[str, Any]) -> dict[str, Any]:
    """How this image came to exist. Recorded because pixels cannot say it."""
    return {
        key: manifest[key]
        for key in ("model", "generated_in", "generated_at", "continuity_method", "prompt_sha256")
        if key in manifest
    }


def upsert_cast_member(
    session: Session, slug: str, manifest: dict[str, Any] | None = None
) -> tuple[CastMember, bool]:
    """Find or create a member. Existing canon is updated, never replaced blind."""
    manifest = manifest or {}
    member = session.execute(select(CastMember).where(CastMember.slug == slug)).scalars().first()
    if member is not None:
        merged = dict(member.canonical_metadata)
        merged.update(_canonical_metadata(manifest))
        member.canonical_metadata = merged
        return member, False

    member = CastMember(
        slug=slug,
        display_name=display_name_for(slug),
        canonical_metadata=_canonical_metadata(manifest),
    )
    session.add(member)
    session.flush()
    return member, True


def resolve_frames(directory: Path, manifest: dict[str, Any]) -> dict[str, Path]:
    """Find a member's two canonical frames without trusting their filenames.

    ``reference.json`` names them under ``frames`` and is kept in step when the
    files are renamed, so it is asked first. A directory with no manifest, or
    one naming a file that is not there, falls back to matching the suffix --
    both ``a-full-length.png`` and ``damo-full-length.png`` resolve.

    Returns role to path, in the order the roles are declared, so the strip
    orders the same way every run.
    """
    found: dict[str, Path] = {}

    frames = manifest.get("frames")
    if isinstance(frames, dict):
        for letter, role in FRAME_ROLES.items():
            named = frames.get(letter)
            if isinstance(named, str) and (directory / named).is_file():
                found[role] = directory / named

    if len(found) == len(FRAME_ROLES):
        return found

    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        for suffix, role in FRAME_SUFFIXES.items():
            if role not in found and path.name.endswith(suffix):
                found[role] = path

    return {role: found[role] for role in FRAME_ROLES.values() if role in found}


def ingest_cast_directory(
    session: Session, store: AssetStore, root: Path, *, report: IngestReport | None = None
) -> IngestReport:
    """Ingest every ``var/cast/<slug>/`` directory found under ``root``."""
    report = report or IngestReport()

    for directory in sorted(path for path in root.iterdir() if path.is_dir()):
        slug = directory.name
        if slug.startswith((".", "_")):
            report.skipped.append(f"{slug}: not a cast directory")
            continue

        manifest = _load_reference_json(directory)
        member, created = upsert_cast_member(session, slug, manifest)
        report.members_seen.append(slug)
        if created:
            report.members_created.append(slug)

        frames = resolve_frames(directory, manifest)
        if not frames:
            report.skipped.append(f"{slug}: no full-length or head-shoulders frame found")

        for index, (role, source) in enumerate(frames.items()):
            filename = source.name
            ingested = visual_library.ingest_asset(
                session,
                store,
                data=source.read_bytes(),
                kind=VisualAssetKind.CAST,
                source_type=VisualAssetSourceType.GENERATED,
                role=role,
                description=f"{display_name_for(slug)} — canonical {role.replace('_', ' ')}",
                metadata=_asset_metadata(manifest) | {"legacy_filename": filename},
                model=manifest.get("model"),
                prompt_hash=manifest.get("prompt_sha256"),
            )
            (report.assets_created if ingested.created else report.assets_already_held).append(
                f"{slug}/{role}"
            )

            # Bytes already held under the previous name: same asset, same
            # identity, new filename. Record where it now lives so the
            # compatibility mirror writes back over the current file rather
            # than resurrecting the old one beside it.
            if ingested.asset.metadata_json.get("legacy_filename") != filename:
                ingested.asset.metadata_json = ingested.asset.metadata_json | {
                    "legacy_filename": filename,
                    "previous_filename": ingested.asset.metadata_json.get("legacy_filename"),
                }
                report.renamed.append(f"{slug}/{filename}")

            # The frames the fixed slots held are the approved primaries: they
            # are what every scene generated so far already used. Approved only
            # on the way in -- a re-run must not re-decide, or an asset the
            # owner has since deprecated would quietly come back.
            if ingested.created:
                visual_library.approve_asset(
                    session,
                    ingested.asset,
                    note="Imported as an existing approved canonical frame",
                )
            visual_library.attach_to_cast_member(
                session,
                member,
                ingested.asset,
                role=role,
                is_primary=True,
                sort_order=index,
            )
            report.links.append(f"{slug}/{role}")

    return report


def ingest_extra_reference(
    session: Session,
    store: AssetStore,
    *,
    slug: str,
    role: str,
    path: Path,
    description: str | None = None,
    approve: bool = False,
    kind: VisualAssetKind = VisualAssetKind.CAST,
    report: IngestReport | None = None,
) -> IngestReport:
    """Ingest one further reference for a member -- the third photograph.

    This is the case the fixed six slots could not hold at all. Here it is an
    ordinary link: a role, a position on the strip, and no code change.

    Pending unless ``approve`` is passed. An image arriving is not a decision
    that it may be used.
    """
    report = report or IngestReport()
    member, created = upsert_cast_member(session, slug)
    report.members_seen.append(slug)
    if created:
        report.members_created.append(slug)

    ingested = visual_library.ingest_asset(
        session,
        store,
        data=path.read_bytes(),
        kind=kind,
        source_type=VisualAssetSourceType.GENERATED,
        role=role,
        description=description,
        metadata={"ingested_from": path.name},
    )
    (report.assets_created if ingested.created else report.assets_already_held).append(
        f"{slug}/{role}"
    )

    if approve:
        visual_library.approve_asset(session, ingested.asset, note="Approved at ingest")

    visual_library.attach_to_cast_member(session, member, ingested.asset, role=role)
    report.links.append(f"{slug}/{role}")
    return report
