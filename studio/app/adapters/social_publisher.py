"""Publisher boundary for Social Studio."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Protocol

from app.config import Settings
from app.db.social_models import PublicationJob, SocialChannel


class PublisherError(RuntimeError):
    """Base delivery failure."""


class PublisherUnavailable(PublisherError):
    """The requested account adapter is not connected yet."""


@dataclass(frozen=True, slots=True)
class PublishResult:
    external_post_id: str
    adapter: str
    receipt: dict[str, object] = field(default_factory=dict)


class SocialPublisher(Protocol):
    def publish(self, job: PublicationJob) -> PublishResult: ...


class FakeSocialPublisher:
    """Deterministic test adapter. Never selected in production by default."""

    def publish(self, job: PublicationJob) -> PublishResult:
        external_id = f"fake:{job.channel.value}:{uuid.UUID(str(job.id))}"
        return PublishResult(
            external_post_id=external_id,
            adapter="fake",
            receipt={"provider": "fake", "job_id": str(job.id)},
        )


class PlatformSocialPublisher:
    """Connection seam for Meta/TikTok account adapters.

    Delivery infrastructure can ship before credentials do without ever recording a
    fake post as live. Account OAuth and platform-specific media handoff plug in here.
    """

    def __init__(self, channel: SocialChannel) -> None:
        self.channel = channel

    def publish(self, job: PublicationJob) -> PublishResult:
        raise PublisherUnavailable(
            f"{self.channel.value} publishing is not connected. Connect the platform account first."
        )


def publisher_for(settings: Settings, channel: SocialChannel) -> SocialPublisher:
    if not settings.social_publishing_enabled or settings.social_publisher_mode == "disabled":
        raise PublisherUnavailable(
            "Social publishing is disabled until a platform account is connected."
        )
    if settings.social_publisher_mode == "fake":
        return FakeSocialPublisher()
    return PlatformSocialPublisher(channel)
