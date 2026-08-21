#!/usr/bin/env python3
"""Smoke the deployed renderer validation contract without spending money."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request

# Studio now sits behind the same session auth admin does (app/session_auth.py,
# 21 August 2026) -- a request with no valid session cookie gets redirected to
# the Cloudflare-fronted login page instead of the real response this script
# is checking for, and following that redirect with urllib's default agent
# gets a 403 from Cloudflare. CI mints a short-lived token from the same
# SESSION_SECRET both boxes already have and passes it here; a local run
# against a dev server with auth disabled just leaves this unset.
SESSION_TOKEN = os.environ.get("SMOKE_SESSION_TOKEN")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _headers() -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT}
    if SESSION_TOKEN:
        headers["Cookie"] = f"sf_admin_session={SESSION_TOKEN}"
    return headers


def get_json(url: str) -> dict[str, object]:
    request = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    base = args.base.rstrip("/")

    manifest = get_json(f"{base}/api/renderer/validation")
    scenes = manifest.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 5:
        raise SystemExit("renderer validation manifest must expose exactly five benchmark scenes")
    if manifest.get("billable_generation_exposed") is not False:
        raise SystemExit("validation deployment must not expose unguarded billable generation")

    pub = get_json(f"{base}/api/renderer/validation/W01-P28")
    instant = str(pub.get("exact_instant", "")).lower()
    if "stands on the pool table" not in instant or "cue horizontal overhead" not in instant:
        raise SystemExit("pub benchmark lost locked hero geometry")

    print("renderer validation smoke: ok")


if __name__ == "__main__":
    main()
