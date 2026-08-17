"""What production is allowed to resolve, and what it must refuse.

``VISUAL_ASSET_LIBRARY.md`` §14 Phase 5 and §13. Every case here is a way the
old path-based resolution could hand a generator the wrong bytes and say
nothing: an unapproved image, a deprecated one, a file replaced underneath the
row, or a directory with two candidates and an mtime to break the tie.
"""

from __future__ import annotations

import json
import uuid
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.db.visual_models import CastMember, VisualAsset
from app.domain.enums import VisualAssetKind, VisualAssetSourceType
from app.services import visual_library
from app.services.reference_resolution import (
    ReferenceUnavailable,
    resolve_asset,
    resolve_cast_reference,
    resolve_scene_master,
    verify_coverage_seed,
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


def test_an_asset_resolves_by_explicit_identifier(
    session: Session, store: FilesystemAssetStore, damo: CastMember
) -> None:
    asset = add(session, store, damo, role="head_shoulders_neutral", colour=(31, 32, 33))
    assert resolve_asset(session, store, asset.id).sha256 == asset.sha256

    with pytest.raises(ReferenceUnavailable, match="no asset"):
        resolve_asset(session, store, uuid.uuid4())


def register(
    session: Session,
    store: FilesystemAssetStore,
    *,
    scene_key: str,
    colour: tuple[int, int, int],
    approve: bool = True,
):
    ingested = visual_library.ingest_asset(
        session,
        store,
        data=png(colour),
        kind=VisualAssetKind.SCENE_MASTER,
        source_type=VisualAssetSourceType.GENERATED,
        role=scene_key,
    )
    master = visual_library.register_scene_master(
        session, scene_key=scene_key, asset=ingested.asset
    )
    if approve:
        visual_library.approve_asset(session, ingested.asset)
        visual_library.approve_scene_master(session, master)
    session.flush()
    return master


def test_each_scene_resolves_its_own_master(session: Session, store: FilesystemAssetStore) -> None:
    """The point of the table: two scenes, two masters, no confusion between them."""
    pub = register(session, store, scene_key="pub-1105", colour=(40, 41, 42))
    street = register(session, store, scene_key="side-street-0130", colour=(43, 44, 45))

    assert resolve_scene_master(session, store, scene_key="pub-1105").asset_id == (
        pub.visual_asset_id
    )
    assert resolve_scene_master(session, store, scene_key="side-street-0130").asset_id == (
        street.visual_asset_id
    )


def test_an_unregistered_scene_is_a_refusal(session: Session, store: FilesystemAssetStore) -> None:
    with pytest.raises(ReferenceUnavailable, match="no master is registered"):
        resolve_scene_master(session, store, scene_key="carpark-0200")


def test_a_registered_candidate_does_not_resolve(
    session: Session, store: FilesystemAssetStore
) -> None:
    """Registering is not approving. A candidate is a proposal."""
    register(session, store, scene_key="pub-1105", colour=(46, 47, 48), approve=False)

    with pytest.raises(ReferenceUnavailable, match="no approved master"):
        resolve_scene_master(session, store, scene_key="pub-1105")


def test_approving_a_second_master_supersedes_the_first(
    session: Session, store: FilesystemAssetStore
) -> None:
    """A scene cannot have two. The old one is superseded, not deleted."""
    first = register(session, store, scene_key="pub-1105", colour=(49, 50, 51))
    second = register(session, store, scene_key="pub-1105", colour=(52, 53, 54))

    assert first.status == "superseded"
    assert second.status == "approved"
    assert second.parent_master_id == first.id
    assert resolve_scene_master(session, store, scene_key="pub-1105").asset_id == (
        second.visual_asset_id
    )


def test_a_master_cannot_be_approved_on_an_unapproved_image(
    session: Session, store: FilesystemAssetStore
) -> None:
    ingested = visual_library.ingest_asset(
        session,
        store,
        data=png(colour=(55, 56, 57)),
        kind=VisualAssetKind.SCENE_MASTER,
        source_type=VisualAssetSourceType.GENERATED,
        role="pub-1105",
    )
    master = visual_library.register_scene_master(
        session, scene_key="pub-1105", asset=ingested.asset
    )
    with pytest.raises(visual_library.SceneMasterConflict, match="pending"):
        visual_library.approve_scene_master(session, master)


def test_one_image_cannot_be_two_scenes_masters(
    session: Session, store: FilesystemAssetStore
) -> None:
    master = register(session, store, scene_key="pub-1105", colour=(58, 59, 60))
    asset = session.get(VisualAsset, master.visual_asset_id)
    assert asset is not None

    with pytest.raises(visual_library.SceneMasterConflict, match="already the approved master"):
        visual_library.register_scene_master(session, scene_key="side-street-0130", asset=asset)


def test_a_veo_seed_from_a_superseded_master_is_refused(
    session: Session, store: FilesystemAssetStore, tmp_path: Path
) -> None:
    """The Veo gate: a frame cut from last week's master must not animate."""
    register(session, store, scene_key="pub-1105", colour=(61, 62, 63))
    current = resolve_scene_master(session, store, scene_key="pub-1105")

    seed_dir = tmp_path / "coverage" / "damo-9x16"
    seed_dir.mkdir(parents=True)
    seed = seed_dir / "frame.png"
    seed.write_bytes(png(colour=(64, 65, 66)))

    (seed_dir / "manifest.json").write_text(
        json.dumps({"shot": "damo-9x16", "source_sha256": "f" * 64, "frame_sha256": "a" * 64}),
        encoding="utf-8",
    )
    with pytest.raises(ReferenceUnavailable, match="was cut from master"):
        verify_coverage_seed(session, store, seed=seed, scene_key="pub-1105")

    (seed_dir / "manifest.json").write_text(
        json.dumps(
            {"shot": "damo-9x16", "source_sha256": current.sha256, "frame_sha256": "a" * 64}
        ),
        encoding="utf-8",
    )
    lineage = verify_coverage_seed(session, store, seed=seed, scene_key="pub-1105")
    assert lineage["scene_master_sha256"] == current.sha256
    assert lineage["coverage_shot"] == "damo-9x16"


def test_a_seed_with_no_manifest_is_refused(
    session: Session, store: FilesystemAssetStore, tmp_path: Path
) -> None:
    register(session, store, scene_key="pub-1105", colour=(67, 68, 69))
    seed = tmp_path / "frame.png"
    seed.write_bytes(png())

    with pytest.raises(ReferenceUnavailable, match="no coverage manifest"):
        verify_coverage_seed(session, store, seed=seed, scene_key="pub-1105")
