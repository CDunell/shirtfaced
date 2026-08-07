"""Scoring a garment design against ``DESIGN_REVIEW_SCORECARD.md``.

Pure function, no I/O: takes a :class:`~app.domain.design_review.DesignReviewInput`
-- a reviewer's already-formed judgement, structured -- and returns the arithmetic
and gate logic the scorecard specifies. It does not decide whether a design is good;
it decides what the scorecard's own rules say given the judgement it was handed.

Adapted from the deterministic scoring pattern in the sibling ``hunter_core``
platform (``ScoringEngine.score()`` / cited ``FitResult``) -- weighted components,
a pure scoring function, evidence required on every rated element. The hard-gate
short-circuit and category floors are Shirtfaced-specific; the source rubric already
had them, they had just never been code.
"""

from __future__ import annotations

from app.domain.design_review import (
    CATEGORY_LIMITS,
    MAX_TOTAL_SCORE,
    ApprovalBand,
    CategoryScore,
    DesignReviewInput,
    DesignReviewOutcome,
    GateStatus,
    HardGate,
    ScoreCategory,
)

# A category a design may legitimately not have. DESIGN_REVIEW_SCORECARD.md §6:
# "Typography: minimum 3/5 when typography is present" -- the only conditional
# floor in the document. Every other category is required; an absent rating there
# means the review is incomplete, not that the category does not apply.
OPTIONAL_CATEGORIES: frozenset[ScoreCategory] = frozenset({ScoreCategory.TYPOGRAPHY})


def _band_for(total_score: float) -> ApprovalBand:
    """§5 Approval Bands. Boundaries are inclusive of their lower edge."""
    if total_score >= 90:
        return ApprovalBand.RELEASE_CANDIDATE
    if total_score >= 80:
        return ApprovalBand.STRONG_REVISE_SELECTIVELY
    if total_score >= 70:
        return ApprovalBand.REWORK
    return ApprovalBand.REJECT_OR_REBUILD


def score_design(review: DesignReviewInput) -> DesignReviewOutcome:
    """Score one design review. Deterministic: same input, same output, always."""
    gates_by_name = {result.gate: result.status for result in review.gate_results}
    failed_gates = [gate for gate in HardGate if gates_by_name.get(gate) is GateStatus.FAIL]
    untested_gates = [
        gate
        for gate in HardGate
        if gates_by_name.get(gate, GateStatus.NOT_TESTED) is GateStatus.NOT_TESTED
    ]

    ratings_by_category = {rating.category: rating for rating in review.category_ratings}
    missing_categories = [
        category
        for category in CATEGORY_LIMITS
        if category not in ratings_by_category and category not in OPTIONAL_CATEGORIES
    ]

    category_scores: list[CategoryScore] = []
    floor_failures: list[ScoreCategory] = []
    total_score = 0.0
    for category, (max_points, floor) in CATEGORY_LIMITS.items():
        rating_record = ratings_by_category.get(category)
        rating = rating_record.rating if rating_record is not None else 0
        # §5: category score = rating / 5 * category maximum.
        points = (rating / 5) * max_points
        below_floor = rating_record is not None and rating < floor
        if below_floor:
            floor_failures.append(category)
        category_scores.append(
            CategoryScore(
                category=category,
                rating=rating,
                points=points,
                max_points=max_points,
                floor=floor,
                below_floor=below_floor,
            )
        )
        total_score += points

    blocked = bool(failed_gates or untested_gates or missing_categories or floor_failures)

    return DesignReviewOutcome(
        design_id=review.design_id,
        design_name=review.design_name,
        blocked=blocked,
        failed_gates=failed_gates,
        untested_gates=untested_gates,
        missing_categories=missing_categories,
        category_scores=category_scores,
        floor_failures=floor_failures,
        total_score=round(total_score, 2),
        max_total_score=MAX_TOTAL_SCORE,
        band=_band_for(total_score),
    )
