"""The Visual Asset Library: one asset substrate, plus the cast that uses it.

``studio/docs/VISUAL_ASSET_LIBRARY.md`` §9 and §18. Every production image —
cast reference, location plate, scene master, coverage frame — is a row in
``visual_assets``, and the domain tables link to it. That is what keeps SHA,
provenance, rights and lineage behaving identically across all of them.

Two deliberate departures from the document, both because the thing it proposes
already exists under another name:

* It proposes a ``characters`` table. One is already there, added by migration
  0029, and it is campaign-scoped: a role in one campaign's story, cascading
  away with it. Canonical cast outlives any campaign — Damo is Damo in every
  world he appears in — so the identity layer is :class:`CastMember`, world
  scoped, and ``characters.cast_member_id`` says which real person a story role
  is cast as. Reusing the campaign table would have made deleting a campaign
  delete the cast.
* It proposes ``rights_status`` as a new vocabulary. :class:`LicenceStatus`
  already carries exactly those three states for archive elements, and is
  already understood to mean "may this be used commercially", so it is reused.

``image_assets`` is left alone. Its ``attempt_id`` is not nullable and means
"a provider produced this", which an uploaded photograph of a person did not.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.base import NO_VALUE

from app.db.base import Base, TimestampMixin
from app.db.models import SHA256_HEX_LENGTH, _enum
from app.domain.enums import (
    LicenceStatus,
    VisualAssetKind,
    VisualAssetSourceType,
    VisualAssetStatus,
)
from app.domain.errors import StudioError


class VisualAsset(Base, TimestampMixin):
    """One immutable image, its identity and its provenance.

    Bytes live in the asset store under ``storage_key``; this row owns
    everything else. §9: ``sha256``, ``byte_size``, the dimensions and the
    storage key are immutable after creation — different bytes are a different
    asset, never an edit of this one. The database enforces that by making the
    hash unique, so ingesting the same file twice returns the existing row
    instead of creating a second identity for it.
    """

    __tablename__ = "visual_assets"
    __table_args__ = (
        UniqueConstraint("sha256", name="uq_visual_assets_sha256"),
        Index("ix_visual_assets_kind_status", "kind", "status"),
        Index("ix_visual_assets_source_type", "source_type"),
        Index("ix_visual_assets_rights_status", "rights_status"),
        CheckConstraint("width > 0 AND height > 0", name="dimensions_positive"),
        CheckConstraint("byte_size > 0", name="byte_size_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    kind: Mapped[VisualAssetKind] = mapped_column(
        _enum(VisualAssetKind, "visual_asset_kind"), nullable=False
    )
    # What the image is of, within its kind. Free text on purpose; see
    # CAST_ASSET_ROLES. Null where the kind alone says everything.
    role: Mapped[str | None] = mapped_column(String(64))
    # Relative to ASSETS_ROOT, so the same row works on any host.
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(SHA256_HEX_LENGTH), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[VisualAssetSourceType] = mapped_column(
        _enum(VisualAssetSourceType, "visual_asset_source_type"), nullable=False
    )
    provider: Mapped[str | None] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(128))
    provider_request_id: Mapped[str | None] = mapped_column(String(128))
    prompt_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))
    status: Mapped[VisualAssetStatus] = mapped_column(
        _enum(VisualAssetStatus, "visual_asset_status"),
        nullable=False,
        default=VisualAssetStatus.PENDING,
        server_default=VisualAssetStatus.PENDING.value,
    )
    # Unknown rights do not stop an asset being held or looked at. They stop it
    # being promoted to something production reaches, §6.4.
    rights_status: Mapped[LicenceStatus] = mapped_column(
        _enum(LicenceStatus, "licence_status"),
        nullable=False,
        default=LicenceStatus.UNVERIFIED,
        server_default=LicenceStatus.UNVERIFIED.value,
    )
    rights_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata_json", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    description: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[str | None] = mapped_column(String(64))

    @property
    def aspect_ratio(self) -> float:
        """Width over height. Derived, never stored: it cannot disagree this way."""
        return self.width / self.height

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<VisualAsset {self.kind.value!r} {self.role!r} {self.sha256[:12]}>"


class AssetLineage(Base):
    """How one asset came from another.

    §9.1. A coverage frame's parent is its scene master; a scene master's parent
    is the location plate it was composited into. Stored as edges rather than
    inferred from filenames, which is what the current tooling does and what
    stops being true the moment a file is renamed.
    """

    __tablename__ = "asset_lineage"
    __table_args__ = (
        UniqueConstraint(
            "parent_asset_id",
            "child_asset_id",
            "relationship",
            name="uq_asset_lineage_parent_asset_id_child_asset_id_relationship",
        ),
        CheckConstraint("parent_asset_id <> child_asset_id", name="no_self_lineage"),
        Index("ix_asset_lineage_child_asset_id", "child_asset_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    parent_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visual_assets.id", ondelete="RESTRICT"), nullable=False
    )
    child_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visual_assets.id", ondelete="CASCADE"), nullable=False
    )
    # crop / edit / generated_from / composited_into / upscaled / colour_corrected.
    relationship_kind: Mapped[str] = mapped_column("relationship", String(48), nullable=False)
    operation_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class CastMember(Base, TimestampMixin):
    """A canonical person in the universe, and the owner of their references.

    Identity and descriptive canon live here. The photographs are separate
    assets linked through :class:`CastMemberAsset`, so a member can have three
    references or twenty without the schema changing shape, §5.1.

    ``world_id`` is nullable: a member may be global, reusable across worlds.
    """

    __tablename__ = "cast_members"
    __table_args__ = (
        UniqueConstraint("world_id", "slug", name="uq_cast_members_world_id_slug"),
        Index("ix_cast_members_status", "status"),
        CheckConstraint("status IN ('active','deprecated')", name="status_known"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    world_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE")
    )
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Age band, build, hair, marks — the continuity facts that must not drift.
    canonical_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="active")

    assets: Mapped[list[CastMemberAsset]] = relationship(
        back_populates="cast_member",
        cascade="all, delete-orphan",
        order_by="CastMemberAsset.sort_order",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<CastMember {self.slug!r}>"


class CastMemberAsset(Base, TimestampMixin):
    """One reference photograph, in one role, for one cast member.

    The link carries the role, the ordering and the primary badge, because they
    are facts about this member's use of the image rather than about the image.
    The same photograph could legitimately be filed under two members — a
    two-hander — without either of them owning it.
    """

    __tablename__ = "cast_member_assets"
    __table_args__ = (
        UniqueConstraint(
            "cast_member_id",
            "visual_asset_id",
            name="uq_cast_member_assets_cast_member_id_visual_asset_id",
        ),
        # One primary per role per member. A second "the neutral head shot" is
        # ambiguity the renderer would have to resolve by guessing.
        Index(
            "uq_cast_member_assets_primary_per_role",
            "cast_member_id",
            "role",
            unique=True,
            postgresql_where=text("is_primary"),
        ),
        Index("ix_cast_member_assets_visual_asset_id", "visual_asset_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cast_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cast_members.id", ondelete="CASCADE"), nullable=False
    )
    visual_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visual_assets.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    notes: Mapped[str | None] = mapped_column(Text)

    cast_member: Mapped[CastMember] = relationship(back_populates="assets")
    asset: Mapped[VisualAsset] = relationship(lazy="joined")


class Tag(Base):
    """A reusable label, §9.2: ``pub``, ``night``, ``2.39``, ``production-safe``."""

    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("slug", name="uq_tags_slug"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class VisualAssetTag(Base):
    """Which tags an asset carries."""

    __tablename__ = "visual_asset_tags"

    visual_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("visual_assets.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class AssetIsImmutable(StudioError):
    """Something tried to change what an asset's bytes are."""


# §9: the hash, the size, the dimensions and the key are fixed at creation.
# Different bytes are a different asset. A CHECK constraint cannot express
# "never changes", so the rule is enforced where the change would be made.
IMMUTABLE_ASSET_FIELDS = ("sha256", "byte_size", "width", "height", "storage_key", "mime_type")


def _refuse_mutation(target: VisualAsset, value: Any, old: Any, _initiator: Any) -> Any:
    """Reject an edit to an immutable field once the row exists."""
    if old is NO_VALUE or old is None or old == value:
        return value
    raise AssetIsImmutable(
        f"Asset {target.sha256[:12]}: bytes and their measurements cannot be edited. "
        "Ingest the new image as its own asset and record the lineage."
    )


for _field in IMMUTABLE_ASSET_FIELDS:
    event.listen(getattr(VisualAsset, _field), "set", _refuse_mutation, retval=True)
