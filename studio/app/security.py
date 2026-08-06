"""Verifying the session admin issued.

Studio has no login. Admin has one, and signs a stateless session cookie with
SESSION_SECRET; Studio is given the same secret and checks the signature. Being
logged into admin is being logged into Studio, which is the whole point -- a
second set of credentials is a second thing to lose.

The token format is admin's, in admin/src/lib/session.ts:

    base64url(email) "." expiryEpoch "." base64url(HMAC-SHA256(payload))

Anything about this file that drifts from that one stops logins working, so the
tests pin the format against tokens minted by admin's own code.
"""

from __future__ import annotations

import base64
import hmac
import time
from hashlib import sha256

# Admin names the cookie. Studio only reads it.
SESSION_COOKIE = "sf_admin_session"


def _b64url_decode(value: str) -> bytes:
    """Decode base64url that, as Node writes it, carries no padding."""
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _sign(payload: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), payload.encode(), sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def verify_session_token(token: str | None, secret: str, *, now: float | None = None) -> str | None:
    """The email in a valid, unexpired token, or None.

    None for every failure: a caller that cannot tell "expired" from "forged"
    cannot leak the difference to whoever is asking.
    """
    if not token or not secret:
        return None

    parts = token.split(".")
    if len(parts) != 3:
        return None
    email_b64, expires_raw, signature = parts

    expected = _sign(f"{email_b64}.{expires_raw}", secret)
    if not hmac.compare_digest(signature, expected):
        return None

    try:
        expires = float(expires_raw)
    except ValueError:
        return None
    if expires < (time.time() if now is None else now):
        return None

    try:
        return _b64url_decode(email_b64).decode()
    except (ValueError, UnicodeDecodeError):
        return None
