"""Composing whole designs, from every part the archive holds.

The point of this layer, measured: the element composer could offer six of
fifty elements because only badges and type layouts declare text slots. This
reaches forty-seven by building compositions, which is how the archive is put
together in the first place.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from app.archive import authored, registry
from app.archive.design_composer import Brief, DesignComposer

BRIEF = Brief(
    primary_text="SHIRTFACED",
    secondary_text="EST 2026",
    placement="centre_chest",
    style_tags=("australian",),
    inks=2,
)


@pytest.fixture
def composer(tmp_path: Path) -> DesignComposer:
    return DesignComposer(tmp_path / "approvals.json")


def test_a_brief_returns_whole_designs(composer: DesignComposer) -> None:
    result = composer.compose(BRIEF, seed=8374)
    assert result.composable
    assert result.options
    assert all(option.svg.startswith("<svg") for option in result.options)


def test_designs_are_made_of_several_parts(composer: DesignComposer) -> None:
    result = composer.compose(BRIEF, seed=8374)
    assert any(len(option.parts) >= 2 for option in result.options)


def test_most_of_the_archive_is_reachable(composer: DesignComposer) -> None:
    """The measurement that justifies this module existing. The element
    composer reached 6 of 50; anything near that here means the parts are
    being locked away again."""
    reached: set[str] = set()
    for seed in range(1, 60):
        for option in composer.compose(BRIEF, seed=seed).options:
            reached.update(option.parts.values())
    assert len(reached) >= 30, f"only {len(reached)} of {len(authored.ALL)} parts reachable"


def test_symbols_are_reachable_despite_having_no_text_slots(
    composer: DesignComposer,
) -> None:
    """A symbol never needed slots -- it is the mark inside a crest."""
    reached: set[str] = set()
    for seed in range(1, 30):
        for option in composer.compose(BRIEF, seed=seed).options:
            reached.update(option.parts.values())
    assert any(key.startswith("symbol_") for key in reached)


def test_composing_is_deterministic(composer: DesignComposer) -> None:
    one = composer.compose(BRIEF, seed=8374)
    two = composer.compose(BRIEF, seed=8374)
    assert [o.grammar_key for o in one.options] == [o.grammar_key for o in two.options]
    assert [o.svg for o in one.options] == [o.svg for o in two.options]


def test_a_different_seed_gives_different_designs(composer: DesignComposer) -> None:
    hashes = {
        composer.compose(BRIEF, seed=seed).options[0].design.content_hash
        for seed in (1, 2, 3, 4, 5)
    }
    assert len(hashes) > 1


def test_options_are_ranked(composer: DesignComposer) -> None:
    result = composer.compose(BRIEF, seed=8374)
    ranked = [option.score * option.confidence for option in result.options]
    assert ranked == sorted(ranked, reverse=True)


@pytest.mark.parametrize(
    "placement", ["pocket", "left_chest", "centre_chest", "full_front", "full_back"]
)
def test_every_placement_produces_something(composer: DesignComposer, placement: str) -> None:
    """A placement where nothing at all can be built is a hole in the grammar,
    not a fact about the placement."""
    result = composer.compose(replace(BRIEF, placement=placement), seed=3)
    assert result.composable, f"{placement}: {result.refusal_reason} {result.refusal_detail}"
    assert result.options


def test_all_options_are_offered_not_trimmed_by_confidence(
    composer: DesignComposer,
) -> None:
    """Confidence is reported per option. Hiding the rest as well decides for
    the reader twice, and the old thresholds almost always bit."""
    result = composer.compose(BRIEF, seed=8374, limit=6)
    assert len(result.options) > 2


# --- Refusal ----------------------------------------------------------------


def test_no_content_is_refused(composer: DesignComposer) -> None:
    result = composer.compose(Brief(placement="centre_chest"), seed=1)
    assert not result.composable
    assert result.refusal_reason == "NO_CONTENT"


def test_an_unknown_placement_is_refused(composer: DesignComposer) -> None:
    result = composer.compose(replace(BRIEF, placement="elbow"), seed=1)
    assert not result.composable
    assert result.refusal_reason == "UNKNOWN_PLACEMENT"


def test_a_refused_grammar_is_reported_with_its_reason(composer: DesignComposer) -> None:
    """A crest on a pocket is too much; saying which grammars could not build
    is the difference between a short list and a mysterious one."""
    result = composer.compose(replace(BRIEF, placement="pocket"), seed=1)
    assert result.composable
    assert result.rejections
    assert all(rejection.reason for rejection in result.rejections)


def test_composing_never_raises(composer: DesignComposer) -> None:
    result = composer.compose(replace(BRIEF, fit="martian"), seed=1)
    assert not result.composable
    assert result.refusal_reason


# --- The feedback edge ------------------------------------------------------


def test_approving_moves_confidence(tmp_path: Path) -> None:
    path = tmp_path / "approvals.json"
    composer = DesignComposer(path)
    before = composer.compose(BRIEF, seed=8374).options[0]

    for _ in range(5):
        composer.record_decision(before.grammar_key, approved=True)

    after = next(
        option
        for option in DesignComposer(path).compose(BRIEF, seed=8374).options
        if option.grammar_key == before.grammar_key
    )
    assert after.confidence > before.confidence
    assert after.decisions == 5


def test_rejecting_lowers_confidence(tmp_path: Path) -> None:
    path = tmp_path / "approvals.json"
    composer = DesignComposer(path)
    before = composer.compose(BRIEF, seed=8374).options[0]

    for _ in range(5):
        composer.record_decision(before.grammar_key, approved=False)

    options = DesignComposer(path).compose(BRIEF, seed=8374, limit=99).options
    after = next(option for option in options if option.grammar_key == before.grammar_key)
    assert after.confidence < before.confidence
    # And it should no longer lead, which is the visible half of the same fact.
    assert options[0].grammar_key != before.grammar_key


def test_placeholders_are_reported_when_one_is_chosen(composer: DesignComposer) -> None:
    """A crude shape must not pass as finished work just because it rendered.

    Asked of the registry rather than of ``authored``, because that is what the
    composer draws from. An authored placeholder that a drawn file has since
    superseded is no longer standing in for anything -- checking the authored
    table would report a finished flame as crude.
    """
    known = registry.by_id()
    for seed in range(1, 40):
        result = composer.compose(BRIEF, seed=seed)
        used = {key for option in result.options for key in option.parts.values()}
        if any(known[key].provisional for key in used if key in known):
            assert any("standing in" in gap for gap in result.gaps)
            return
    pytest.skip("no placeholder was chosen across the seeds tried")
