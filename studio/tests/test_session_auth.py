"""Verifies session_auth.py against a real token minted by the Node side.

The token and secret below are copied from a real run of
admin/src/lib/session.ts's createSessionToken() during the incident this file
exists to close (21 August 2026) -- not hand-constructed, so a subtle mismatch
in the HMAC/base64url scheme between the two languages would actually be
caught here rather than passing two self-consistent-but-both-wrong halves.
"""

from __future__ import annotations

import time

from app.session_auth import _b64url_encode, _sign, verify_session_token

# From admin/.env's local-dev SESSION_SECRET.
SECRET = "ff22ed2c39c04a9b81e358ef567cb49b9b03f19bc1496a04e824ae0a19b3ad58"

# Minted by createSessionToken("admin@shirtfaced.wtf") using SECRET above.
REAL_NODE_TOKEN = (
    "YWRtaW5Ac2hpcnRmYWNlZC53dGY.1787866650."
    "qwXbE7gDb4A0XWbbLXlldgVx3l_vWubymnpUrRxaQ0A"
)


def test_verifies_a_real_token_minted_by_the_node_side() -> None:
    assert verify_session_token(REAL_NODE_TOKEN, SECRET) == "admin@shirtfaced.wtf"


def test_rejects_the_same_token_under_the_wrong_secret() -> None:
    assert verify_session_token(REAL_NODE_TOKEN, "a-different-secret") is None


def test_rejects_a_missing_token() -> None:
    assert verify_session_token(None, SECRET) is None
    assert verify_session_token("", SECRET) is None


def test_rejects_a_malformed_token() -> None:
    assert verify_session_token("not-three-dot-separated-parts", SECRET) is None
    assert verify_session_token("a.b.c.d", SECRET) is None


def test_rejects_a_tampered_signature() -> None:
    email_b64, expires, _signature = REAL_NODE_TOKEN.split(".")
    tampered = f"{email_b64}.{expires}.not-the-real-signature"
    assert verify_session_token(tampered, SECRET) is None


def test_rejects_an_expired_token() -> None:
    expired_epoch = int(time.time()) - 3600
    email_b64 = _b64url_encode(b"admin@shirtfaced.wtf")
    payload = f"{email_b64}.{expired_epoch}"
    expired_token = f"{payload}.{_sign(SECRET, payload)}"
    assert verify_session_token(expired_token, SECRET) is None


def test_round_trips_a_freshly_signed_token() -> None:
    future_epoch = int(time.time()) + 3600
    email_b64 = _b64url_encode(b"someone-else@shirtfaced.wtf")
    payload = f"{email_b64}.{future_epoch}"
    token = f"{payload}.{_sign(SECRET, payload)}"
    assert verify_session_token(token, SECRET) == "someone-else@shirtfaced.wtf"
