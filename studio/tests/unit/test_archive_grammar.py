"""Designs built from several parts.

Up to here the archive could place one shape. These cover the part that makes it
a design engine rather than a shape library: a frame with a mark inside it and a
word over the top, chosen and arranged together.
"""

from __future__ import annotations

import pytest

from app.archive import authored
from app.archive.assemble import assemble
from app.archive.grammar import BY_KEY, GRAMMARS, density_budget, grammars_for
from app.archive.placements import placement
from app.archive.render import Palette, RefusedToRender

PALETTE = Palette(garment="#101010", inks=("#C6FF00", "#F2F0EA"))
CONTENT = {"primary_text": "SHIRTFACED", "secondary_text": "EST 2026"}
CENTRE_CHEST = placement("centre_chest")


def _build(key: str, seed: int = 8374, **kwargs):
    return assemble(
        BY_KEY[key],
        kwargs.pop("content", CONTENT),
        authored.ALL,
        kwargs.pop("palette", PALETTE),
        kwargs.pop("placement", CENTRE_CHEST),
        seed=seed,
        width_mm=230,
        height_mm=230,
    )


def test_a_design_is_made_of_several_parts() -> None:
    """The whole point: not one shape on a shirt."""
    design = _build("crest")
    assert len(design.chosen) >= 2
    assert design.svg.count("<path") >= 3


@pytest.mark.parametrize("grammar", [g.key for g in GRAMMARS])
def test_every_grammar_builds(grammar: str) -> None:
    design = _build(grammar)
    assert design.svg.startswith("<svg")
    assert design.reads_as


@pytest.mark.parametrize("grammar", [g.key for g in GRAMMARS])
def test_assembly_is_deterministic(grammar: str) -> None:
    assert _build(grammar).content_hash == _build(grammar).content_hash


def test_a_different_seed_gives_a_different_design() -> None:
    """Otherwise the seed is decoration and every brief has one answer."""
    hashes = {_build("crest", seed=seed).content_hash for seed in (1, 2, 3, 4, 5)}
    assert len(hashes) > 1


def test_different_seeds_choose_different_elements() -> None:
    choices = {tuple(sorted(_build("crest", seed=seed).chosen.values())) for seed in range(1, 12)}
    assert len(choices) > 1


def test_style_weights_rather_than_filters() -> None:
    """Filtering on style makes thousands of parts behave like ten, so an
    off-style element must remain reachable across seeds."""
    picks = set()
    for seed in range(1, 40):
        picks.update(_build("crest", seed=seed).chosen.values())
    assert len(picks) > 3


# --- The density budget ------------------------------------------------------


def test_a_small_placement_carries_less() -> None:
    assert density_budget(placement("left_chest")) < density_budget(placement("full_front"))


def test_a_grammar_too_heavy_for_a_placement_is_refused() -> None:
    """A crest is a frame plus an arched title plus a mark. That is more than a
    90mm left chest can hold, and crowding it in would be the wrong answer."""
    with pytest.raises(RefusedToRender) as raised:
        _build("crest", placement=placement("left_chest"))
    assert raised.value.reason == "DENSITY_BUDGET_EXCEEDED"


def test_a_light_grammar_still_builds_on_a_small_placement() -> None:
    """Refusing everything small would be as wrong as crowding it."""
    design = _build("stencil", placement=placement("left_chest"))
    assert design.density_spent <= design.density_allowed


@pytest.mark.parametrize("grammar", [g.key for g in GRAMMARS])
def test_no_design_ever_overspends_its_budget(grammar: str) -> None:
    for name in ("left_chest", "pocket", "centre_chest", "full_front"):
        try:
            design = _build(grammar, placement=placement(name))
        except RefusedToRender:
            continue  # a grammar too heavy for a placement is a valid answer
        assert design.density_spent <= design.density_allowed, f"{grammar} on {name}"


def test_a_dropped_part_is_reported_not_silently_omitted() -> None:
    design = _build("stencil", placement=placement("pocket"), seed=8374)
    for role in design.dropped:
        assert any(role in warning for warning in design.warnings)


# --- Knockout ----------------------------------------------------------------


def test_a_mark_on_a_solid_frame_knocks_out() -> None:
    """Drawn in the same ink it would be invisible, which is what happened."""
    design = _build("crest", seed=8374)
    if "frame_circle_0001" in design.chosen.values():
        assert PALETTE.garment in design.svg


def test_text_over_a_solid_shape_knocks_out() -> None:
    design = _build("ticket", seed=8374)
    assert PALETTE.garment in design.svg


# --- Which grammars suit a brief --------------------------------------------


def test_a_brief_with_one_line_still_finds_grammars() -> None:
    fits = grammars_for({"primary_text"}, {"frame", "symbol", "ornament"})
    assert fits
    assert all("secondary_text" not in fit.grammar.content_slots() or fit.unfilled for fit in fits)


def test_grammars_using_more_of_the_content_rank_first() -> None:
    fits = grammars_for({"primary_text", "secondary_text"}, {"frame", "symbol", "ornament"})
    assert fits[0].fills >= fits[-1].fills


def test_a_grammar_needing_a_family_we_lack_is_not_offered() -> None:
    fits = grammars_for({"primary_text"}, {"frame"})
    for fit in fits:
        for part in fit.grammar.parts:
            if part.families and not part.optional:
                assert "frame" in part.families


def test_an_optional_part_does_not_block_a_grammar() -> None:
    """A crest without a footer is still a crest."""
    keys = {fit.grammar.key for fit in grammars_for({"primary_text"}, {"frame", "symbol"})}
    assert "crest" in keys


def test_missing_required_content_is_refused() -> None:
    with pytest.raises(RefusedToRender) as raised:
        _build("crest", content={"secondary_text": "EST 2026"})
    assert raised.value.reason == "MISSING_REQUIRED_CONTENT"


def test_every_grammar_reads_as_something_a_person_would_say() -> None:
    """A suggestion that cannot explain itself is not a suggestion."""
    for grammar in GRAMMARS:
        assert len(grammar.reads_as.split()) >= 4


# --- Placeholders stay visible ----------------------------------------------


def test_a_provisional_element_says_what_it_is_waiting_for() -> None:
    """A placeholder without a brief is just a bad shape nobody remembers to fix."""
    for element in authored.ALL:
        if element.provisional:
            assert len(element.provisional.split()) >= 8, element.id


def test_provisional_elements_are_still_usable() -> None:
    """They stand in until something replaces them. Removing one takes the gap
    out of the system along with the shape, and then nothing reports it."""
    standing_in = [element for element in authored.ALL if element.provisional]
    assert standing_in
    for element in standing_in:
        assert element.licence.usable, element.id


def test_the_archive_reports_how_much_of_it_is_standing_in() -> None:
    """So the number has to fall deliberately rather than be forgotten."""
    standing_in = [element for element in authored.ALL if element.provisional]
    assert len(standing_in) <= 10, (
        f"{len(standing_in)} elements are placeholders. If this has grown, "
        "placeholders are being added faster than they are being replaced."
    )
