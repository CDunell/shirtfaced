"""Publisher boundary for Social Studio.

Domain state never depends on Meta/TikTok response shapes. Real channel adapters can
replace the fake without changing publication jobs or the Social Studio interface.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.db.social_models import PublicationJob


@dataclass(frozen=True, slots=True)
class PublishResult:
    """The small domain result every platform adapter must return."""

    external_post_id: str


class SocialPublisher(Protocol):
    """One publication adapter contract."""

    def publish(self, job: PublicationJob) -> PublishResult:
        """Publish the exact derivative attached to ``job``."""
        ...


class FakeSocialPublisher:
    """Deterministic publisher used until real platform adapters are connected."""

    def publish(self, job: PublicationJob) -> PublishResult:
        # Stable by job ID, which makes repeated execution naturally idempotent.
        external_id = f"fake:{job.channel.value}:{uuid.UUID(str(job.id))}"
        return PublishResult(external_post_id=external_id)
