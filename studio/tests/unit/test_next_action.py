"""Every screen states its next action.

Item 6 of Phase 1. These tests are about wording as much as logic, because the
exit test is a person who has not used the tool getting through the chain
without being told which screen to visit. A sentence that names a state rather
than an action fails that test while passing every type check.
"""

from __future__ import annotations

import pytest

from app.db.concept_models import ApprovedDesign, DesignAsset, DesignAttempt
from app.domain.design_review import CATEGORY_LIMITS, HardGate, ReviewResult, ScoreCategory
from app.domain.enums import DesignAssetKind, DesignAttemptState
from app.services.design_scoring import empty_review, evaluate_review
from app.services.next_action import approved_next_action, next_action

from .test_design_scoring import passing_gates, review


def attempt(state: DesignAttemptState, *, assets: bool = False) -> DesignAttempt:
    """A transient attempt. No session: these are pure sentence rules."""
    row = DesignAttempt(state=state)
    if assets:
        row.assets = [
            DesignAsset(
                kind=DesignAssetKind.ARTWORK,
                relative_path="a.png",
                sha256="0" * 64,
                mime_type="image/png",
                byte_size=1,
            )
        ]
    return row


def complete(percentage: float = 90) -> object:
    from .test_design_scoring import score_categories

    return evaluate_review(review(score_categories=score_categories(percentage)))


def test_an_attempt_with_no_artwork_says_where_the_artwork_comes_from() -> None:
    """Decision 0.1 made visible: the app owns everything but the pixels, and
    the screen has to say so or the reader looks for a generate button."""
    sentence = next_action(attempt(DesignAttemptState.PLANNED))

    assert "Copy the brief" in sentence
    assert "ChatGPT, Gemini or Claude" in sentence
    assert "nothing is billed" in sentence


def test_fresh_artwork_asks_for_measurement_then_the_scorecard() -> None:
    sentence = next_action(
        attempt(DesignAttemptState.GENERATED, assets=True),
        evaluate_review(empty_review("x")),
    )

    assert "Measure it" in sentence
    assert "thirteen gates" in sentence
    assert "nine categories" in sentence


def test_a_part_answered_review_counts_what_is_left() -> None:
    """Counts, not thirteen names in a sentence nobody reads."""
    partial = review(
        hard_gates=passing_gates()[:10],
        score_categories=[ScoreCategory.from_rating(c, 4) for c in list(CATEGORY_LIMITS)[:7]],
    )
    sentence = next_action(
        attempt(DesignAttemptState.GENERATED, assets=True), evaluate_review(partial)
    )

    assert "3 gates" in sentence
    assert "2 categories" in sentence
    assert "outstanding" in sentence


def test_one_outstanding_item_is_singular() -> None:
    partial = review(
        hard_gates=passing_gates()[:12],
        score_categories=[ScoreCategory.from_rating(c, 4) for c in CATEGORY_LIMITS],
    )
    sentence = next_action(
        attempt(DesignAttemptState.GENERATED, assets=True), evaluate_review(partial)
    )

    assert "1 gate " in sentence
    assert "gates" not in sentence


def test_a_passing_review_not_yet_submitted_says_so_rather_than_the_opposite() -> None:
    """Found by running the exit test in a browser.

    A fully answered, passing review sitting in `generated` was routed through
    the not-eligible sentence and told "scored 80/100, below the 75 needed" --
    directly contradicting the verdict panel above it, which said every gate
    was answered and every floor met.
    """
    sentence = next_action(
        attempt(DesignAttemptState.GENERATED, assets=True),
        complete(80),
    )

    assert "80/100" in sentence
    assert "below" not in sentence
    assert "Submit it for a decision" in sentence


def test_a_passing_review_awaiting_decision_offers_both_ways_out() -> None:
    sentence = next_action(attempt(DesignAttemptState.AWAITING_DECISION), complete(90))

    assert "90/100" in sentence
    assert "Approve it" in sentence
    assert "send it back" in sentence


def test_a_failed_gate_says_the_design_has_to_change() -> None:
    """The scorecard's own rule, in the sentence: a hard failure is not
    something a high score or another look can settle."""
    from .test_design_scoring import score_categories

    gates = passing_gates()
    gates[0] = HardGate(id=gates[0].id, label=gates[0].label, result=ReviewResult.FAIL)
    failed = review(hard_gates=gates, score_categories=score_categories(95))

    sentence = next_action(attempt(DesignAttemptState.AWAITING_DECISION), evaluate_review(failed))

    assert "1 gate has failed" in sentence
    assert "cannot be averaged away" in sentence
    assert "sent back" in sentence


def test_a_breached_floor_is_named_ahead_of_the_total() -> None:
    """A uniform 60% breaches the three 4/5 floors, and the floor is the more
    actionable thing to say -- the reviewer needs to know *which* category,
    not that the sum came up short."""
    sentence = next_action(attempt(DesignAttemptState.AWAITING_DECISION), complete(60))

    assert "Below the floor on" in sentence
    assert "Dominant Proposition" in sentence
    assert "not the rating" in sentence


def test_below_the_threshold_with_every_floor_met_blames_the_total() -> None:
    """Nothing identifiably wrong, still not release-worthy. The reviewer
    should be told the total is the problem rather than hunting for a gate."""
    evaluation = evaluate_review(
        review(
            score_categories=[
                ScoreCategory.from_rating(
                    category_id,
                    4
                    if category_id
                    in ("dominant_proposition", "composition_and_hierarchy", "production_integrity")
                    else 3,
                )
                for category_id in CATEGORY_LIMITS
            ]
        )
    )
    sentence = next_action(attempt(DesignAttemptState.AWAITING_DECISION), evaluation)

    assert "68/100" in sentence
    assert "below the 75" in sentence
    assert "not the rating" in sentence


def test_an_approved_attempt_asks_for_the_three_things_print_needs() -> None:
    sentence = next_action(attempt(DesignAttemptState.APPROVED))

    assert "Record it as a version" in sentence
    assert "garment" in sentence
    assert "print zone" in sentence
    assert "print width" in sentence


def test_a_variation_request_says_to_start_a_new_attempt() -> None:
    sentence = next_action(attempt(DesignAttemptState.VARIATION_REQUESTED))

    assert "new attempt" in sentence


@pytest.mark.parametrize(
    "spec",
    [
        {},
        {"garment_key": "garment_tee_crew_front"},
        {"garment_key": "garment_tee_crew_front", "zone_key": "centre_chest"},
    ],
)
def test_a_version_missing_its_print_spec_names_what_is_missing(spec: dict[str, object]) -> None:
    version = ApprovedDesign(version=1, approved_by="owner", production_spec=spec)

    sentence = approved_next_action(version)

    assert "Print needs" in sentence
    assert "Record them on the version" in sentence


def test_a_complete_version_says_exactly_what_will_be_printed() -> None:
    version = ApprovedDesign(
        version=2,
        approved_by="owner",
        production_spec={
            "garment_key": "garment_tee_crew_front",
            "zone_key": "centre_chest",
            "print_width_mm": 240,
        },
    )

    sentence = approved_next_action(version)

    assert "v2" in sentence
    assert "240mm" in sentence
    assert "centre chest" in sentence
    assert "_" not in sentence, "keys are for the database, not for a sentence"


def test_a_superseded_version_points_at_the_current_one() -> None:
    import datetime as dt

    version = ApprovedDesign(
        version=1,
        approved_by="owner",
        production_spec={},
        superseded_at=dt.datetime(2026, 8, 14, tzinfo=dt.UTC),
    )

    assert "Superseded" in approved_next_action(version)


def test_no_sentence_is_a_bare_status_word() -> None:
    """The rule these are written to: name the thing to do, not the state the
    row is in. "Awaiting decision" is a status; it is not an instruction."""
    sentences = [
        next_action(attempt(DesignAttemptState.PLANNED)),
        next_action(attempt(DesignAttemptState.GENERATED, assets=True)),
        next_action(attempt(DesignAttemptState.AWAITING_DECISION), complete(90)),
        next_action(attempt(DesignAttemptState.APPROVED)),
    ]

    for sentence in sentences:
        assert sentence.endswith("."), sentence
        assert len(sentence.split()) >= 6, sentence
        assert "awaiting_decision" not in sentence
