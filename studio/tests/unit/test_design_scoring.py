"""Scoring a design review record against DESIGN_REVIEW_SCORECARD.md.

The rubric already specifies exact arithmetic and gate logic in prose; this pins
that logic is followed correctly, not whether any particular design is good.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domain.design_review import (
    CATEGORY_LIMITS,
    MAX_TOTAL_SCORE,
    ApprovalBand,
    CategoryRating,
    DesignReviewInput,
    GateResult,
    GateStatus,
    HardGate,
    ScoreCategory,
)
from app.services.design_scoring import score_design

ALL_GATES_PASS = [
    GateResult(gate=gate, status=GateStatus.PASS, evidence=f"{gate.value} checked, clean")
    for gate in HardGate
]


def _rating(category: ScoreCategory, value: int, evidence: str = "reviewed") -> CategoryRating:
    return CategoryRating(category=category, rating=value, evidence=evidence)


def _all_categories_at(value: int) -> list[CategoryRating]:
    return [_rating(category, value) for category in CATEGORY_LIMITS]


def test_max_total_score_matches_the_scorecard() -> None:
    """§4: 10+10+15+10+10+15+10+15+5 = 100."""
    assert MAX_TOTAL_SCORE == 100


def test_a_fully_rated_design_with_no_failures_is_not_blocked() -> None:
    review = DesignReviewInput(
        design_id="D-001",
        design_name="Test Design",
        gate_results=ALL_GATES_PASS,
        category_ratings=_all_categories_at(5),
    )
    outcome = score_design(review)

    assert outcome.blocked is False
    assert outcome.total_score == 100.0
    assert outcome.band is ApprovalBand.RELEASE_CANDIDATE


def test_a_single_failed_gate_blocks_regardless_of_score() -> None:
    """§1: 'A high score cannot override a hard failure.'"""
    gates = [
        GateResult(
            gate=HardGate.UNRESOLVED_RIGHTS_RISK,
            status=GateStatus.FAIL,
            evidence="artwork source unverified",
        ),
        *[g for g in ALL_GATES_PASS if g.gate is not HardGate.UNRESOLVED_RIGHTS_RISK],
    ]
    review = DesignReviewInput(
        design_id="D-002",
        design_name="Perfect Except Rights",
        gate_results=gates,
        category_ratings=_all_categories_at(5),
    )
    outcome = score_design(review)

    assert outcome.total_score == 100.0
    assert outcome.blocked is True
    assert outcome.failed_gates == [HardGate.UNRESOLVED_RIGHTS_RISK]


def test_an_untested_gate_blocks_the_same_as_a_failed_one() -> None:
    """Missing evidence is not a pass. DESIGN_REVIEW_SCORECARD.md §2."""
    gates = [g for g in ALL_GATES_PASS if g.gate is not HardGate.PRODUCTION_FAILURE]
    review = DesignReviewInput(
        design_id="D-003",
        design_name="One Gate Never Checked",
        gate_results=gates,
        category_ratings=_all_categories_at(5),
    )
    outcome = score_design(review)

    assert outcome.blocked is True
    assert outcome.untested_gates == [HardGate.PRODUCTION_FAILURE]
    assert outcome.failed_gates == []


def test_a_missing_required_category_blocks() -> None:
    ratings = [
        r for r in _all_categories_at(5) if r.category is not ScoreCategory.PRODUCTION_INTEGRITY
    ]
    review = DesignReviewInput(
        design_id="D-004",
        design_name="Production Never Rated",
        gate_results=ALL_GATES_PASS,
        category_ratings=ratings,
    )
    outcome = score_design(review)

    assert outcome.blocked is True
    assert outcome.missing_categories == [ScoreCategory.PRODUCTION_INTEGRITY]
    # Uncomputed categories contribute no points -- not a free pass, a zero.
    assert outcome.total_score == MAX_TOTAL_SCORE - 15


def test_typography_may_be_omitted_without_blocking() -> None:
    """§6: the floor applies 'when typography is present' -- the one conditional category."""
    ratings = [r for r in _all_categories_at(5) if r.category is not ScoreCategory.TYPOGRAPHY]
    review = DesignReviewInput(
        design_id="D-005",
        design_name="No Type In This One",
        gate_results=ALL_GATES_PASS,
        category_ratings=ratings,
    )
    outcome = score_design(review)

    assert outcome.missing_categories == []
    assert outcome.blocked is False
    assert outcome.total_score == MAX_TOTAL_SCORE - 10


def test_a_category_below_its_floor_blocks_even_with_a_high_total() -> None:
    """§6: floors are independent of the total. A design can score well and still fail here."""
    ratings = _all_categories_at(5)
    ratings = [
        _rating(ScoreCategory.BRAND_RECOGNITION, 2, "no permanent identity mark legible")
        if r.category is ScoreCategory.BRAND_RECOGNITION
        else r
        for r in ratings
    ]
    review = DesignReviewInput(
        design_id="D-006",
        design_name="Everything Else Perfect",
        gate_results=ALL_GATES_PASS,
        category_ratings=ratings,
    )
    outcome = score_design(review)

    assert outcome.total_score == 91.0  # 100 - (15 - 15*2/5)
    assert outcome.band is ApprovalBand.RELEASE_CANDIDATE  # the number alone would pass
    assert outcome.blocked is True  # but the floor still blocks it
    assert outcome.floor_failures == [ScoreCategory.BRAND_RECOGNITION]


@pytest.mark.parametrize(
    ("total", "expected_band"),
    [
        (100.0, ApprovalBand.RELEASE_CANDIDATE),
        (90.0, ApprovalBand.RELEASE_CANDIDATE),
        (89.99, ApprovalBand.STRONG_REVISE_SELECTIVELY),
        (80.0, ApprovalBand.STRONG_REVISE_SELECTIVELY),
        (79.99, ApprovalBand.REWORK),
        (70.0, ApprovalBand.REWORK),
        (69.99, ApprovalBand.REJECT_OR_REBUILD),
        (0.0, ApprovalBand.REJECT_OR_REBUILD),
    ],
)
def test_band_boundaries(total: float, expected_band: ApprovalBand) -> None:
    from app.services.design_scoring import _band_for

    assert _band_for(total) is expected_band


def test_evidence_is_required_on_a_gate_result() -> None:
    with pytest.raises(ValidationError):
        GateResult(gate=HardGate.NO_DOMINANT_PROPOSITION, status=GateStatus.PASS, evidence="   ")


def test_evidence_is_required_on_a_category_rating() -> None:
    with pytest.raises(ValidationError):
        CategoryRating(category=ScoreCategory.TYPOGRAPHY, rating=5, evidence="")


def test_the_not_yours_tee_review_reconstructed() -> None:
    """The honest manual review from this session's item-5 attempt, as data.

    good-times-bad-decisions aside: this was a real placeholder product photo, not a
    design run through the constitution, so it was never actually approved or
    rejected -- the review was aborted before a decision. Reconstructed here as a
    regression fixture because the arithmetic was worked out by hand and is worth
    pinning: total 66/100, blocked on two independent floor failures (Brand
    Recognition 2/5, Production Integrity 2/5) plus unresolved gates the single
    lifestyle photo couldn't provide evidence for.
    """
    gate_results = [
        GateResult(
            gate=HardGate.NO_CLEAR_PRODUCT_DEFINITION,
            status=GateStatus.FAIL,
            evidence="fit block and production method not confirmed for this SKU",
        ),
        GateResult(
            gate=HardGate.NO_COLLECTION_ROLE,
            status=GateStatus.PASS,
            evidence="assigned Core for the first time in this review",
        ),
        GateResult(
            gate=HardGate.NO_DOMINANT_PROPOSITION,
            status=GateStatus.PASS,
            evidence="heart + barbed wire + 'not yours never was' reads in under 3 seconds",
        ),
        GateResult(
            gate=HardGate.HIERARCHY_COLLAPSE,
            status=GateStatus.PASS,
            evidence="icon dominant, type clearly secondary, no competing elements",
        ),
        GateResult(
            gate=HardGate.DISTANCE_FAILURE,
            status=GateStatus.PASS,
            evidence="heart mass survives thumbnail test, though proposition leans on text",
        ),
        GateResult(
            gate=HardGate.GARMENT_CONFLICT,
            status=GateStatus.PASS,
            evidence="centred upper back, clear of seams in the one available photo",
        ),
        GateResult(
            gate=HardGate.PRODUCTION_FAILURE,
            status=GateStatus.NOT_TESTED,
            evidence=(
                "sub-heart text illegible even at 6x digital zoom; "
                "source resolution insufficient to confirm"
            ),
        ),
        GateResult(
            gate=HardGate.IDENTITY_SUBSTITUTION,
            status=GateStatus.NOT_TESTED,
            evidence="no confirmed legible permanent mark to test substitution against",
        ),
        GateResult(
            gate=HardGate.WEAK_WITHOUT_THE_LOGO,
            status=GateStatus.PASS,
            evidence="design has independent value, does not rely on an enlarged logo",
        ),
        GateResult(
            gate=HardGate.COLLECTION_REDUNDANCY,
            status=GateStatus.PASS,
            evidence="no other heart-motif design in the current demo range",
        ),
        GateResult(
            gate=HardGate.MOCK_UP_ONLY_SUCCESS,
            status=GateStatus.PASS,
            evidence="concept works independent of the alley lighting or model pose",
        ),
        GateResult(
            gate=HardGate.UNRESOLVED_RIGHTS_RISK,
            status=GateStatus.NOT_TESTED,
            evidence=(
                "artwork and photography provenance unconfirmed; all placeholder "
                "content flagged disposable elsewhere in the repo"
            ),
        ),
    ]
    category_ratings = [
        _rating(
            ScoreCategory.PRODUCT_FIT,
            4,
            "sits naturally on the back, oversized cut suits a bold graphic",
        ),
        _rating(
            ScoreCategory.DOMINANT_PROPOSITION, 5, "single clear concept, confidently executed"
        ),
        _rating(
            ScoreCategory.COMPOSITION_AND_HIERARCHY, 4, "clean three-level read, well balanced"
        ),
        _rating(
            ScoreCategory.DISTANCE_AND_SILHOUETTE,
            3,
            "mass survives at distance, payoff depends on legible text",
        ),
        _rating(
            ScoreCategory.TYPOGRAPHY,
            3,
            "main type clean at normal distance, micro sub-line unverifiable",
        ),
        _rating(
            ScoreCategory.BRAND_RECOGNITION, 2, "no confirmed legible permanent identity asset"
        ),
        _rating(
            ScoreCategory.COLLECTION_CONTRIBUTION,
            4,
            "distinct concept versus the current demo range",
        ),
        _rating(
            ScoreCategory.PRODUCTION_INTEGRITY,
            2,
            "illegible micro-text, no flat production file available",
        ),
        _rating(
            ScoreCategory.COMMERCIAL_WEARABILITY,
            4,
            "understandable and wearable without campaign context",
        ),
    ]
    review = DesignReviewInput(
        design_id="not-yours-tee",
        design_name="Not Yours Tee",
        gate_results=gate_results,
        category_ratings=category_ratings,
    )

    outcome = score_design(review)

    assert outcome.total_score == 66.0
    assert outcome.band is ApprovalBand.REJECT_OR_REBUILD
    assert outcome.blocked is True
    assert set(outcome.floor_failures) == {
        ScoreCategory.BRAND_RECOGNITION,
        ScoreCategory.PRODUCTION_INTEGRITY,
    }
    assert HardGate.NO_CLEAR_PRODUCT_DEFINITION in outcome.failed_gates
    assert HardGate.PRODUCTION_FAILURE in outcome.untested_gates
    assert HardGate.IDENTITY_SUBSTITUTION in outcome.untested_gates
    assert HardGate.UNRESOLVED_RIGHTS_RISK in outcome.untested_gates
