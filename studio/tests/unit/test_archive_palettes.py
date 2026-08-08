"""Choosing inks, and whether they can be printed on a given cloth.

Every design the engine composed used the same six inks in the same order, so a
screen of options came back looking like one option. These cover the two things
that make the choice honest rather than decorative: contrast is measured against
the garment, and the seed decides, so colour is part of what a seed means.
"""

from __future__ import annotations

from app.archive.palettes import BY_KEY, choose, luminance, separation, usable_for


def test_an_ink_that_cannot_be_seen_on_the_cloth_is_not_offered() -> None:
    """A black ink on a black shirt is not a subtle design, it is a blank one."""
    on_black = {system.key for system in usable_for("#101010")}

    assert "single_dark" not in on_black
    assert "single_light" in on_black


def test_the_same_ink_is_a_different_decision_on_a_different_garment() -> None:
    """Contrast is a property of the pair, which is the whole reason for this."""
    on_natural = {system.key for system in usable_for("#F2F0EA")}

    assert "single_light" not in on_natural, "off-white on cream"
    assert "single_dark" in on_natural


def test_a_mid_grey_garment_still_gets_an_answer() -> None:
    """Refusing to colour a design is worse than picking the best available."""
    assert usable_for("#808080"), "a mid-grey garment came back with nothing"


def test_the_seed_decides_so_colour_is_part_of_what_a_seed_means() -> None:
    assert choose("#101010", 7).key == choose("#101010", 7).key
    keys = {choose("#101010", seed).key for seed in range(8)}
    assert len(keys) > 1, "every seed chose the same system"


def test_naming_a_system_overrides_the_seed() -> None:
    """The owner choosing the season's colours is not the engine's business."""
    assert choose("#101010", 3, named="house").key == "house"


def test_an_unknown_name_falls_back_rather_than_failing() -> None:
    """A typo in a brief should still return a design."""
    assert choose("#101010", 3, named="no-such-system") in tuple(BY_KEY.values())


def test_luminance_runs_black_to_white() -> None:
    assert luminance("#000000") == 0.0
    assert round(luminance("#FFFFFF"), 3) == 1.0
    assert separation("#000000", "#FFFFFF") == 1.0


def test_asking_for_fewer_inks_never_returns_none() -> None:
    """Zero inks is not a cheaper print, it is no print."""
    assert len(BY_KEY["house"].for_count(0)) == 1


def test_an_ink_matching_the_garment_is_skipped_not_just_the_leading_one() -> None:
    """The fault that printed a blank shirt.

    Workwear is amber, black and off-white. On a black garment its *second* ink
    is the garment, so any design whose mark landed on ink two came back as an
    empty shirt: a valid file that prints nothing. Checking only the leading ink
    let it through, and it took a render to see.
    """
    inks = BY_KEY["workwear"].for_count(2, garment="#101010")

    assert "#101010" not in inks, "an ink the same colour as the cloth was offered"
    assert len(inks) == 2, "dropping the clash should not cost an ink"


def test_a_system_with_nothing_visible_still_returns_an_ink() -> None:
    """A design has to come back. Returning no inks would emit nothing at all."""
    assert BY_KEY["single_dark"].for_count(2, garment="#101010")
