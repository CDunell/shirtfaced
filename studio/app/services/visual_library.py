"""Ingesting, approving and exporting Visual Asset Library assets.

``studio/docs/VISUAL_ASSET_LIBRARY.md`` §5.3 lists what an upload must do. This
module is that list, in one place, so the API route, the CLI importer and any
later location or scene-master ingest all get the same behaviour rather than
three approximations of it.

The two rules everything here turns on:

* **Bytes are identity.** An asset is addressed by the SHA-256 of its bytes.
  Ingesting the same file twice returns the row that already exists; it never
  makes a second identity for one photograph. Changing bytes is a new asset,
  never an edit.
* **Approval is a decision, not a timestamp.** Nothing becomes canonical by
  being newest. Approve and deprecate are explicit calls that write an audit
  event, and deprecation never deletes.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import logging
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore
from app.db.models import AuditEvent
from app.db.visual_models import CastMember, CastMemberAsset, SceneMaster, VisualAsset
from app.domain.enums import (
    PRIMARY_CAST_ROLES,
    AuditEventType,
    LicenceStatus,
    VisualAssetKind,
    VisualAssetSourceType,
    VisualAssetStatus,
)
from app.domain.errors import StudioError

logger = logging.getLogger(__name__)

OWNER = "owner"

# 50 MB, matching the renderer's canonical cast upload. A cast reference is a
# photograph, not a scan of a poster.
MAX_ASSET_BYTES = 50 * 1024 * 1024
# Smaller than this cannot be a usable production reference, and is almost
# always a thumbnail uploaded by mistake. §13 wants a readable image.
MIN_EDGE_PIXELS = 256

MIME_TYPES = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}
EXTENSIONS = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}

ROLE_PATTERN = re.compile(r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$")

# Everything this library holds is invented here: generated worlds, generated
# cast, no real people, no third party with a claim. Recorded on every asset so
# the provenance is a stated fact rather than an assumption a later reader has
# to make. Pass rights_metadata explicitly for anything that did come from
# outside.
DEFAULT_RIGHTS: dict[str, Any] = {"owner": "Shirtfaced", "origin": "owner-generated"}

# The suffix each legacy role's file carries. The stem was ``a``/``b`` until 17
# August 2026 and is now the member's slug; the suffix survived both, so the
# mirror composes a name rather than storing one.
LEGACY_CAST_SUFFIXES = {
    "full_body_neutral": "full-length.png",
    "head_shoulders_neutral": "head-shoulders.png",
}


class AssetRejected(StudioError):
    """The bytes are not an image this library will hold."""


class CastMemberNotFound(StudioError):
    """No such cast member."""


@dataclass(frozen=True)
class ImageFacts:
    """What the bytes themselves say, before anything is stored."""

    sha256: str
    byte_size: int
    width: int
    height: int
    mime_type: str


@dataclass(frozen=True)
class Ingested:
    """An ingest's outcome. ``created`` is false when the SHA was already held."""

    asset: VisualAsset
    created: bool


def inspect(data: bytes) -> ImageFacts:
    """Read and validate an image, or say precisely why it was refused.

    Validation is limited to what is genuinely a property of the file: that it
    decodes, that it is a format the store can serve, and that it is not so
    small it cannot be a reference. Nothing about subject matter, aspect or
    provenance is judged here -- everything gets ingested, and the rights
    question is asked later, where there is something to ask it about.
    """
    if not data:
        raise AssetRejected("The upload was empty.")
    if len(data) > MAX_ASSET_BYTES:
        limit = MAX_ASSET_BYTES // 1024 // 1024
        raise AssetRejected(f"{len(data) / 1024 / 1024:.1f} MB exceeds the {limit} MB limit.")

    try:
        with Image.open(BytesIO(data)) as image:
            image.load()
            image_format = image.format
            width, height = image.size
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise AssetRejected("The file could not be decoded as an image.") from error

    if image_format not in MIME_TYPES:
        raise AssetRejected(f"{image_format} is not a format this library stores.")
    if width < MIN_EDGE_PIXELS or height < MIN_EDGE_PIXELS:
        raise AssetRejected(f"{width}x{height} is too small to be a usable reference.")

    return ImageFacts(
        sha256=hashlib.sha256(data).hexdigest(),
        byte_size=len(data),
        width=width,
        height=height,
        mime_type=MIME_TYPES[image_format],
    )


def storage_key_for(facts: ImageFacts, kind: VisualAssetKind) -> str:
    """A content-addressed key. Two shards keep directory listings usable."""
    return f"visual/{kind.value}/{facts.sha256[:2]}/{facts.sha256}{EXTENSIONS[facts.mime_type]}"


def find_by_sha(session: Session, sha256: str) -> VisualAsset | None:
    return session.execute(
        select(VisualAsset).where(VisualAsset.sha256 == sha256)
    ).scalar_one_or_none()


def ingest_asset(
    session: Session,
    store: AssetStore,
    *,
    data: bytes,
    kind: VisualAssetKind,
    source_type: VisualAssetSourceType,
    role: str | None = None,
    description: str | None = None,
    rights_status: LicenceStatus = LicenceStatus.VERIFIED,
    rights_metadata: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    provider: str | None = None,
    model: str | None = None,
    provider_request_id: str | None = None,
    prompt_hash: str | None = None,
) -> Ingested:
    """Store bytes and record the asset, or return the one already held.

    The bytes are written before the row, and the key is the hash, so a failure
    between the two leaves an orphan file that the next ingest of the same
    image overwrites with identical content. The reverse order would leave a
    row pointing at nothing, which is the failure that cannot be repaired.
    """
    facts = inspect(data)

    existing = find_by_sha(session, facts.sha256)
    if existing is not None:
        logger.info("visual asset %s already held as %s", facts.sha256[:12], existing.id)
        return Ingested(asset=existing, created=False)

    key = storage_key_for(facts, kind)
    store.save(key, data, facts.mime_type)

    asset = VisualAsset(
        kind=kind,
        role=_validated_role(role) if role else None,
        storage_key=key,
        sha256=facts.sha256,
        mime_type=facts.mime_type,
        width=facts.width,
        height=facts.height,
        byte_size=facts.byte_size,
        source_type=source_type,
        provider=provider,
        model=model,
        provider_request_id=provider_request_id,
        prompt_hash=prompt_hash,
        status=VisualAssetStatus.PENDING,
        rights_status=rights_status,
        rights_metadata=rights_metadata or DEFAULT_RIGHTS,
        metadata_json=metadata or {},
        description=description,
    )
    session.add(asset)
    session.flush()

    session.add(
        AuditEvent(
            event_type=AuditEventType.VISUAL_ASSET_INGESTED,
            actor=OWNER,
            payload_json={
                "asset_id": str(asset.id),
                "kind": kind.value,
                "role": asset.role,
                "sha256": facts.sha256,
                "source_type": source_type.value,
                "dimensions": f"{facts.width}x{facts.height}",
            },
        )
    )
    return Ingested(asset=asset, created=True)


def _validated_role(role: str) -> str:
    """A role is a slug. Which slugs exist is not the database's business.

    ``CAST_ASSET_ROLES`` is what the interface offers; a role outside it is
    still stored, because a photograph nobody anticipated must still be
    filable. The only refusal is a string that is not a slug at all, since that
    is a bug in the caller rather than a new kind of reference.
    """
    cleaned = role.strip().lower()
    if not ROLE_PATTERN.match(cleaned):
        raise AssetRejected(f"{role!r} is not a usable role name.")
    return cleaned


def approve_asset(
    session: Session, asset: VisualAsset, *, actor: str = OWNER, note: str | None = None
) -> VisualAsset:
    """Mark an asset production-usable, and record who said so."""
    prior = asset.status
    asset.status = VisualAssetStatus.APPROVED
    asset.approved_at = dt.datetime.now(dt.UTC)
    asset.approved_by = actor
    session.add(
        AuditEvent(
            event_type=AuditEventType.VISUAL_ASSET_APPROVED,
            actor=actor,
            payload_json={
                "asset_id": str(asset.id),
                "sha256": asset.sha256,
                "prior_state": prior.value,
                "new_state": asset.status.value,
                "note": note,
            },
        )
    )
    return asset


def deprecate_asset(
    session: Session, asset: VisualAsset, *, actor: str = OWNER, note: str | None = None
) -> VisualAsset:
    """Retire an asset from production without destroying it.

    §12: bytes an approved master or a finished clip depends on are never hard
    deleted. A deprecated asset stays resolvable, and its links stay intact, so
    the history of what was used remains readable.
    """
    prior = asset.status
    asset.status = VisualAssetStatus.DEPRECATED
    session.add(
        AuditEvent(
            event_type=AuditEventType.VISUAL_ASSET_DEPRECATED,
            actor=actor,
            payload_json={
                "asset_id": str(asset.id),
                "sha256": asset.sha256,
                "prior_state": prior.value,
                "new_state": asset.status.value,
                "note": note,
            },
        )
    )
    return asset


def attach_to_cast_member(
    session: Session,
    member: CastMember,
    asset: VisualAsset,
    *,
    role: str,
    is_primary: bool = False,
    sort_order: int | None = None,
    notes: str | None = None,
    actor: str = OWNER,
) -> CastMemberAsset:
    """File an asset as one of a member's references.

    Passing ``is_primary`` demotes whatever currently holds the badge for that
    role, rather than failing on the unique index: the caller is stating which
    image is the neutral head shot, and there can only be one answer.
    """
    role = _validated_role(role)

    link = session.execute(
        select(CastMemberAsset).where(
            CastMemberAsset.cast_member_id == member.id,
            CastMemberAsset.visual_asset_id == asset.id,
        )
    ).scalar_one_or_none()

    if sort_order is None:
        highest = session.execute(
            select(func.max(CastMemberAsset.sort_order)).where(
                CastMemberAsset.cast_member_id == member.id
            )
        ).scalar()
        sort_order = 0 if highest is None else highest + 1

    if link is None:
        link = CastMemberAsset(
            cast_member_id=member.id,
            visual_asset_id=asset.id,
            role=role,
            sort_order=sort_order,
            notes=notes,
        )
        session.add(link)
        changed = True
    else:
        changed = link.role != role
        link.role = role
        if notes is not None and notes != link.notes:
            link.notes = notes
            changed = True

    if is_primary and not link.is_primary:
        _demote_current_primary(session, member_id=member.id, role=role, keeping=asset.id)
        session.flush()
        link.is_primary = True
        changed = True

    session.flush()
    # Re-running an import re-states facts that are already true. Only an actual
    # change is something that happened, and the audit trail records what
    # happened.
    if changed:
        session.add(
            AuditEvent(
                event_type=AuditEventType.CAST_ASSET_LINKED,
                actor=actor,
                payload_json={
                    "cast_member": member.slug,
                    "asset_id": str(asset.id),
                    "sha256": asset.sha256,
                    "role": role,
                    "is_primary": link.is_primary,
                },
            )
        )
    return link


def _demote_current_primary(session: Session, *, member_id: Any, role: str, keeping: Any) -> None:
    for other in session.execute(
        select(CastMemberAsset).where(
            CastMemberAsset.cast_member_id == member_id,
            CastMemberAsset.role == role,
            CastMemberAsset.is_primary.is_(True),
            CastMemberAsset.visual_asset_id != keeping,
        )
    ).scalars():
        other.is_primary = False


def detach_from_cast_member(session: Session, link: CastMemberAsset) -> None:
    """Remove a reference from a member. The asset and its bytes remain.

    §11: delete means detach, not destroy. The asset keeps its identity, its
    audit trail and any lineage pointing at it.
    """
    session.delete(link)


def cast_member_by_slug(session: Session, slug: str) -> CastMember:
    member = session.execute(select(CastMember).where(CastMember.slug == slug)).scalars().first()
    if member is None:
        raise CastMemberNotFound(f"No cast member {slug!r}.")
    return member


class SceneMasterConflict(StudioError):
    """Approving this would leave a scene with two masters."""


def register_scene_master(
    session: Session,
    *,
    scene_key: str,
    asset: VisualAsset,
    notes: str | None = None,
    actor: str = OWNER,
) -> SceneMaster:
    """Record an image as a candidate master for one scene.

    Registering is not approving, §12. A candidate is a proposal; production
    resolves approved masters only, so an image can be registered and looked at
    without any generator being able to reach it.
    """
    existing = session.execute(
        select(SceneMaster).where(SceneMaster.visual_asset_id == asset.id)
    ).scalar_one_or_none()
    if existing is not None:
        if existing.scene_key != scene_key:
            raise SceneMasterConflict(
                f"That image is already the {existing.status} master for "
                f"{existing.scene_key!r}. One image is one master."
            )
        return existing

    master = SceneMaster(scene_key=scene_key, visual_asset_id=asset.id, notes=notes)
    session.add(master)
    session.flush()
    session.add(
        AuditEvent(
            event_type=AuditEventType.SCENE_MASTER_REGISTERED,
            actor=actor,
            payload_json={
                "scene_master_id": str(master.id),
                "scene_key": scene_key,
                "asset_id": str(asset.id),
                "sha256": asset.sha256,
            },
        )
    )
    return master


def approve_scene_master(
    session: Session, master: SceneMaster, *, actor: str = OWNER, note: str | None = None
) -> SceneMaster:
    """Make this the one master for its scene, superseding whatever held it.

    The previous approved master becomes ``superseded`` rather than being
    deleted or edited: coverage frames and finished clips cite it, and their
    lineage has to stay readable after it stops being current.
    """
    if master.asset.status is not VisualAssetStatus.APPROVED:
        raise SceneMasterConflict(
            f"The image is {master.asset.status.value}. Approve the asset before the master, "
            "so a scene cannot be built on something nobody approved."
        )

    previous = (
        session.execute(
            select(SceneMaster).where(
                SceneMaster.scene_key == master.scene_key,
                SceneMaster.status == "approved",
                SceneMaster.id != master.id,
            )
        )
        .scalars()
        .all()
    )
    for superseded in previous:
        superseded.status = "superseded"
        master.parent_master_id = master.parent_master_id or superseded.id
    session.flush()

    master.status = "approved"
    master.approved_at = dt.datetime.now(dt.UTC)
    master.approved_by = actor
    session.add(
        AuditEvent(
            event_type=AuditEventType.SCENE_MASTER_APPROVED,
            actor=actor,
            payload_json={
                "scene_master_id": str(master.id),
                "scene_key": master.scene_key,
                "asset_id": str(master.visual_asset_id),
                "sha256": master.asset.sha256,
                "superseded": [str(one.id) for one in previous],
                "note": note,
            },
        )
    )
    return master


def _as_png(data: bytes, mime_type: str) -> bytes:
    """PNG bytes, re-encoding only when the source is not already PNG."""
    if mime_type == "image/png":
        return data
    with Image.open(BytesIO(data)) as image:
        buffer = BytesIO()
        image.convert("RGB").save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


def legacy_filename_for(slug: str, role: str, asset: VisualAsset) -> str:
    """What the mirror should call this file on disk.

    Whatever it was called when it was imported, if the import recorded it --
    the point of the mirror is to keep working for code that opens a path, and
    that code was pointed at the name the owner chose. Only when nothing is
    recorded does it fall back to the current convention, ``<slug>-<suffix>``.
    """
    recorded = asset.metadata_json.get("legacy_filename")
    if isinstance(recorded, str) and recorded:
        return recorded
    return f"{slug}-{LEGACY_CAST_SUFFIXES[role]}"


def export_legacy_cast_mirror(session: Session, store: AssetStore, root: Path) -> list[Path]:
    """Rewrite ``var/cast/<slug>/`` from the database.

    A compatibility view, §10, for renderer code that still opens two fixed
    filenames. The database decides what those files contain; the files decide
    nothing. Only approved primaries in the two legacy roles can be expressed,
    which is exactly the limitation that made the library necessary.

    The legacy names end in ``.png`` and the renderer's cast upload accepted
    PNG only, so a JPEG reference is re-encoded on the way out rather than
    written under a name that lies about its format. The mirror is therefore
    not byte-identical to the asset; the asset remains the truth.

    Returns the paths written, so a caller can report them rather than claim.
    """
    written: list[Path] = []
    members = session.execute(select(CastMember).order_by(CastMember.slug)).scalars().all()

    for member in members:
        for role in PRIMARY_CAST_ROLES:
            link = session.execute(
                select(CastMemberAsset)
                .join(VisualAsset, VisualAsset.id == CastMemberAsset.visual_asset_id)
                .where(
                    CastMemberAsset.cast_member_id == member.id,
                    CastMemberAsset.role == role,
                    CastMemberAsset.is_primary.is_(True),
                    VisualAsset.status == VisualAssetStatus.APPROVED,
                )
            ).scalar_one_or_none()
            if link is None:
                continue

            asset = session.get(VisualAsset, link.visual_asset_id)
            if asset is None:  # pragma: no cover - foreign key prevents this
                continue

            destination = root / member.slug / legacy_filename_for(member.slug, role, asset)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(_as_png(store.load(asset.storage_key), asset.mime_type))
            written.append(destination)

    return written
