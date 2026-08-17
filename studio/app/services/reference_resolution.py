"""Resolving a production reference to exact bytes, by identity.

``VISUAL_ASSET_LIBRARY.md`` §14 Phase 5. Before this, every consumer opened a
path: ``var/cast/damo/b-head-shoulders.png`` in three scripts and six of them in
the renderer route. On 17 August 2026 those files were renamed and every one of
those callers broke at once, which is the argument for this module stated as an
incident.

A resolution here answers with an asset ID and the SHA-256 of the bytes it
returns, and the caller records both. That is what makes a generated frame
traceable: the manifest does not say "the file that was at this path that day",
it says which asset, and what its bytes hashed to.

Three refusals, all of them §13's production-readiness gate rather than taste:

* **Not approved is not usable.** Pending means it arrived; it does not mean
  anyone decided. Deprecated means someone decided against it.
* **Ambiguity is a refusal, not a coin toss.** Two approved primaries for one
  role, or two approved masters for one scene, raise. Nothing here picks the
  newest file, the newest row, or the first name in a preference list.
* **A missing file is not a missing asset.** If the row exists and the bytes do
  not, that is said plainly, because the two have completely different fixes.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore, AssetStoreError
from app.db.visual_models import CastMember, CastMemberAsset, SceneMaster, VisualAsset
from app.domain.enums import VisualAssetStatus
from app.domain.errors import StudioError

logger = logging.getLogger(__name__)


class ReferenceUnavailable(StudioError):
    """No approved asset answers this request, and none may be substituted."""


@dataclass(frozen=True)
class ResolvedReference:
    """Bytes, and the identity they came from.

    ``sha256`` is recomputed from the bytes actually loaded rather than copied
    from the row. A row and a file that disagree is exactly the corruption this
    is meant to catch, and copying the stored hash would hide it.
    """

    asset_id: uuid.UUID
    sha256: str
    stored_sha256: str
    data: bytes
    mime_type: str
    width: int
    height: int
    role: str | None
    label: str

    @property
    def intact(self) -> bool:
        return self.sha256 == self.stored_sha256

    def as_manifest(self) -> dict[str, object]:
        """What a generation manifest should record about this input."""
        return {
            "label": self.label,
            "asset_id": str(self.asset_id),
            "sha256": self.sha256,
            "role": self.role,
            "mime_type": self.mime_type,
            "dimensions": [self.width, self.height],
        }


def load_reference(store: AssetStore, asset: VisualAsset, label: str) -> ResolvedReference:
    try:
        data = store.load(asset.storage_key)
    except AssetStoreError as error:
        raise ReferenceUnavailable(
            f"{label}: asset {asset.id} is recorded but its bytes could not be read. {error}"
        ) from error

    digest = hashlib.sha256(data).hexdigest()
    if digest != asset.sha256:
        # Never returned. A reference whose bytes are not the bytes that were
        # approved is not the reference, whatever the path says.
        raise ReferenceUnavailable(
            f"{label}: asset {asset.id} stores {asset.sha256[:12]} but the file hashes to "
            f"{digest[:12]}. The store has been altered underneath the database."
        )

    return ResolvedReference(
        asset_id=asset.id,
        sha256=digest,
        stored_sha256=asset.sha256,
        data=data,
        mime_type=asset.mime_type,
        width=asset.width,
        height=asset.height,
        role=asset.role,
        label=label,
    )


def _require_approved(asset: VisualAsset, label: str) -> None:
    if asset.status is not VisualAssetStatus.APPROVED:
        raise ReferenceUnavailable(
            f"{label}: asset {asset.id} is {asset.status.value}, not approved. "
            "Approve it in the Cast library, or name a different asset."
        )


def resolve_asset(
    session: Session, store: AssetStore, asset_id: uuid.UUID, *, label: str | None = None
) -> ResolvedReference:
    """Resolve one asset by its identifier. The explicit form, always allowed."""
    name = label or str(asset_id)
    asset = session.get(VisualAsset, asset_id)
    if asset is None:
        raise ReferenceUnavailable(f"{name}: no asset {asset_id}.")
    _require_approved(asset, name)
    return load_reference(store, asset, name)


def resolve_cast_reference(
    session: Session, store: AssetStore, *, slug: str, role: str
) -> ResolvedReference:
    """The approved primary reference for one cast member in one role.

    This is what replaces ``var/cast/<slug>/<something>.png``. The filename is
    not consulted, so renaming the mirror cannot change what a scene is built
    from -- and neither can adding a fourth photograph, unless someone makes it
    the primary on purpose.
    """
    label = f"{slug}/{role}"
    member = session.execute(select(CastMember).where(CastMember.slug == slug)).scalars().first()
    if member is None:
        raise ReferenceUnavailable(f"{label}: no cast member {slug!r}.")

    links = (
        session.execute(
            select(CastMemberAsset).where(
                CastMemberAsset.cast_member_id == member.id,
                CastMemberAsset.role == role,
                CastMemberAsset.is_primary.is_(True),
            )
        )
        .scalars()
        .all()
    )

    if not links:
        held = (
            session.execute(
                select(CastMemberAsset.role).where(CastMemberAsset.cast_member_id == member.id)
            )
            .scalars()
            .all()
        )
        raise ReferenceUnavailable(
            f"{label}: {member.display_name} has no primary {role!r} reference. "
            f"Held: {', '.join(sorted(set(held))) or 'nothing'}."
        )
    if len(links) > 1:  # pragma: no cover - the partial unique index prevents this
        raise ReferenceUnavailable(
            f"{label}: {len(links)} primaries for one role. Refusing to choose."
        )

    asset = session.get(VisualAsset, links[0].visual_asset_id)
    if asset is None:  # pragma: no cover - foreign key prevents this
        raise ReferenceUnavailable(f"{label}: the linked asset is missing.")
    _require_approved(asset, label)
    return load_reference(store, asset, label)


def resolve_scene_master(
    session: Session, store: AssetStore, *, scene_key: str
) -> ResolvedReference:
    """The approved master for one scene, by scene, and only ever one.

    This replaces two different guesses at the same question. The coverage tool
    tried ``composition-gpt.png``, then ``.jpg``, then ``.jpeg`` and took the
    first that existed; the rich-pub script took whichever of them had the
    newest modification time. Both were answering "which file", not "which
    master", and on the production box those two files are different images.

    A scene with no approved master is a refusal. It is not an invitation to
    fall back to a directory.
    """
    label = f"scene:{scene_key}"
    masters = (
        session.execute(select(SceneMaster).where(SceneMaster.scene_key == scene_key))
        .scalars()
        .all()
    )
    approved = [master for master in masters if master.status == "approved"]

    if not approved:
        if masters:
            states = ", ".join(sorted({master.status for master in masters}))
            raise ReferenceUnavailable(
                f"{label}: no approved master. {len(masters)} registered ({states}). "
                "Approve one before generating against this scene."
            )
        raise ReferenceUnavailable(
            f"{label}: no master is registered for this scene. Register the approved "
            "composition and approve it before anything is generated from it."
        )
    if len(approved) > 1:  # pragma: no cover - the partial unique index prevents this
        raise ReferenceUnavailable(
            f"{label}: {len(approved)} approved masters. Refusing to choose."
        )

    master = approved[0]
    asset = session.get(VisualAsset, master.visual_asset_id)
    if asset is None:  # pragma: no cover - foreign key prevents this
        raise ReferenceUnavailable(f"{label}: the master's asset is missing.")
    _require_approved(asset, label)
    return load_reference(store, asset, label)


def verify_coverage_seed(
    session: Session, store: AssetStore, *, seed: Path, scene_key: str
) -> dict[str, object]:
    """Refuse a Veo seed that is not coverage of this scene's approved master.

    A seed is a 9:16 crop the coverage tool saved, with a manifest beside it
    naming the master it came from. The Veo scripts used to take a path and the
    SHA of that same path -- self-consistent, and silent about whether the frame
    belonged to the master the scene is actually built on. The production box
    holds four coverage frames whose parent SHA matches no file that exists any
    more, so that distinction is not hypothetical.

    Returns the lineage a run should record: which master, which frame.

    Reads the manifest from disk because coverage frames are not database rows
    yet -- §8 is unbuilt. When they are, this reads the row instead and the
    manifest becomes an export like every other file under ``var``.
    """
    manifest_path = seed.parent / "manifest.json"
    if not manifest_path.is_file():
        raise ReferenceUnavailable(
            f"{seed.name}: no coverage manifest beside the seed, so the master it was cut "
            "from cannot be established."
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReferenceUnavailable(f"{manifest_path}: unreadable coverage manifest.") from error

    master = resolve_scene_master(session, store, scene_key=scene_key)

    parent = manifest.get("source_sha256")
    if parent != master.sha256:
        raise ReferenceUnavailable(
            f"{seed.name} was cut from master {str(parent)[:12]}, but the approved master "
            f"for {scene_key} is {master.sha256[:12]} (asset {master.asset_id}). Re-cut the "
            "coverage from the approved master."
        )

    return {
        "scene": scene_key,
        "scene_master_asset_id": str(master.asset_id),
        "scene_master_sha256": master.sha256,
        "coverage_shot": manifest.get("shot"),
        "coverage_frame_sha256": manifest.get("frame_sha256"),
    }
