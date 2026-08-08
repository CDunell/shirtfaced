"""The approval loop, which is the point of the engine.

DESIGN_ENGINE_ADAPTATION.md section 9 names one thread to prove before anything
else: compose, approve, and watch the template's confidence move. Section 10
makes it the kill gate -- if approving does not move the number within twenty
decisions, the loop is decorative and the design is wrong.

So these are not incidental coverage. They are the assertion that the engine
learns, and the first one caught a fault that made it learn backwards.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.composition_engine import (
    Brief,
    CompositionEngine,
    Element,
)

TEMPLATES = Path(__file__).resolve().parents[2] / "var" / "design_corpus" / "design_templates.json"

BRIEF = Brief(
    elements=(Element(kind="image", content="photo"), Element(kind="text", content="SHIRTFACED")),
    tradition="streetwear",
)


@pytest.fixture
def engine(tmp_path: Path) -> CompositionEngine:
    """A fresh engine with no learned history."""
    return CompositionEngine(TEMPLATES, tmp_path / "approvals.json")


def _leading(engine: CompositionEngine) -> object:
    composition = engine.compose(BRIEF)
    assert composition.composable, composition.refusal_reason
    return composition.options[0]


def _confidence_of(engine: CompositionEngine, template_id: str) -> float | None:
    composition = engine.compose(BRIEF)
    for option in composition.options:
        if option.template_id == template_id:
            return option.confidence
    return None


def test_approving_moves_the_number(engine: CompositionEngine) -> None:
    """The kill gate. If this fails the whole design is wrong."""
    first = _leading(engine)
    engine.record_decision(2, first.template_id, approved=True)

    after = _confidence_of(engine, first.template_id)

    assert after is not None
    assert after > first.confidence, "an approval did not move the confidence"


def test_a_rejection_never_raises_confidence(engine: CompositionEngine) -> None:
    """The fault this file was written to catch.

    Corpus evidence was capped only while there were no decisions, so the first
    rejection lifted the cap and the confidence *rose* -- 0.476 to 0.577 --
    because losing the cap was worth more than the rejection took away. A
    decision against something must never make it more certain.
    """
    first = _leading(engine)
    engine.record_decision(2, first.template_id, approved=False)

    after = _confidence_of(engine, first.template_id)

    assert after is None or after < first.confidence, "a rejection raised the confidence"


def test_enough_rejections_take_it_below_the_floor(engine: CompositionEngine) -> None:
    """Refusal is the point of the doubt layer. Something must be able to fall out."""
    first = _leading(engine)
    for _ in range(8):
        engine.record_decision(2, first.template_id, approved=False)

    assert _confidence_of(engine, first.template_id) is None


def test_approval_gains_shrink_as_evidence_accumulates(engine: CompositionEngine) -> None:
    """Two out of two is not twice as trustworthy as one out of one.

    n/(n + PRIOR) is the single most portable idea carried across from the
    Feature Factory, and without it the tenth approval would be worth as much as
    the first.
    """
    first = _leading(engine)
    before = first.confidence

    engine.record_decision(2, first.template_id, approved=True)
    after_one = _confidence_of(engine, first.template_id)
    assert after_one is not None
    first_gain = after_one - before

    for _ in range(9):
        engine.record_decision(2, first.template_id, approved=True)
    after_ten = _confidence_of(engine, first.template_id)
    assert after_ten is not None

    engine.record_decision(2, first.template_id, approved=True)
    after_eleven = _confidence_of(engine, first.template_id)
    assert after_eleven is not None
    eleventh_gain = after_eleven - after_ten

    assert eleventh_gain < first_gain, "later approvals counted as much as the first"


def test_decisions_survive_a_restart(tmp_path: Path) -> None:
    """The feedback edge is durable or it is not a feedback edge.

    Held in a file rather than in the process, because the thing being learned
    is the owner's taste and it has to outlive a deploy.
    """
    store = tmp_path / "approvals.json"
    first_run = CompositionEngine(TEMPLATES, store)
    leading = _leading(first_run)
    for _ in range(3):
        first_run.record_decision(2, leading.template_id, approved=True)
    learned = _confidence_of(first_run, leading.template_id)

    second_run = CompositionEngine(TEMPLATES, store)

    assert _confidence_of(second_run, leading.template_id) == learned


def test_decisions_are_keyed_by_template_not_by_name(engine: CompositionEngine) -> None:
    """The corpus yields two distinct arrangements both called "wide band".

    Keying approvals by the descriptive name would pool them into one score, so
    approving one would silently vouch for the other.
    """
    composition = engine.compose(BRIEF)
    names = [o.template_name for o in composition.options]
    keys = [engine.template_key(2, o.template_id) for o in composition.options]

    assert len(set(keys)) == len(keys), "two options share an approval key"
    if len(set(names)) < len(names):
        assert len(set(keys)) > len(set(names)), "colliding names were not separated by id"
