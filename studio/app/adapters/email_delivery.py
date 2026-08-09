"""Provider-neutral email delivery adapters."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class EmailPayload:
    to_email: str
    from_email: str
    reply_to: str
    subject: str
    html_body: str
    text_body: str


@dataclass(frozen=True)
class EmailReceipt:
    adapter: str
    external_message_id: str
    metadata: dict[str, object]


class EmailDeliveryError(RuntimeError):
    """Raised when an adapter cannot deliver a message."""


class EmailAdapter(Protocol):
    name: str

    def send(self, payload: EmailPayload) -> EmailReceipt:
        """Deliver one message or raise EmailDeliveryError."""
        ...


class DisabledEmailAdapter:
    """Production-safe default: sending is impossible until configured."""

    name = "disabled"

    def send(self, payload: EmailPayload) -> EmailReceipt:
        del payload
        raise EmailDeliveryError("Email delivery is disabled; no provider is configured.")


class LocalPreviewEmailAdapter:
    """Development adapter that writes inspectable HTML/text artifacts to disk."""

    name = "local"

    def __init__(self, root: Path) -> None:
        self._root = root

    def send(self, payload: EmailPayload) -> EmailReceipt:
        self._root.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(
            f"{payload.to_email}\0{payload.subject}\0{payload.html_body}".encode()
        ).hexdigest()[:20]
        stem = f"email-{digest}"
        html_path = self._root / f"{stem}.html"
        text_path = self._root / f"{stem}.txt"
        html_path.write_text(payload.html_body, encoding="utf-8")
        text_path.write_text(
            f"To: {payload.to_email}\nFrom: {payload.from_email}\nReply-To: {payload.reply_to}\n"
            f"Subject: {payload.subject}\n\n{payload.text_body}",
            encoding="utf-8",
        )
        return EmailReceipt(
            adapter=self.name,
            external_message_id=f"local:{digest}",
            metadata={"html_path": str(html_path), "text_path": str(text_path)},
        )
