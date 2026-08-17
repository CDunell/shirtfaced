"""Coverage frames as rows, and the gate in front of Veo.

``VISUAL_ASSET_LIBRARY.md`` §8 and §15 Phase E. The failures these cover are all
ways a file-based frame could reach a paid run without anyone deciding it should:
one nobody approved, one cut from a master that has since been replaced, or one
that simply is not the shot the run asked for.
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
from app.db.visual_models import AssetLineage, CoverageFrame, SceneMaster
from app.domain.enums import VisualAssetKind, VisualAssetSourceType
from app.services import visual_library
from app.services.coverage_library import (
    CoverageRejected,
    approve_for_veo,
    crop_bytes,
    derive_coverage_frame,
    resolve_veo_seed,
    vertical_box,
)

pytestmark = pytest.mark.integration


def master_png(width: int = 1600, height: int = 900, seed: int = 0) -> bytes:
    """A landscape master with horizontal variation, so crops differ by offset."""
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    assert pixels is not None
    for x in range(width):
        for y in range(0, height, 8):
            pixels[x, y] = ((x + seed) % 256, (y + seed) % 256, seed % 256)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def store(tmp_path: Path) -> FilesystemAssetStore:
    return FilesystemAssetStore(tmp_path / "assets")


def approved_master(
    session: Session, store: FilesystemAssetStore, *, scene_key: str = "pub-1105", seed: int = 0
) -> SceneMaster:
    ingested = visual_library.ingest_asset(
        session,
        store,
        data=master_png(seed=seed),
        kind=VisualAssetKind.SCENE_MASTER,
        source_type=VisualAssetSourceType.GENERATED,
        role=scene_key,
    )
    visual_library.approve_asset(session, ingested.asset)
    master = visual_library.register_scene_master(
        session, scene_key=scene_key, asset=ingested.asset
    )
    visual_library.approve_scene_master(session, master)
    session.flush()
    return master


def test_a_frame_is_an_exact_nine_by_sixteen_crop(
    session: Session, store: FilesystemAssetStore
) -> None:
    approved_master(session, store)

    frame = derive_coverage_frame(session, store, scene_key="pub-1105", name="pub-1105-a", x=0)
    session.flush()

    assert frame.width * 16 == frame.height * 9
    assert (frame.width, frame.height) == (504, 896)  # 900 reduced to a multiple of 16
    assert frame.aspect_ratio == "9:16"
    assert frame.operation == "crop_only"


def test_the_crop_is_reproducible_from_the_master_and_the_box(
    session: Session, store: FilesystemAssetStore
) -> None:
    """Original pixels: the row's geometry regenerates the row's bytes."""
    master = approved_master(session, store)
    frame = derive_coverage_frame(session, store, scene_key="pub-1105", name="pub-1105-b", x=120)
    session.flush()

    box = vertical_box(
        master_width=master.asset.width,
        master_height=master.asset.height,
        x=frame.x,
        y=frame.y,
        height=frame.height,
    )
    again = crop_bytes(store.load(master.asset.storage_key), box)
    assert hashlib.sha256(again).hexdigest() == frame.frame_sha256


def test_different_offsets_are_different_frames(
    session: Session, store: FilesystemAssetStore
) -> None:
    approved_master(session, store)
    left = derive_coverage_frame(session, store, scene_key="pub-1105", name="left", x=0)
    right = derive_coverage_frame(session, store, scene_key="pub-1105", name="right", x=800)
    session.flush()

    assert left.frame_sha256 != right.frame_sha256
    assert left.visual_asset_id != right.visual_asset_id


def test_a_crop_outside_the_master_is_refused(
    session: Session, store: FilesystemAssetStore
) -> None:
    approved_master(session, store)
    with pytest.raises(CoverageRejected, match="falls outside"):
        derive_coverage_frame(session, store, scene_key="pub-1105", name="off-edge", x=1400)


def test_the_frame_records_which_master_it_observed(
    session: Session, store: FilesystemAssetStore
) -> None:
    master = approved_master(session, store)
    frame = derive_coverage_frame(session, store, scene_key="pub-1105", name="pub-1105-a", x=10)
    session.flush()

    assert frame.source_master_sha256 == master.asset.sha256
    lineage = session.execute(
        select(AssetLineage).where(AssetLineage.child_asset_id == frame.visual_asset_id)
    ).scalar_one()
    assert lineage.parent_asset_id == master.visual_asset_id
    assert lineage.relationship_kind == "crop"


def test_recutting_a_shot_replaces_it_rather_than_duplicating(
    session: Session, store: FilesystemAssetStore
) -> None:
    approved_master(session, store)
    first = derive_coverage_frame(session, store, scene_key="pub-1105", name="pub-1105-a", x=0)
    session.flush()
    first_id, first_sha = first.id, first.frame_sha256

    second = derive_coverage_frame(session, store, scene_key="pub-1105", name="pub-1105-a", x=300)
    session.flush()

    assert second.id == first_id, "one shot is one row"
    assert second.frame_sha256 != first_sha
    assert len(session.execute(select(CoverageFrame)).scalars().all()) == 1


def test_cutting_is_not_approving(session: Session, store: FilesystemAssetStore) -> None:
    approved_master(session, store)
    frame = derive_coverage_frame(session, store, scene_key="pub-1105", name="pub-1105-a", x=0)
    session.flush()

    assert frame.approved_for_veo is False
    with pytest.raises(CoverageRejected, match="not approved for Veo"):
        resolve_veo_seed(session, store, scene_key="pub-1105", name="pub-1105-a")


def test_an_approved_frame_resolves_to_its_exact_bytes(
    session: Session, store: FilesystemAssetStore
) -> None:
    approved_master(session, store)
    frame = derive_coverage_frame(session, store, scene_key="pub-1105", name="pub-1105-a", x=0)
    approve_for_veo(session, frame)
    session.flush()

    resolved = resolve_veo_seed(session, store, scene_key="pub-1105", name="pub-1105-a")
    assert resolved.sha256 == frame.frame_sha256
    assert resolved.width * 16 == resolved.height * 9


def test_an_unknown_shot_says_what_is_held(session: Session, store: FilesystemAssetStore) -> None:
    approved_master(session, store)
    derive_coverage_frame(session, store, scene_key="pub-1105", name="pub-1105-a", x=0)
    session.flush()

    with pytest.raises(CoverageRejected, match="pub-1105-a"):
        resolve_veo_seed(session, store, scene_key="pub-1105", name="pub-1105-z")


def test_a_frame_from_a_superseded_master_stops_resolving(
    session: Session, store: FilesystemAssetStore
) -> None:
    """The failure that has already happened once, now caught before spend."""
    approved_master(session, store, seed=1)
    frame = derive_coverage_frame(session, store, scene_key="pub-1105", name="pub-1105-a", x=0)
    approve_for_veo(session, frame)
    session.flush()
    assert resolve_veo_seed(session, store, scene_key="pub-1105", name="pub-1105-a") is not None

    approved_master(session, store, seed=2)  # the master is replaced
    session.flush()

    with pytest.raises(CoverageRejected, match="Redo it against the current one"):
        resolve_veo_seed(session, store, scene_key="pub-1105", name="pub-1105-a")


def test_a_frame_cannot_be_approved_against_a_master_that_moved_on(
    session: Session, store: FilesystemAssetStore
) -> None:
    approved_master(session, store, seed=3)
    frame = derive_coverage_frame(session, store, scene_key="pub-1105", name="pub-1105-a", x=0)
    session.flush()

    approved_master(session, store, seed=4)
    session.flush()

    with pytest.raises(CoverageRejected, match="Re-cut"):
        approve_for_veo(session, frame)


def test_each_scene_keeps_its_own_frames(session: Session, store: FilesystemAssetStore) -> None:
    approved_master(session, store, scene_key="pub-1105", seed=5)
    approved_master(session, store, scene_key="side-street-0130", seed=6)
    derive_coverage_frame(session, store, scene_key="pub-1105", name="wide", x=0)
    derive_coverage_frame(session, store, scene_key="side-street-0130", name="wide", x=0)
    session.flush()

    frames = session.execute(select(CoverageFrame)).scalars().all()
    assert len(frames) == 2, "the same shot name in two scenes is two rows"
    assert len({frame.scene_master_id for frame in frames}) == 2
    assert len({frame.frame_sha256 for frame in frames}) == 2
