"""The Visual Asset Library's rules, against a real database.

``VISUAL_ASSET_LIBRARY.md`` §16 lists the tests the library needs before
anything depends on it. The ones a Phase 1/2 build can actually make true are
here: duplicate SHA, immutable measurements, role ordering, deprecation without
deletion, deterministic compatibility export, and hashes preserved through the
import.

The scene-master and coverage entries in that list are not here, because the
tables they test do not exist yet. A test that passes by having nothing to
check is worse than an absent one.
"""

from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.db.models import AuditEvent
from app.db.visual_models import AssetIsImmutable, CastMember, CastMemberAsset, VisualAsset
from app.domain.enums import (
    AuditEventType,
    LicenceStatus,
    VisualAssetKind,
    VisualAssetSourceType,
    VisualAssetStatus,
)
from app.services import cast_ingest, visual_library

pytestmark = pytest.mark.integration


def png(width: int = 512, height: int = 512, colour: tuple[int, int, int] = (200, 30, 30)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), colour).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def store(tmp_path: Path) -> FilesystemAssetStore:
    return FilesystemAssetStore(tmp_path / "assets")


@pytest.fixture
def member(session: Session) -> CastMember:
    created = CastMember(slug="damo", display_name="Damo")
    session.add(created)
    session.flush()
    return created


def ingest(session: Session, store: FilesystemAssetStore, data: bytes, role: str = "shouting"):
    return visual_library.ingest_asset(
        session,
        store,
        data=data,
        kind=VisualAssetKind.CAST,
        source_type=VisualAssetSourceType.UPLOAD,
        role=role,
    )


def test_the_same_bytes_ingest_once(session: Session, store: FilesystemAssetStore) -> None:
    """A photograph uploaded twice is one asset, not two identities for one face."""
    data = png()
    first = ingest(session, store, data)
    second = ingest(session, store, data, role="laughing")

    assert first.created is True
    assert second.created is False
    assert first.asset.id == second.asset.id
    assert session.execute(select(VisualAsset)).scalars().all() == [first.asset]


def test_different_bytes_are_different_assets(
    session: Session, store: FilesystemAssetStore
) -> None:
    first = ingest(session, store, png(colour=(10, 10, 10)))
    second = ingest(session, store, png(colour=(20, 20, 20)))
    assert first.asset.id != second.asset.id


def test_the_stored_hash_is_the_hash_of_the_bytes(
    session: Session, store: FilesystemAssetStore
) -> None:
    data = png()
    asset = ingest(session, store, data).asset
    assert asset.sha256 == hashlib.sha256(data).hexdigest()
    assert store.load(asset.storage_key) == data


def test_measurements_cannot_be_edited(session: Session, store: FilesystemAssetStore) -> None:
    """§9: changing bytes is a new asset. There is no in-place edit."""
    asset = ingest(session, store, png()).asset
    with pytest.raises(AssetIsImmutable):
        asset.sha256 = "0" * 64
    with pytest.raises(AssetIsImmutable):
        asset.width = 9999


def test_an_unreadable_upload_is_refused(session: Session, store: FilesystemAssetStore) -> None:
    with pytest.raises(visual_library.AssetRejected):
        ingest(session, store, b"this is not an image")


def test_a_thumbnail_sized_upload_is_refused(session: Session, store: FilesystemAssetStore) -> None:
    with pytest.raises(visual_library.AssetRejected):
        ingest(session, store, png(width=64, height=64))


def test_a_role_outside_the_offered_list_is_still_stored(
    session: Session, store: FilesystemAssetStore
) -> None:
    """Everything gets ingested. The vocabulary guides; it does not gate."""
    asset = ingest(session, store, png(), role="mid_sneeze").asset
    assert asset.role == "mid_sneeze"


def test_references_keep_their_order_and_one_primary_per_role(
    session: Session, store: FilesystemAssetStore, member: CastMember
) -> None:
    first = ingest(session, store, png(colour=(1, 1, 1)), role="head_shoulders_neutral").asset
    second = ingest(session, store, png(colour=(2, 2, 2)), role="head_shoulders_neutral").asset

    visual_library.attach_to_cast_member(
        session, member, first, role="head_shoulders_neutral", is_primary=True
    )
    visual_library.attach_to_cast_member(
        session, member, second, role="head_shoulders_neutral", is_primary=True
    )
    session.flush()

    primaries = (
        session.execute(
            select(CastMemberAsset).where(
                CastMemberAsset.cast_member_id == member.id,
                CastMemberAsset.is_primary.is_(True),
            )
        )
        .scalars()
        .all()
    )

    assert len(primaries) == 1, "two images cannot both be the neutral head shot"
    assert primaries[0].visual_asset_id == second.id
    orders = [link.sort_order for link in sorted(member.assets, key=lambda link: link.sort_order)]
    assert orders == sorted(orders)


def test_a_member_can_hold_a_third_reference(
    session: Session, store: FilesystemAssetStore, member: CastMember
) -> None:
    """The acceptance criterion of §15 Phase A, and the reason for the build."""
    for index, role in enumerate(
        ("full_body_neutral", "head_shoulders_neutral", "expression_bridge", "shouting")
    ):
        asset = ingest(session, store, png(colour=(index * 40, 5, 5)), role=role).asset
        visual_library.attach_to_cast_member(session, member, asset, role=role)
    session.flush()

    assert len(member.assets) == 4
    assert {link.role for link in member.assets} == {
        "full_body_neutral",
        "head_shoulders_neutral",
        "expression_bridge",
        "shouting",
    }


def test_deprecation_keeps_the_asset_and_its_bytes(
    session: Session, store: FilesystemAssetStore, member: CastMember
) -> None:
    asset = ingest(session, store, png()).asset
    visual_library.attach_to_cast_member(session, member, asset, role="shouting")
    visual_library.approve_asset(session, asset)
    visual_library.deprecate_asset(session, asset, note="Superseded")
    session.flush()

    assert asset.status is VisualAssetStatus.DEPRECATED
    assert session.get(VisualAsset, asset.id) is not None
    assert store.exists(asset.storage_key)


def test_detaching_a_reference_does_not_destroy_the_asset(
    session: Session, store: FilesystemAssetStore, member: CastMember
) -> None:
    asset = ingest(session, store, png()).asset
    link = visual_library.attach_to_cast_member(session, member, asset, role="shouting")
    session.flush()

    visual_library.detach_from_cast_member(session, link)
    session.flush()

    assert session.get(CastMemberAsset, link.id) is None
    assert session.get(VisualAsset, asset.id) is not None
    assert store.exists(asset.storage_key)


def test_approval_and_deprecation_are_audited(
    session: Session, store: FilesystemAssetStore
) -> None:
    asset = ingest(session, store, png()).asset
    visual_library.approve_asset(session, asset, note="Looks right")
    visual_library.deprecate_asset(session, asset, note="Replaced")
    session.flush()

    recorded = [
        event.event_type
        for event in session.execute(select(AuditEvent)).scalars()
        if str(event.payload_json.get("asset_id")) == str(asset.id)
    ]
    assert AuditEventType.VISUAL_ASSET_INGESTED in recorded
    assert AuditEventType.VISUAL_ASSET_APPROVED in recorded
    assert AuditEventType.VISUAL_ASSET_DEPRECATED in recorded


def test_the_import_preserves_hashes_and_is_idempotent(
    session: Session, store: FilesystemAssetStore, tmp_path: Path
) -> None:
    """§14 Phase 2: a second run re-links, and ingests nothing twice."""
    cast_root = tmp_path / "cast"
    (cast_root / "damo").mkdir(parents=True)
    full = png(colour=(3, 3, 3))
    head = png(colour=(4, 4, 4))
    (cast_root / "damo" / "a-full-length.png").write_bytes(full)
    (cast_root / "damo" / "b-head-shoulders.png").write_bytes(head)

    first = cast_ingest.ingest_cast_directory(session, store, cast_root)
    session.flush()
    second = cast_ingest.ingest_cast_directory(session, store, cast_root)
    session.flush()

    assert len(first.assets_created) == 2
    assert second.assets_created == []
    assert len(second.assets_already_held) == 2

    held = {asset.sha256 for asset in session.execute(select(VisualAsset)).scalars()}
    assert held == {hashlib.sha256(full).hexdigest(), hashlib.sha256(head).hexdigest()}


def test_a_renamed_frame_is_the_same_asset(
    session: Session, store: FilesystemAssetStore, tmp_path: Path
) -> None:
    """The files were renamed on 17 August 2026. Identity is the bytes, not the name."""
    cast_root = tmp_path / "cast"
    directory = cast_root / "damo"
    directory.mkdir(parents=True)
    full = png(colour=(7, 7, 7))
    head = png(colour=(8, 8, 8))
    (directory / "a-full-length.png").write_bytes(full)
    (directory / "b-head-shoulders.png").write_bytes(head)

    first = cast_ingest.ingest_cast_directory(session, store, cast_root)
    session.flush()
    assert len(first.assets_created) == 2

    (directory / "a-full-length.png").rename(directory / "damo-full-length.png")
    (directory / "b-head-shoulders.png").rename(directory / "damo-head-shoulders.png")
    (directory / "reference.json").write_text(
        '{"slug": "damo", "frames": {"a": "damo-full-length.png", "b": "damo-head-shoulders.png"}}',
        encoding="utf-8",
    )

    second = cast_ingest.ingest_cast_directory(session, store, cast_root)
    session.flush()

    assert second.assets_created == [], "a rename is not a new photograph"
    assert len(second.assets_already_held) == 2
    assert len(second.renamed) == 2
    assert len(session.execute(select(VisualAsset)).scalars().all()) == 2

    # And the mirror follows the rename rather than resurrecting the old name.
    written = visual_library.export_legacy_cast_mirror(session, store, cast_root)
    assert directory / "damo-full-length.png" in written
    assert not (directory / "a-full-length.png").exists()


def test_frames_resolve_without_a_manifest(tmp_path: Path) -> None:
    """A directory with no reference.json still resolves, on the suffix."""
    directory = tmp_path / "gary"
    directory.mkdir()
    (directory / "gary-full-length.png").write_bytes(png())
    (directory / "gary-head-shoulders.png").write_bytes(png(colour=(9, 9, 9)))

    resolved = cast_ingest.resolve_frames(directory, {})
    assert resolved["full_body_neutral"].name == "gary-full-length.png"
    assert resolved["head_shoulders_neutral"].name == "gary-head-shoulders.png"


def test_the_legacy_mirror_is_rebuilt_from_the_database(
    session: Session, store: FilesystemAssetStore, tmp_path: Path
) -> None:
    """§10: the JSON/filesystem view is generated, and never the truth."""
    cast_root = tmp_path / "cast"
    (cast_root / "damo").mkdir(parents=True)
    full = png(colour=(5, 5, 5))
    (cast_root / "damo" / "a-full-length.png").write_bytes(full)
    (cast_root / "damo" / "b-head-shoulders.png").write_bytes(png(colour=(6, 6, 6)))

    cast_ingest.ingest_cast_directory(session, store, cast_root)
    session.flush()

    target = cast_root / "damo" / "a-full-length.png"
    target.write_bytes(b"someone edited the mirror by hand")

    written = visual_library.export_legacy_cast_mirror(session, store, cast_root)
    assert target in written
    assert target.read_bytes() == full

    # Deterministic: exporting again produces the same bytes.
    visual_library.export_legacy_cast_mirror(session, store, cast_root)
    assert target.read_bytes() == full


def test_only_approved_primaries_reach_the_mirror(
    session: Session, store: FilesystemAssetStore, member: CastMember, tmp_path: Path
) -> None:
    asset = ingest(session, store, png(), role="full_body_neutral").asset
    visual_library.attach_to_cast_member(
        session, member, asset, role="full_body_neutral", is_primary=True
    )
    session.flush()

    assert visual_library.export_legacy_cast_mirror(session, store, tmp_path) == []

    visual_library.approve_asset(session, asset)
    session.flush()
    assert visual_library.export_legacy_cast_mirror(session, store, tmp_path) != []


def test_rights_are_verified_by_default(session: Session, store: FilesystemAssetStore) -> None:
    """Owner's ruling, 17 August 2026: everything here is invented here.

    The worlds, the cast, the locations and the masters are all generated, there
    are no photographs of real people, and there is no third party with a claim.
    An ingest that had to be told this every time was asking a question with one
    answer, and the location gate refused the owner's own plates while it did.
    """
    asset = ingest(session, store, png()).asset

    assert asset.rights_status is LicenceStatus.VERIFIED
    assert asset.rights_metadata == {"owner": "Shirtfaced", "origin": "owner-generated"}
