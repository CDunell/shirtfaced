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
