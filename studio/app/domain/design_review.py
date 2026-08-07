"""Structured representations of a garment design review.

``DESIGN_REVIEW_SCORECARD.md`` and ``SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md`` are
already written as a deterministic rubric -- twelve pass/fail gates, nine weighted
0-5 categories with explicit floors, a fixed points formula. Nobody had encoded the
arithmetic; every design that had been reviewed to date was scored by hand. This
module is that rubric as data. ``app.services.design_scoring`` is the pure function
that scores it. Neither module touches an image, a database or a model -- feature
extraction (does this design have one dominant proposition? does the thumbnail test
pass?) is a separate, harder problem this deliberately does not solve. What goes in
here is the judgement a human (or a future extractor) has already reached, structured
so the arithmetic and the gates stop being done by hand.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HardGate(StrEnum):
    """The twelve hard-fail gates, ``DESIGN_REVIEW_SCORECARD.md`` §3.

    Named after what each gate catches, not "HF-01" through "HF-12" -- the numbers
    are the source document's citation, not a naming scheme worth repeating in code.
    """

    NO_CLEAR_PRODUCT_DEFINITION = "no_clear_product_definition"
    NO_COLLECTION_ROLE = "no_collection_role"
    NO_DOMINANT_PROPOSITION = "no_dominant_proposition"
    HIERARCHY_COLLAPSE = "hierarchy_collapse"
    DISTANCE_FAILURE = "distance_failure"
    GARMENT_CONFLICT = "garment_conflict"
    PRODUCTION_FAILURE = "production_failure"
    IDENTITY_SUBSTITUTION = "identity_substitution"
    WEAK_WITHOUT_THE_LOGO = "weak_without_the_logo"
    COLLECTION_REDUNDANCY = "collection_redundancy"
    MOCK_UP_ONLY_SUCCESS = "mock_up_only_success"
    UNRESOLVED_RIGHTS_RISK = "unresolved_rights_risk"


class GateStatus(StrEnum):
    """The outcome of one hard gate.

    ``NOT_TESTED`` is not a pass. ``DESIGN_REVIEW_SCORECARD.md`` §2's mandatory
    evidence list (front/back artwork, worn-body mock-up, actual-size proof, and so
    on) is frequently not all available -- one photograph is not enough evidence to
    approve or reject some gates. A gate the evidence cannot speak to blocks release
    exactly as a failed one does; it does not default to passing by omission.
    """

    PASS = "pass"
    FAIL = "fail"
    NOT_TESTED = "not_tested"


class GateResult(BaseModel):
    """One hard gate's outcome, with the evidence it was decided on."""

    model_config = ConfigDict(frozen=True)

    gate: HardGate
    status: GateStatus
    evidence: str = Field(min_length=1, max_length=2000)

    @field_validator("evidence")
    @classmethod
    def _evidence_is_not_a_shrug(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "A gate result needs the evidence it was decided on, not an empty "
                "string. See DESIGN_REVIEW_SCORECARD.md §11: 'identify the failed "
                "mechanism, not merely state dislike.'"
            )
        return value


class ScoreCategory(StrEnum):
    """The nine weighted categories, ``DESIGN_REVIEW_SCORECARD.md`` §4."""

    PRODUCT_FIT = "product_fit"
    DOMINANT_PROPOSITION = "dominant_proposition"
    COMPOSITION_AND_HIERARCHY = "composition_and_hierarchy"
    DISTANCE_AND_SILHOUETTE = "distance_and_silhouette"
    TYPOGRAPHY = "typography"
    BRAND_RECOGNITION = "brand_recognition"
    COLLECTION_CONTRIBUTION = "collection_contribution"
    PRODUCTION_INTEGRITY = "production_integrity"
    COMMERCIAL_WEARABILITY = "commercial_wearability"


# category -> (maximum points, category floor). §4 for the maxima, §6 for the
# floors. Typography's floor is conditional in the source text ("minimum 3/5 when
# typography is present") -- callers that omit a typography-free design should not
# rate this category rather than rating it 0, since 0 would trip the floor for a
# design the rule does not apply to.
CATEGORY_LIMITS: dict[ScoreCategory, tuple[int, int]] = {
    ScoreCategory.PRODUCT_FIT: (10, 3),
    ScoreCategory.DOMINANT_PROPOSITION: (10, 4),
    ScoreCategory.COMPOSITION_AND_HIERARCHY: (15, 4),
    ScoreCategory.DISTANCE_AND_SILHOUETTE: (10, 3),
    ScoreCategory.TYPOGRAPHY: (10, 3),
    ScoreCategory.BRAND_RECOGNITION: (15, 3),
    ScoreCategory.COLLECTION_CONTRIBUTION: (10, 3),
    ScoreCategory.PRODUCTION_INTEGRITY: (15, 4),
    ScoreCategory.COMMERCIAL_WEARABILITY: (5, 3),
}

MAX_TOTAL_SCORE: int = sum(maximum for maximum, _floor in CATEGORY_LIMITS.values())


class CategoryRating(BaseModel):
    """One category's 0-5 rating, with the evidence it was decided on."""

    model_config = ConfigDict(frozen=True)

    category: ScoreCategory
    rating: int = Field(ge=0, le=5)
    evidence: str = Field(min_length=1, max_length=2000)

    @field_validator("evidence")
    @classmethod
    def _evidence_is_not_a_shrug(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "A category rating needs the evidence it was decided on. See "
                "DESIGN_REVIEW_SCORECARD.md §11."
            )
        return value


class DesignReviewInput(BaseModel):
    """What a human reviewer (or a future extractor) has already determined.

    This is the record; scoring the record is a separate, pure step. A
    ``DesignReviewInput`` with no ratings and no gate results is valid -- it just
    scores as fully blocked, which is correct: an unreviewed design is not an
    approved one.
    """

    model_config = ConfigDict(frozen=True)

    design_id: str = Field(min_length=1, max_length=200)
    design_name: str = Field(min_length=1, max_length=200)
    gate_results: list[GateResult] = Field(default_factory=list)
    category_ratings: list[CategoryRating] = Field(default_factory=list)


class ApprovalBand(StrEnum):
    """``DESIGN_REVIEW_SCORECARD.md`` §5's four bands."""

    RELEASE_CANDIDATE = "release_candidate"
    STRONG_REVISE_SELECTIVELY = "strong_revise_selectively"
    REWORK = "rework"
    REJECT_OR_REBUILD = "reject_or_rebuild"


class CategoryScore(BaseModel):
    """One category's computed points, alongside the rating that produced them."""

    model_config = ConfigDict(frozen=True)

    category: ScoreCategory
    rating: int
    points: float
    max_points: int
    floor: int
    below_floor: bool


class DesignReviewOutcome(BaseModel):
    """The result of scoring a ``DesignReviewInput``.

    ``blocked`` is the fact that matters first. ``DESIGN_REVIEW_SCORECARD.md`` §1:
    "A high score cannot override a hard failure." ``total_score`` and ``band`` are
    still computed when blocked -- for the diagnostic, not as a route around it.
    """

    model_config = ConfigDict(frozen=True)

    design_id: str
    design_name: str
    blocked: bool
    failed_gates: list[HardGate]
    untested_gates: list[HardGate]
    missing_categories: list[ScoreCategory]
    category_scores: list[CategoryScore]
    floor_failures: list[ScoreCategory]
    total_score: float
    max_total_score: int
    band: ApprovalBand
