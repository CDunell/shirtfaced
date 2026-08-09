"""Email Studio foundation routes."""

from __future__ import annotations

import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import PROJECT_ROOT, Settings, get_settings
from app.db.email_models import ConsentState, EmailMessage
from app.db.session import get_db_session
from app.services.email_service import (
    TEMPLATES,
    create_preview_message,
    deliver_message,
    get_or_create_contact,
    record_marketing_consent,
)

router = APIRouter(prefix="/api/email", tags=["email"])
SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


class EmailInput(BaseModel):
    email: str = Field(min_length=3, max_length=320)

    @field_validator("email")
    @classmethod
    def _email_shape(cls, value: str) -> str:
        clean = value.strip().lower()
        if clean.count("@") != 1 or "." not in clean.rsplit("@", 1)[1]:
            raise ValueError("Enter a valid email address.")
        return clean


class PreviewInput(EmailInput):
    display_name: str = Field(default="mate", max_length=200)
    template_key: str


class ConsentInput(EmailInput):
    subscribed: bool
    source: str = Field(default="studio", max_length=120)


class MessageView(BaseModel):
    id: uuid.UUID
    recipient_email: str
    template_key: str
    purpose: str
    subject: str
    html_body: str
    text_body: str
    state: str
    eligible: bool | None = None
    eligibility_reason: str | None = None
    adapter: str | None = None
    failure_reason: str | None = None
    external_message_id: str | None = None


def _message_view(
    message: EmailMessage, eligible: bool | None = None, reason: str | None = None
) -> MessageView:
    return MessageView(
        id=message.id,
        recipient_email=message.recipient_email,
        template_key=message.template_key,
        purpose=message.purpose.value,
        subject=message.subject,
        html_body=message.html_body,
        text_body=message.text_body,
        state=message.state.value,
        eligible=eligible,
        eligibility_reason=reason,
        adapter=message.adapter,
        failure_reason=message.failure_reason,
        external_message_id=message.external_message_id,
    )


@router.get("/templates")
def templates() -> list[dict[str, str]]:
    return [
        {
            "key": template.key,
            "name": template.name,
            "purpose": template.purpose.value,
            "subject": template.subject,
        }
        for template in TEMPLATES
    ]


@router.get("/dns-plan")
def dns_plan() -> dict[str, object]:
    path = PROJECT_ROOT / "email" / "dns-plan.json"
    if not path.is_file():
        raise HTTPException(status_code=500, detail="Email DNS plan is missing.")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise HTTPException(status_code=500, detail="Email DNS plan is invalid.")
    return value


@router.post("/consent")
def consent(payload: ConsentInput, session: SessionDependency) -> dict[str, str]:
    contact = get_or_create_contact(session, payload.email)
    state = ConsentState.SUBSCRIBED if payload.subscribed else ConsentState.UNSUBSCRIBED
    record_marketing_consent(session, contact, state, payload.source)
    session.commit()
    return {"email": contact.email, "state": state.value}


@router.post("/preview", response_model=MessageView)
def preview(payload: PreviewInput, session: SessionDependency) -> MessageView:
    try:
        message, allowed, reason = create_preview_message(
            session,
            email=payload.email,
            display_name=payload.display_name,
            template_key=payload.template_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    session.commit()
    return _message_view(message, allowed, reason)


@router.post("/messages/{message_id}/test-send", response_model=MessageView)
def test_send(
    message_id: uuid.UUID, session: SessionDependency, settings: SettingsDependency
) -> MessageView:
    message = session.scalar(
        select(EmailMessage)
        .options(selectinload(EmailMessage.contact))
        .where(EmailMessage.id == message_id)
    )
    if message is None:
        raise HTTPException(status_code=404, detail="Email message not found.")
    deliver_message(session, settings, message)
    session.commit()
    return _message_view(message)
