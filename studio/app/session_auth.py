"""Shared session-cookie verification.

Studio has no login of its own. Per admin/README.md's own description of the
intended design, it "verifies the session cookie admin signs, using the same
SESSION_SECRET" -- that was never actually implemented, and studio.shirtfaced.wtf
was reachable by anyone who found the hostname, no session required, with real
OpenAI/Gemini-billed generate endpoints behind it. Confirmed live, not just
suspected from reading the code, on 21 August 2026.

This reimplements admin/src/lib/session.ts's HMAC scheme exactly (same secret,
same token shape: base64url(email).expiryEpoch.base64url(signature)) so a
session minted by Admin's login verifies here without either side knowing
about the other's language or framework.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time

SESSION_COOKIE = "sf_admin_session"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded)


def _sign(secret: str, value: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(digest)


def verify_session_token(token: str | None, secret: str) -> str | None:
    """Returns the signed-in email, or None if the token is missing, malformed,
    incorrectly signed, or expired. Mirrors verifySessionToken in session.ts."""
    if not token:
        return None

    parts = token.split(".")
    if len(parts) != 3:
        return None
    email_b64, expires_str, signature = parts

    payload = f"{email_b64}.{expires_str}"
    expected = _sign(secret, payload)
    if not hmac.compare_digest(signature, expected):
        return None

    try:
        expires = float(expires_str)
    except ValueError:
        return None
    if expires < time.time():
        return None

    try:
        return _b64url_decode(email_b64).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None
