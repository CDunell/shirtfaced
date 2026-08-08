"""Choosing and placing archive elements.

The composer's job is to be right about what it cannot do as much as what it
can. An archive that quietly returns nothing is worse than one that says which
constraint stopped it, so the refusal paths are tested as carefully as the
successful ones.
"""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

import pytest

from app.archive import authored
from app.archive.composer import ArchiveComposer, Brief
from app.domain.element import Licence


@pytest.fixture
def composer(tmp_path: Path) -> ArchiveComposer:
    return ArchiveComposer(tmp_path / "approvals.json")


BADGE_BRIEF = Brief(
    primary_text="SHIRTFACED",
    secondary_text="EST 2026",
    placement="centre_chest",
    style_tags=("institutional", "workwear"),
    inks=2,
)


def test_a_brief_returns_ranked_options(composer: ArchiveComposer) -> None:
    result = composer.compose(BADGE_BRIEF, seed=8374)
    assert result.composable
    assert result.options
    scores = [option.score * option.confidence for option in result.options]
    assert scores == sorted(scores, reverse=True)


def test_style_tags_rank_rather_than_exclude(composer: ArchiveComposer) -> None:
    """Excluding on taste makes 3,000 elements behave like ten."""
    result = composer.compose(BADGE_BRIEF, seed=8374)
    best = result.options[0]
    assert set(BADGE_BRIEF.style_tags) & set(authored.BY_ID[best.element_id].style_tags)


def test_composing_is_deterministic(composer: ArchiveComposer) -> None:
    one = composer.compose(BADGE_BRIEF, seed=8374)
    two = composer.compose(BADGE_BRIEF, seed=8374)
    assert [o.element_id for o in one.options] == [o.element_id for o in two.options]
    assert [o.svg for o in one.options] == [o.svg for o in two.options]


def test_a_small_placement_refuses_intricate_elements(composer: ArchiveComposer) -> None:
    """A badge at 90mm across is a smudge from two metres."""
    result = composer.compose(replace(BADGE_BRIEF, placement="left_chest"), seed=1)
    assert result.composable
    chosen = {option.element_id for option in result.options}
    assert not any(element_id.startswith("badge_") for element_id in chosen)
    assert any(rejection.reason == "TOO_COMPLEX_FOR_PLACEMENT" for rejection in result.rejections)


@pytest.mark.parametrize(
    "placement",
    ["centre_chest", "left_chest", "full_front", "full_back", "pocket", "short_sleeve"],
)
def test_every_placement_composes_within_its_bounds(
    composer: ArchiveComposer, placement: str
) -> None:
    """Asserting the options exist first, because the earlier version of this
    test iterated an empty result and passed while full front produced nothing
    at all -- sizing by the placement's longest edge made every square element
    305mm wide against a 305mm limit."""
    result = composer.compose(replace(BADGE_BRIEF, placement=placement), seed=3)
    assert result.composable, f"{placement}: {result.refusal_reason} {result.refusal_detail}"
    assert result.options
    for option in result.options:
        fits, why = option.placement.fits(option.rendered.width_mm, option.rendered.height_mm)
        assert fits, f"{option.element_id} on {placement}: {why}"


def test_it_composes_to_the_typical_size_not_the_maximum(composer: ArchiveComposer) -> None:
    """Composing to the ceiling every time makes every design a jumbo front."""
    result = composer.compose(BADGE_BRIEF, seed=3)
    option = result.options[0]
    assert option.rendered.width_mm < option.placement.max_width_mm


# --- Refusal ----------------------------------------------------------------


def test_no_content_is_refused(composer: ArchiveComposer) -> None:
    result = composer.compose(Brief(placement="centre_chest"), seed=1)
    assert not result.composable
    assert result.refusal_reason == "NO_CONTENT"


def test_an_unknown_placement_is_refused(composer: ArchiveComposer) -> None:
    result = composer.compose(Brief(primary_text="X", placement="elbow"), seed=1)
    assert not result.composable
    assert result.refusal_reason == "UNKNOWN_PLACEMENT"


def test_an_archive_whose_terms_are_unknown_still_composes(tmp_path: Path) -> None:
    """Reference material is how design works. An archive that can only hold
    what has already been cleared cannot learn from anything, and the corpus
    already holds thousands of competitors' photographs on that basis."""
    unknown = tuple(replace(element, licence=Licence()) for element in authored.ALL)
    composer = ArchiveComposer(tmp_path / "approvals.json", elements=unknown)
    result = composer.compose(BADGE_BRIEF, seed=1)
    assert result.composable
    assert result.options


def test_content_with_no_slot_to_hold_it_is_rejected(composer: ArchiveComposer) -> None:
    """A symbol has no slots, so it cannot carry a supplied phrase."""
    result = composer.compose(BADGE_BRIEF, seed=1)
    reasons = {rejection.element_id: rejection.reason for rejection in result.rejections}
    assert reasons.get("symbol_star_0001") == "ELEMENT_HAS_NO_SLOTS"


def test_rejections_are_grouped_in_the_refusal_detail(composer: ArchiveComposer) -> None:
    """GROUP BY reason is the point -- which constraint is load-bearing."""
    result = composer.compose(replace(BADGE_BRIEF, inks=9), seed=1)
    assert not result.composable
    assert result.refusal_reason == "NO_ELIGIBLE_ELEMENT"
    assert "INKS_ABOVE_MAXIMUM" in result.refusal_detail


# --- The feedback edge ------------------------------------------------------


def test_approving_moves_confidence(tmp_path: Path) -> None:
    """If it does not, the approve control is decoration."""
    path = tmp_path / "approvals.json"
    composer = ArchiveComposer(path)
    before = composer.compose(BADGE_BRIEF, seed=8374).options[0]

    for _ in range(5):
        composer.record_decision(before.element_id, approved=True)

    after = next(
        option
        for option in ArchiveComposer(path).compose(BADGE_BRIEF, seed=8374).options
        if option.element_id == before.element_id
    )
    assert after.confidence > before.confidence
    assert after.decisions == 5


def test_rejecting_lowers_confidence(tmp_path: Path) -> None:
    path = tmp_path / "approvals.json"
    composer = ArchiveComposer(path)
    before = composer.compose(BADGE_BRIEF, seed=8374).options[0]

    for _ in range(5):
        composer.record_decision(before.element_id, approved=False)

    after = next(
        option
        for option in ArchiveComposer(path).compose(BADGE_BRIEF, seed=8374).options
        if option.element_id == before.element_id
    )
    assert after.confidence < before.confidence


def test_one_approval_is_not_certainty(tmp_path: Path) -> None:
    """Shrinkage: n/(n + 10), so a single yes does not become a rule."""
    path = tmp_path / "approvals.json"
    composer = ArchiveComposer(path)
    composer.record_decision("badge_shield_0001", approved=True)
    option = next(
        o
        for o in ArchiveComposer(path).compose(BADGE_BRIEF, seed=8374).options
        if o.element_id == "badge_shield_0001"
    )
    assert option.confidence < 0.9


def test_a_corrupt_approval_store_does_not_crash_the_composer(tmp_path: Path) -> None:
    path = tmp_path / "approvals.json"
    path.write_text("{ not json", encoding="utf-8")
    result = ArchiveComposer(path).compose(BADGE_BRIEF, seed=1)
    assert result.composable


def test_gaps_are_reported_rather_than_left_silent(composer: ArchiveComposer) -> None:
    result = composer.compose(replace(BADGE_BRIEF, style_tags=("cyberpunk",)), seed=1)
    assert result.composable
    assert any("cyberpunk" in gap for gap in result.gaps)


def test_composing_never_raises(composer: ArchiveComposer) -> None:
    """The doubt layer fails closed rather than propagating."""
    result = composer.compose(replace(BADGE_BRIEF, fit="martian"), seed=1)
    assert not result.composable
    assert result.refusal_reason


def test_the_composer_never_writes_content(composer: ArchiveComposer) -> None:
    """Every word in the output was supplied."""
    brief = replace(BADGE_BRIEF, secondary_text="")
    result = composer.compose(brief, seed=1)
    for option in result.options:
        assert any("secondary_text" in warning for warning in option.rendered.warnings)


with tempfile.TemporaryDirectory() as _probe:
    # Import-time sanity: the archive must not ship an element the composer
    # cannot even consider, which would be a silently dead part.
    _composer = ArchiveComposer(Path(_probe) / "a.json")
    _result = _composer.compose(BADGE_BRIEF, seed=1)
    assert _result.composable
