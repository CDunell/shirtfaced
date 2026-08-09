"""Shirtfaced-owned email preview, eligibility and delivery rules."""

from __future__ import annotations

import html
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.email_delivery import (
    DisabledEmailAdapter,
    EmailAdapter,
    EmailDeliveryError,
    EmailPayload,
    LocalPreviewEmailAdapter,
)
from app.config import Settings
from app.db.email_models import (
    ConsentState,
    EmailConsentEvent,
    EmailContact,
    EmailMessage,
    EmailMessageState,
    EmailPurpose,
    EmailSuppression,
    SuppressionReason,
    SuppressionScope,
)


@dataclass(frozen=True)
class EmailTemplate:
    key: str
    name: str
    purpose: EmailPurpose
    subject: str
    heading: str
    body: str


TEMPLATES: tuple[EmailTemplate, ...] = (
    EmailTemplate(
        key="welcome",
        name="Welcome",
        purpose=EmailPurpose.MARKETING,
        subject="Welcome to Shirtfaced",
        heading="You found us.",
        body="Drops, questionable decisions and the good stuff worth opening your inbox for.",
    ),
    EmailTemplate(
        key="drop-live",
        name="Drop live",
        purpose=EmailPurpose.MARKETING,
        subject="It is live.",
        heading="The drop is live.",
        body="New Shirtfaced is up. Get in before your size becomes someone else's problem.",
    ),
    EmailTemplate(
        key="order-confirmation",
        name="Order confirmation",
        purpose=EmailPurpose.TRANSACTIONAL,
        subject="Order confirmed",
        heading="Good choice.",
        body="Your Shirtfaced order is confirmed. We will send the next update when it moves.",
    ),
)


def normalise_email(value: str) -> str:
    return value.strip().lower()


def template_for(key: str) -> EmailTemplate:
    return next((template for template in TEMPLATES if template.key == key), None) or _unknown(key)


def _unknown(key: str) -> EmailTemplate:
    raise ValueError(f"Unknown email template: {key}")


def render_template(template: EmailTemplate, recipient_name: str = "mate") -> tuple[str, str]:
    safe_name = html.escape(recipient_name.strip() or "mate")
    html_body = (
        "<!doctype html><html><body style=\"margin:0;background:#f4f4f1;color:#111;"
        "font-family:Arial,sans-serif\"><main style=\"max-width:640px;margin:0 auto;"
        "padding:48px 24px\">"
        "<div style=\"font-size:28px;font-weight:800;margin-bottom:48px\">shirtfaced</div>"
        f"<p>Hey {safe_name},</p><h1>{html.escape(template.heading)}</h1>"
        f"<p>{html.escape(template.body)}</p>"
        "<hr style=\"margin:48px 0;border:0;border-top:1px solid #ccc\">"
        "<p style=\"font-size:12px;color:#666\">SHIRTFACED / AUSTRALIA</p>"
        "</main></body></html>"
    )
    text_body = (
        f"Hey {recipient_name.strip() or 'mate'},\n\n{template.heading}\n\n"
        f"{template.body}\n\nSHIRTFACED / AUSTRALIA"
    )
    return html_body, text_body


def get_or_create_contact(
    session: Session,
    email: str,
    display_name: str | None = None,
) -> EmailContact:
    normalised = normalise_email(email)
    contact = session.scalar(select(EmailContact).where(EmailContact.email == normalised))
    if contact is not None:
        return contact
    contact = EmailContact(email=normalised, display_name=display_name)
    session.add(contact)
    session.flush()
    return contact


def record_marketing_consent(
    session: Session, contact: EmailContact, state: ConsentState, source: str
) -> EmailConsentEvent:
    event = EmailConsentEvent(
        contact_id=contact.id,
        purpose=EmailPurpose.MARKETING,
        state=state,
        source=source,
    )
    session.add(event)
    if state is ConsentState.UNSUBSCRIBED:
        session.add(
            EmailSuppression(
                contact_id=contact.id,
                scope=SuppressionScope.MARKETING,
                reason=SuppressionReason.UNSUBSCRIBE,
                source=source,
            )
        )
    session.flush()
    return event


def eligibility(session: Session, contact: EmailContact, purpose: EmailPurpose) -> tuple[bool, str]:
    suppressions = session.scalars(
        select(EmailSuppression).where(EmailSuppression.contact_id == contact.id)
    ).all()
    globally_blocked = any(
        item.scope is SuppressionScope.GLOBAL
        or item.reason in {SuppressionReason.HARD_BOUNCE, SuppressionReason.COMPLAINT}
        for item in suppressions
    )
    if globally_blocked:
        return False, "global suppression"
    if purpose is EmailPurpose.TRANSACTIONAL:
        return True, "transactional"
    if any(item.scope is SuppressionScope.MARKETING for item in suppressions):
        return False, "marketing suppression"
    latest = session.scalar(
        select(EmailConsentEvent)
        .where(
            EmailConsentEvent.contact_id == contact.id,
            EmailConsentEvent.purpose == EmailPurpose.MARKETING,
        )
        .order_by(EmailConsentEvent.occurred_at.desc(), EmailConsentEvent.created_at.desc())
        .limit(1)
    )
    if latest is None or latest.state is not ConsentState.SUBSCRIBED:
        return False, "marketing consent required"
    return True, "eligible"


def build_adapter(settings: Settings) -> EmailAdapter:
    if settings.email_adapter_mode == "local":
        if not settings.debug:
            raise EmailDeliveryError("Local email adapter is only allowed with DEBUG=true.")
        return LocalPreviewEmailAdapter(settings.email_preview_root_resolved)
    return DisabledEmailAdapter()


def create_preview_message(
    session: Session,
    *,
    email: str,
    display_name: str,
    template_key: str,
) -> tuple[EmailMessage, bool, str]:
    template = template_for(template_key)
    contact = get_or_create_contact(session, email, display_name)
    allowed, reason = eligibility(session, contact, template.purpose)
    html_body, text_body = render_template(template, display_name)
    message = EmailMessage(
        contact_id=contact.id,
        recipient_email=contact.email,
        purpose=template.purpose,
        template_key=template.key,
        subject=template.subject,
        html_body=html_body,
        text_body=text_body,
        state=EmailMessageState.PREVIEW,
    )
    session.add(message)
    session.flush()
    return message, allowed, reason


def deliver_message(session: Session, settings: Settings, message: EmailMessage) -> EmailMessage:
    if message.contact is None:
        message.state = EmailMessageState.BLOCKED
        message.failure_reason = "contact missing"
        return message
    allowed, reason = eligibility(session, message.contact, message.purpose)
    if not allowed:
        message.state = EmailMessageState.BLOCKED
        message.failure_reason = reason
        return message
    adapter = build_adapter(settings)
    message.attempt_count += 1
    message.adapter = adapter.name
    try:
        receipt = adapter.send(
            EmailPayload(
                to_email=message.recipient_email,
                from_email=(
                    settings.email_from_transactional
                    if message.purpose is EmailPurpose.TRANSACTIONAL
                    else settings.email_from_marketing
                ),
                reply_to=settings.email_reply_to,
                subject=message.subject,
                html_body=message.html_body,
                text_body=message.text_body,
            )
        )
    except EmailDeliveryError as exc:
        message.state = EmailMessageState.FAILED
        message.failure_reason = str(exc)
        return message
    message.state = EmailMessageState.SENT
    message.external_message_id = receipt.external_message_id
    message.delivery_receipt = receipt.metadata
    return message
