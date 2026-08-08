from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDIO = ROOT / "studio"


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected block not found in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Settings: delivery is inert until explicitly enabled. Tests opt into fake mode.
config = STUDIO / "app/config.py"
replace(
    config,
    '    # --- Interface --------------------------------------------------------------\n',
    '''    # --- Social publishing ------------------------------------------------------\n    # Scheduled delivery is intentionally inert until an account adapter is connected.\n    social_publishing_enabled: bool = False\n    social_publisher_mode: Literal["disabled", "fake", "platform"] = "disabled"\n    social_max_attempts: int = Field(default=5, ge=1, le=20)\n    social_retry_base_seconds: int = Field(default=60, ge=5, le=86400)\n\n    # --- Interface --------------------------------------------------------------\n''',
)

# Persistence for delivery attempts and receipts.
models = STUDIO / "app/db/social_models.py"
replace(
    models,
    'from sqlalchemy.dialects.postgresql import UUID\n',
    'from sqlalchemy.dialects.postgresql import JSONB, UUID\n',
)
replace(
    models,
    '    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))\n\n    post:',
    '''    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))\n    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("5"))\n    next_attempt_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))\n    last_attempt_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))\n    adapter: Mapped[str | None] = mapped_column(String(120))\n    publish_receipt: Mapped[dict[str, object] | None] = mapped_column(JSONB)\n\n    post:''',
)

migration = STUDIO / "app/db/migrations/versions/0020_social_delivery.py"
migration.write_text('''"""social delivery attempts and receipts\n\nRevision ID: 0020\nRevises: 0019\nCreate Date: 2026-08-09\n"""\n\nfrom __future__ import annotations\n\nfrom collections.abc import Sequence\n\nimport sqlalchemy as sa\nfrom alembic import op\nfrom sqlalchemy.dialects import postgresql\n\nrevision: str = "0020"\ndown_revision: str | None = "0019"\nbranch_labels: str | Sequence[str] | None = None\ndepends_on: str | Sequence[str] | None = None\n\n\ndef upgrade() -> None:\n    op.add_column("publication_jobs", sa.Column("max_attempts", sa.Integer(), server_default="5", nullable=False))\n    op.add_column("publication_jobs", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True))\n    op.add_column("publication_jobs", sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True))\n    op.add_column("publication_jobs", sa.Column("adapter", sa.String(length=120), nullable=True))\n    op.add_column("publication_jobs", sa.Column("publish_receipt", postgresql.JSONB(astext_type=sa.Text()), nullable=True))\n    op.create_index("ix_publication_jobs_retry_due", "publication_jobs", ["state", "next_attempt_at"])\n\n\ndef downgrade() -> None:\n    op.drop_index("ix_publication_jobs_retry_due", table_name="publication_jobs")\n    op.drop_column("publication_jobs", "publish_receipt")\n    op.drop_column("publication_jobs", "adapter")\n    op.drop_column("publication_jobs", "last_attempt_at")\n    op.drop_column("publication_jobs", "next_attempt_at")\n    op.drop_column("publication_jobs", "max_attempts")\n''', encoding="utf-8")

# Replace the fake-only publisher boundary with a production-safe selector.
publisher = STUDIO / "app/adapters/social_publisher.py"
publisher.write_text('''"""Publisher boundary for Social Studio."""\n\nfrom __future__ import annotations\n\nimport uuid\nfrom dataclasses import dataclass, field\nfrom typing import Protocol\n\nfrom app.config import Settings\nfrom app.db.social_models import PublicationJob, SocialChannel\n\n\nclass PublisherError(RuntimeError):\n    """Base delivery failure."""\n\n\nclass PublisherUnavailable(PublisherError):\n    """The requested account adapter is not connected yet."""\n\n\n@dataclass(frozen=True, slots=True)\nclass PublishResult:\n    external_post_id: str\n    adapter: str\n    receipt: dict[str, object] = field(default_factory=dict)\n\n\nclass SocialPublisher(Protocol):\n    def publish(self, job: PublicationJob) -> PublishResult: ...\n\n\nclass FakeSocialPublisher:\n    """Deterministic test adapter. Never selected in production by default."""\n\n    def publish(self, job: PublicationJob) -> PublishResult:\n        external_id = f"fake:{job.channel.value}:{uuid.UUID(str(job.id))}"\n        return PublishResult(\n            external_post_id=external_id,\n            adapter="fake",\n            receipt={"provider": "fake", "job_id": str(job.id)},\n        )\n\n\nclass PlatformSocialPublisher:\n    """Connection seam for Meta/TikTok account adapters.\n\n    Delivery infrastructure can ship before credentials do without ever recording a\n    fake post as live. Account OAuth and platform-specific media handoff plug in here.\n    """\n\n    def __init__(self, channel: SocialChannel) -> None:\n        self.channel = channel\n\n    def publish(self, job: PublicationJob) -> PublishResult:\n        raise PublisherUnavailable(\n            f"{self.channel.value} publishing is not connected. Connect the platform account first."\n        )\n\n\ndef publisher_for(settings: Settings, channel: SocialChannel) -> SocialPublisher:\n    if not settings.social_publishing_enabled or settings.social_publisher_mode == "disabled":\n        raise PublisherUnavailable("Social publishing is disabled until a platform account is connected.")\n    if settings.social_publisher_mode == "fake":\n        return FakeSocialPublisher()\n    return PlatformSocialPublisher(channel)\n''', encoding="utf-8")

service = STUDIO / "app/services/social_delivery.py"
service.write_text('''"""One execution path for scheduled and immediate social publication."""\n\nfrom __future__ import annotations\n\nimport datetime as dt\n\nfrom sqlalchemy import or_, select\nfrom sqlalchemy.orm import Session\n\nfrom app.adapters.social_publisher import PublisherError, SocialPublisher, publisher_for\nfrom app.config import Settings\nfrom app.db.social_models import PublicationJob, PublicationState, SocialPost, SocialPostState\n\n\ndef _retry_at(now: dt.datetime, retry_count: int, base_seconds: int) -> dt.datetime:\n    delay = min(base_seconds * (2 ** max(retry_count - 1, 0)), 6 * 60 * 60)\n    return now + dt.timedelta(seconds=delay)\n\n\ndef execute_publication_job(\n    session: Session,\n    job: PublicationJob,\n    settings: Settings,\n    *,\n    publisher: SocialPublisher | None = None,\n) -> PublicationJob:\n    """Publish once, recording the attempt, receipt and deterministic retry state."""\n    if job.state == PublicationState.PUBLISHED:\n        return job\n    if job.state in {PublicationState.CANCELLED, PublicationState.HELD}:\n        raise PublisherError(f"{job.state.value} jobs cannot publish.")\n    if job.derivative.review_state != "approved" or job.post.approved_at is None:\n        raise PublisherError("The social output is not approved.")\n\n    now = dt.datetime.now(dt.UTC)\n    job.state = PublicationState.PUBLISHING\n    job.last_attempt_at = now\n    job.retry_count += 1\n    job.max_attempts = max(job.max_attempts or settings.social_max_attempts, 1)\n    session.flush()\n\n    try:\n        selected = publisher or publisher_for(settings, job.channel)\n        result = selected.publish(job)\n    except Exception as error:\n        job.failure_reason = str(error)\n        job.adapter = type(publisher).__name__ if publisher is not None else None\n        if job.retry_count >= job.max_attempts:\n            job.state = PublicationState.FAILED\n            job.next_attempt_at = None\n        else:\n            job.state = PublicationState.SCHEDULED\n            job.next_attempt_at = _retry_at(now, job.retry_count, settings.social_retry_base_seconds)\n        session.commit()\n        raise\n\n    job.external_post_id = result.external_post_id\n    job.adapter = result.adapter\n    job.publish_receipt = result.receipt\n    job.published_at = now\n    job.failure_reason = None\n    job.next_attempt_at = None\n    job.state = PublicationState.PUBLISHED\n\n    remaining = [\n        item\n        for item in job.post.jobs\n        if item.id != job.id\n        and item.state not in {PublicationState.PUBLISHED, PublicationState.CANCELLED}\n    ]\n    if not remaining:\n        job.post.state = SocialPostState.LIVE\n    session.commit()\n    return job\n\n\ndef run_due_publications(\n    session: Session, settings: Settings, *, limit: int = 25\n) -> list[PublicationJob]:\n    """Claim due jobs in schedule order and run them through the shared executor."""\n    if not settings.social_publishing_enabled:\n        return []\n    now = dt.datetime.now(dt.UTC)\n    jobs = (\n        session.execute(\n            select(PublicationJob)\n            .where(PublicationJob.state == PublicationState.SCHEDULED)\n            .where(PublicationJob.scheduled_at.is_not(None))\n            .where(PublicationJob.scheduled_at <= now)\n            .where(\n                or_(\n                    PublicationJob.next_attempt_at.is_(None),\n                    PublicationJob.next_attempt_at <= now,\n                )\n            )\n            .order_by(PublicationJob.scheduled_at, PublicationJob.created_at)\n            .with_for_update(skip_locked=True)\n            .limit(limit)\n        )\n        .scalars()\n        .all()\n    )\n    completed: list[PublicationJob] = []\n    for job in jobs:\n        try:\n            execute_publication_job(session, job, settings)\n        except Exception:\n            # Failure and retry state are already durable. One bad platform call must\n            # not prevent later due jobs from being attempted.\n            continue\n        completed.append(job)\n    return completed\n''', encoding="utf-8")

worker = STUDIO / "scripts/run_social_publish_queue.py"
worker.write_text('''"""Run one bounded pass over due social publication jobs."""\n\nfrom __future__ import annotations\n\nfrom app.config import get_settings\nfrom app.db.session import get_session_factory\nfrom app.services.social_delivery import run_due_publications\n\n\ndef main() -> int:\n    settings = get_settings()\n    if not settings.social_publishing_enabled:\n        print("Social publishing disabled; queue left untouched.")\n        return 0\n    with get_session_factory()() as session:\n        jobs = run_due_publications(session, settings)\n        print(f"Published {len(jobs)} due social job(s).")\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n''', encoding="utf-8")

# Route immediate and due execution through the same service.
routes = STUDIO / "app/routes/social.py"
replace(routes, '"""Persistent Social Studio review, scheduling and fake publishing."""', '"""Persistent Social Studio review, scheduling and publication."""')
replace(
    routes,
    'from app.adapters.social_publisher import FakeSocialPublisher, SocialPublisher\n',
    'from app.adapters.social_publisher import PublisherError\n',
)
replace(
    routes,
    'from app.db.social_models import (\n',
    'from app.db.social_models import (\n',
)
replace(
    routes,
    ')\n\nrouter = APIRouter(prefix="/api/social", tags=["social"])\n',
    ')\nfrom app.services.social_delivery import execute_publication_job, run_due_publications\n\nrouter = APIRouter(prefix="/api/social", tags=["social"])\n',
)
replace(routes, '\nDEFAULT_PUBLISHER: SocialPublisher = FakeSocialPublisher()\n', '')
replace(
    routes,
    '    retry_count: int\n',
    '''    retry_count: int\n    max_attempts: int\n    next_attempt_at: dt.datetime | None\n    last_attempt_at: dt.datetime | None\n    adapter: str | None\n    publish_receipt: dict[str, object] | None\n''',
)
replace(
    routes,
    '        retry_count=job.retry_count,\n',
    '''        retry_count=job.retry_count,\n        max_attempts=job.max_attempts,\n        next_attempt_at=job.next_attempt_at,\n        last_attempt_at=job.last_attempt_at,\n        adapter=job.adapter,\n        publish_receipt=job.publish_receipt,\n''',
)
start = routes.read_text(encoding="utf-8")
old_start = start.index('\ndef _publish_job(')
old_end = start.index('\n\n@router.get("/derivatives/{derivative_id}/file")', old_start)
new_block = '''\n@router.post("/jobs/{job_id}/publish-now", response_model=JobView)\ndef publish_now(\n    job_id: uuid.UUID, session: SessionDependency, settings: SettingsDependency\n) -> JobView:\n    """Execute one job through the same delivery path used by the schedule worker."""\n    job = session.get(PublicationJob, job_id)\n    if job is None:\n        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such publication job.")\n    try:\n        execute_publication_job(session, job, settings)\n    except PublisherError as error:\n        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error\n    except Exception as error:\n        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Publisher failed.") from error\n    return _job_view(job, session)\n\n\n@router.post("/queue/run-due", response_model=list[JobView])\ndef run_due_jobs(session: SessionDependency, settings: SettingsDependency) -> list[JobView]:\n    """Manual execution hook using the exact same bounded worker pass."""\n    jobs = run_due_publications(session, settings)\n    return [_job_view(job, session) for job in jobs]\n'''
routes.write_text(start[:old_start] + new_block + start[old_end:], encoding="utf-8")

# Queue UI exposes delivery state instead of pretending the adapter is fake.
web_api = STUDIO / "web/src/api/social.ts"
replace(
    web_api,
    '  retry_count: number;\n',
    '''  retry_count: number;\n  max_attempts: number;\n  next_attempt_at: string | null;\n  last_attempt_at: string | null;\n  adapter: string | null;\n  publish_receipt: Record<string, unknown> | null;\n''',
)
bench = STUDIO / "web/src/components/SocialBench.tsx"
replace(bench, '                      Fake publish now\n', '                      Publish now\n')
replace(
    bench,
    '                      {job.caption ? <ParagraphXSmall>{job.caption}</ParagraphXSmall> : null}\n',
    '''                      {job.caption ? <ParagraphXSmall>{job.caption}</ParagraphXSmall> : null}\n                      {job.failure_reason ? (\n                        <ParagraphXSmall>\n                          Delivery: {job.failure_reason} · attempt {String(job.retry_count)}/\n                          {String(job.max_attempts)}\n                        </ParagraphXSmall>\n                      ) : null}\n''',
)

# Tests opt into the deterministic adapter and assert receipts/retry metadata.
tests = STUDIO / "tests/integration/test_social_publishing_api.py"
replace(
    tests,
    '        debug=True,\n',
    '        debug=True,\n        social_publishing_enabled=True,\n        social_publisher_mode="fake",\n',
)
replace(
    tests,
    '    assert first.json()["external_post_id"] == second.json()["external_post_id"]\n',
    '''    assert first.json()["external_post_id"] == second.json()["external_post_id"]\n    assert first.json()["adapter"] == "fake"\n    assert first.json()["publish_receipt"]["provider"] == "fake"\n    assert first.json()["retry_count"] == 1\n''',
)

# Environment documentation.
env = STUDIO / ".env.example"
with env.open("a", encoding="utf-8") as handle:
    handle.write('''\n# Social publishing is off until platform credentials/adapters are connected.\nSOCIAL_PUBLISHING_ENABLED=false\nSOCIAL_PUBLISHER_MODE=disabled\nSOCIAL_MAX_ATTEMPTS=5\nSOCIAL_RETRY_BASE_SECONDS=60\n''')

# One-shot systemd worker every minute. Disabled settings make it a no-op.
(STUDIO / "deploy/shirtfaced-social-publisher.service").write_text('''[Unit]\nDescription=Shirtfaced Social publication queue pass\nAfter=network-online.target shirtfaced-studio.service\n\n[Service]\nType=oneshot\nWorkingDirectory=/var/www/shirtfaced-app/studio\nEnvironmentFile=/etc/shirtfaced/studio.env\nExecStart=/var/www/shirtfaced-app/studio/.venv/bin/python scripts/run_social_publish_queue.py\n''', encoding="utf-8")
(STUDIO / "deploy/shirtfaced-social-publisher.timer").write_text('''[Unit]\nDescription=Run Shirtfaced Social publication queue every minute\n\n[Timer]\nOnBootSec=45s\nOnUnitActiveSec=60s\nAccuracySec=5s\nPersistent=true\nUnit=shirtfaced-social-publisher.service\n\n[Install]\nWantedBy=timers.target\n''', encoding="utf-8")

deploy = STUDIO / "deploy/deploy-studio.sh"
replace(
    deploy,
    'say "Restarting"\nsudo systemctl restart shirtfaced-studio\n',
    '''say "Installing Social publisher timer"\nsudo install -m 0644 "$STUDIO_DIR/deploy/shirtfaced-social-publisher.service" /etc/systemd/system/shirtfaced-social-publisher.service\nsudo install -m 0644 "$STUDIO_DIR/deploy/shirtfaced-social-publisher.timer" /etc/systemd/system/shirtfaced-social-publisher.timer\nsudo systemctl daemon-reload\nsudo systemctl enable --now shirtfaced-social-publisher.timer\n\nsay "Restarting"\nsudo systemctl restart shirtfaced-studio\n''',
)

# Keep implementation scope honest.
doc = ROOT / "docs/stage-2/SOCIAL_PUBLISHING_IMPLEMENTATION_SCOPE.md"
if doc.exists():
    with doc.open("a", encoding="utf-8") as handle:
        handle.write('''\n\n## Scheduled delivery worker — 2026-08-09\n\nThe queue now has one execution service shared by manual **Publish now** and the minute\nsystemd timer. Attempts, exponential retry timing, terminal failure, adapter identity and\npublish receipts are persisted. Production publishing defaults to disabled: the worker is\na no-op until a platform account adapter is explicitly connected. Test environments may\nselect the deterministic fake adapter; production must never record fake posts as live.\n''')
