"""Locations, scouting plates, and what may become a base master.

``VISUAL_ASSET_LIBRARY.md`` §6 and §13. The gate that matters is rights: a scene
generated into a plate is sold from it, so an unverified licence stops the
promotion and nothing else about holding the image.

The width rule here is arithmetic and nothing more. §6.3 prefers 2.39:1 and this
reports whether a plate meets that, but it refuses only a plate too narrow to
yield a single 9:16 frame — a preference enforced as a gate would be an invented
constraint, which is a mistake this repository has made enough times to name.

Rights pass by construction since the owner's ruling of 17 August 2026: the
locations are invented here, so assets default to verified. The two tests below
that exercise the rights gate mark an asset otherwise on purpose, which is now
the only way that state arises.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.db.visual_models import LocationAsset, ScoutLocation
from app.domain.enums import (
    LicenceStatus,
    LocationAssetRole,
    VisualAssetKind,
    VisualAssetSourceType,
)
from app.services import visual_library
from app.services.location_library import (
    LocationRejected,
    assess_base_master,
    attach_plate,
    promote_to_base_master,
    register_location,
    resolve_base_master,
)
from app.services.reference_resolution import ReferenceUnavailable

pytestmark = pytest.mark.integration


def plate(width: int = 2390, height: int = 1000, shade: int = 90) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), (shade, shade, shade)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def store(tmp_path: Path) -> FilesystemAssetStore:
    return FilesystemAssetStore(tmp_path / "assets")


def held(
    session: Session,
    store: FilesystemAssetStore,
    *,
    width: int = 2390,
    height: int = 1000,
    shade: int = 90,
    approve: bool = True,
    rights: LicenceStatus = LicenceStatus.VERIFIED,
):
    ingested = visual_library.ingest_asset(
        session,
        store,
        data=plate(width, height, shade),
        kind=VisualAssetKind.LOCATION,
        source_type=VisualAssetSourceType.COMMISSIONED,
        rights_status=rights,
    )
    if approve:
        visual_library.approve_asset(session, ingested.asset)
    session.flush()
    return ingested.asset


def pub(session: Session) -> ScoutLocation:
    return register_location(session, slug="railway-hotel", display_name="Railway Hotel")


def test_locations_nest(session: Session) -> None:
    hotel = pub(session)
    room = register_location(
        session, slug="railway-hotel-back-room", display_name="Back room", parent=hotel
    )
    session.flush()

    assert room.parent_location_id == hotel.id
    assert room.parent is not None and room.parent.slug == "railway-hotel"


def test_registering_the_same_place_twice_is_one_row(session: Session) -> None:
    first = pub(session)
    second = register_location(session, slug="railway-hotel", display_name="Railway Hotel")
    assert first.id == second.id


def test_a_plate_with_unverified_rights_is_held_but_cannot_be_promoted(
    session: Session, store: FilesystemAssetStore
) -> None:
    """§6.4: unknown rights never stop an asset being held. They stop this."""
    location = pub(session)
    asset = held(session, store, rights=LicenceStatus.UNVERIFIED)
    link = attach_plate(session, location, asset, role=LocationAssetRole.EMPTY_PLATE)
    session.flush()

    assert link.id is not None, "the plate is held"
    readiness = assess_base_master(link)
    assert readiness.rights_verified is False
    with pytest.raises(LocationRejected, match="rights are unverified"):
        promote_to_base_master(session, link)


def test_a_refused_licence_is_refused_for_promotion(
    session: Session, store: FilesystemAssetStore
) -> None:
    location = pub(session)
    asset = held(session, store, rights=LicenceStatus.REFUSED)
    link = attach_plate(session, location, asset, role=LocationAssetRole.EMPTY_PLATE)
    session.flush()

    with pytest.raises(LocationRejected, match="rights are refused"):
        promote_to_base_master(session, link)


def test_a_detail_survey_is_not_a_stage(session: Session, store: FilesystemAssetStore) -> None:
    location = pub(session)
    link = attach_plate(
        session, location, held(session, store), role=LocationAssetRole.SURVEY_DETAIL
    )
    session.flush()

    with pytest.raises(LocationRejected, match="is a reference, not a stage"):
        promote_to_base_master(session, link)


def test_a_plate_too_narrow_for_one_vertical_frame_is_refused(
    session: Session, store: FilesystemAssetStore
) -> None:
    """Arithmetic, not taste: 9:16 of this height does not fit in this width."""
    location = pub(session)
    asset = held(session, store, width=400, height=1000, shade=40)
    link = attach_plate(session, location, asset, role=LocationAssetRole.EMPTY_PLATE)
    session.flush()

    with pytest.raises(LocationRejected, match="cannot yield one full-height 9:16 frame"):
        promote_to_base_master(session, link)


def test_a_sixteen_by_nine_plate_is_allowed_and_reports_its_room(
    session: Session, store: FilesystemAssetStore
) -> None:
    """The preference for 2.39:1 is reported, never enforced."""
    location = pub(session)
    asset = held(session, store, width=1600, height=900, shade=70)
    link = attach_plate(session, location, asset, role=LocationAssetRole.PARTICIPANT_NEUTRAL_BASE)
    session.flush()

    readiness = assess_base_master(link)
    assert readiness.ready
    assert readiness.meets_the_wide_preference is False
    assert readiness.lateral_room_px == 1600 - round(900 * 9 / 16)

    promote_to_base_master(session, link)
    session.flush()
    assert link.is_base_master is True


def test_promoting_a_second_plate_demotes_the_first(
    session: Session, store: FilesystemAssetStore
) -> None:
    location = pub(session)
    first = attach_plate(
        session, location, held(session, store, shade=10), role=LocationAssetRole.EMPTY_PLATE
    )
    second = attach_plate(
        session, location, held(session, store, shade=20), role=LocationAssetRole.EMPTY_PLATE
    )
    promote_to_base_master(session, first)
    session.flush()
    promote_to_base_master(session, second)
    session.flush()

    assert first.is_base_master is False
    assert second.is_base_master is True


def test_a_scene_resolves_the_plate_of_the_place_it_is_in(
    session: Session, store: FilesystemAssetStore
) -> None:
    location = pub(session)
    link = attach_plate(
        session, location, held(session, store, shade=30), role=LocationAssetRole.EMPTY_PLATE
    )
    promote_to_base_master(session, link)
    session.flush()

    resolved = resolve_base_master(session, store, slug="railway-hotel")
    assert resolved.asset_id == link.visual_asset_id
    assert resolved.intact


def test_a_sub_location_falls_back_to_its_parent(
    session: Session, store: FilesystemAssetStore
) -> None:
    """The reason locations nest at all."""
    hotel = pub(session)
    register_location(
        session, slug="railway-hotel-back-room", display_name="Back room", parent=hotel
    )
    link = attach_plate(
        session, hotel, held(session, store, shade=50), role=LocationAssetRole.EMPTY_PLATE
    )
    promote_to_base_master(session, link)
    session.flush()

    resolved = resolve_base_master(session, store, slug="railway-hotel-back-room")
    assert resolved.asset_id == link.visual_asset_id
    assert resolved.label == "location:railway-hotel"


def test_a_place_with_no_plate_anywhere_above_it_is_a_refusal(
    session: Session, store: FilesystemAssetStore
) -> None:
    hotel = pub(session)
    register_location(session, slug="side-street", display_name="Side street", parent=hotel)
    session.flush()

    with pytest.raises(ReferenceUnavailable, match="no approved base master"):
        resolve_base_master(session, store, slug="side-street")


def test_an_unknown_location_is_a_refusal(session: Session, store: FilesystemAssetStore) -> None:
    with pytest.raises(ReferenceUnavailable, match="no such location"):
        resolve_base_master(session, store, slug="nowhere")


def test_attaching_the_same_plate_twice_updates_rather_than_duplicates(
    session: Session, store: FilesystemAssetStore
) -> None:
    location = pub(session)
    asset = held(session, store, shade=60)
    first = attach_plate(session, location, asset, role=LocationAssetRole.SCOUT_PHOTO)
    session.flush()
    second = attach_plate(session, location, asset, role=LocationAssetRole.EMPTY_PLATE)
    session.flush()

    assert first.id == second.id
    assert second.role is LocationAssetRole.EMPTY_PLATE
    assert len(location.assets) == 1


def test_plates_keep_the_order_they_were_filed_in(
    session: Session, store: FilesystemAssetStore
) -> None:
    location = pub(session)
    orders = [
        attach_plate(
            session,
            location,
            held(session, store, shade=shade),
            role=LocationAssetRole.SCOUT_PHOTO,
        ).sort_order
        for shade in (11, 12, 13)
    ]
    session.flush()
    assert orders == sorted(orders)
    assert len(set(orders)) == 3


def test_a_link_is_reachable_from_the_location(
    session: Session, store: FilesystemAssetStore
) -> None:
    location = pub(session)
    attach_plate(
        session, location, held(session, store, shade=80), role=LocationAssetRole.SURVEY_WIDE
    )
    session.flush()

    assert isinstance(location.assets[0], LocationAsset)
    assert location.assets[0].role is LocationAssetRole.SURVEY_WIDE
