"""Verifying the session admin issues.

Studio has no login: it trusts a cookie admin signed. That makes the token format
a contract between two codebases in two languages, and a contract nothing checks
is one that drifts. The fixture below was minted by admin's own session.ts and is
byte-identical to what this module produces, so a change on either side that
breaks logins fails a test instead of failing in production.
"""

from __future__ import annotations

import base64
import hmac
from hashlib import sha256

import pytest

from app.security import verify_session_token

SECRET = "test-secret"
EMAIL = "admin@shirtfaced.wtf"

# node -e "..." against admin/src/lib/session.ts, expiring 2100-01-01.
ADMIN_ISSUED = "YWRtaW5Ac2hpcnRmYWNlZC53dGY.4102444800.l627RRrZXP5CY7-DSIqskr0IBJbmVCAyIzIiA1LHj8w"


def mint(email: str, expires: int, secret: str = SECRET) -> str:
    """A token in admin's format, for the cases a fixed fixture cannot cover."""
    payload = f"{base64.urlsafe_b64encode(email.encode()).decode().rstrip('=')}.{expires}"
    signature = (
        base64.urlsafe_b64encode(hmac.new(secret.encode(), payload.encode(), sha256).digest())
        .decode()
        .rstrip("=")
    )
    return f"{payload}.{signature}"


def test_a_token_admin_issued_is_accepted() -> None:
    assert verify_session_token(ADMIN_ISSUED, SECRET) == EMAIL


def test_the_expiry_is_honoured() -> None:
    assert verify_session_token(ADMIN_ISSUED, SECRET, now=4102444801.0) is None


def test_a_token_signed_with_another_secret_is_rejected() -> None:
    """The whole mechanism: only the holder of the secret can mint a session."""
    forged = mint(EMAIL, 4102444800, secret="not-the-secret")

    assert verify_session_token(forged, SECRET) is None


def test_an_edited_payload_is_rejected() -> None:
    """Signature covers the email, so a valid session cannot be renamed."""
    _, expires, signature = ADMIN_ISSUED.split(".")
    other = base64.urlsafe_b64encode(b"someone@else.example").decode().rstrip("=")

    assert verify_session_token(f"{other}.{expires}.{signature}", SECRET) is None


def test_an_edited_expiry_is_rejected() -> None:
    email_b64, _, signature = ADMIN_ISSUED.split(".")

    assert verify_session_token(f"{email_b64}.9999999999.{signature}", SECRET) is None


@pytest.mark.parametrize(
    "token",
    ["", "not-a-token", "a.b", "a.b.c.d", "...", ADMIN_ISSUED.replace(".", "-")],
    ids=["empty", "garbage", "too-few-parts", "too-many-parts", "empty-parts", "no-separators"],
)
def test_malformed_tokens_are_rejected_without_raising(token: str) -> None:
    """These arrive from the internet. A crash here is a 500 on every request."""
    assert verify_session_token(token, SECRET) is None


def test_no_secret_means_nothing_is_accepted() -> None:
    """Fails closed. A deployment that forgot the secret must not be wide open."""
    assert verify_session_token(ADMIN_ISSUED, "") is None
