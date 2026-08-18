"""The Nano contact-sheet route, and the gate it shares with the crop route.

``NANO_BANANA_CONTACT_SHEET_PIPELINE.md`` §8 supersedes the deterministic crop
for this path. An extraction is generated rather than cut, so these cover what
that changes: no crop box, a panel number instead of coordinates, the sheet as
parent, and a reference manifest recorded as lineage rather than prose.

Verified against the model's published limits on 18 August 2026: up to 14
reference images, character consistency for up to five people, and 9:16 among
the supported output ratios. Nothing here assumes more than that.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.db.visual_models import AssetLineage, CoverageFrame, SceneContactSheet, SceneMaster
from app.domain.enums import VisualAssetKind, VisualAssetSourceType
from app.services import coverage_library, visual_library
from app.services.coverage_library import (
    CoverageRejected,
    approve_contact_sheet,
    approve_for_veo,
    approved_contact_sheet,
    record_panel_extraction,
    register_contact_sheet,
    resolve_veo_seed,
)

pytestmark = pytest.mark.integration


def png(width: int = 1600, height: int = 900, shade: int = 60) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), (shade, shade, shade)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def store(tmp_path: Path) -> FilesystemAssetStore:
    return FilesystemAssetStore(tmp_path / "assets")


def approved_master(
    session: Session, store: FilesystemAssetStore, *, scene_key: str = "W01-P28", shade: int = 10
) -> SceneMaster:
    ingested = visual_library.ingest_asset(
        session,
        store,
        data=png(shade=shade),
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


def cast_reference(session: Session, store: FilesystemAssetStore, shade: int):
    ingested = visual_library.ingest_asset(
        session,
        store,
        data=png(width=1024, height=1024, shade=shade),
        kind=VisualAssetKind.CAST,
        source_type=VisualAssetSourceType.GENERATED,
        role="contact_sheet",
    )
    visual_library.approve_asset(session, ingested.asset)
    session.flush()
    return ingested.asset


def sheet_for(
    session: Session, store: FilesystemAssetStore, *, shade: int = 30, approve: bool = True, **kw
) -> SceneContactSheet:
    return register_contact_sheet(
        session,
        store,
        scene_key=kw.pop("scene_key", "W01-P28"),
        label=kw.pop("label", "w01-p28-coverage"),
        data=png(width=2048, height=2048, shade=shade),
        approve=approve,
        **kw,
    )


def test_a_sheet_records_every_reference_it_was_given(
    session: Session, store: FilesystemAssetStore
) -> None:
    """§6's input manifest, as lineage edges rather than a note."""
    master = approved_master(session, store)
    damo = cast_reference(session, store, shade=101)
    emma = cast_reference(session, store, shade=102)

    sheet = sheet_for(session, store, reference_asset_ids=[damo.id, emma.id])
    session.flush()

    parents = {
        (row.parent_asset_id, row.relationship_kind)
        for row in session.execute(
            select(AssetLineage).where(AssetLineage.child_asset_id == sheet.visual_asset_id)
        ).scalars()
    }
    assert (master.visual_asset_id, "generated_from_master") in parents
    assert (damo.id, "generated_from_reference") in parents
    assert (emma.id, "generated_from_reference") in parents


def test_registering_a_sheet_is_not_approving_it(
    session: Session, store: FilesystemAssetStore
) -> None:
    approved_master(session, store)
    sheet = sheet_for(session, store, approve=False)
    session.flush()

    assert sheet.status == "candidate"
    with pytest.raises(CoverageRejected, match="no approved coverage contact sheet"):
        approved_contact_sheet(session, scene_key="W01-P28")


def test_approving_a_second_sheet_supersedes_the_first(
    session: Session, store: FilesystemAssetStore
) -> None:
    approved_master(session, store)
    first = sheet_for(session, store, shade=31)
    second = sheet_for(session, store, shade=32, label="w01-p28-coverage-v2")
    session.flush()

    assert first.status == "superseded"
    assert approved_contact_sheet(session, scene_key="W01-P28").id == second.id


def test_a_panel_extraction_has_no_crop_box(session: Session, store: FilesystemAssetStore) -> None:
    """It is generated, so coordinates could neither name it nor reproduce it."""
    approved_master(session, store)
    sheet = sheet_for(session, store)
    session.flush()

    frame = record_panel_extraction(
        session,
        store,
        scene_key="W01-P28",
        name="damo-wide",
        panel=1,
        data=png(width=1080, height=1920, shade=44),
    )
    session.flush()

    assert frame.is_extraction
    assert (frame.x, frame.y) == (None, None)
    assert frame.panel == 1
    assert frame.operation == "nano_extraction"
    assert frame.contact_sheet_id == sheet.id
    assert (frame.width, frame.height) == (1080, 1920)


def test_the_extraction_cites_the_sheet_as_its_parent(
    session: Session, store: FilesystemAssetStore
) -> None:
    approved_master(session, store)
    sheet = sheet_for(session, store)
    frame = record_panel_extraction(
        session,
        store,
        scene_key="W01-P28",
        name="damo-close",
        panel=4,
        data=png(width=1080, height=1920, shade=45),
    )
    session.flush()

    edge = session.execute(
        select(AssetLineage).where(
            AssetLineage.child_asset_id == frame.visual_asset_id,
            AssetLineage.relationship_kind == "extracted_from_panel",
        )
    ).scalar_one()
    assert edge.parent_asset_id == sheet.visual_asset_id
    assert edge.operation_metadata == {"panel": 4}


def test_one_panel_is_one_shot(session: Session, store: FilesystemAssetStore) -> None:
    approved_master(session, store)
    sheet_for(session, store)
    first = record_panel_extraction(
        session,
        store,
        scene_key="W01-P28",
        name="damo-wide",
        panel=1,
        data=png(width=1080, height=1920, shade=46),
    )
    session.flush()
    again = record_panel_extraction(
        session,
        store,
        scene_key="W01-P28",
        name="damo-wide-v2",
        panel=1,
        data=png(width=1080, height=1920, shade=47),
    )
    session.flush()

    assert again.id == first.id
    assert again.name == "damo-wide-v2"
    assert len(session.execute(select(CoverageFrame)).scalars().all()) == 1


def test_a_panel_outside_the_grid_is_refused(session: Session, store: FilesystemAssetStore) -> None:
    approved_master(session, store)
    sheet_for(session, store)
    session.flush()

    with pytest.raises(CoverageRejected, match="outside a 3x3 sheet"):
        record_panel_extraction(
            session,
            store,
            scene_key="W01-P28",
            name="nope",
            panel=10,
            data=png(width=1080, height=1920),
        )


def test_extraction_needs_an_approved_sheet(session: Session, store: FilesystemAssetStore) -> None:
    approved_master(session, store)
    sheet_for(session, store, approve=False)
    session.flush()

    with pytest.raises(CoverageRejected, match="no approved coverage contact sheet"):
        record_panel_extraction(
            session,
            store,
            scene_key="W01-P28",
            name="damo-wide",
            panel=1,
            data=png(width=1080, height=1920),
        )


def test_an_extraction_reaches_veo_only_after_review(
    session: Session, store: FilesystemAssetStore
) -> None:
    """§5: a panel becomes a first frame only once someone has approved it."""
    approved_master(session, store)
    sheet_for(session, store)
    frame = record_panel_extraction(
        session,
        store,
        scene_key="W01-P28",
        name="damo-wide",
        panel=1,
        data=png(width=1080, height=1920, shade=48),
    )
    session.flush()

    assert frame.approved_for_veo is False
    with pytest.raises(CoverageRejected, match="not approved for Veo"):
        resolve_veo_seed(session, store, scene_key="W01-P28", name="damo-wide")

    approve_for_veo(session, frame)
    session.flush()
    assert resolve_veo_seed(session, store, scene_key="W01-P28", name="damo-wide").sha256 == (
        frame.frame_sha256
    )


def test_a_shot_from_a_superseded_sheet_stops_resolving(
    session: Session, store: FilesystemAssetStore
) -> None:
    """A new sheet is a new set of observations; panel 1 is not the same picture."""
    approved_master(session, store)
    sheet_for(session, store, shade=33)
    frame = record_panel_extraction(
        session,
        store,
        scene_key="W01-P28",
        name="damo-wide",
        panel=1,
        data=png(width=1080, height=1920, shade=49),
    )
    approve_for_veo(session, frame)
    session.flush()
    assert resolve_veo_seed(session, store, scene_key="W01-P28", name="damo-wide") is not None

    sheet_for(session, store, shade=34, label="w01-p28-coverage-v2")
    session.flush()

    with pytest.raises(CoverageRejected, match="contact sheet is superseded"):
        resolve_veo_seed(session, store, scene_key="W01-P28", name="damo-wide")


def test_a_sheet_of_a_superseded_master_cannot_be_approved(
    session: Session, store: FilesystemAssetStore
) -> None:
    approved_master(session, store, shade=11)
    sheet = sheet_for(session, store, approve=False, shade=35)
    session.flush()

    approved_master(session, store, shade=12)  # the master is replaced
    session.flush()

    with pytest.raises(CoverageRejected, match="its master is superseded"):
        approve_contact_sheet(session, sheet)


def test_the_crop_route_still_works(session: Session, store: FilesystemAssetStore) -> None:
    """§8 supersedes it for the Nano path, not everywhere."""
    approved_master(session, store, shade=13)
    frame = coverage_library.derive_coverage_frame(
        session, store, scene_key="W01-P28", name="literal-crop", x=0
    )
    session.flush()

    assert frame.is_extraction is False
    assert frame.operation == "crop_only"
    assert frame.x == 0 and frame.width is not None


def test_the_same_shot_can_be_re_extracted_from_a_new_sheet(
    session: Session, store: FilesystemAssetStore
) -> None:
    """Reject a sheet, generate another, extract the same shots. The normal loop.

    Extraction used to find the frame to update by ``(contact_sheet_id, panel)``,
    so a shot extracted from a replacement sheet was a new row -- and collided
    with the one the rejected sheet had left behind on
    ``uq_coverage_frames_scene_master_id_name``. Every re-extraction after a
    rejection failed with a 500, which is the path a person takes whenever a
    sheet is not good enough.
    """
    master = approved_master(session, store)
    first = sheet_for(session, store, shade=41)
    frame = record_panel_extraction(
        session, store, scene_key="W01-P28", name="damo-medium", panel=4, data=png(shade=60)
    )
    session.flush()
    original = frame.id

    coverage_library.reject_contact_sheet(session, first)
    second = sheet_for(session, store, shade=42, label="w01-p28-coverage-v2")
    session.flush()

    again = record_panel_extraction(
        session, store, scene_key="W01-P28", name="damo-medium", panel=4, data=png(shade=61)
    )
    session.flush()

    # One shot, not two, and it now belongs to the sheet it was cut from.
    assert again.id == original
    assert again.contact_sheet_id == second.id
    assert again.scene_master_id == master.id
    held = (
        session.execute(select(CoverageFrame).where(CoverageFrame.scene_master_id == master.id))
        .scalars()
        .all()
    )
    assert [one.name for one in held] == ["damo-medium"]


def test_a_shot_can_move_to_a_different_panel_number(
    session: Session, store: FilesystemAssetStore
) -> None:
    """The prompt's numbering can change between sheets; the shot is the name."""
    approved_master(session, store)
    sheet_for(session, store, shade=43)
    record_panel_extraction(
        session, store, scene_key="W01-P28", name="world-return", panel=9, data=png(shade=70)
    )
    session.flush()

    moved = record_panel_extraction(
        session, store, scene_key="W01-P28", name="world-return", panel=8, data=png(shade=71)
    )
    session.flush()

    assert moved.panel == 8
