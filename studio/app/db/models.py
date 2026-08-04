"""ORM models.

``World`` and ``Shot`` are present. Generation attempts, image assets, reviews,
decisions, canon proposals, usage records and audit events are added by the phases
that first need them, each with its own Alembic migration.
"""

from __future__ import annotations

import datetime as dt
import uuid
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.domain.enums import (
    ACTIVE_ATTEMPT_STATES,
    AssetKind,
    AttemptState,
    AuditEventType,
    CanonProposalStatus,
    FailureCode,
    HumanDecisionKind,
    ReviewRecommendation,
    ReviewVerdict,
    ShotStatus,
    SyncState,
    WorldStatus,
)

__all__ = [
    "SHA256_HEX_LENGTH",
    "AssetKind",
    "AttemptState",
    "AuditEvent",
    "AutomatedReview",
    "CanonProposal",
    "GenerationAttempt",
    "HumanDecision",
    "ImageAsset",
    "Shot",
    "ShotStatus",
    "World",
    "WorldStatus",
]

SHA256_HEX_LENGTH = 64


def _enum(enum_type: type[StrEnum], name: str) -> Enum:
    """A native PostgreSQL enum storing the member values, not their Python names."""
    return Enum(enum_type, name=name, values_callable=lambda e: [member.value for member in e])


class World(Base, TimestampMixin):
    """A creative world backed by ``WORLD.md``, ``CONTINUITY.md`` and ``SHOTLIST.md``."""

    __tablename__ = "worlds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # Relative to WORLDS_ROOT. Stored relative so the same database works on a
    # developer machine and on the Oracle host.
    directory_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[WorldStatus] = mapped_column(
        _enum(WorldStatus, "world_status"),
        nullable=False,
        default=WorldStatus.ACTIVE,
        server_default=WorldStatus.ACTIVE.value,
    )
    # SHA-256 of each canonical document as last loaded; null until the first load.
    world_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))
    continuity_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))
    shotlist_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))

    shots: Mapped[list[Shot]] = relationship(
        back_populates="world",
        cascade="all, delete-orphan",
        order_by="Shot.sequence",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<World slug={self.slug!r} status={self.status.value!r}>"


class Shot(Base, TimestampMixin):
    """One planned photograph, imported from ``SHOTLIST.md``."""

    __tablename__ = "shots"
    __table_args__ = (
        UniqueConstraint("world_id", "external_id", name="uq_shots_world_id_external_id"),
        # Supports the deterministic selector: eligible shots for a world, in
        # priority then sequence order.
        Index(
            "ix_shots_world_id_status_priority_sequence",
            "world_id",
            "status",
            "priority",
            "sequence",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
    )
    # The human-facing identifier from the shotlist, such as W01-011.
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("100"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    hero_product: Mapped[str | None] = mapped_column(String(120))
    camera_position: Mapped[str | None] = mapped_column(String(120))
    lighting_source: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[ShotStatus] = mapped_column(
        _enum(ShotStatus, "shot_status"),
        nullable=False,
        default=ShotStatus.PLANNED,
        server_default=ShotStatus.PLANNED.value,
    )
    disabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    # Line in SHOTLIST.md this shot came from, so a problem can be pointed at.
    source_line: Mapped[int | None] = mapped_column(Integer)

    world: Mapped[World] = relationship(back_populates="shots")
    attempts: Mapped[list[GenerationAttempt]] = relationship(
        back_populates="shot",
        cascade="all, delete-orphan",
        order_by="GenerationAttempt.attempt_number",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Shot {self.external_id!r} status={self.status.value!r}>"


class GenerationAttempt(Base, TimestampMixin):
    """One attempt to produce an image for a shot.

    Everything needed to explain the result is recorded here: the exact prompt, the
    model settings, the shot metadata as it stood, and the hashes of the three
    canonical documents. A generated image must be traceable to its prompt, its model
    settings and the source world version, and the documents can be edited afterwards.
    """

    __tablename__ = "generation_attempts"
    __table_args__ = (
        UniqueConstraint(
            "shot_id", "attempt_number", name="uq_generation_attempts_shot_id_attempt_number"
        ),
        Index("ix_generation_attempts_world_id_created_at", "world_id", text("created_at DESC")),
        # One active attempt per world. Enforced by the database, not by a process
        # lock, because production restarts and may later run more than one worker.
        Index(
            "uq_generation_attempts_one_active_per_world",
            "world_id",
            unique=True,
            postgresql_where=text(
                "state IN ("
                + ", ".join(f"'{state.value}'" for state in sorted(ACTIVE_ATTEMPT_STATES))
                + ")"
            ),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False
    )
    shot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shots.id", ondelete="CASCADE"), nullable=False
    )
    # Set when this attempt retries or varies an earlier one, so the chain is intact.
    parent_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_attempts.id", ondelete="SET NULL")
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[AttemptState] = mapped_column(
        _enum(AttemptState, "attempt_state"),
        nullable=False,
        default=AttemptState.PLANNED,
        server_default=AttemptState.PLANNED.value,
    )

    selection_reason: Mapped[str | None] = mapped_column(Text)
    production_prompt: Mapped[str | None] = mapped_column(Text)
    prompt_plan_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    image_model: Mapped[str | None] = mapped_column(String(120))
    image_size: Mapped[str | None] = mapped_column(String(32))
    image_quality: Mapped[str | None] = mapped_column(String(32))
    image_format: Mapped[str | None] = mapped_column(String(16))
    # Logged for provider support. Never a key, never a payload.
    provider_request_id: Mapped[str | None] = mapped_column(String(120))

    # The shot as it stood when this attempt ran; the shotlist can change afterwards.
    hero_product: Mapped[str | None] = mapped_column(String(120))
    camera_position: Mapped[str | None] = mapped_column(String(120))
    world_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))
    continuity_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))
    shotlist_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))

    failure_code: Mapped[FailureCode | None] = mapped_column(_enum(FailureCode, "failure_code"))
    failure_message: Mapped[str | None] = mapped_column(Text)

    world: Mapped[World] = relationship()
    shot: Mapped[Shot] = relationship(back_populates="attempts")
    assets: Mapped[list[ImageAsset]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )
    reviews: Mapped[list[AutomatedReview]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="AutomatedReview.created_at",
    )
    # At most one. The uniqueness is enforced by the database, not by this mapping.
    decision: Mapped[HumanDecision | None] = relationship(
        back_populates="attempt", cascade="all, delete-orphan", uselist=False
    )

    @property
    def latest_review(self) -> AutomatedReview | None:
        """Reviews are immutable; a re-review adds another, so the last one stands."""
        return self.reviews[-1] if self.reviews else None

    @property
    def is_active(self) -> bool:
        return self.state in ACTIVE_ATTEMPT_STATES

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<GenerationAttempt {self.attempt_number} state={self.state.value!r}>"


class ImageAsset(Base):
    """A stored image file belonging to an attempt.

    The database holds metadata and a stable object key. Bytes live in the asset
    store, so the same rows work against a mounted volume today and object storage
    later.
    """

    __tablename__ = "image_assets"
    __table_args__ = (
        UniqueConstraint("attempt_id", "kind", name="uq_image_assets_attempt_id_kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("generation_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[AssetKind] = mapped_column(_enum(AssetKind, "asset_kind"), nullable=False)
    # Relative to ASSETS_ROOT, so the same row works on any host.
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(SHA256_HEX_LENGTH), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    attempt: Mapped[GenerationAttempt] = relationship(back_populates="assets")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<ImageAsset {self.kind.value!r} {self.relative_path!r}>"


class AutomatedReview(Base):
    """One structured review of a generated image.

    Reviews are immutable. Retrying a review adds another row rather than replacing
    this one, so the history of what the model said is never lost.

    A review is evidence for the owner. It never changes shot status, never appends
    continuity and never edits canon.
    """

    __tablename__ = "automated_reviews"
    __table_args__ = (Index("ix_automated_reviews_attempt_id", "attempt_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("generation_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    review_model: Mapped[str] = mapped_column(String(120), nullable=False)
    # Bumped when the review schema changes, so old reviews stay interpretable.
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    provider_request_id: Mapped[str | None] = mapped_column(String(120))

    recommendation: Mapped[ReviewRecommendation] = mapped_column(
        _enum(ReviewRecommendation, "review_recommendation"), nullable=False
    )
    verdict: Mapped[ReviewVerdict] = mapped_column(
        _enum(ReviewVerdict, "review_verdict"), nullable=False
    )

    mood_score: Mapped[int] = mapped_column(Integer, nullable=False)
    australian_authenticity_score: Mapped[int] = mapped_column(Integer, nullable=False)
    product_visibility_score: Mapped[int] = mapped_column(Integer, nullable=False)
    documentary_credibility_score: Mapped[int] = mapped_column(Integer, nullable=False)
    story_score: Mapped[int] = mapped_column(Integer, nullable=False)

    branding_compliant: Mapped[bool] = mapped_column(Boolean, nullable=False)
    vehicle_compliant: Mapped[bool] = mapped_column(Boolean, nullable=False)

    strongest_success: Mapped[str] = mapped_column(Text, nullable=False)
    material_drift: Mapped[str | None] = mapped_column(Text)
    recommended_action: Mapped[str | None] = mapped_column(Text)
    next_hero_product: Mapped[str | None] = mapped_column(String(120))
    next_camera: Mapped[str | None] = mapped_column(String(120))

    # The nine gates exactly as returned, so evidence and codes survive intact.
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # The canon this image was judged against, which may differ from the canon it was
    # generated against if the documents were edited in between.
    world_document_hash: Mapped[str | None] = mapped_column(String(SHA256_HEX_LENGTH))

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    attempt: Mapped[GenerationAttempt] = relationship(back_populates="reviews")

    @property
    def new_rule_proposal(self) -> str | None:
        """The rule the reviewer deliberately proposed, if any.

        Distinct from ``material_drift``, which describes what went wrong in this one
        frame. Only this becomes a permanent lesson; drift prose never does.
        """
        value = (self.raw_json or {}).get("new_rule_proposal")
        return str(value).strip() or None if value else None

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<AutomatedReview {self.recommendation.value!r}>"


class CanonProposal(Base):
    """A permanent rule the review model believes is worth adding.

    Stored as a proposal and nothing more. ``WORLD.md`` changes only after the owner
    approves it explicitly, which is the canon proposal phase's job.
    """

    __tablename__ = "canon_proposals"
    __table_args__ = (Index("ix_canon_proposals_world_id_status", "world_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False
    )
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_attempts.id", ondelete="SET NULL")
    )
    status: Mapped[CanonProposalStatus] = mapped_column(
        _enum(CanonProposalStatus, "canon_proposal_status"),
        nullable=False,
        default=CanonProposalStatus.PENDING,
        server_default=CanonProposalStatus.PENDING.value,
    )
    proposed_heading: Mapped[str | None] = mapped_column(String(200))
    proposed_text: Mapped[str] = mapped_column(Text, nullable=False)
    insertion_anchor: Mapped[str | None] = mapped_column(String(200))
    reason: Mapped[str | None] = mapped_column(Text)
    human_note: Mapped[str | None] = mapped_column(Text)
    git_commit: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    decided_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    world: Mapped[World] = relationship()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<CanonProposal {self.status.value!r}>"


class HumanDecision(Base):
    """The owner's final decision on one attempt.

    Exactly one per attempt, enforced by a unique constraint rather than only by an
    application check: a double-click, a refresh and a network retry all arrive as
    separate requests.

    The decision is recorded first and independently of the file and Git work that
    follows, because those cannot share a transaction with it. Each downstream system
    reports its own outcome, so a response can say "decided, but not yet written"
    rather than implying the decision rolled back.
    """

    __tablename__ = "human_decisions"
    __table_args__ = (UniqueConstraint("attempt_id", name="uq_human_decisions_attempt_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("generation_attempts.id", ondelete="CASCADE"),
        nullable=False,
    )
    decision: Mapped[HumanDecisionKind] = mapped_column(
        _enum(HumanDecisionKind, "human_decision_kind"), nullable=False
    )
    # The owner's words, verbatim. Never rewritten by a model.
    reason: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    instruction: Mapped[str | None] = mapped_column(Text)
    promote_to_reference: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    actor: Mapped[str] = mapped_column(String(64), nullable=False, server_default=text("'owner'"))
    # Lets a retried request return the existing decision instead of a 409.
    idempotency_key: Mapped[str | None] = mapped_column(String(128))

    markdown_sync: Mapped[SyncState] = mapped_column(
        _enum(SyncState, "sync_state"),
        nullable=False,
        default=SyncState.NOT_ATTEMPTED,
        server_default=SyncState.NOT_ATTEMPTED.value,
    )
    git_sync: Mapped[SyncState] = mapped_column(
        _enum(SyncState, "sync_state"),
        nullable=False,
        default=SyncState.NOT_ATTEMPTED,
        server_default=SyncState.NOT_ATTEMPTED.value,
    )
    reference_sync: Mapped[SyncState] = mapped_column(
        _enum(SyncState, "sync_state"),
        nullable=False,
        default=SyncState.NOT_ATTEMPTED,
        server_default=SyncState.NOT_ATTEMPTED.value,
    )
    git_commit: Mapped[str | None] = mapped_column(String(64))
    # Set when a downstream step failed. The decision stands; something needs a human.
    reconciliation_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    reconciliation_detail: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    attempt: Mapped[GenerationAttempt] = relationship(back_populates="decision")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<HumanDecision {self.decision.value!r}>"


class AuditEvent(Base):
    """Append-only record of what the application did.

    Never updated and never deleted. Payloads carry no secrets and no signed URLs.
    """

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_world_id_created_at", "world_id", text("created_at DESC")),
        Index("ix_audit_events_attempt_id", "attempt_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    world_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE")
    )
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_attempts.id", ondelete="CASCADE")
    )
    event_type: Mapped[AuditEventType] = mapped_column(
        _enum(AuditEventType, "audit_event_type"), nullable=False
    )
    actor: Mapped[str] = mapped_column(String(64), nullable=False, server_default=text("'owner'"))
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<AuditEvent {self.event_type.value!r}>"
