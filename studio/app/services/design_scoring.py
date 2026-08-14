"""Judging a design against the scorecard, and keeping the judgement.

The other half of the port described in ``app/domain/design_review.py``:
that module is the contract, this is ``workflow.ts``'s ``evaluateReview`` and
``nextStatusForReview`` plus the persistence they never had.

Three things happen here and they are deliberately separable:

* ``evaluate_review`` is pure. Same input, same verdict, no session, no clock.
  It is the function the unit tests pin against the TypeScript it replaced.
* ``score_design`` stores that verdict against an attempt. One review row per
  attempt, rewritable while the attempt is undecided and frozen the moment a
  ``design_decisions`` row exists -- because a review edited after the decision
  it justified is no longer a justification.
* ``guard_decision`` is what makes the gate real. ``decide_attempt`` records
  whatever it is told; this refuses an approval that the scorecard does not
  support, and says which gate or floor refused it.

**Why the gate lives on the server.** An approval is a row. If the browser
decided eligibility and the server merely recorded the answer, an approval
could be posted without passing a single gate. The check has to run where the
row is written, which is why Phase 0.2 chose a Python port over copying the
TypeScript into ``studio/web``.

**What this will never do.** Decide whether the joke lands, whether the idea is
worth making, or whether it belongs in the range. Those are the nine categories
and they are answered by a person; this only checks that they *were* answered
and does the arithmetic the scorecard specifies on the answers.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.concept_models import DesignAttempt, DesignDecision, DesignReviewRecord
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
    ReviewEvaluation,
    ReviewResult,
    ScoreCategory,
    approval_band,
    points_floor,
)
from app.domain.enums import DesignDecisionKind
from app.domain.errors import StudioError

__all__ = [
    "ReviewFrozen",
    "ScoredReview",
    "evaluate_review",
    "guard_decision",
    "load_review",
    "next_status_for_review",
    "score_design",
]


class ReviewFrozen(StudioError):
    """The attempt has been decided; its review is now history. HTTP 409."""


class NotEligible(StudioError):
    """The scorecard does not support the decision being asked for. HTTP 422."""


def evaluate_review(review: DesignReviewInput) -> ReviewEvaluation:
    """``evaluateReview``, ported. Pure: no session, no clock, no I/O.

    Every one of the thirteen gates is required. A gate the caller did not send
    is treated as ``not_tested`` rather than absent, which is the behaviour of
    the TypeScript and the reason a review cannot be passed by omission.
    """
    answered = {gate.id: gate for gate in review.hard_gates}
    required = [
        answered.get(
            gate_id,
            HardGate(
                id=gate_id,
                label=GATE_LABELS[gate_id],
                result=ReviewResult.NOT_TESTED,
            ),
        )
        for gate_id in HARD_GATE_IDS
    ]

    failed = [gate for gate in required if gate.result is ReviewResult.FAIL]
    untested = [gate for gate in required if gate.result is ReviewResult.NOT_TESTED]

    total = sum(category.score for category in review.score_categories)
    maximum = sum(category.maximum for category in review.score_categories)
    percentage = 0.0 if maximum == 0 else (total / maximum) * 100

    below_floor = [
        category
        for category in review.score_categories
        if category.minimum_required is not None and category.score < category.minimum_required
    ]
    rated = {category.id for category in review.score_categories}
    unrated = [category_id for category_id in CATEGORY_LIMITS if category_id not in rated]

    gates_passed = not failed and not untested
    # An unrated category blocks exactly as an untested gate does, and this is
    # the one place this port is deliberately stricter than the TypeScript.
    # ``evaluateReview`` had no fixed rubric -- its own tests scored a single
    # synthetic "overall" category -- so it had nothing to notice a missing one
    # against. Here the nine are the rubric, and percentage is a share of what
    # was rated: eight of nine at full marks is 100%, and without this check it
    # approves a design nobody ever rated for typography. A gap is not evidence
    # of absence.
    complete = gates_passed and not unrated
    eligible_design = complete and not below_floor and percentage >= APPROVAL_PERCENTAGE
    eligible_production = (
        complete
        and not below_floor
        and percentage >= PRODUCTION_PERCENTAGE
        and review.decision is ReviewDecision.PRODUCTION_APPROVED
    )

    return ReviewEvaluation(
        hard_gate_passed=gates_passed,
        failed_hard_gates=failed,
        untested_hard_gates=untested,
        total_score=round(total, 2),
        maximum_score=round(maximum, 2),
        percentage=percentage,
        failed_category_minimums=below_floor,
        unrated_categories=unrated,
        eligible_for_design_approval=eligible_design,
        eligible_for_production_approval=eligible_production,
        band=approval_band(percentage),
        blockers=_blockers(failed, untested, below_floor, unrated, percentage),
    )


def _blockers(
    failed: list[HardGate],
    untested: list[HardGate],
    below_floor: list[ScoreCategory],
    unrated: list[str],
    percentage: float,
) -> list[str]:
    """Why this cannot be approved, in the words a reviewer needs to act on.

    Phrased once, here, so the attempt screen and any later screen give the
    same reason. An untested gate is reported separately from a failed one
    because they need opposite work: one needs answering, the other needs the
    design changed.
    """
    reasons: list[str] = []
    for gate in failed:
        reasons.append(f"{gate.label} failed" + (f" — {gate.evidence}" if gate.evidence else ""))
    if untested:
        names = ", ".join(gate.label for gate in untested)
        reasons.append(
            f"{len(untested)} gate{'s' if len(untested) != 1 else ''} not answered: {names}"
        )
    if unrated:
        names = ", ".join(CATEGORY_LIMITS[category_id][0] for category_id in unrated)
        reasons.append(
            f"{len(unrated)} categor{'ies' if len(unrated) != 1 else 'y'} not rated: {names}"
        )
    for category in below_floor:
        floor = category.minimum_required or 0
        reasons.append(
            f"{category.label} is {category.score:g}/{category.maximum}, "
            f"below its floor of {floor:g}"
        )
    if not failed and not untested and not unrated and percentage < APPROVAL_PERCENTAGE:
        reasons.append(
            f"{percentage:.0f}/100 is below the {APPROVAL_PERCENTAGE:.0f} needed for approval"
        )
    return reasons


def next_status_for_review(review: DesignReviewInput) -> DesignStatus:
    """``nextStatusForReview``, ported unchanged."""
    result = evaluate_review(review)

    if review.decision is ReviewDecision.REJECTED:
        return DesignStatus.REJECTED
    if review.decision is ReviewDecision.ARCHIVED:
        return DesignStatus.ARCHIVED
    if not result.eligible_for_design_approval:
        return DesignStatus.REVISION_REQUIRED
    if review.decision is ReviewDecision.PRODUCTION_APPROVED:
        return (
            DesignStatus.PRODUCTION_APPROVED
            if result.eligible_for_production_approval
            else DesignStatus.REVISION_REQUIRED
        )
    if review.decision is ReviewDecision.PRODUCTION_REVIEW:
        return DesignStatus.PRODUCTION_REVIEW
    return DesignStatus.DESIGN_APPROVED


@dataclass(frozen=True)
class ScoredReview:
    """The stored review and what it evaluated to."""

    record: DesignReviewRecord
    evaluation: ReviewEvaluation


def load_review(session: Session, attempt: DesignAttempt) -> DesignReviewRecord | None:
    """The attempt's review, or ``None`` when nobody has started one.

    Queried rather than read off the relationship for the same reason
    ``design_pipeline`` queries its decision: a row inserted by this session
    does not invalidate the parent's cached collection.
    """
    return session.execute(
        select(DesignReviewRecord).where(DesignReviewRecord.design_attempt_id == attempt.id)
    ).scalar_one_or_none()


def score_design(
    session: Session,
    attempt: DesignAttempt,
    review: DesignReviewInput,
    *,
    measurements: dict[str, Any] | None = None,
) -> ScoredReview:
    """Evaluate a review and store it against its attempt.

    One row per attempt: answering three more gates updates the review rather
    than starting a second one, because a review is a working document until
    the decision is made and a pile of partial reviews answers nothing. Once
    the attempt carries a decision the row is frozen -- what justified that
    decision must stay readable exactly as it was.
    """
    reviewer = review.reviewer_id.strip()
    if not reviewer:
        raise NotEligible("a review nobody signed is not a review")

    decided = session.execute(
        select(DesignDecision).where(DesignDecision.design_attempt_id == attempt.id)
    ).scalar_one_or_none()
    if decided is not None:
        raise ReviewFrozen(
            f"attempt was decided {decided.decision.value} by {decided.actor}; "
            "its review is the record of why and cannot be edited afterwards"
        )

    evaluation = evaluate_review(review)
    record = load_review(session, attempt)
    if record is None:
        record = DesignReviewRecord(design_attempt_id=attempt.id)
        session.add(record)

    record.reviewer = reviewer
    record.hard_gates = [gate.to_dict() for gate in review.hard_gates]
    record.score_categories = [category.to_dict() for category in review.score_categories]
    record.rationale = review.rationale
    record.requested_decision = review.decision.value
    record.evaluation = evaluation.to_dict()
    record.total_score = evaluation.total_score
    record.percentage = round(evaluation.percentage, 2)
    record.band = evaluation.band.value
    record.eligible_for_design_approval = evaluation.eligible_for_design_approval
    record.scored_at = dt.datetime.now(dt.UTC)
    if measurements is not None:
        record.measurements = measurements

    session.flush()
    return ScoredReview(record=record, evaluation=evaluation)


def guard_decision(
    session: Session, attempt: DesignAttempt, decision: DesignDecisionKind
) -> ReviewEvaluation | None:
    """Refuse an approval the scorecard does not support.

    Only approval is gated. Rejecting or asking for a variation needs no
    scorecard -- an owner who can see it is wrong should not have to fill in
    twenty-two controls to say so, and the scorecard's own conduct rules put
    the burden on approval, not on refusal.

    Returns the evaluation that permitted the approval, so the caller can store
    the numbers alongside the decision. ``None`` for the ungated decisions.
    """
    if decision is not DesignDecisionKind.APPROVED:
        return None

    record = load_review(session, attempt)
    if record is None:
        raise NotEligible(
            "this attempt has no review. Answer the thirteen gates and rate the nine "
            "categories before approving it -- the scorecard cannot be skipped by "
            "approving straight from the queue."
        )

    evaluation = evaluate_review(_input_from(record))
    if not evaluation.eligible_for_design_approval:
        reasons = "; ".join(evaluation.blockers) or "the review does not meet the scorecard"
        raise NotEligible(f"the scorecard does not support approving this design: {reasons}")
    return evaluation


def _input_from(record: DesignReviewRecord) -> DesignReviewInput:
    """The stored review, back as the input it was evaluated from."""
    return DesignReviewInput(
        design_id=str(record.design_attempt_id),
        reviewer_id=record.reviewer,
        hard_gates=[HardGate.of(raw) for raw in record.hard_gates],
        score_categories=[ScoreCategory.of(raw) for raw in record.score_categories],
        decision=ReviewDecision(record.requested_decision),
        rationale=record.rationale,
    )


def empty_review(attempt_id: str, reviewer: str = "") -> DesignReviewInput:
    """A blank review: every gate not tested, no category rated.

    The starting point the attempt screen renders, and the thing a measurement
    then fills part of. Explicit rather than implied, so "not answered" is a
    stored state rather than a missing key.
    """
    return DesignReviewInput(
        design_id=attempt_id,
        reviewer_id=reviewer,
        hard_gates=[
            HardGate(id=gate_id, label=GATE_LABELS[gate_id], result=ReviewResult.NOT_TESTED)
            for gate_id in HARD_GATE_IDS
        ],
        score_categories=[],
    )


def rubric() -> dict[str, Any]:
    """The whole rubric, for a form to render without hardcoding any of it.

    Every label, question, maximum and floor comes from ``design_review``, so a
    change to the scorecard reaches the screen without a second edit.
    """
    from app.domain.design_review import (
        CATEGORY_GROUPS,
        CATEGORY_PROMPTS,
        GATE_GROUPS,
        GATE_QUESTIONS,
        GROUP_BLURBS,
        GROUP_LABELS,
        RATING_MEANINGS,
    )

    return {
        "groups": [
            {"id": group_id, "label": label, "blurb": GROUP_BLURBS[group_id]}
            for group_id, label in GROUP_LABELS.items()
        ],
        "gates": [
            {
                "id": gate_id,
                "label": GATE_LABELS[gate_id],
                "question": GATE_QUESTIONS[gate_id],
                "group": GATE_GROUPS[gate_id],
            }
            for gate_id in HARD_GATE_IDS
        ],
        "categories": [
            {
                "id": category_id,
                "label": label,
                "prompt": CATEGORY_PROMPTS[category_id],
                "maximum": maximum,
                "ratingFloor": rating_floor,
                "minimumRequired": points_floor(category_id),
                "group": CATEGORY_GROUPS[category_id],
            }
            for category_id, (label, maximum, rating_floor) in CATEGORY_LIMITS.items()
        ],
        "ratingMeanings": list(RATING_MEANINGS),
        "approvalPercentage": APPROVAL_PERCENTAGE,
        "productionPercentage": PRODUCTION_PERCENTAGE,
        "bands": [band.value for band in ApprovalBand],
    }
