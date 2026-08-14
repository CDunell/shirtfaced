"""The scorecard engine, pinned to the TypeScript it replaced.

``admin/src/design-system/workflow.test.ts`` was deleted with the code it
tested (Phase 0.2, ``DESIGN_FLOW_PLAN.md``). Its seven cases are the first
seven here, translated rather than reinterpreted, because a port is only a port
if it still fails where the original failed.

The rest pin the parts the TypeScript never had: the scorecard's own category
limits and floors, its 0-5 to points conversion, its approval bands, and the
blocker sentences the attempt screen shows.
"""

from __future__ import annotations

import pytest

from app.domain.design_review import (
    APPROVAL_PERCENTAGE,
    CATEGORY_LIMITS,
    GATE_LABELS,
    HARD_GATE_IDS,
    PRODUCTION_PERCENTAGE,
    ApprovalBand,
    DesignReviewInput,
    DesignStatus,
    HardGate,
    ReviewDecision,
    ReviewResult,
    ScoreCategory,
    approval_band,
    can_transition,
    points_floor,
)
from app.services.design_scoring import (
    empty_review,
    evaluate_review,
    next_status_for_review,
    rubric,
)


def passing_gates() -> list[HardGate]:
    return [
        HardGate(id=gate_id, label=gate_id, result=ReviewResult.PASS, evidence="reviewed")
        for gate_id in HARD_GATE_IDS
    ]


def score_categories(percentage: float = 90) -> list[ScoreCategory]:
    """The nine real categories, every one at the same share of its maximum.

    ``workflow.test.ts`` scored a single synthetic "overall" category out of
    100, which it could do because the TypeScript had no fixed rubric. This
    port does, and an unrated category blocks -- so the parity cases are
    rebuilt on the real nine. The maximums total 100, so a uniform share lands
    the percentage exactly on the target, and any share at or above 0.8 clears
    every floor (the highest is 4/5).
    """
    return [
        ScoreCategory(
            id=category_id,
            label=label,
            score=round(maximum * percentage / 100, 2),
            maximum=maximum,
            minimum_required=points_floor(category_id),
        )
        for category_id, (label, maximum, _floor) in CATEGORY_LIMITS.items()
    ]


def rated(default: int = 3, **overrides: int) -> list[ScoreCategory]:
    """The nine categories at stated 0-5 ratings."""
    return [
        ScoreCategory.from_rating(category_id, overrides.get(category_id, default))
        for category_id in CATEGORY_LIMITS
    ]


def review(**overrides: object) -> DesignReviewInput:
    fields: dict[str, object] = {
        "design_id": "22222222-2222-4222-8222-222222222222",
        "reviewer_id": "human-reviewer",
        "hard_gates": passing_gates(),
        "score_categories": score_categories(),
        "decision": ReviewDecision.DESIGN_APPROVED,
        "rationale": "Passes the documented design gates.",
    }
    fields.update(overrides)
    return DesignReviewInput(**fields)  # type: ignore[arg-type]


# --- The seven cases from workflow.test.ts -----------------------------------


def test_workflow_permits_intended_forward_transitions() -> None:
    assert can_transition(DesignStatus.DRAFT, DesignStatus.BRIEF_READY)
    assert can_transition(DesignStatus.REVIEW_READY, DesignStatus.DESIGN_APPROVED)
    assert can_transition(DesignStatus.PRODUCTION_APPROVED, DesignStatus.RELEASED)


def test_workflow_blocks_invalid_jumps() -> None:
    assert not can_transition(DesignStatus.DRAFT, DesignStatus.RELEASED)
    assert not can_transition(DesignStatus.BRIEF_READY, DesignStatus.PRODUCTION_APPROVED)
    assert not can_transition(DesignStatus.RELEASED, DesignStatus.DRAFT)


def test_a_failed_hard_gate_blocks_approval_regardless_of_score() -> None:
    gates = passing_gates()
    gates[0] = HardGate(id=gates[0].id, label=gates[0].label, result=ReviewResult.FAIL)

    result = evaluate_review(review(hard_gates=gates))

    assert result.hard_gate_passed is False
    assert result.eligible_for_design_approval is False
    assert next_status_for_review(review(hard_gates=gates)) is DesignStatus.REVISION_REQUIRED


def test_an_untested_hard_gate_blocks_approval() -> None:
    result = evaluate_review(review(hard_gates=passing_gates()[1:]))

    assert len(result.untested_hard_gates) == 1
    assert result.eligible_for_design_approval is False


def test_a_passing_human_review_can_approve_design() -> None:
    candidate = review()
    result = evaluate_review(candidate)

    assert result.eligible_for_design_approval is True
    assert next_status_for_review(candidate) is DesignStatus.DESIGN_APPROVED


def test_production_approval_requires_the_higher_threshold_and_human_decision() -> None:
    candidate = review(
        decision=ReviewDecision.PRODUCTION_APPROVED, score_categories=score_categories(86)
    )
    result = evaluate_review(candidate)

    assert result.eligible_for_production_approval is True
    assert next_status_for_review(candidate) is DesignStatus.PRODUCTION_APPROVED


def test_category_minimums_cannot_be_hidden_by_a_high_total() -> None:
    candidate = review(
        score_categories=[
            ScoreCategory(
                id="composition", label="Composition", score=20, maximum=20, minimum_required=12
            ),
            ScoreCategory(
                id="production", label="Production", score=5, maximum=10, minimum_required=7
            ),
            ScoreCategory(id="other", label="Other", score=70, maximum=70),
        ]
    )

    result = evaluate_review(candidate)

    assert result.percentage == 95
    assert len(result.failed_category_minimums) == 1
    assert result.eligible_for_design_approval is False


# --- The scorecard the TypeScript never carried ------------------------------


def test_the_thirteen_gates_are_the_constitution_twelve_plus_rights() -> None:
    """Pinned so a rename is a deliberate migration, not an accident.

    These ids are stored in ``design_reviews.hard_gates`` as JSON. Renaming one
    silently turns every stored review's answer into an unanswered gate, which
    would un-approve designs already approved.
    """
    assert len(HARD_GATE_IDS) == 13
    assert HARD_GATE_IDS[-1] == "rights_cleared_for_sale"
    assert set(GATE_LABELS) == set(HARD_GATE_IDS)


def test_the_nine_categories_total_one_hundred_points() -> None:
    """``DESIGN_REVIEW_SCORECARD.md`` §4: "Weighted total: 100 points"."""
    assert len(CATEGORY_LIMITS) == 9
    assert sum(maximum for _label, maximum, _floor in CATEGORY_LIMITS.values()) == 100


@pytest.mark.parametrize(
    ("category_id", "expected"),
    [
        # §6, converted from the stated 0-5 rating onto the points scale.
        ("product_fit", 6.0),  # 3/5 of 10
        ("dominant_proposition", 8.0),  # 4/5 of 10
        ("composition_and_hierarchy", 12.0),  # 4/5 of 15
        ("production_integrity", 12.0),  # 4/5 of 15
        ("commercial_wearability", 3.0),  # 3/5 of 5
    ],
)
def test_category_floors_are_points_not_ratings(category_id: str, expected: float) -> None:
    """The bug this guards: comparing a points score against a raw 0-5 number.

    Every floor would pass silently -- a 4-point score against a "floor" of 3
    clears, when the real floor is 12 of 15.
    """
    assert points_floor(category_id) == expected


def test_a_rating_converts_to_points_the_way_the_scorecard_says() -> None:
    """§5: ``category score = rating / 5 * category maximum``."""
    strong = ScoreCategory.from_rating("composition_and_hierarchy", 4)
    assert strong.score == 12.0
    assert strong.maximum == 15
    assert strong.minimum_required == 12.0

    assert ScoreCategory.from_rating("commercial_wearability", 5).score == 5.0
    assert ScoreCategory.from_rating("product_fit", 0).score == 0.0

    with pytest.raises(ValueError, match="0 to 5"):
        ScoreCategory.from_rating("product_fit", 6)


@pytest.mark.parametrize(
    ("percentage", "band"),
    [
        (100, ApprovalBand.RELEASE_CANDIDATE),
        (90, ApprovalBand.RELEASE_CANDIDATE),
        (89.9, ApprovalBand.REVISE_SELECTIVELY),
        (80, ApprovalBand.REVISE_SELECTIVELY),
        (70, ApprovalBand.REWORK),
        (69.9, ApprovalBand.REJECT_OR_REBUILD),
        (0, ApprovalBand.REJECT_OR_REBUILD),
    ],
)
def test_approval_bands(percentage: float, band: ApprovalBand) -> None:
    assert approval_band(percentage) is band


def test_a_perfect_score_does_not_approve_a_design_with_a_hard_failure() -> None:
    """§5's closing line, and §1: "A high score cannot override a hard failure"."""
    gates = passing_gates()
    gates[4] = HardGate(id=gates[4].id, label=gates[4].label, result=ReviewResult.FAIL)
    candidate = review(hard_gates=gates, score_categories=score_categories(100))

    result = evaluate_review(candidate)

    assert result.percentage == 100
    assert result.band is ApprovalBand.RELEASE_CANDIDATE
    assert result.eligible_for_design_approval is False


def test_a_full_rubric_at_every_floor_still_needs_seventy_five_percent() -> None:
    """Rating every category at exactly its own floor clears all nine floors and
    still lands below the approval threshold -- so the floors and the total are
    genuinely two different tests, not one dressed as two."""
    at_floor = [
        ScoreCategory.from_rating(category_id, rating_floor)
        for category_id, (_label, _maximum, rating_floor) in CATEGORY_LIMITS.items()
    ]
    result = evaluate_review(review(score_categories=at_floor))

    assert result.failed_category_minimums == []
    assert result.percentage == 68
    assert result.percentage < APPROVAL_PERCENTAGE
    assert result.eligible_for_design_approval is False


def test_an_unrated_category_is_reported_rather_than_scored_as_zero() -> None:
    """A gap is not evidence of absence.

    Eight of nine rated at full marks is 100% *of what was rated*, passes every
    gate and clears every floor -- and must still not approve, because nobody
    ever rated the typography. This one caught a real hole: the check was in
    the docstring and not in the arithmetic.
    """
    partial = [
        ScoreCategory.from_rating(category_id, 5)
        for category_id in CATEGORY_LIMITS
        if category_id != "typography"
    ]
    result = evaluate_review(review(score_categories=partial))

    assert result.percentage == 100
    assert result.band is ApprovalBand.RELEASE_CANDIDATE
    assert result.hard_gate_passed is True
    assert result.failed_category_minimums == []
    assert result.unrated_categories == ["typography"]
    assert result.eligible_for_design_approval is False
    assert any("Typography" in blocker for blocker in result.blockers)


def test_an_empty_review_blocks_and_says_why_in_full() -> None:
    result = evaluate_review(empty_review("an-attempt", "owner"))

    assert result.eligible_for_design_approval is False
    assert len(result.untested_hard_gates) == 13
    assert len(result.unrated_categories) == 9
    assert result.percentage == 0
    joined = " ".join(result.blockers)
    assert "13 gates not answered" in joined
    assert "9 categories not rated" in joined


def test_below_threshold_with_everything_answered_says_so_plainly() -> None:
    """The one blocker that only appears when nothing else is wrong.

    "Competent and acceptable" everywhere, lifted to "strong" on the three
    categories whose floor demands it, is 68/100 -- a design with nothing
    identifiably wrong with it that still does not earn release. That is the
    scorecard working as intended, and the reviewer should be told the total is
    the problem rather than hunting for a gate they missed.
    """
    result = evaluate_review(
        review(
            score_categories=rated(
                3, dominant_proposition=4, composition_and_hierarchy=4, production_integrity=4
            )
        )
    )

    assert result.failed_category_minimums == []
    assert result.unrated_categories == []
    assert result.percentage == 68
    assert result.blockers == [f"68/100 is below the {APPROVAL_PERCENTAGE:.0f} needed for approval"]


def test_rejection_needs_no_score() -> None:
    """A reviewer who can see it is wrong should not have to fill in
    twenty-two controls to say so. Only approval is gated."""
    refusal = DesignReviewInput(
        design_id="an-attempt", reviewer_id="owner", decision=ReviewDecision.REJECTED
    )
    assert next_status_for_review(refusal) is DesignStatus.REJECTED

    archived = DesignReviewInput(
        design_id="an-attempt", reviewer_id="owner", decision=ReviewDecision.ARCHIVED
    )
    assert next_status_for_review(archived) is DesignStatus.ARCHIVED


def test_the_rubric_renders_every_gate_and_category_into_three_groups() -> None:
    """The form is built from this, so a gate missing here is a gate no person
    can ever answer -- which is the exact failure Phase 1 exists to fix."""
    shape = rubric()

    assert [group["id"] for group in shape["groups"]] == [
        "validate_recognition",
        "validate_production",
        "review_against_collection",
    ]
    assert len(shape["gates"]) == 13
    assert len(shape["categories"]) == 9
    assert {gate["group"] for gate in shape["gates"]} == {group["id"] for group in shape["groups"]}
    assert {category["group"] for category in shape["categories"]} == {
        group["id"] for group in shape["groups"]
    }
    # Every control carries the question it is asking, not just a field name.
    assert all(gate["question"] for gate in shape["gates"])
    assert all(category["prompt"] for category in shape["categories"])
    assert len(shape["ratingMeanings"]) == 6
    assert shape["approvalPercentage"] == APPROVAL_PERCENTAGE
    assert shape["productionPercentage"] == PRODUCTION_PERCENTAGE
