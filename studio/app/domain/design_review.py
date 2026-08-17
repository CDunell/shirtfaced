"""The design review contract: gates, categories, and what a review means.

Ported from ``admin/src/design-system/domain.ts`` and ``workflow.ts`` on
14 August 2026 by owner decision (Phase 0.2 of ``DESIGN_FLOW_PLAN.md``), and
those files deleted in the same change. This is the only copy.

**Why it moved rather than being called where it was.** The two-pipeline split
puts product in studio and world in admin, and this is the product judgement
engine. The move was cheap because nothing in admin imported it -- no page, no
route, only its own test file. It was a tested contract island in the wrong
building.

**Why it is Python and server-side.** The decision it gates is stored by studio,
whose server is Python. Evaluating in the browser and having the server record
the verdict would let an approval be posted without passing the gates; the gate
has to run where the row is written.

This is not a second implementation of anything -- §8 of
``DESIGN_ENGINE_ADAPTATION.md`` deleted a Python copy that ran *alongside* the
TypeScript one, in a different app, without the workflow. One engine was the
rule then and is the rule now. What changed is which building it stands in.

The three lists here -- gate ids, category limits, thresholds -- are the single
source of truth for both measurement (``design_extraction``) and judgement
(``design_scoring``). They were duplicated in ``design_extraction`` before this
port and are imported from here now, because two copies of a rubric drift and
the drift is invisible until something is approved that should not have been.

**A known discrepancy, recorded rather than resolved.** These thirteen gates are
the constitution's §16 twelve plus rights, which is what the code has always
enforced. They are *not* ``DESIGN_REVIEW_SCORECARD.md``'s HF-01..HF-12: that
document's *HF-10 Collection Redundancy* has no gate id at all, and this list's
*essential text illegible*, *identity geometry altered* and *production files do
not match art* have no HF number. Reconciling the two documents is the owner's
call and belongs to Phase 4. Porting the list as it stands keeps the code
honest about what it actually checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

__all__ = [
    "APPROVAL_PERCENTAGE",
    "CATEGORY_LIMITS",
    "GATE_LABELS",
    "HARD_GATE_IDS",
    "PRODUCTION_PERCENTAGE",
    "ApprovalBand",
    "DesignReviewInput",
    "DesignStatus",
    "HardGate",
    "ReviewDecision",
    "ReviewEvaluation",
    "ReviewResult",
    "ScoreCategory",
    "approval_band",
    "can_transition",
    "category_group",
    "gate_group",
    "points_floor",
]


class ReviewResult(StrEnum):
    """A hard gate's answer. ``NOT_TESTED`` blocks release exactly as ``FAIL``
    does -- the scorecard's own rule, and the reason a partly-filled review is
    worth more than a fully-filled one that guessed."""

    PASS = "pass"
    FAIL = "fail"
    NOT_TESTED = "not_tested"


class DesignStatus(StrEnum):
    """The eleven design statuses, verbatim from ``domain.ts``.

    That file is not in the repository: ``admin/src/design-system/`` was deleted
    in 4187e2f, which is the commit that made this the only copy. Checked
    against the original again on 18 August 2026 from a surviving snapshot --
    same eleven, same order. The pin that outlives the snapshot is
    ``tests/unit/test_design_scoring.py``, which is ``workflow.test.ts``'s seven
    cases translated rather than reinterpreted.

    Ported intact because the owner's decision was to move the engine, not to
    edit it, and because ``next_status_for_review`` is part of the tested
    contract. Nothing in studio drives this machine today -- the product
    pipeline runs on ``DesignAttemptState`` and ``ConceptStatus``, which are
    driven by ``design_pipeline``. Phase 3's ``ProductionItem`` is where these
    two vocabularies either meet or one of them is deleted with a written
    reason. Until then this is the review's own vocabulary for what a review
    *means*, not a second lifecycle anything is stored in.
    """

    DRAFT = "draft"
    BRIEF_READY = "brief_ready"
    ARTWORK_IN_PROGRESS = "artwork_in_progress"
    REVIEW_READY = "review_ready"
    REVISION_REQUIRED = "revision_required"
    DESIGN_APPROVED = "design_approved"
    PRODUCTION_REVIEW = "production_review"
    PRODUCTION_APPROVED = "production_approved"
    RELEASED = "released"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ReviewDecision(StrEnum):
    """What a reviewer asks for. A subset of ``DesignStatus``, as in
    ``designReviewSchema.decision``."""

    REVISION_REQUIRED = "revision_required"
    DESIGN_APPROVED = "design_approved"
    PRODUCTION_REVIEW = "production_review"
    PRODUCTION_APPROVED = "production_approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


ALLOWED_TRANSITIONS: dict[DesignStatus, tuple[DesignStatus, ...]] = {
    DesignStatus.DRAFT: (DesignStatus.BRIEF_READY, DesignStatus.ARCHIVED),
    DesignStatus.BRIEF_READY: (
        DesignStatus.ARTWORK_IN_PROGRESS,
        DesignStatus.DRAFT,
        DesignStatus.ARCHIVED,
    ),
    DesignStatus.ARTWORK_IN_PROGRESS: (
        DesignStatus.REVIEW_READY,
        DesignStatus.BRIEF_READY,
        DesignStatus.ARCHIVED,
    ),
    DesignStatus.REVIEW_READY: (
        DesignStatus.REVISION_REQUIRED,
        DesignStatus.DESIGN_APPROVED,
        DesignStatus.REJECTED,
    ),
    DesignStatus.REVISION_REQUIRED: (
        DesignStatus.ARTWORK_IN_PROGRESS,
        DesignStatus.REVIEW_READY,
        DesignStatus.REJECTED,
        DesignStatus.ARCHIVED,
    ),
    DesignStatus.DESIGN_APPROVED: (
        DesignStatus.PRODUCTION_REVIEW,
        DesignStatus.REVISION_REQUIRED,
        DesignStatus.ARCHIVED,
    ),
    DesignStatus.PRODUCTION_REVIEW: (
        DesignStatus.PRODUCTION_APPROVED,
        DesignStatus.REVISION_REQUIRED,
        DesignStatus.REJECTED,
    ),
    DesignStatus.PRODUCTION_APPROVED: (
        DesignStatus.RELEASED,
        DesignStatus.PRODUCTION_REVIEW,
        DesignStatus.ARCHIVED,
    ),
    DesignStatus.RELEASED: (DesignStatus.ARCHIVED,),
    DesignStatus.REJECTED: (DesignStatus.ARTWORK_IN_PROGRESS, DesignStatus.ARCHIVED),
    DesignStatus.ARCHIVED: (),
}


def can_transition(source: DesignStatus, target: DesignStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[source]


# The thirteen hard-gate ids, verbatim from ``workflow.ts``'s ``HARD_GATE_IDS``
# -- a file deleted in 4187e2f, so the citation is to history rather than to
# a path. Re-checked against a surviving snapshot on 18 August 2026: same
# thirteen, same order, same reason recorded against the last of them.
# The order is the order a reviewer meets them; the ids are what callers match
# on and must not be renamed without a migration of stored reviews.
HARD_GATE_IDS: tuple[str, ...] = (
    "product_blank_defined",
    "collection_role_defined",
    "dominant_proposition_clear",
    "thumbnail_hierarchy_survives",
    "essential_text_legible",
    "construction_conflicts_resolved",
    "production_detail_feasible",
    "identity_geometry_preserved",
    "logo_removal_recognition_survives",
    "competitor_substitution_survives",
    "worn_body_review_completed",
    "production_files_match_art",
    # Rights are checked here, on a finished design, rather than at the point
    # material enters the archive. Gating intake stops the archive holding
    # anything it has not cleared, which stops it learning from anything -- and
    # the question is not answerable about a reference anyway. It is answerable
    # about a design that is about to be sold.
    "rights_cleared_for_sale",
)

GATE_LABELS: dict[str, str] = {
    "product_blank_defined": "Product and blank defined",
    "collection_role_defined": "Collection role defined",
    "dominant_proposition_clear": "Dominant proposition is clear",
    "thumbnail_hierarchy_survives": "Thumbnail hierarchy survives (T1)",
    "essential_text_legible": "Essential text legible under blur (T2)",
    "construction_conflicts_resolved": "No construction conflicts",
    "production_detail_feasible": "Production detail feasible",
    "identity_geometry_preserved": "Identity geometry preserved",
    "logo_removal_recognition_survives": "Recognition survives logo removal (T4)",
    "competitor_substitution_survives": "Resists competitor substitution (T5)",
    "worn_body_review_completed": "Worn-body review completed",
    "production_files_match_art": "Production files match approved art",
    "rights_cleared_for_sale": "Rights cleared for sale",
}

# The question each gate actually asks, in the reviewer's own terms. The label
# is a name; this is what a person has to decide. Written from
# ``DESIGN_REVIEW_SCORECARD.md`` §3 and the constitution's §16 so the form asks
# the documented question rather than a paraphrase of a field name.
GATE_QUESTIONS: dict[str, str] = {
    "product_blank_defined": (
        "Is the garment, blank, fit, colour and production method all decided and written down?"
    ),
    "collection_role_defined": (
        "Can you say which role this plays in the range -- anchor, core, expression, hero "
        "or collaboration?"
    ),
    "dominant_proposition_clear": ("Within three seconds, is the main visual idea identifiable?"),
    "thumbnail_hierarchy_survives": (
        "At thumbnail size, does one element still lead, or do two or more compete equally?"
    ),
    "essential_text_legible": "At production size, is every essential word readable?",
    "construction_conflicts_resolved": (
        "Does important artwork avoid seams, pockets, hood fall, armholes and expected folds?"
    ),
    "production_detail_feasible": (
        "Can the nominated method actually hold these lines, gaps, tonal steps and registration?"
    ),
    "identity_geometry_preserved": (
        "Is the permanent identity mark at its approved geometry, proportion and clear space?"
    ),
    "logo_removal_recognition_survives": (
        "Cover the logo. Does the artwork still have independent value and look composed?"
    ),
    "competitor_substitution_survives": (
        "Swap in a competitor's mark. Does the design become false or incoherent?"
    ),
    "worn_body_review_completed": (
        "Has it been reviewed on a body -- front, side and back, with normal arm position?"
    ),
    "production_files_match_art": "Do the production files match the artwork that was approved?",
    "rights_cleared_for_sale": (
        "Are the rights to every source, reference, likeness and typeface cleared for sale?"
    ),
}

# The nine weighted categories, ``DESIGN_REVIEW_SCORECARD.md`` §4 and §6 --
# id -> (label, maximum points, floor). The floor is stated in the source text
# as a 0-5 rating ("minimum 3/5"); ``points_floor`` converts it onto the same
# points scale as ``score``, which is what ``evaluate_review`` compares against.
# Comparing a points score against a raw 0-5 number would defeat every floor
# check silently.
CATEGORY_LIMITS: dict[str, tuple[str, int, int]] = {
    "product_fit": ("Product Fit", 10, 3),
    "dominant_proposition": ("Dominant Proposition", 10, 4),
    "composition_and_hierarchy": ("Composition and Hierarchy", 15, 4),
    "distance_and_silhouette": ("Distance and Silhouette", 10, 3),
    "typography": ("Typography", 10, 3),
    "brand_recognition": ("Brand Recognition", 15, 3),
    "collection_contribution": ("Collection Contribution", 10, 3),
    "production_integrity": ("Production Integrity", 15, 4),
    "commercial_wearability": ("Commercial Wearability", 5, 3),
}

# What each category is actually assessing, condensed from the scorecard's own
# bullet lists so the reviewer is rating the documented thing.
CATEGORY_PROMPTS: dict[str, str] = {
    "product_fit": (
        "Zone use, seam compatibility, suitability for the blank and wash -- and whether the "
        "garment improves the graphic rather than merely carrying it."
    ),
    "dominant_proposition": (
        "One clear primary idea, an immediate focal point, and no unnecessary competing devices."
    ),
    "composition_and_hierarchy": (
        "H1/H2/H3 reading order, eye path, framing and cropping, front-to-back relationship, "
        "control of density."
    ),
    "distance_and_silhouette": (
        "Thumbnail recognition, blur survival, silhouette strength, contrast structure, "
        "readability across a room."
    ),
    "typography": (
        "Identity, display and information roles kept distinct; legibility at final size; "
        "spacing; type-to-image relationship."
    ),
    "brand_recognition": (
        "Permanent identity assets, recurring placement and scale behaviour, and whether "
        "recognition survives removing the largest logo."
    ),
    "collection_contribution": (
        "A defined range role, distinction from neighbours, contribution to collection rhythm, "
        "colour and intensity balance."
    ),
    "production_integrity": (
        "Screen-print or embroidery feasibility, line and gap integrity, tonal separation, "
        "colour-count justification, ageing behaviour."
    ),
    "commercial_wearability": (
        "Whether a customer understands it without explanation, wears it outside campaign "
        "styling, and has a credible reason to buy."
    ),
}

# The 0-5 rating scale, ``DESIGN_REVIEW_SCORECARD.md`` §4. Shown beside every
# rating control: "3" has a documented meaning and guessing at it is how a
# rubric becomes arithmetic about taste.
RATING_MEANINGS: tuple[str, ...] = (
    "absent or structurally failed",
    "materially weak",
    "below release standard",
    "competent and acceptable",
    "strong",
    "exceptional and clearly intentional",
)

# The constitution's steps 7, 8 and 9 -- validate recognition, validate
# production, review against the collection. Three different questions, kept as
# three groups rather than one undifferentiated list of twenty-two controls.
RECOGNITION = "validate_recognition"
PRODUCTION = "validate_production"
COLLECTION = "review_against_collection"

GROUP_LABELS: dict[str, str] = {
    RECOGNITION: "Validate recognition",
    PRODUCTION: "Validate production",
    COLLECTION: "Review against the collection",
}

GROUP_BLURBS: dict[str, str] = {
    RECOGNITION: (
        "Constitution step 7. Does it read, does it say one thing, and is it recognisably "
        "ours with the logo covered?"
    ),
    PRODUCTION: (
        "Constitution step 8. Can it be made, on this blank, by this method, and does it "
        "survive being worn?"
    ),
    COLLECTION: (
        "Constitution step 9. Does it earn a place in the range, and can it be sold? "
        "Rights sit here because the question is answerable about a finished design, "
        "not about a reference."
    ),
}

GATE_GROUPS: dict[str, str] = {
    "dominant_proposition_clear": RECOGNITION,
    "thumbnail_hierarchy_survives": RECOGNITION,
    "essential_text_legible": RECOGNITION,
    "identity_geometry_preserved": RECOGNITION,
    "logo_removal_recognition_survives": RECOGNITION,
    "competitor_substitution_survives": RECOGNITION,
    "product_blank_defined": PRODUCTION,
    "construction_conflicts_resolved": PRODUCTION,
    "production_detail_feasible": PRODUCTION,
    "worn_body_review_completed": PRODUCTION,
    "production_files_match_art": PRODUCTION,
    "collection_role_defined": COLLECTION,
    "rights_cleared_for_sale": COLLECTION,
}

CATEGORY_GROUPS: dict[str, str] = {
    "dominant_proposition": RECOGNITION,
    "composition_and_hierarchy": RECOGNITION,
    "distance_and_silhouette": RECOGNITION,
    "typography": RECOGNITION,
    "brand_recognition": RECOGNITION,
    "product_fit": PRODUCTION,
    "production_integrity": PRODUCTION,
    "collection_contribution": COLLECTION,
    "commercial_wearability": COLLECTION,
}

# ``workflow.ts``'s two thresholds, re-checked 18 August 2026 against the
# snapshot. Design approval at 75, production approval
# at 85, both on top of every gate passing and every floor met.
APPROVAL_PERCENTAGE = 75.0
PRODUCTION_PERCENTAGE = 85.0


class ApprovalBand(StrEnum):
    """``DESIGN_REVIEW_SCORECARD.md`` §5. A band is a description of the score,
    never a decision -- a 90 does not approve a design with a hard failure."""

    RELEASE_CANDIDATE = "release_candidate"
    REVISE_SELECTIVELY = "revise_selectively"
    REWORK = "rework"
    REJECT_OR_REBUILD = "reject_or_rebuild"


BAND_LABELS: dict[ApprovalBand, str] = {
    ApprovalBand.RELEASE_CANDIDATE: "Release candidate",
    ApprovalBand.REVISE_SELECTIVELY: "Strong, revise selectively",
    ApprovalBand.REWORK: "Rework",
    ApprovalBand.REJECT_OR_REBUILD: "Reject or rebuild",
}


def approval_band(percentage: float) -> ApprovalBand:
    if percentage >= 90:
        return ApprovalBand.RELEASE_CANDIDATE
    if percentage >= 80:
        return ApprovalBand.REVISE_SELECTIVELY
    if percentage >= 70:
        return ApprovalBand.REWORK
    return ApprovalBand.REJECT_OR_REBUILD


def points_floor(category_id: str) -> float:
    """A category's release floor, in the same points-out-of-maximum scale as
    its ``score`` -- not the 0-5 rating the scorecard states it in."""
    _label, maximum, rating_floor = CATEGORY_LIMITS[category_id]
    return round((rating_floor / 5) * maximum, 2)


def gate_group(gate_id: str) -> str:
    return GATE_GROUPS[gate_id]


def category_group(category_id: str) -> str:
    return CATEGORY_GROUPS[category_id]


@dataclass(frozen=True)
class HardGate:
    """One gate's answer. ``hardGateSchema``'s four fields, unchanged."""

    id: str
    label: str
    result: ReviewResult
    evidence: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "label": self.label,
            "result": self.result.value,
            "evidence": self.evidence,
        }

    @classmethod
    def of(cls, raw: dict[str, Any]) -> HardGate:
        """One stored gate, back off JSONB. An unreadable result reads as
        ``not_tested``, which blocks -- never as a pass."""
        gate_id = str(raw["id"])
        try:
            result = ReviewResult(str(raw.get("result") or ""))
        except ValueError:
            result = ReviewResult.NOT_TESTED
        return cls(
            id=gate_id,
            label=str(raw.get("label") or GATE_LABELS.get(gate_id, gate_id)),
            result=result,
            evidence=str(raw.get("evidence") or ""),
        )


@dataclass(frozen=True)
class ScoreCategory:
    """One category's rating, carried as points. ``scoreCategorySchema``."""

    id: str
    label: str
    score: float
    maximum: int
    minimum_required: float | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "score": self.score,
            "maximum": self.maximum,
            "minimumRequired": self.minimum_required,
            "notes": self.notes,
        }

    @classmethod
    def of(cls, raw: dict[str, Any]) -> ScoreCategory:
        """One stored category, back off JSONB.

        ``Any`` rather than ``object`` because that is what a JSONB column
        actually hands back, and a signature that claims otherwise buys its
        precision with a stack of ``type: ignore``. The maximum falls back to
        the rubric rather than to zero: a stored row that lost its maximum
        would otherwise divide a real score by nothing and read as 0%.
        """
        category_id = str(raw["id"])
        fallback_label, fallback_maximum, _floor = CATEGORY_LIMITS.get(
            category_id, (category_id, 0, 0)
        )
        minimum = raw.get("minimumRequired", raw.get("minimum_required"))
        return cls(
            id=category_id,
            label=str(raw.get("label") or fallback_label),
            score=float(raw.get("score") or 0),
            maximum=int(raw.get("maximum") or fallback_maximum),
            minimum_required=None if minimum is None else float(minimum),
            notes=str(raw.get("notes") or ""),
        )

    @classmethod
    def from_rating(cls, category_id: str, rating: int, notes: str = "") -> ScoreCategory:
        """A 0-5 rating as the scorecard states it, converted to points.

        ``category score = rating / 5 * category maximum``, §5 verbatim. This is
        the only place that conversion happens, so a rating entered in a form
        and a rating measured from an image land on the same scale.
        """
        if not 0 <= rating <= 5:
            raise ValueError(f"a rating is 0 to 5, got {rating}")
        label, maximum, _floor = CATEGORY_LIMITS[category_id]
        return cls(
            id=category_id,
            label=label,
            score=round((rating / 5) * maximum, 2),
            maximum=maximum,
            minimum_required=points_floor(category_id),
            notes=notes,
        )


@dataclass(frozen=True)
class DesignReviewInput:
    """Everything ``score_design`` needs to reach a verdict.

    ``designReviewSchema`` minus the identifiers the caller already holds. A
    complete input answers all thirteen gates and all nine categories; an
    incomplete one is still accepted and still evaluated, because the honest
    answer to a half-filled review is "not eligible, and here is what is
    missing" rather than a refusal to look.
    """

    design_id: str
    reviewer_id: str
    hard_gates: list[HardGate] = field(default_factory=list)
    score_categories: list[ScoreCategory] = field(default_factory=list)
    decision: ReviewDecision = ReviewDecision.DESIGN_APPROVED
    rationale: str = ""


@dataclass(frozen=True)
class ReviewEvaluation:
    """``evaluateReview``'s return, field for field, plus the scorecard's band.

    ``blockers`` is this port's own addition: the reasons in the reviewer's
    words. ``evaluateReview`` returns the failing rows and leaves the caller to
    phrase it, and every caller phrasing it separately is how two screens end up
    disagreeing about why something cannot ship.
    """

    hard_gate_passed: bool
    failed_hard_gates: list[HardGate]
    untested_hard_gates: list[HardGate]
    total_score: float
    maximum_score: float
    percentage: float
    failed_category_minimums: list[ScoreCategory]
    unrated_categories: list[str]
    eligible_for_design_approval: bool
    eligible_for_production_approval: bool
    band: ApprovalBand
    blockers: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "hardGatePassed": self.hard_gate_passed,
            "failedHardGates": [gate.to_dict() for gate in self.failed_hard_gates],
            "untestedHardGates": [gate.to_dict() for gate in self.untested_hard_gates],
            "totalScore": self.total_score,
            "maximumScore": self.maximum_score,
            "percentage": round(self.percentage, 2),
            "failedCategoryMinimums": [
                category.to_dict() for category in self.failed_category_minimums
            ],
            "unratedCategories": list(self.unrated_categories),
            "eligibleForDesignApproval": self.eligible_for_design_approval,
            "eligibleForProductionApproval": self.eligible_for_production_approval,
            "band": self.band.value,
            "bandLabel": BAND_LABELS[self.band],
            "blockers": list(self.blockers),
        }
