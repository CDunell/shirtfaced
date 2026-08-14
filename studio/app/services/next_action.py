"""What to do next, in a sentence.

Item 6 of Phase 1: *every screen states its next action in plain sentences, not
inferred from state*. This is where those sentences live, and there is one copy
of each because two screens phrasing the same situation separately is how they
end up disagreeing about it.

The rule the sentences are written to: **name the thing to do, not the state
the row is in.** "Awaiting decision" is a status; "Answer the four gates nobody
has answered, then approve it" is an instruction. A person who has never used
the tool can follow the second and can only guess at the first.

They are computed from rows that already exist rather than stored, so they
cannot drift from what is actually true. Phase 3 lifts this onto a
``ProductionItem`` and shows it as a button; until then it rides on the
responses the attempt screen already fetches.
"""

from __future__ import annotations

from app.db.concept_models import ApprovedDesign, DesignAttempt
from app.domain.design_review import (
    APPROVAL_PERCENTAGE,
    CATEGORY_LIMITS,
    HARD_GATE_IDS,
    ReviewEvaluation,
)
from app.domain.enums import DesignAttemptState

__all__ = ["approved_next_action", "next_action"]


def next_action(attempt: DesignAttempt, evaluation: ReviewEvaluation | None = None) -> str:
    """The one obvious next thing to do with this attempt."""
    state = attempt.state

    if state is DesignAttemptState.FAILED:
        return (
            "This attempt failed and cannot be carried further. Start a new attempt on "
            "the same concept."
        )

    # The "go and make the artwork" sentence belongs to the states before a
    # review, and only to them. Asked in state order rather than by looking at
    # the assets first, because an approved attempt whose file has gone missing
    # should not be told to go and draw it again.
    if state in (
        DesignAttemptState.PLANNED,
        DesignAttemptState.GENERATING,
        DesignAttemptState.GENERATED,
    ):
        if not attempt.assets:
            return (
                "Copy the brief, make the artwork in ChatGPT, Gemini or Claude, then bring "
                "the file back to the drop zone below. Nothing is generated here and nothing "
                "is billed."
            )
        if state is not DesignAttemptState.GENERATED:
            # record_asset lifts an attempt to GENERATED, so artwork without
            # that state means the row was left behind by an older path.
            return "Artwork is attached but the attempt was never marked generated. Re-attach it."
        if evaluation is None or not _started(evaluation):
            return (
                "Artwork attached. Measure it, then answer the thirteen gates and rate "
                "the nine categories."
            )
        if evaluation.eligible_for_design_approval:
            return (
                f"Answered in full and passing at {evaluation.percentage:.0f}/100. "
                "Submit it for a decision."
            )
        return _judgement_sentence(evaluation) + " Then submit it for a decision."

    if state is DesignAttemptState.AWAITING_DECISION:
        if evaluation is None:
            return "Answer the scorecard, then approve this design or send it back."
        if evaluation.eligible_for_design_approval:
            return (
                f"Passed at {evaluation.percentage:.0f}/100 with no failed gates. "
                "Approve it, or send it back with a reason."
            )
        return _judgement_sentence(evaluation) + " Until then it can only be sent back."

    if state is DesignAttemptState.VARIATION_REQUESTED:
        return (
            "A variation was asked for. Start a new attempt on this concept and bring "
            "back the reworked artwork."
        )

    if state is DesignAttemptState.REJECTED:
        return "Rejected. Nothing further happens to this attempt."

    if state is DesignAttemptState.APPROVED:
        if attempt.approved_design is None:
            return (
                "Approved. Record it as a version, choosing the garment, the print zone "
                "and the print width -- Print needs all three."
            )
        return approved_next_action(attempt.approved_design)

    # No fallback sentence: every DesignAttemptState is answered above, and
    # mypy proves it. A default here would be dead code that quietly absorbed
    # any state added later instead of failing the type check -- which is the
    # one moment a new state needs somebody to write its sentence.


def _started(evaluation: ReviewEvaluation) -> bool:
    """Whether anybody -- or any measurement -- has answered anything yet."""
    return len(evaluation.untested_hard_gates) < len(HARD_GATE_IDS) or len(
        evaluation.unrated_categories
    ) < len(CATEGORY_LIMITS)


def _judgement_sentence(evaluation: ReviewEvaluation) -> str:
    """What is still outstanding, counted rather than described.

    Counts rather than a list: thirteen gate names in a sentence is a paragraph
    nobody reads, and the form immediately below shows which ones they are.
    """
    outstanding: list[str] = []
    if evaluation.untested_hard_gates:
        count = len(evaluation.untested_hard_gates)
        outstanding.append(f"{count} gate{'s' if count != 1 else ''}")
    if evaluation.unrated_categories:
        count = len(evaluation.unrated_categories)
        outstanding.append(f"{count} categor{'ies' if count != 1 else 'y'}")

    if outstanding:
        return f"Answer the {' and '.join(outstanding)} still outstanding."

    if evaluation.failed_hard_gates:
        count = len(evaluation.failed_hard_gates)
        return (
            f"{count} gate{'s have' if count != 1 else ' has'} failed. "
            "A failed gate cannot be averaged away by a high score -- the design has to change."
        )

    if evaluation.failed_category_minimums:
        names = ", ".join(category.label for category in evaluation.failed_category_minimums)
        return f"Below the floor on {names}. The design has to change, not the rating."

    # Reached only when every gate passed and every floor was met, so the
    # total is the only thing left that can be short. Callers must check
    # eligibility before asking for this sentence -- a passing review routed
    # here once and was told it scored "below the 75 needed" at 80/100, which
    # contradicted the verdict panel directly above it.
    return (
        f"Scored {evaluation.percentage:.0f}/100, below the "
        f"{APPROVAL_PERCENTAGE:.0f} needed. The design has to change, not the rating."
    )


def approved_next_action(version: ApprovedDesign) -> str:
    """The one obvious next thing to do with an approved version."""
    spec = version.production_spec or {}
    zone = str(spec.get("zone_key") or "")
    garment = str(spec.get("garment_key") or "")
    width = spec.get("print_width_mm")

    if version.superseded_at is not None:
        return f"Superseded. v{version.version} is history; print the current version instead."

    if not (zone and garment and width):
        missing = [
            name
            for name, value in (("garment", garment), ("print zone", zone), ("print width", width))
            if not value
        ]
        return (
            f"Approved as v{version.version}, but Print needs the "
            f"{' and the '.join(missing)} before it can place this. Record them on the version."
        )

    return (
        f"Approved as v{version.version}. Print it at {float(width):.0f}mm in the "
        f"{zone.replace('_', ' ')} zone on {garment.replace('_', ' ')}."
    )
