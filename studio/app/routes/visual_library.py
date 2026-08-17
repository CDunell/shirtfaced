"""The Visual Asset Library over HTTP.

``studio/docs/VISUAL_ASSET_LIBRARY.md`` §11, cast subset. What the renderer's
cast form did -- validate, hash, store -- happens here too, but the result is a
row with an identity rather than a file at a fixed path, so a member can have a
third reference, or a twentieth, without a code change.

Bytes are served from ``/api/visual-assets/{id}/bytes`` by database key, never
by a path from the request.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.adapters.asset_store import AssetStoreError, FilesystemAssetStore
from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.db.visual_models import CastMember, CastMemberAsset, VisualAsset
from app.domain.enums import (
    CAST_ASSET_ROLES,
    LicenceStatus,
    VisualAssetKind,
    VisualAssetSourceType,
    VisualAssetStatus,
)
from app.domain.errors import StudioError
from app.services import visual_library

router = APIRouter(prefix="/api", tags=["visual-library"])

SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]

# An asset's bytes never change, so the URL can be cached hard.
CACHE_CONTROL = "private, max-age=31536000, immutable"


class AssetOut(BaseModel):
    """One asset as the interface needs it."""

    id: uuid.UUID
    kind: VisualAssetKind
    role: str | None
    sha256: str
    mime_type: str
    width: int
    height: int
    byte_size: int
    aspect_ratio: float
    source_type: VisualAssetSourceType
    status: VisualAssetStatus
    rights_status: LicenceStatus
    description: str | None
    approved_by: str | None

    @classmethod
    def of(cls, asset: VisualAsset) -> AssetOut:
        return cls(
            id=asset.id,
            kind=asset.kind,
            role=asset.role,
            sha256=asset.sha256,
            mime_type=asset.mime_type,
            width=asset.width,
            height=asset.height,
            byte_size=asset.byte_size,
            aspect_ratio=round(asset.aspect_ratio, 4),
            source_type=asset.source_type,
            status=asset.status,
            rights_status=asset.rights_status,
            description=asset.description,
            approved_by=asset.approved_by,
        )


class CastAssetOut(BaseModel):
    """An asset in its place on a member's reference strip."""

    link_id: uuid.UUID
    role: str
    sort_order: int
    is_primary: bool
    notes: str | None
    asset: AssetOut
    # Set when an upload turned out to be bytes the library already held, so
    # the interface can say so instead of implying a new photograph arrived.
    duplicate_of: uuid.UUID | None = None


class CastMemberOut(BaseModel):
    slug: str
    id: uuid.UUID
    display_name: str
    description: str | None
    status: str
    canonical_metadata: dict[str, Any]
    assets: list[CastAssetOut]


class CastMemberIn(BaseModel):
    slug: str = Field(min_length=1, max_length=64)
    display_name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    canonical_metadata: dict[str, Any] = Field(default_factory=dict)


class LinkUpdateIn(BaseModel):
    """Role, order and the primary badge. Nothing here touches the bytes."""

    role: str | None = None
    sort_order: int | None = None
    is_primary: bool | None = None
    notes: str | None = None


class DecisionIn(BaseModel):
    note: str | None = None
    actor: str = "owner"


def _store(settings: Settings) -> FilesystemAssetStore:
    return FilesystemAssetStore(settings.assets_root_resolved)


def _member_out(member: CastMember) -> CastMemberOut:
    return CastMemberOut(
        slug=member.slug,
        id=member.id,
        display_name=member.display_name,
        description=member.description,
        status=member.status,
        canonical_metadata=member.canonical_metadata,
        assets=[
            CastAssetOut(
                link_id=link.id,
                role=link.role,
                sort_order=link.sort_order,
                is_primary=link.is_primary,
                notes=link.notes,
                asset=AssetOut.of(link.asset),
            )
            for link in sorted(member.assets, key=lambda link: (link.sort_order, link.role))
        ],
    )


def _get_member(session: Session, slug: str) -> CastMember:
    member = (
        session.execute(
            select(CastMember)
            .options(selectinload(CastMember.assets).selectinload(CastMemberAsset.asset))
            .where(CastMember.slug == slug)
        )
        .scalars()
        .first()
    )
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No cast member {slug!r}.")
    return member


def _get_asset(session: Session, asset_id: uuid.UUID) -> VisualAsset:
    asset = session.get(VisualAsset, asset_id)
    if asset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such asset.")
    return asset


@router.get("/cast", summary="Every cast member and their references")
def list_cast(session: SessionDependency) -> list[CastMemberOut]:
    members = (
        session.execute(
            select(CastMember)
            .options(selectinload(CastMember.assets).selectinload(CastMemberAsset.asset))
            .order_by(CastMember.slug)
        )
        .scalars()
        .unique()
    )
    return [_member_out(member) for member in members]


@router.get("/cast/roles", summary="The reference roles the interface offers")
def list_roles() -> list[str]:
    """A vocabulary, not a constraint: any slug can be stored, §5.2."""
    return list(CAST_ASSET_ROLES)


@router.get("/cast/{slug}", summary="One cast member")
def get_cast_member(slug: str, session: SessionDependency) -> CastMemberOut:
    return _member_out(_get_member(session, slug))


@router.post("/cast", status_code=status.HTTP_201_CREATED, summary="Add a cast member")
def create_cast_member(payload: CastMemberIn, session: SessionDependency) -> CastMemberOut:
    existing = (
        session.execute(select(CastMember).where(CastMember.slug == payload.slug)).scalars().first()
    )
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{payload.slug!r} already exists.")

    member = CastMember(
        slug=payload.slug,
        display_name=payload.display_name,
        description=payload.description,
        canonical_metadata=payload.canonical_metadata,
    )
    session.add(member)
    session.commit()
    return _member_out(_get_member(session, member.slug))


@router.post(
    "/cast/{slug}/assets",
    status_code=status.HTTP_201_CREATED,
    summary="Upload a reference for a cast member",
)
async def upload_cast_asset(
    slug: str,
    session: SessionDependency,
    settings: SettingsDependency,
    file: Annotated[UploadFile, File()],
    role: Annotated[str, Form()],
    description: Annotated[str | None, Form()] = None,
    is_primary: Annotated[bool, Form()] = False,
    approve: Annotated[bool, Form()] = False,
    source_type: Annotated[VisualAssetSourceType, Form()] = VisualAssetSourceType.UPLOAD,
) -> CastAssetOut:
    """Validate, hash, store, link -- the ten steps of §5.3, in one request.

    Re-uploading a file already held is not an error. It returns the existing
    asset and files it under the requested role, which is what the person
    meant; a duplicate SHA is reported through ``duplicate_of`` rather than a
    refusal that loses the intent.
    """
    member = _get_member(session, slug)
    data = await file.read(visual_library.MAX_ASSET_BYTES + 1)

    try:
        ingested = visual_library.ingest_asset(
            session,
            _store(settings),
            data=data,
            kind=VisualAssetKind.CAST,
            source_type=source_type,
            role=role,
            description=description,
        )
        link = visual_library.attach_to_cast_member(
            session, member, ingested.asset, role=role, is_primary=is_primary
        )
        if approve:
            visual_library.approve_asset(session, ingested.asset)
    except visual_library.AssetRejected as error:
        session.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except (AssetStoreError, StudioError) as error:
        session.rollback()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error

    session.commit()
    session.refresh(link)
    return CastAssetOut(
        link_id=link.id,
        role=link.role,
        sort_order=link.sort_order,
        is_primary=link.is_primary,
        notes=link.notes,
        asset=AssetOut.of(link.asset),
        duplicate_of=None if ingested.created else ingested.asset.id,
    )


@router.patch("/cast/{slug}/assets/{link_id}", summary="Role, order or primary badge")
def update_cast_asset(
    slug: str, link_id: uuid.UUID, payload: LinkUpdateIn, session: SessionDependency
) -> CastAssetOut:
    member = _get_member(session, slug)
    link = session.get(CastMemberAsset, link_id)
    if link is None or link.cast_member_id != member.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such reference on this member.")

    if payload.role is not None:
        link.role = payload.role
    if payload.sort_order is not None:
        link.sort_order = payload.sort_order
    if payload.notes is not None:
        link.notes = payload.notes
    if payload.is_primary is not None:
        if payload.is_primary:
            visual_library.attach_to_cast_member(
                session,
                member,
                link.asset,
                role=link.role,
                is_primary=True,
                sort_order=link.sort_order,
            )
        else:
            link.is_primary = False

    session.commit()
    session.refresh(link)
    return CastAssetOut(
        link_id=link.id,
        role=link.role,
        sort_order=link.sort_order,
        is_primary=link.is_primary,
        notes=link.notes,
        asset=AssetOut.of(link.asset),
    )


@router.delete(
    "/cast/{slug}/assets/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Detach a reference. The asset and its bytes remain",
)
def detach_cast_asset(slug: str, link_id: uuid.UUID, session: SessionDependency) -> Response:
    member = _get_member(session, slug)
    link = session.get(CastMemberAsset, link_id)
    if link is None or link.cast_member_id != member.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such reference on this member.")

    visual_library.detach_from_cast_member(session, link)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/visual-assets", summary="Search the library")
def search_assets(
    session: SessionDependency,
    kind: Annotated[VisualAssetKind | None, Query()] = None,
    asset_status: Annotated[VisualAssetStatus | None, Query(alias="status")] = None,
    role: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AssetOut]:
    query = select(VisualAsset).order_by(VisualAsset.created_at.desc()).limit(limit)
    if kind is not None:
        query = query.where(VisualAsset.kind == kind)
    if asset_status is not None:
        query = query.where(VisualAsset.status == asset_status)
    if role is not None:
        query = query.where(VisualAsset.role == role)
    return [AssetOut.of(asset) for asset in session.execute(query).scalars()]


@router.get("/visual-assets/{asset_id}", summary="One asset")
def get_visual_asset(asset_id: uuid.UUID, session: SessionDependency) -> AssetOut:
    return AssetOut.of(_get_asset(session, asset_id))


@router.get("/visual-assets/{asset_id}/bytes", summary="The image itself")
def get_visual_asset_bytes(
    asset_id: uuid.UUID, session: SessionDependency, settings: SettingsDependency
) -> Response:
    asset = _get_asset(session, asset_id)
    try:
        data = _store(settings).load(asset.storage_key)
    except AssetStoreError as error:
        # The row exists but the bytes do not. Say which, rather than 404.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    return Response(
        content=data, media_type=asset.mime_type, headers={"Cache-Control": CACHE_CONTROL}
    )


@router.post("/visual-assets/{asset_id}/approve", summary="Approve for production use")
def approve_visual_asset(
    asset_id: uuid.UUID, payload: DecisionIn, session: SessionDependency
) -> AssetOut:
    asset = visual_library.approve_asset(
        session, _get_asset(session, asset_id), actor=payload.actor, note=payload.note
    )
    session.commit()
    session.refresh(asset)
    return AssetOut.of(asset)


@router.post("/visual-assets/{asset_id}/deprecate", summary="Retire without deleting")
def deprecate_visual_asset(
    asset_id: uuid.UUID, payload: DecisionIn, session: SessionDependency
) -> AssetOut:
    asset = visual_library.deprecate_asset(
        session, _get_asset(session, asset_id), actor=payload.actor, note=payload.note
    )
    session.commit()
    session.refresh(asset)
    return AssetOut.of(asset)
