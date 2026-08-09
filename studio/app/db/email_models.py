"""Persistence for Shirtfaced email contacts, consent and delivery audit."""

from __future__ import annotations

import datetime as dt
import uuid
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class EmailPurpose(StrEnum):
    TRANSACTIONAL = "transactional"
    MARKETING = "marketing"


class ConsentState(StrEnum):
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"


class SuppressionScope(StrEnum):
    GLOBAL = "global"
    MARKETING = "marketing"


class SuppressionReason(StrEnum):
    UNSUBSCRIBE = "unsubscribe"
    HARD_BOUNCE = "hard_bounce"
    COMPLAINT = "complaint"
    MANUAL = "manual"
    LEGAL = "legal"


class EmailMessageState(StrEnum):
    PREVIEW = "preview"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    BLOCKED = "blocked"


def _enum(enum_type: type[StrEnum], name: str) -> Enum:
    return Enum(enum_type, name=name, values_callable=lambda e: [member.value for member in e])


class EmailContact(Base, TimestampMixin):
    """Canonical Shirtfaced-owned email identity."""

    __tablename__ = "email_contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String(200))
    customer_ref: Mapped[str | None] = mapped_column(String(200), index=True)

    consent_events: Mapped[list[EmailConsentEvent]] = relationship(
        back_populates="contact",
        cascade="all, delete-orphan",
        order_by="EmailConsentEvent.occurred_at",
    )
    suppressions: Mapped[list[EmailSuppression]] = relationship(
        back_populates="contact", cascade="all, delete-orphan"
    )
    messages: Mapped[list[EmailMessage]] = relationship(back_populates="contact")


class EmailConsentEvent(Base):
    """Append-only consent history. Current state is derived from the latest event."""

    __tablename__ = "email_consent_events"
    __table_args__ = (
        Index(
            "ix_email_consent_contact_purpose_time",
            "contact_id",
            "purpose",
            text("occurred_at DESC"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_contacts.id", ondelete="CASCADE"), nullable=False
    )
    purpose: Mapped[EmailPurpose] = mapped_column(
        _enum(EmailPurpose, "email_purpose"), nullable=False
    )
    state: Mapped[ConsentState] = mapped_column(
        _enum(ConsentState, "email_consent_state"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    source_detail: Mapped[str | None] = mapped_column(String(500))
    occurred_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    contact: Mapped[EmailContact] = relationship(back_populates="consent_events")


class EmailSuppression(Base):
    """Durable delivery block created by consent, deliverability or owner action."""

    __tablename__ = "email_suppressions"
    __table_args__ = (
        Index("ix_email_suppressions_contact_scope", "contact_id", "scope"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_contacts.id", ondelete="CASCADE"), nullable=False
    )
    scope: Mapped[SuppressionScope] = mapped_column(
        _enum(SuppressionScope, "email_suppression_scope"), nullable=False
    )
    reason: Mapped[SuppressionReason] = mapped_column(
        _enum(SuppressionReason, "email_suppression_reason"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    contact: Mapped[EmailContact] = relationship(back_populates="suppressions")


class EmailMessage(Base, TimestampMixin):
    """Rendered email intent and delivery receipt."""

    __tablename__ = "email_messages"
    __table_args__ = (
        Index("ix_email_messages_state_created_at", "state", text("created_at DESC")),
        Index("ix_email_messages_contact_created_at", "contact_id", text("created_at DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_contacts.id", ondelete="SET NULL")
    )
    recipient_email: Mapped[str] = mapped_column(String(320), nullable=False)
    purpose: Mapped[EmailPurpose] = mapped_column(
        _enum(EmailPurpose, "email_purpose"), nullable=False
    )
    template_key: Mapped[str] = mapped_column(String(160), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    html_body: Mapped[str] = mapped_column(Text, nullable=False)
    text_body: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[EmailMessageState] = mapped_column(
        _enum(EmailMessageState, "email_message_state"),
        nullable=False,
        default=EmailMessageState.PREVIEW,
        server_default=EmailMessageState.PREVIEW.value,
    )
    adapter: Mapped[str | None] = mapped_column(String(120))
    external_message_id: Mapped[str | None] = mapped_column(String(240), unique=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    sent_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    delivery_receipt: Mapped[dict[str, object] | None] = mapped_column(JSONB)

    contact: Mapped[EmailContact | None] = relationship(back_populates="messages")
