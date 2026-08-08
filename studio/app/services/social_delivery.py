"""One execution path for scheduled and immediate social publication."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.adapters.social_publisher import PublisherError, SocialPublisher, publisher_for
from app.config import Settings
from app.db.social_models import PublicationJob, PublicationState, SocialPostState


def _retry_at(now: dt.datetime, retry_count: int, base_seconds: int) -> dt.datetime:
    delay = min(base_seconds * (2 ** max(retry_count - 1, 0)), 6 * 60 * 60)
    return now + dt.timedelta(seconds=delay)


def execute_publication_job(
    session: Session,
    job: PublicationJob,
    settings: Settings,
    *,
    publisher: SocialPublisher | None = None,
) -> PublicationJob:
    """Publish once, recording the attempt, receipt and deterministic retry state."""
    if job.state == PublicationState.PUBLISHED:
        return job
    if job.state in {PublicationState.CANCELLED, PublicationState.HELD}:
        raise PublisherError(f"{job.state.value} jobs cannot publish.")
    if job.derivative.review_state != "approved" or job.post.approved_at is None:
        raise PublisherError("The social output is not approved.")

    now = dt.datetime.now(dt.UTC)
    job.state = PublicationState.PUBLISHING
    job.last_attempt_at = now
    job.retry_count += 1
    job.max_attempts = max(job.max_attempts or settings.social_max_attempts, 1)
    session.flush()

    try:
        selected = publisher or publisher_for(settings, job.channel)
        result = selected.publish(job)
    except Exception as error:
        job.failure_reason = str(error)
        job.adapter = type(publisher).__name__ if publisher is not None else None
        if job.retry_count >= job.max_attempts:
            job.state = PublicationState.FAILED
            job.next_attempt_at = None
        else:
            job.state = PublicationState.SCHEDULED
            job.next_attempt_at = _retry_at(
                now, job.retry_count, settings.social_retry_base_seconds
            )
        session.commit()
        raise

    job.external_post_id = result.external_post_id
    job.adapter = result.adapter
    job.publish_receipt = result.receipt
    job.published_at = now
    job.failure_reason = None
    job.next_attempt_at = None
    job.state = PublicationState.PUBLISHED

    remaining = [
        item
        for item in job.post.jobs
        if item.id != job.id
        and item.state not in {PublicationState.PUBLISHED, PublicationState.CANCELLED}
    ]
    if not remaining:
        job.post.state = SocialPostState.LIVE
    session.commit()
    return job


def run_due_publications(
    session: Session, settings: Settings, *, limit: int = 25
) -> list[PublicationJob]:
    """Claim due jobs in schedule order and run them through the shared executor."""
    if not settings.social_publishing_enabled:
        return []
    now = dt.datetime.now(dt.UTC)
    jobs = (
        session.execute(
            select(PublicationJob)
            .where(PublicationJob.state == PublicationState.SCHEDULED)
            .where(PublicationJob.scheduled_at.is_not(None))
            .where(PublicationJob.scheduled_at <= now)
            .where(
                or_(
                    PublicationJob.next_attempt_at.is_(None),
                    PublicationJob.next_attempt_at <= now,
                )
            )
            .order_by(PublicationJob.scheduled_at, PublicationJob.created_at)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    completed: list[PublicationJob] = []
    for job in jobs:
        try:
            execute_publication_job(session, job, settings)
        except Exception:
            # Failure and retry state are already durable. One bad platform call must
            # not prevent later due jobs from being attempted.
            continue
        completed.append(job)
    return completed
