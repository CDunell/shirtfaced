"""One row per thing being made, and the one thing to do to it next.

Phase 3 of ``DESIGN_FLOW_PLAN.md``. The plan's governing rule is that at every
point there is exactly one obvious next action, and that following the chain
requires no knowledge of which screen owns what. Phase 1 made each screen state
its own next action; this makes the *set* of them answerable in one place, so
the question "what should I be doing" has an answer that is not "open six
screens and work it out".

**Derived, never stored.** A ``ProductionItem`` is assembled from rows that
already exist -- the concept, its attempts, their reviews, the approved version.
There is no `production_items` table and there should not be one: a stored copy
of a derived state is a copy that drifts, and the drift is silent. The cost is a
query per screen load; the benefit is that this can never disagree with the
tables it describes.

That also means Phase 3 ships **without a migration**, which matters while a
second session is working the same alembic chain.

**Ordering is the product.** A list is only useful if the top of it is the right
place to start, so items sort by how much they are waiting on a person, then by
how far along they are, then by the concept's own priority. A concept nobody has
touched sorts below an attempt that has been waiting for a decision, because the
untouched one is not blocked -- it is merely unstarted.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.concept_models import DesignAttempt, DesignConcept
from app.domain.design_review import ReviewEvaluation
from app.domain.enums import ConceptStatus, DesignAttemptState
from app.services.design_scoring import evaluate_review, stored_input
from app.services.next_action import next_action

__all__ = ["ProductionItem", "work_queue"]


# What each stage means for ordering. Lower sorts first. The numbers are gaps of
# ten so a stage can be inserted later without renumbering the rest.
_URGENCY: dict[str, int] = {
    "awaiting_decision": 10,  # blocked on a person, and they are the person
    "review_open": 20,  # artwork in, scorecard part-answered
    "needs_artwork": 30,  # brief ready, nothing brought back yet
    "needs_brief": 35,  # an idea with no product decided around it yet
    "approved_unversioned": 40,  # decided, not yet frozen as a version
    "ready_to_print": 50,  # a version exists
    "unstarted": 60,  # in the backlog, never attempted
    "settled": 70,  # rejected, superseded, or otherwise finished with
}


@dataclass(frozen=True)
class ProductionItem:
    """One concept, its live attempt, and what to do next."""

    concept_id: uuid.UUID
    library: str
    external_number: int
    title: str
    concept_status: str
    # Where the idea came from, when it came from research rather than Markdown.
    research_run_id: str
    research_concept_number: int | None
    # The constitution's steps 2 and 4, and whether artwork may begin.
    collection_role: str | None
    graphic_archetype: str | None
    brief_ready: bool

    attempt_id: uuid.UUID | None
    attempt_number: int | None
    attempt_state: str | None
    has_artwork: bool

    percentage: float | None
    eligible: bool
    blockers: list[str]

    approved_version: int | None
    approved_design_id: uuid.UUID | None

    stage: str
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "concept_id": str(self.concept_id),
            "library": self.library,
            "external_number": self.external_number,
            "title": self.title,
            "concept_status": self.concept_status,
            "research_run_id": self.research_run_id,
            "research_concept_number": self.research_concept_number,
            "collection_role": self.collection_role,
            "graphic_archetype": self.graphic_archetype,
            "brief_ready": self.brief_ready,
            "attempt_id": None if self.attempt_id is None else str(self.attempt_id),
            "attempt_number": self.attempt_number,
            "attempt_state": self.attempt_state,
            "has_artwork": self.has_artwork,
            "percentage": self.percentage,
            "eligible": self.eligible,
            "blockers": list(self.blockers),
            "approved_version": self.approved_version,
            "approved_design_id": (
                None if self.approved_design_id is None else str(self.approved_design_id)
            ),
            "stage": self.stage,
            "next_action": self.next_action,
        }


def work_queue(session: Session, *, include_settled: bool = False) -> list[ProductionItem]:
    """Everything in flight, most-blocked first.

    One query with its relationships loaded, rather than a query per concept:
    the backlog is 260 rows today and the screen is opened constantly.
    """
    concepts = (
        session.execute(
            select(DesignConcept).options(
                selectinload(DesignConcept.attempts).selectinload(DesignAttempt.assets),
                selectinload(DesignConcept.attempts).selectinload(DesignAttempt.decision),
                selectinload(DesignConcept.attempts).selectinload(DesignAttempt.review),
                selectinload(DesignConcept.attempts).selectinload(DesignAttempt.approved_design),
                selectinload(DesignConcept.approved_versions),
                selectinload(DesignConcept.brief),
            )
        )
        .scalars()
        .all()
    )

    items = [_item(concept) for concept in concepts]
    if not include_settled:
        items = [item for item in items if item.stage != "settled"]

    return sorted(
        items,
        key=lambda item: (
            _URGENCY.get(item.stage, 99),
            # Within a stage, the furthest along first: an attempt at 80/100 is
            # closer to done than one at 20, and finishing beats starting.
            -(item.percentage or 0),
            item.external_number,
        ),
    )


def _item(concept: DesignConcept) -> ProductionItem:
    attempt = _live_attempt(concept)
    evaluation = _evaluation(attempt)
    version = _standing_version(concept)

    return ProductionItem(
        concept_id=concept.id,
        library=concept.library.value,
        external_number=concept.external_number,
        title=concept.title,
        concept_status=concept.status.value,
        research_run_id=str(concept.parsed_json.get("vintage_research_run_id") or ""),
        research_concept_number=_int_or_none(concept.parsed_json.get("research_concept_number")),
        collection_role=(
            None
            if concept.brief is None or concept.brief.collection_role is None
            else concept.brief.collection_role.value
        ),
        graphic_archetype=(
            None
            if concept.brief is None or concept.brief.graphic_archetype is None
            else concept.brief.graphic_archetype.value
        ),
        brief_ready=bool(concept.brief is not None and concept.brief.ready_for_artwork),
        attempt_id=None if attempt is None else attempt.id,
        attempt_number=None if attempt is None else attempt.attempt_number,
        attempt_state=None if attempt is None else attempt.state.value,
        has_artwork=bool(attempt is not None and attempt.assets),
        percentage=None if evaluation is None else round(evaluation.percentage, 1),
        eligible=bool(evaluation is not None and evaluation.eligible_for_design_approval),
        blockers=[] if evaluation is None else list(evaluation.blockers),
        approved_version=None if version is None else version.version,
        approved_design_id=None if version is None else version.id,
        stage=_stage(concept, attempt, version),
        next_action=_next_action(concept, attempt, evaluation),
    )


def _live_attempt(concept: DesignConcept) -> DesignAttempt | None:
    """The attempt the work is actually on: the highest-numbered one.

    Not the highest-numbered *undecided* one. A concept whose latest attempt was
    rejected is not still working on the attempt before it -- it is waiting for
    somebody to start another, and the sentence should say so.
    """
    if not concept.attempts:
        return None
    return max(concept.attempts, key=lambda attempt: attempt.attempt_number)


def _standing_version(concept: DesignConcept) -> Any | None:
    """The current approved version, ignoring superseded ones."""
    standing = [version for version in concept.approved_versions if version.superseded_at is None]
    if not standing:
        return None
    return max(standing, key=lambda version: version.version)


def _evaluation(attempt: DesignAttempt | None) -> ReviewEvaluation | None:
    """The attempt's verdict, or ``None`` when nobody has started a review.

    Read off the loaded relationship rather than queried, because this runs once
    per concept and a query each would make the screen quadratic in the backlog.
    """
    if attempt is None or attempt.review is None:
        return None
    return evaluate_review(stored_input(attempt.review))


def _stage(concept: DesignConcept, attempt: DesignAttempt | None, version: Any | None) -> str:
    if version is not None:
        return "ready_to_print"
    if attempt is None:
        if concept.status not in (ConceptStatus.BACKLOG, ConceptStatus.READY):
            return "settled"
        # An idea with no product decided around it cannot open an attempt at
        # all, so telling somebody to start one would send them into a refusal.
        ready = concept.brief is not None and concept.brief.ready_for_artwork
        return "unstarted" if ready else "needs_brief"

    state = attempt.state
    if state is DesignAttemptState.AWAITING_DECISION:
        return "awaiting_decision"
    if state is DesignAttemptState.APPROVED:
        return "approved_unversioned"
    if state in (DesignAttemptState.PLANNED, DesignAttemptState.GENERATING):
        return "needs_artwork"
    if state is DesignAttemptState.GENERATED:
        return "needs_artwork" if not attempt.assets else "review_open"
    # rejected, variation_requested, failed
    return "settled"


def _next_action(
    concept: DesignConcept,
    attempt: DesignAttempt | None,
    evaluation: ReviewEvaluation | None,
) -> str:
    """The sentence, from the one place that phrases them.

    Concepts with no attempt are the only case ``next_action`` cannot answer,
    because it takes an attempt. Everything else defers, so Work and the attempt
    screen cannot disagree about the same row.
    """
    if attempt is None:
        if concept.status not in (ConceptStatus.BACKLOG, ConceptStatus.READY):
            return f"Nothing is outstanding: this concept is {concept.status.value}."
        brief = concept.brief
        if brief is None or not brief.ready_for_artwork:
            missing = []
            if brief is None or brief.collection_role is None:
                missing.append("its role in the range")
            if brief is None or brief.graphic_archetype is None:
                missing.append("its graphic archetype")
            return (
                f"Write the brief: choose {' and '.join(missing)}. The constitution "
                "decides what a product is before any artwork exists, and the advisor "
                "recommends from the corpus as you choose."
            )
        return (
            "The product is defined. Start an attempt, and the brief goes with it "
            "as the thing the artwork is made against."
        )
    return next_action(attempt, evaluation)


def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) else None
