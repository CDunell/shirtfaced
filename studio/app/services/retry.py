"""Bounded retry for transient provider failures.

Three attempts, exponential backoff with jitter. Authentication, permission and
validation failures are never retried: they will fail identically, and each retry of
an image call may cost money.
"""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass

from app.adapters.image_generation import ImageGenerationError
from app.domain.enums import PERMANENT_FAILURES

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetryPolicy:
    """How many times, and how long to wait between."""

    max_attempts: int = 3
    initial_delay_seconds: float = 1.0
    multiplier: float = 2.0
    max_delay_seconds: float = 20.0
    # Jitter spreads retries so repeated failures do not align.
    jitter: float = 0.25

    def delay_for(self, attempt: int, random_value: float) -> float:
        """Delay before ``attempt`` (1-based), given a random value in [0, 1)."""
        base = min(
            self.initial_delay_seconds * (self.multiplier ** (attempt - 1)),
            self.max_delay_seconds,
        )
        return base * (1.0 - self.jitter + 2.0 * self.jitter * random_value)


DEFAULT_POLICY = RetryPolicy()


def call_with_retry[T](
    operation: Callable[[], T],
    policy: RetryPolicy = DEFAULT_POLICY,
    *,
    sleep: Callable[[float], None] = time.sleep,
    random_value: Callable[[], float] = random.random,
) -> T:
    """Run ``operation``, retrying only transient failures.

    ``sleep`` and ``random_value`` are injectable so tests do not wait and do not
    depend on chance.
    """
    last_error: ImageGenerationError | None = None

    for attempt in range(1, policy.max_attempts + 1):
        try:
            return operation()
        except ImageGenerationError as error:
            last_error = error

            if error.code in PERMANENT_FAILURES:
                logger.info("Not retrying a %s failure.", error.code.value)
                raise
            if attempt == policy.max_attempts:
                break

            delay = policy.delay_for(attempt, random_value())
            logger.info(
                "Attempt %d of %d failed (%s). Retrying in %.1fs.",
                attempt,
                policy.max_attempts,
                error.code.value,
                delay,
            )
            sleep(delay)

    assert last_error is not None
    raise last_error
