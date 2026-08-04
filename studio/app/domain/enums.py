"""Enumerations shared by the domain and the database."""

from __future__ import annotations

from enum import StrEnum


class WorldStatus(StrEnum):
    """Lifecycle of a world.

    Version 1 runs a single active world. ``archived`` exists so a finished world can
    be retained for its history without appearing as a production target.
    """

    ACTIVE = "active"
    ARCHIVED = "archived"


class AttemptState(StrEnum):
    """Lifecycle of one generation attempt, per the architecture document.

    Phase 3 carries an attempt as far as ``GENERATED``. Review moves it through
    ``REVIEWING`` to ``AWAITING_DECISION``; the human decision settles it at
    ``APPROVED`` or ``REJECTED``.
    """

    PLANNED = "planned"
    PROMPT_READY = "prompt_ready"
    GENERATING = "generating"
    GENERATED = "generated"
    REVIEWING = "reviewing"
    AWAITING_DECISION = "awaiting_decision"
    APPROVED = "approved"
    REJECTED = "rejected"
    # Terminal, and deliberately not "rejected": the owner asked for another take,
    # which is not the same as saying the image was wrong. Recording it as a rejection
    # would pollute rejected-drift learning, which is the planner's strongest input.
    VARIATION_REQUESTED = "variation_requested"
    FAILED = "failed"


# An attempt in one of these states occupies the world: a partial unique index
# permits only one at a time, so a second Continue World is refused with 409 rather
# than quietly starting a parallel generation.
ACTIVE_ATTEMPT_STATES: frozenset[AttemptState] = frozenset(
    {
        AttemptState.PLANNED,
        AttemptState.PROMPT_READY,
        AttemptState.GENERATING,
        AttemptState.GENERATED,
        AttemptState.REVIEWING,
        AttemptState.AWAITING_DECISION,
    }
)


class HumanDecisionKind(StrEnum):
    """What the owner decided. Final, and never inferred from a review."""

    APPROVED = "approved"
    REJECTED = "rejected"
    VARIATION_REQUESTED = "variation_requested"


# The attempt state each decision moves the attempt to. All three are terminal and
# outside the active set, so the world is released either way.
DECISION_ATTEMPT_STATES: dict[HumanDecisionKind, AttemptState] = {
    HumanDecisionKind.APPROVED: AttemptState.APPROVED,
    HumanDecisionKind.REJECTED: AttemptState.REJECTED,
    HumanDecisionKind.VARIATION_REQUESTED: AttemptState.VARIATION_REQUESTED,
}


class SyncState(StrEnum):
    """Whether a downstream system caught up with the decision.

    The database, the filesystem and Git cannot share a transaction, so each is
    reported separately rather than collapsed into one success flag.
    """

    NOT_ATTEMPTED = "not_attempted"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class AuditEventType(StrEnum):
    """Append-only record of what happened."""

    DECISION_RECORDED = "decision_recorded"
    MARKDOWN_UPDATED = "markdown_updated"
    MARKDOWN_FAILED = "markdown_failed"
    WORLD_REIMPORTED = "world_reimported"
    IMPORT_FAILED = "import_failed"
    GIT_COMMITTED = "git_committed"
    GIT_FAILED = "git_failed"
    REFERENCE_PROMOTED = "reference_promoted"
    REFERENCE_FAILED = "reference_failed"
    REFERENCE_ARCHIVED = "reference_archived"
    REFERENCE_PINNED = "reference_pinned"
    RECONCILIATION_REQUIRED = "reconciliation_required"


class ReviewRecommendation(StrEnum):
    """What the review model advises.

    A recommendation, never a decision. The owner records the outcome separately in
    the human decision, using the canon's own vocabulary.
    """

    APPROVE = "APPROVE_RECOMMENDED"
    APPROVE_WITH_NOTE = "APPROVE_WITH_NOTE_RECOMMENDED"
    REJECT = "REJECT_RECOMMENDED"
    UNCERTAIN = "REVIEW_UNCERTAIN"


class ReviewVerdict(StrEnum):
    """The verdict vocabulary used by the product specification and data model.

    Derived from the recommendation, so both the gate-based review contract and the
    original three-value verdict are satisfied without inventing anything.
    """

    APPROVED = "approved"
    APPROVED_WITH_NOTE = "approved_with_note"
    REJECTED = "rejected"
    UNCERTAIN = "uncertain"


RECOMMENDATION_VERDICTS: dict[ReviewRecommendation, ReviewVerdict] = {
    ReviewRecommendation.APPROVE: ReviewVerdict.APPROVED,
    ReviewRecommendation.APPROVE_WITH_NOTE: ReviewVerdict.APPROVED_WITH_NOTE,
    ReviewRecommendation.REJECT: ReviewVerdict.REJECTED,
    ReviewRecommendation.UNCERTAIN: ReviewVerdict.UNCERTAIN,
}


class GateStatus(StrEnum):
    """The outcome of one review gate."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class GateName(StrEnum):
    """The nine gates, named after the Continuity Director's tests in WORLD.md."""

    MOOD = "mood"
    AUSTRALIAN_AUTHENTICITY = "australian_authenticity"
    PRODUCT_VISIBILITY = "product_visibility"
    THIRD_PARTY_BRANDING = "third_party_branding"
    VEHICLE_CONTINUITY = "vehicle_continuity"
    WARDROBE_BALANCE = "wardrobe_balance"
    COMPOSITION = "composition"
    DOCUMENTARY_CREDIBILITY = "documentary_credibility"
    STORY = "story"


class ProposalClassification(StrEnum):
    """How a proposed rule relates to canon that already exists.

    Advisory only. It orders the queue and explains the recommendation; the owner
    decides. The two live rulings on 5 August 2026 both went against what a naive
    reading would have said, which is why this never decides anything.
    """

    ALREADY_COVERED = "already_covered"
    GENUINE_ADDITION = "genuine_addition"
    REFINEMENT = "refinement"
    CONTRADICTION = "contradiction"
    TOO_SPECIFIC = "too_specific"


# Classifications that do not warrant a canon change on their own. Approval is still
# the owner's to give; these simply sort to the bottom of the queue.
NON_ADDITIVE_CLASSIFICATIONS: frozenset[ProposalClassification] = frozenset(
    {
        ProposalClassification.ALREADY_COVERED,
        ProposalClassification.TOO_SPECIFIC,
        ProposalClassification.CONTRADICTION,
    }
)


class CanonProposalStatus(StrEnum):
    """Lifecycle of a proposed permanent rule.

    A proposal never changes WORLD.md. Only an explicit human approval can, and that
    arrives with the canon proposal phase.
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"


class ReferenceState(StrEnum):
    """Where a reference frame sits in the library.

    Only ``ACTIVE`` and ``PINNED`` reach the planner. The rest is history: nothing is
    deleted, because an approved frame is a record of a decision as well as an input.
    """

    ACTIVE = "active"
    ARCHIVED = "archived"
    # Exceptional frames. Never aged out automatically.
    PINNED = "pinned"


# The states the planner reads. Pinned frames are always among them.
PLANNING_REFERENCE_STATES: frozenset[ReferenceState] = frozenset(
    {ReferenceState.ACTIVE, ReferenceState.PINNED}
)


class AssetKind(StrEnum):
    """What a stored image is."""

    ORIGINAL = "original"
    THUMBNAIL = "thumbnail"
    REFERENCE = "reference"


class FailureCode(StrEnum):
    """Why an attempt failed.

    Classified rather than free text so failures can be counted, and so retry can
    refuse the ones that will never succeed on their own.
    """

    PLANNING_FAILED = "planning_failed"
    REVIEW_FAILED = "review_failed"
    PROVIDER_ERROR = "provider_error"
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_REFUSED = "provider_refused"
    INVALID_IMAGE = "invalid_image"
    STORAGE_FAILED = "storage_failed"
    CONFIGURATION = "configuration"
    INTERNAL = "internal"


# Retrying these repeats the same failure: the cause is a key, a permission, a
# configuration value or a rule, none of which change by asking again.
PERMANENT_FAILURES: frozenset[FailureCode] = frozenset(
    {
        FailureCode.PROVIDER_REFUSED,
        FailureCode.CONFIGURATION,
    }
)


class ShotStatus(StrEnum):
    """Lifecycle of a planned shot, per the data model."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    ABANDONED = "abandoned"


# Status markers used in SHOTLIST.md. The emoji are the documented form; the text
# spellings keep the file usable in a plain terminal, as the Markdown contract
# requires.
SHOT_STATUS_MARKERS: dict[str, ShotStatus] = {
    "⬜": ShotStatus.PLANNED,
    "🟡": ShotStatus.IN_PROGRESS,
    "✅": ShotStatus.APPROVED,
    "❌": ShotStatus.REJECTED,
    "planned": ShotStatus.PLANNED,
    "in progress": ShotStatus.IN_PROGRESS,
    "in-progress": ShotStatus.IN_PROGRESS,
    "in_progress": ShotStatus.IN_PROGRESS,
    "approved": ShotStatus.APPROVED,
    "rejected": ShotStatus.REJECTED,
    "abandoned": ShotStatus.ABANDONED,
}


def parse_shot_status(value: str) -> ShotStatus | None:
    """Resolve a shotlist status cell, or ``None`` when it is not recognised."""
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned in SHOT_STATUS_MARKERS:
        return SHOT_STATUS_MARKERS[cleaned]
    return SHOT_STATUS_MARKERS.get(cleaned.casefold())
