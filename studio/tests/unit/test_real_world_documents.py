"""The world documents actually shipped in the repository.

The fixtures elsewhere are simplified. This is the real thing: if World 1 stops
loading, this fails.
"""

from __future__ import annotations

import pytest

from app.adapters.markdown_store import MarkdownStore
from app.config import PROJECT_ROOT
from app.domain.enums import ShotStatus
from app.services.rotation import RotationState, apply_continuity
from app.services.world_loader import load_world

WORLDS_ROOT = PROJECT_ROOT / "worlds"

pytestmark = pytest.mark.skipif(
    not (WORLDS_ROOT / "world-01" / "SHOTLIST.md").is_file(),
    reason="World 1 documents are not present.",
)


@pytest.fixture
def world():  # type: ignore[no-untyped-def]
    return load_world(MarkdownStore(WORLDS_ROOT), "world-01")


def test_world_one_loads(world) -> None:  # type: ignore[no-untyped-def]
    assert world.slug == "world-01"
    assert "SHIRTFACED" in world.name


def test_all_twenty_shots_are_read(world) -> None:  # type: ignore[no-untyped-def]
    assert len(world.shots) == 20
    assert world.shots[0].external_id == "W01-001"
    assert world.shots[-1].external_id == "W01-020"


def test_the_shotlist_statuses_match_the_document(world) -> None:  # type: ignore[no-untyped-def]
    by_id = {shot.external_id: shot for shot in world.shots}

    assert by_id["W01-001"].status is ShotStatus.APPROVED
    assert by_id["W01-008"].status is ShotStatus.REJECTED
    # Approved by the owner on 5 August 2026, after seven attempts and the vehicle
    # canon that came out of them.
    assert by_id["W01-011"].status is ShotStatus.APPROVED
    assert len(world.planned_shots) == 9


def test_the_next_planned_shot_is_the_lobby(world) -> None:  # type: ignore[no-untyped-def]
    """The lift became a lobby, which is the rule rather than a preference.

    Subjects stay out of small built enclosures -- car cabins, lifts, tents -- and
    stand next to, in front of, or sitting on them instead. So the shot moved twice:
    first the camera came out of the lift, then the cast did, and what is left is the
    room the lift is in.

    That is the general form of everything the vehicle canon was reaching for. A
    model cannot delete the seats from a room that does not need any.
    """
    upcoming = world.planned_shots[0]

    assert upcoming.external_id == "W01-012"
    assert upcoming.title == "Apartment lobby"
    assert upcoming.hero_product == "Hoodie waist"
    assert upcoming.camera_position == "From the entrance"


def test_the_tote_is_never_a_hero_product(world) -> None:  # type: ignore[no-untyped-def]
    """The tote is an accessory, not a lead product.

    Black is the documented seller for the t-shirt, hoodie and cap; nothing
    establishes it for the tote, and nothing makes the tote worth composing a frame
    around. A subject carrying one is incidental. It sat at the top of the rotation
    for three shots and scored 2/5 for visibility every time it was asked to lead.
    """
    offenders = [
        shot.external_id
        for shot in world.shots
        if "tote" in (shot.hero_product or "").strip().lower()
    ]

    assert not offenders, f"These shots make the tote the hero: {offenders}"


def test_no_camera_is_in_the_box_with_the_subjects(world) -> None:  # type: ignore[no-untyped-def]
    """We are observers, and an observer is outside the thing observed.

    The general rule, of which the vehicle canon is a special case. It is about small
    enclosed containers -- a cabin, a lift -- not interiors as such. "Inside lounge"
    is compliant: the subjects are on the balcony and the camera watches them through
    the doorway from the next room, which is exactly the shape the rule wants.
    """
    in_the_box = {
        "rear seat",
        "front seat",
        "driver's seat",
        "passenger seat",
        "in the car",
        "inside the car",
        "inside lift",
        "in the lift",
        "inside the lift",
    }

    offenders = [
        shot.external_id
        for shot in world.shots
        if (shot.camera_position or "").strip().lower() in in_the_box
    ]

    assert not offenders, (
        f"These shots put the camera inside the space the subjects occupy: {offenders}. "
        "The camera watches from the next room, the hallway or the footpath."
    )


def test_no_shot_makes_the_car_the_mechanism(world) -> None:  # type: ignore[no-untyped-def]
    """Nobody enters or leaves a vehicle.

    Getting in and out is what forces the geometry to be right, and it is not worth
    the attempts it costs. Standing beside a car is fine; being carried by one is not.
    """
    getting_in_or_out = ("piling into", "climbing in", "getting in", "getting out", "half in")

    offenders = [
        shot.external_id
        for shot in world.shots
        if any(phrase in (shot.title or "").strip().lower() for phrase in getting_in_or_out)
    ]

    assert not offenders, f"These shots use the car as the mechanism: {offenders}"


def test_the_two_branding_rules_do_not_contradict_each_other() -> None:
    """WORLD.md and CONTINUITY.md both reach the planner, and both describe branding.

    WORLD.md settled it as two rules: anything the brand sells is blank always, and
    anything it does not may carry real branding as background clutter, because the
    absence of that clutter is what makes a frame look staged. CONTINUITY.md kept an
    earlier one-line summary saying readable third-party branding anywhere in frame is
    a failure. That note predates the decision that replaced it and was never removed.

    Both went to the planner and to the reviewer on every request, which is the most
    likely explanation for three consecutive contradictory branding verdicts. A model
    asked to enforce two incompatible rules will look unreliable whichever it picks.
    """
    documents = MarkdownStore(WORLDS_ROOT).read_world_documents("world-01")
    rotation = apply_continuity(RotationState(), documents["CONTINUITY.md"].text)
    notes = " ".join(rotation.canon_notes).lower()

    assert "anywhere in frame is a failure" not in notes, (
        "CONTINUITY.md is telling the planner that any readable third-party mark "
        "fails, which contradicts WORLD.md Rule Two."
    )
    # The surviving rule has to actually say what it permits, not just drop the ban.
    assert "background" in notes
    assert "blank always" in notes


def test_the_camera_priorities_sent_to_the_planner_stay_out_of_cars() -> None:
    """The rule has to hold in CONTINUITY.md too, not just in WORLD.md.

    ``Next Camera Priority`` is parsed into rotation state and rendered into the
    planning message as "Preferred next camera positions". When vehicle interiors
    were banned in WORLD.md, "Inside a car looking outward" and "From the rear seat
    through an open door" stayed behind here, so the planner went on being told to do
    the banned thing by a document nobody thought to check. A rule that only one
    document agrees with is not in force.
    """
    documents = MarkdownStore(WORLDS_ROOT).read_world_documents("world-01")
    rotation = apply_continuity(RotationState(), documents["CONTINUITY.md"].text)

    banned = ("inside a car", "rear seat", "front seat", "climbing in", "getting in")
    offenders = [
        entry
        for entry in rotation.next_camera_priority
        if any(phrase in entry.lower() for phrase in banned)
    ]

    assert not offenders, f"These camera priorities contradict the vehicle canon: {offenders}"


def test_hero_products_and_cameras_are_read(world) -> None:  # type: ignore[no-untyped-def]
    by_id = {shot.external_id: shot for shot in world.shots}

    assert by_id["W01-006"].hero_product == "Hoodie"
    assert by_id["W01-006"].camera_position == "Dining room"
    assert by_id["W01-020"].hero_product == "Cap"
    assert by_id["W01-020"].camera_position == "Window seat"


def test_documents_hash_to_distinct_values(world) -> None:  # type: ignore[no-untyped-def]
    digests = {
        world.world_document.sha256,
        world.continuity_document.sha256,
        world.shotlist_document.sha256,
    }

    assert len(digests) == 3
