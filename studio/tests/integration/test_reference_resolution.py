"""What production is allowed to resolve, and what it must refuse.

``VISUAL_ASSET_LIBRARY.md`` §14 Phase 5 and §13. Every case here is a way the
old path-based resolution could hand a generator the wrong bytes and say
nothing: an unapproved image, a deprecated one, a file replaced underneath the
row, or a directory with two candidates and an mtime to break the tie.
"""

from __future__ import annotations

import uuid
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.db.visual_models import CastMember
from app.domain.enums import VisualAssetKind, VisualAssetSourceType
from app.services import visual_library
from app.services.reference_resolution import (
    ReferenceUnavailable,
    resolve_asset,
    resolve_cast_reference,
    resolve_only_approved,
)

pytestmark = pytest.mark.integration


def png(colour: tuple[int, int, int] = (120, 90, 60)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (600, 800), colour).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def store(tmp_path: Path) -> FilesystemAssetStore:
    return FilesystemAssetStore(tmp_path / "assets")


@pytest.fixture
def damo(session: Session) -> CastMember:
    member = CastMember(slug="damo", display_name="Damo")
    session.add(member)
    session.flush()
    return member


def add(
    session: Session,
    store: FilesystemAssetStore,
    member: CastMember | None,
    *,
    role: str,
    colour: tuple[int, int, int],
    approve: bool = True,
    primary: bool = True,
    kind: VisualAssetKind = VisualAssetKind.CAST,
):
    ingested = visual_library.ingest_asset(
        session,
        store,
        data=png(colour),
        kind=kind,
        source_type=VisualAssetSourceType.UPLOAD,
        role=role,
    )
    if approve:
        visual_library.approve_asset(session, ingested.asset)
    if member is not None:
        visual_library.attach_to_cast_member(
            session, member, ingested.asset, role=role, is_primary=primary
        )
    session.flush()
    return ingested.asset


def test_the_primary_reference_resolves_to_its_exact_bytes(
    session: Session, store: FilesystemAssetStore, damo: CastMember
) -> None:
    asset = add(session, store, damo, role="head_shoulders_neutral", colour=(1, 2, 3))

    resolved = resolve_cast_reference(session, store, slug="damo", role="head_shoulders_neutral")

    assert resolved.asset_id == asset.id
    assert resolved.sha256 == asset.sha256
    assert resolved.intact
    assert resolved.as_manifest()["asset_id"] == str(asset.id)


def test_renaming_the_mirror_cannot_change_what_resolves(
    session: Session, store: FilesystemAssetStore, damo: CastMember, tmp_path: Path
) -> None:
    """The 17 August rename. Resolution never consults a filename."""
    asset = add(session, store, damo, role="head_shoulders_neutral", colour=(4, 5, 6))
    mirror = tmp_path / "cast"
    visual_library.export_legacy_cast_mirror(session, store, mirror)
    for path in (mirror / "damo").iterdir():
        path.rename(path.with_name(f"renamed-{path.name}"))

    resolved = resolve_cast_reference(session, store, slug="damo", role="head_shoulders_neutral")
    assert resolved.sha256 == asset.sha256


def test_a_pending_reference_is_refused(
    session: Session, store: FilesystemAssetStore, damo: CastMember
) -> None:
    """Arriving is not being decided on."""
    add(session, store, damo, role="expression_bridge", colour=(7, 8, 9), approve=False)

    with pytest.raises(ReferenceUnavailable, match="pending"):
        resolve_cast_reference(session, store, slug="damo", role="expression_bridge")


def test_a_deprecated_reference_is_refused(
    session: Session, store: FilesystemAssetStore, damo: CastMember
) -> None:
    asset = add(session, store, damo, role="head_shoulders_neutral", colour=(10, 11, 12))
    visual_library.deprecate_asset(session, asset, note="Superseded")
    session.flush()

    with pytest.raises(ReferenceUnavailable, match="deprecated"):
        resolve_cast_reference(session, store, slug="damo", role="head_shoulders_neutral")


def test_a_role_with_no_primary_says_what_is_held(
    session: Session, store: FilesystemAssetStore, damo: CastMember
) -> None:
    add(session, store, damo, role="head_shoulders_neutral", colour=(13, 14, 15))

    with pytest.raises(ReferenceUnavailable, match="full_body_neutral"):
        resolve_cast_reference(session, store, slug="damo", role="full_body_neutral")


def test_an_unknown_member_is_refused(session: Session, store: FilesystemAssetStore) -> None:
    with pytest.raises(ReferenceUnavailable, match="no cast member"):
        resolve_cast_reference(session, store, slug="nobody", role="head_shoulders_neutral")


def test_bytes_replaced_underneath_the_row_are_refused(
    session: Session, store: FilesystemAssetStore, damo: CastMember
) -> None:
    """The failure a path-based read reports as success."""
    asset = add(session, store, damo, role="head_shoulders_neutral", colour=(16, 17, 18))
    store.save(asset.storage_key, png(colour=(99, 99, 99)), asset.mime_type)

    with pytest.raises(ReferenceUnavailable, match="altered underneath"):
        resolve_cast_reference(session, store, slug="damo", role="head_shoulders_neutral")


def test_a_missing_file_is_not_reported_as_a_missing_asset(
    session: Session, store: FilesystemAssetStore, damo: CastMember
) -> None:
    asset = add(session, store, damo, role="head_shoulders_neutral", colour=(19, 20, 21))
    path = store.path_for(asset.storage_key)
    assert path is not None
    path.unlink()

    with pytest.raises(ReferenceUnavailable, match="recorded but its bytes"):
        resolve_cast_reference(session, store, slug="damo", role="head_shoulders_neutral")


def test_two_approved_masters_refuse_rather_than_choose(
    session: Session, store: FilesystemAssetStore
) -> None:
    """No newest-mtime, no newest row. Ambiguity is a refusal."""
    add(
        session,
        store,
        None,
        role="pub-1105",
        colour=(22, 23, 24),
        kind=VisualAssetKind.SCENE_MASTER,
    )

    resolved = resolve_only_approved(session, store, kind=VisualAssetKind.SCENE_MASTER)
    assert resolved.role == "pub-1105"

    add(
        session,
        store,
        None,
        role="pub-1105",
        colour=(25, 26, 27),
        kind=VisualAssetKind.SCENE_MASTER,
    )
    with pytest.raises(ReferenceUnavailable, match="2 approved"):
        resolve_only_approved(session, store, kind=VisualAssetKind.SCENE_MASTER)


def test_no_approved_master_is_a_refusal_not_a_fallback(
    session: Session, store: FilesystemAssetStore
) -> None:
    add(
        session,
        store,
        None,
        role="pub-1105",
        colour=(28, 29, 30),
        kind=VisualAssetKind.SCENE_MASTER,
        approve=False,
    )

    with pytest.raises(ReferenceUnavailable, match="no approved scene_master"):
        resolve_only_approved(session, store, kind=VisualAssetKind.SCENE_MASTER)


def test_an_asset_resolves_by_explicit_identifier(
    session: Session, store: FilesystemAssetStore, damo: CastMember
) -> None:
    asset = add(session, store, damo, role="head_shoulders_neutral", colour=(31, 32, 33))
    assert resolve_asset(session, store, asset.id).sha256 == asset.sha256

    with pytest.raises(ReferenceUnavailable, match="no asset"):
        resolve_asset(session, store, uuid.uuid4())
