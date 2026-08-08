"""Persistent Social Studio review, scheduling and fake publishing."""

from __future__ import annotations

import datetime as dt
import json
import uuid
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.adapters.asset_store import AssetStoreError, FilesystemAssetStore
from app.adapters.social_publisher import FakeSocialPublisher, SocialPublisher
from app.config import Settings, get_settings
from app.db.models import Photo
from app.db.session import get_db_session
from app.db.social_models import (
    CadencePolicy,
    PublicationJob,
    PublicationState,
    SocialChannel,
    SocialDerivative,
    SocialPost,
    SocialPostState,
)

router = APIRouter(prefix="/api/social", tags=["social"])
SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]

DEFAULT_PUBLISHER: SocialPublisher = FakeSocialPublisher()

OUTPUT_CHANNELS: dict[str, SocialChannel] = {
    "instagram_feed": SocialChannel.INSTAGRAM_FEED,
    "instagram_story": SocialChannel.INSTAGRAM_STORY,
    "reel_cover": SocialChannel.INSTAGRAM_REEL,
    "tiktok_cover": SocialChannel.TIKTOK,
}


class DerivativeInput(BaseModel):
    output_key: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    filename: str


class DerivativeView(BaseModel):
    id: uuid.UUID
    output_key: str
    channel: str
    width: int
    height: int
    filename: str
    sha256: str
    byte_size: int
    url: str


class JobView(BaseModel):
    id: uuid.UUID
    social_post_id: uuid.UUID
    derivative_id: uuid.UUID
    channel: str
    state: str
    scheduled_at: dt.datetime | None
    scheduled_timezone: str
    recommended_at: dt.datetime | None
    locked: bool
    external_post_id: str | None
    published_at: dt.datetime | None
    failure_reason: str | None
    retry_count: int


class PostView(BaseModel):
    id: uuid.UUID
    source_photo_id: uuid.UUID
    source_label: str
    theme: str
    branding: str
    caption: str
    campaign_id: uuid.UUID | None
    state: str
    approved_at: dt.datetime | None
    rejected_at: dt.datetime | None
    created_at: dt.datetime
    derivatives: list[DerivativeView]
    jobs: list[JobView]


class RejectInput(BaseModel):
    reason: str = ""


class QueueInput(BaseModel):
    timezone: str = "Australia/Brisbane"
    scheduled_at: dt.datetime | None = None


class ScheduleInput(BaseModel):
    scheduled_at: dt.datetime
    timezone: str = "Australia/Brisbane"


def _job_view(job: PublicationJob) -> JobView:
    return JobView(
        id=job.id,
        social_post_id=job.social_post_id,
        derivative_id=job.derivative_id,
        channel=job.channel.value,
        state=job.state.value,
        scheduled_at=job.scheduled_at,
        scheduled_timezone=job.scheduled_timezone,
        recommended_at=job.recommended_at,
        locked=job.locked,
        external_post_id=job.external_post_id,
        published_at=job.published_at,
        failure_reason=job.failure_reason,
        retry_count=job.retry_count,
    )


def _post_view(post: SocialPost, session: Session) -> PostView:
    photo = session.get(Photo, post.source_photo_id)
    return PostView(
        id=post.id,
        source_photo_id=post.source_photo_id,
        source_label=photo.label if photo else "Missing source",
        theme=post.theme,
        branding=post.branding,
        caption=post.caption,
        campaign_id=post.campaign_id,
        state=post.state.value,
        approved_at=post.approved_at,
        rejected_at=post.rejected_at,
        created_at=post.created_at,
        derivatives=[
            DerivativeView(
                id=item.id,
                output_key=item.output_key,
                channel=item.channel.value,
                width=item.width,
                height=item.height,
                filename=item.filename,
                sha256=item.sha256,
                byte_size=item.byte_size,
                url=f"/api/social/derivatives/{item.id}/file",
            )
            for item in post.derivatives
        ],
        jobs=[_job_view(item) for item in post.jobs],
    )


def _load_post(post_id: uuid.UUID, session: Session) -> SocialPost:
    post = session.execute(
        select(SocialPost)
        .options(selectinload(SocialPost.derivatives), selectinload(SocialPost.jobs))
        .where(SocialPost.id == post_id)
    ).scalar_one_or_none()
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such social post.")
    return post


def _default_policy(session: Session) -> CadencePolicy:
    policy = (
        session.execute(
            select(CadencePolicy)
            .where(CadencePolicy.active.is_(True))
            .order_by(CadencePolicy.created_at)
        )
        .scalars()
        .first()
    )
    if policy is None:
        policy = CadencePolicy(
            name="Default social cadence",
            minimum_spacing_minutes=1440,
            preferred_hour_local=19,
            active=True,
        )
        session.add(policy)
        session.flush()
    return policy


def _recommended_time(session: Session, policy: CadencePolicy, timezone: str) -> dt.datetime:
    try:
        zone = ZoneInfo(timezone)
    except Exception as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown timezone.") from error

    now = dt.datetime.now(dt.UTC)
    latest = session.execute(
        select(PublicationJob.scheduled_at)
        .where(PublicationJob.scheduled_at.is_not(None))
        .where(PublicationJob.state.not_in([PublicationState.CANCELLED, PublicationState.FAILED]))
        .order_by(desc(PublicationJob.scheduled_at))
        .limit(1)
    ).scalar_one_or_none()
    spacing = dt.timedelta(minutes=policy.minimum_spacing_minutes)
    floor = max(now, (latest + spacing) if latest else now)
    local = floor.astimezone(zone)
    candidate = local.replace(hour=policy.preferred_hour_local, minute=0, second=0, microsecond=0)
    if candidate < local:
        candidate += dt.timedelta(days=1)
    return candidate.astimezone(dt.UTC)


@router.post("/posts", response_model=PostView, status_code=status.HTTP_201_CREATED)
async def create_post(
    session: SessionDependency,
    settings: SettingsDependency,
    source_photo_id: Annotated[uuid.UUID, Form()],
    theme: Annotated[str, Form()],
    branding: Annotated[str, Form()],
    derivative_metadata: Annotated[str, Form()],
    files: Annotated[list[UploadFile], File()],
    caption: Annotated[str, Form()] = "",
) -> PostView:
    """Persist the exact files made by GO as one review package."""
    photo = session.get(Photo, source_photo_id)
    if photo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such source photo.")

    try:
        metadata = [
            DerivativeInput.model_validate(item) for item in json.loads(derivative_metadata)
        ]
    except (ValueError, TypeError) as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid derivative metadata."
        ) from error
    if len(metadata) != len(files) or not metadata:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Derivative metadata must match the uploaded files.",
        )

    post = SocialPost(
        source_photo_id=source_photo_id,
        theme=theme,
        branding=branding,
        caption=caption,
        state=SocialPostState.REVIEW_REQUIRED,
    )
    session.add(post)
    session.flush()
    store = FilesystemAssetStore(settings.assets_root_resolved)

    for index, (meta, upload) in enumerate(zip(metadata, files, strict=True)):
        channel = OUTPUT_CHANNELS.get(meta.output_key)
        if channel is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown social output.")
        data = await upload.read()
        if not data:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "A derivative is empty.")
        mime_type = upload.content_type or "image/jpeg"
        key = f"social/{post.id}/{index:02d}-{meta.output_key}.jpg"
        try:
            stored = store.save(key, data, mime_type)
        except AssetStoreError as error:
            session.rollback()
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
        session.add(
            SocialDerivative(
                social_post_id=post.id,
                output_key=meta.output_key,
                channel=channel,
                relative_path=stored.key,
                mime_type=stored.mime_type,
                width=meta.width,
                height=meta.height,
                sha256=stored.sha256,
                byte_size=stored.byte_size,
                filename=meta.filename,
            )
        )

    session.commit()
    return _post_view(_load_post(post.id, session), session)


@router.get("/posts", response_model=list[PostView])
def list_posts(session: SessionDependency, state: SocialPostState | None = None) -> list[PostView]:
    query = select(SocialPost).options(
        selectinload(SocialPost.derivatives), selectinload(SocialPost.jobs)
    )
    if state is not None:
        query = query.where(SocialPost.state == state)
    posts = session.execute(query.order_by(desc(SocialPost.created_at))).scalars().all()
    return [_post_view(post, session) for post in posts]


@router.post("/posts/{post_id}/approve", response_model=PostView)
def approve_post(post_id: uuid.UUID, session: SessionDependency) -> PostView:
    post = _load_post(post_id, session)
    if post.state == SocialPostState.REJECTED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Rejected packages cannot be approved.")
    post.state = SocialPostState.APPROVED
    post.approved_at = dt.datetime.now(dt.UTC)
    session.commit()
    return _post_view(_load_post(post_id, session), session)


@router.post("/posts/{post_id}/reject", response_model=PostView)
def reject_post(post_id: uuid.UUID, body: RejectInput, session: SessionDependency) -> PostView:
    del body  # reserved for the durable approval-decision ledger in the next domain phase
    post = _load_post(post_id, session)
    if post.jobs:
        raise HTTPException(status.HTTP_409_CONFLICT, "Queued packages cannot be rejected.")
    post.state = SocialPostState.REJECTED
    post.rejected_at = dt.datetime.now(dt.UTC)
    session.commit()
    return _post_view(_load_post(post_id, session), session)


@router.post("/posts/{post_id}/queue", response_model=list[JobView])
def queue_post(post_id: uuid.UUID, body: QueueInput, session: SessionDependency) -> list[JobView]:
    post = _load_post(post_id, session)
    if post.state not in {SocialPostState.APPROVED, SocialPostState.QUEUED}:
        raise HTTPException(status.HTTP_409_CONFLICT, "Approve the post before queueing it.")

    policy = _default_policy(session)
    recommended = _recommended_time(session, policy, body.timezone)
    scheduled = body.scheduled_at or recommended
    locked = body.scheduled_at is not None
    existing = {
        job.derivative_id: job for job in post.jobs if job.state != PublicationState.CANCELLED
    }

    for derivative in post.derivatives:
        if derivative.id in existing:
            continue
        session.add(
            PublicationJob(
                social_post_id=post.id,
                derivative_id=derivative.id,
                channel=derivative.channel,
                scheduled_at=scheduled,
                scheduled_timezone=body.timezone,
                recommended_at=recommended,
                cadence_policy_id=policy.id,
                locked=locked,
                state=PublicationState.SCHEDULED,
            )
        )
    post.state = SocialPostState.QUEUED
    session.commit()
    post = _load_post(post.id, session)
    return [_job_view(job) for job in post.jobs]


@router.get("/queue", response_model=list[JobView])
def list_queue(session: SessionDependency) -> list[JobView]:
    jobs = (
        session.execute(
            select(PublicationJob)
            .where(
                PublicationJob.state.in_(
                    [
                        PublicationState.QUEUED,
                        PublicationState.SCHEDULED,
                        PublicationState.HELD,
                        PublicationState.FAILED,
                    ]
                )
            )
            .order_by(PublicationJob.scheduled_at, PublicationJob.created_at)
        )
        .scalars()
        .all()
    )
    return [_job_view(job) for job in jobs]


@router.get("/live", response_model=list[JobView])
def list_live(session: SessionDependency) -> list[JobView]:
    jobs = (
        session.execute(
            select(PublicationJob)
            .where(PublicationJob.state == PublicationState.PUBLISHED)
            .order_by(desc(PublicationJob.published_at))
        )
        .scalars()
        .all()
    )
    return [_job_view(job) for job in jobs]


@router.post("/jobs/{job_id}/schedule", response_model=JobView)
def schedule_job(job_id: uuid.UUID, body: ScheduleInput, session: SessionDependency) -> JobView:
    job = session.get(PublicationJob, job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such publication job.")
    if job.state in {PublicationState.PUBLISHED, PublicationState.CANCELLED}:
        raise HTTPException(status.HTTP_409_CONFLICT, "That job can no longer be rescheduled.")
    try:
        ZoneInfo(body.timezone)
    except Exception as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Unknown timezone.") from error
    job.scheduled_at = body.scheduled_at
    job.scheduled_timezone = body.timezone
    job.locked = True
    job.state = PublicationState.SCHEDULED
    session.commit()
    return _job_view(job)


@router.post("/jobs/{job_id}/hold", response_model=JobView)
def hold_job(job_id: uuid.UUID, session: SessionDependency) -> JobView:
    job = session.get(PublicationJob, job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such publication job.")
    if job.state == PublicationState.PUBLISHED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Published jobs cannot be held.")
    job.state = PublicationState.HELD
    job.locked = True
    session.commit()
    return _job_view(job)


@router.post("/jobs/{job_id}/cancel", response_model=JobView)
def cancel_job(job_id: uuid.UUID, session: SessionDependency) -> JobView:
    job = session.get(PublicationJob, job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such publication job.")
    if job.state == PublicationState.PUBLISHED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Published jobs cannot be cancelled.")
    job.state = PublicationState.CANCELLED
    job.locked = True
    session.commit()
    return _job_view(job)


def _publish_job(
    job: PublicationJob, session: Session, publisher: SocialPublisher = DEFAULT_PUBLISHER
) -> JobView:
    """Execute one approved job through a replaceable platform adapter."""
    if job.state == PublicationState.CANCELLED:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cancelled jobs cannot publish.")
    if job.state == PublicationState.PUBLISHED:
        return _job_view(job)
    post = _load_post(job.social_post_id, session)
    if post.approved_at is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "The social package is not approved.")
    job.state = PublicationState.PUBLISHING
    session.flush()
    try:
        result = publisher.publish(job)
    except Exception as error:
        job.state = PublicationState.FAILED
        job.failure_reason = str(error)
        job.retry_count += 1
        session.commit()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Publisher failed.") from error
    job.external_post_id = result.external_post_id
    job.published_at = dt.datetime.now(dt.UTC)
    job.failure_reason = None
    job.state = PublicationState.PUBLISHED
    remaining = [
        item
        for item in post.jobs
        if item.id != job.id
        and item.state not in {PublicationState.PUBLISHED, PublicationState.CANCELLED}
    ]
    if not remaining:
        post.state = SocialPostState.LIVE
    session.commit()
    return _job_view(job)


@router.post("/jobs/{job_id}/publish-now", response_model=JobView)
def fake_publish_now(job_id: uuid.UUID, session: SessionDependency) -> JobView:
    """Execute one job through the configured publisher; safe to call twice."""
    job = session.get(PublicationJob, job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such publication job.")
    return _publish_job(job, session)


@router.post("/queue/run-due", response_model=list[JobView])
def run_due_jobs(session: SessionDependency) -> list[JobView]:
    """Execution hook for cron/worker infrastructure; publish all due unlocked jobs."""
    now = dt.datetime.now(dt.UTC)
    jobs = (
        session.execute(
            select(PublicationJob)
            .where(PublicationJob.state == PublicationState.SCHEDULED)
            .where(PublicationJob.scheduled_at.is_not(None))
            .where(PublicationJob.scheduled_at <= now)
            .order_by(PublicationJob.scheduled_at, PublicationJob.created_at)
        )
        .scalars()
        .all()
    )
    return [_publish_job(job, session) for job in jobs]


@router.get("/derivatives/{derivative_id}/file")
def get_derivative(
    derivative_id: uuid.UUID, session: SessionDependency, settings: SettingsDependency
) -> Response:
    derivative = session.get(SocialDerivative, derivative_id)
    if derivative is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such social derivative.")
    store = FilesystemAssetStore(settings.assets_root_resolved)
    try:
        data = store.load(derivative.relative_path)
    except AssetStoreError as error:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    return Response(
        content=data,
        media_type=derivative.mime_type,
        headers={"Cache-Control": "private, max-age=31536000, immutable"},
    )
