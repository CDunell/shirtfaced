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
  role, or two approved scene masters, raise. Nothing here picks the newest
  file, the newest row, or the first one it happens to see.
* **A missing file is not a missing asset.** If the row exists and the bytes do
  not, that is said plainly, because the two have completely different fixes.
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore, AssetStoreError
from app.db.visual_models import CastMember, CastMemberAsset, VisualAsset
from app.domain.enums import VisualAssetKind, VisualAssetStatus
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


def _load(store: AssetStore, asset: VisualAsset, label: str) -> ResolvedReference:
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
    return _load(store, asset, name)


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
    return _load(store, asset, label)


def resolve_only_approved(
    session: Session,
    store: AssetStore,
    *,
    kind: VisualAssetKind,
    role: str | None = None,
    label: str | None = None,
) -> ResolvedReference:
    """The single approved asset of a kind, or a refusal naming the candidates.

    For inputs that have no owning record yet -- a scene master, before §7's
    tables exist. It replaces selection by newest modification time, which is
    the one resolution rule the document forbids by name: a file touched by a
    backup is not an approval.
    """
    name = label or f"{kind.value}{'/' + role if role else ''}"
    query = select(VisualAsset).where(
        VisualAsset.kind == kind, VisualAsset.status == VisualAssetStatus.APPROVED
    )
    if role is not None:
        query = query.where(VisualAsset.role == role)

    candidates = session.execute(query.order_by(VisualAsset.created_at)).scalars().all()

    if not candidates:
        raise ReferenceUnavailable(
            f"{name}: no approved {kind.value} asset is registered. "
            "Ingest it and approve it before generating against it."
        )
    if len(candidates) > 1:
        listed = ", ".join(f"{asset.id} ({asset.sha256[:12]})" for asset in candidates)
        raise ReferenceUnavailable(
            f"{name}: {len(candidates)} approved {kind.value} assets. Name one explicitly. "
            f"Candidates: {listed}."
        )

    return _load(store, candidates[0], name)
