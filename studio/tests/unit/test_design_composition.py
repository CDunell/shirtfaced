"""Composing a design through the service the routes call.

These cover the parts that need no database: what the composer is asked, what
comes back, and how a brief that cannot be answered is refused. The refusals
matter as much as the successes -- a reason code travels to whoever wrote the
brief, and "500" tells them nothing.
"""

from __future__ import annotations

import pytest

from app.services.design_composition import CompositionRefused, Request, compose, garment_for


def test_a_brief_composes_against_a_real_garment() -> None:
    garment, options = compose(
        Request(
            seed=7,
            garment_key="garment_tee_crew_front",
            primary_text="SHIRTFACED",
            secondary_text="EST 2026",
        )
    )

    assert garment.zones, "the garment carried no print zones"
    assert options, "nothing was composed"
    assert all(option.design.svg for option in options)


def test_the_same_brief_composes_to_the_same_bytes() -> None:
    """The whole point of the seed. Different bytes here means a reprint drifts."""
    brief = Request(seed=99, garment_key="garment_tee_crew_front", primary_text="SHIRTFACED")

    first = compose(brief)[1]
    second = compose(brief)[1]

    assert [o.design.content_hash for o in first] == [o.design.content_hash for o in second]
    assert [o.design.svg for o in first] == [o.design.svg for o in second]


def test_a_different_seed_composes_something_else() -> None:
    """Otherwise the seed is decoration and every brief has one answer."""
    one = compose(Request(seed=1, garment_key="garment_tee_crew_front", primary_text="SHIRTFACED"))[
        1
    ]
    two = compose(Request(seed=2, garment_key="garment_tee_crew_front", primary_text="SHIRTFACED"))[
        1
    ]

    assert {o.design.content_hash for o in one} != {o.design.content_hash for o in two}


def test_designs_are_sized_to_the_garments_own_zone() -> None:
    """The placement table is a default; the garment in front of you is the fact."""
    garment, options = compose(
        Request(
            seed=3,
            garment_key="garment_tee_crew_front",
            primary_text="SHIRTFACED",
            placement="centre_chest",
        )
    )
    zone = garment.zones["centre_chest"]

    for option in options:
        assert option.design.width_mm <= zone.width + 0.01
        assert option.design.height_mm <= zone.height + 0.01


def test_an_unknown_garment_is_refused_not_substituted() -> None:
    """Falling back to a tee would place the design in the wrong zones."""
    with pytest.raises(CompositionRefused) as caught:
        garment_for("garment_that_does_not_exist")

    assert caught.value.reason == "UNKNOWN_GARMENT"


def test_a_garment_key_cannot_climb_out_of_its_folder() -> None:
    """The key names a file. It is not a path, and it comes over HTTP."""
    for key in ("../secrets", "..\\secrets", ".hidden"):
        with pytest.raises(CompositionRefused) as caught:
            garment_for(key)
        assert caught.value.reason == "BAD_GARMENT_KEY", key


def test_a_brief_with_no_words_is_refused_with_a_reason() -> None:
    """The archive never invents content, so an empty brief has no answer."""
    with pytest.raises(CompositionRefused) as caught:
        compose(Request(seed=1, garment_key="garment_tee_crew_front"))

    assert caught.value.reason == "NO_CONTENT"


def test_an_unknown_placement_is_refused() -> None:
    with pytest.raises(CompositionRefused) as caught:
        compose(
            Request(
                seed=1,
                garment_key="garment_tee_crew_front",
                primary_text="SHIRTFACED",
                placement="left_elbow",
            )
        )

    assert caught.value.reason == "UNKNOWN_PLACEMENT"
