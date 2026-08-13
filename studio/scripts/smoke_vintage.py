"""Walk the vintage chain end to end and say which link is broken.

Written 2026-08-14 after the same class of failure three times in one day. Each
time a change was verified next to itself rather than at the far end: the
listing count was checked but not an image, so every image 404'd for hours; the
benches were confirmed to render but no research run was ever started, so a
path guard refused every evidence image and nobody knew; the manual endpoint's
page was named without once calling it.

The common shape is that every one of those checks passed. A green deploy, a
correct count and a rendering page are all compatible with a feature that does
nothing. Only the far end tells you.

So this exercises the links a person actually uses, in order, and reports each
one. It fetches real bytes rather than status codes, because a 200 serving an
HTML error page is the failure it is meant to catch.

    python scripts/smoke_vintage.py                       # against production
    python scripts/smoke_vintage.py --base http://localhost:8000
    python scripts/smoke_vintage.py --era 1990s

Exit code is the number of failed links, so CI or a cron can read it.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE = "https://studio.shirtfaced.wtf"
TIMEOUT = 60

IMAGE_MAGIC = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a", b"RIFF")

# Cloudflare fronts the studio and refuses Python-urllib's default agent
# with a 403, which reads exactly like the app being broken. Carrying a
# browser agent is what the collectors already do, for the same reason.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


class Link:
    """One step, its result, and what it proves."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.ok = False
        self.detail = ""


def _get(url: str) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers={"Accept": "*/*", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return 0, str(error).encode()


def _post(url: str, body: dict[str, Any]) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return 0, str(error).encode()


def run(base: str, era: str) -> list[Link]:
    links: list[Link] = []
    base = base.rstrip("/")

    # 1. The evidence listing, and its counts.
    evidence = Link("evidence API returns records")
    status, body = _get(f"{base}/api/vintage-evidence")
    records: list[dict[str, Any]] = []
    if status == 200:
        try:
            payload = json.loads(body)
            records = payload.get("records") or []
            manifest = payload.get("manifest") or {}
            evidence.ok = len(records) > 0
            evidence.detail = f"{len(records)} listings, {manifest.get('image_count', 0)} images"
        except json.JSONDecodeError:
            evidence.detail = "200 but not JSON"
    else:
        evidence.detail = f"HTTP {status}"
    links.append(evidence)

    # 2. An actual image. The failure that ran for hours was here, behind a
    #    listing count that was perfectly correct.
    image = Link("an evidence image serves real bytes")
    candidate = next((r for r in records if r.get("images")), None)
    if candidate is None:
        image.detail = "no record carried an image url"
    else:
        url = f"{base}{candidate['images'][0]}"
        status, body = _get(url)
        if status != 200:
            image.detail = f"HTTP {status} — {body[:80].decode('utf-8', 'replace')}"
        elif not body.startswith(IMAGE_MAGIC):
            # A 200 serving HTML is the case a status check would have passed.
            image.detail = f"200 but not an image: {body[:40]!r}"
        else:
            image.ok = True
            image.detail = f"{len(body)} bytes from listing {candidate['listing_id']}"
    links.append(image)

    # 3. Evidence selection for research. Uses the same code path both research
    #    routes depend on, so this is what proves research can run at all.
    prepare = Link("research can select evidence (no API spend)")
    status, body = _post(
        f"{base}/api/vintage-research/manual/prepare",
        {"era": era, "image_limit": 4},
    )
    prepared: dict[str, Any] = {}
    if status == 200:
        try:
            prepared = json.loads(body)
            chosen = prepared.get("evidence_images") or []
            prepare.ok = len(chosen) > 0 and bool(prepared.get("pass1_prompt"))
            prepare.detail = f"{len(chosen)} images selected for era={era}"
        except json.JSONDecodeError:
            prepare.detail = "200 but not JSON"
    else:
        prepare.detail = f"HTTP {status} — {body[:110].decode('utf-8', 'replace')}"
    links.append(prepare)

    # 4. Every selected image must fetch. Selection succeeding says nothing
    #    about whether the bytes behind it are reachable.
    selected = Link("every selected image fetches")
    chosen = prepared.get("evidence_images") or []
    if not chosen:
        selected.detail = "nothing selected to check"
    else:
        bad = []
        for item in chosen:
            status, body = _get(f"{base}{item['image_url']}")
            if status != 200 or not body.startswith(IMAGE_MAGIC):
                bad.append(f"{item['image_url']} -> {status}")
        selected.ok = not bad
        selected.detail = "all fetched" if not bad else f"{len(bad)} failed: {bad[0]}"
    links.append(selected)

    # 5. Runs list and pipeline targets: what the review screen needs to work.
    runs = Link("research runs list")
    status, body = _get(f"{base}/api/vintage-research/runs")
    if status == 200:
        try:
            rows = json.loads(body)
            runs.ok = isinstance(rows, list)
            runs.detail = f"{len(rows)} runs"
        except json.JSONDecodeError:
            runs.detail = "200 but not JSON"
    else:
        runs.detail = f"HTTP {status}"
    links.append(runs)

    targets = Link("design concept targets")
    status, body = _get(f"{base}/api/vintage-research/design-concepts")
    if status == 200:
        try:
            rows = json.loads(body)
            targets.ok = isinstance(rows, list)
            targets.detail = f"{len(rows)} targets"
            if not rows:
                targets.detail += " — send to pipeline will have nothing to pick"
        except json.JSONDecodeError:
            targets.detail = "200 but not JSON"
    else:
        targets.detail = f"HTTP {status}"
    links.append(targets)

    # 6. The retired pages must redirect, not 404 or serve a stale copy.
    for path in ("/vintage-evidence", "/vintage-research"):
        redirect = Link(f"{path} redirects to the shell")
        request = urllib.request.Request(
            path if path.startswith("http") else base + path,
            headers={"User-Agent": USER_AGENT},
        )

        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *_: Any, **__: Any) -> None:
                return None

        opener = urllib.request.build_opener(_NoRedirect)
        try:
            with opener.open(request, timeout=TIMEOUT) as response:
                redirect.detail = f"HTTP {response.status} — expected a redirect"
        except urllib.error.HTTPError as error:
            redirect.ok = error.code in (301, 302, 303, 307, 308)
            redirect.detail = f"HTTP {error.code} -> {error.headers.get('Location', '?')}"
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            redirect.detail = str(error)[:60]
        links.append(redirect)

    return links


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--era", default="1990s")
    args = parser.parse_args(argv[1:])

    print(f"vintage chain against {args.base}\n")
    links = run(args.base, args.era)
    for link in links:
        mark = "ok  " if link.ok else "FAIL"
        print(f"  [{mark}] {link.name}\n         {link.detail}")

    failed = [link for link in links if not link.ok]
    print(f"\n{len(links) - len(failed)}/{len(links)} links good")
    if failed:
        print("broken: " + ", ".join(link.name for link in failed))
    return len(failed)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
