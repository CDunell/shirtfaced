"""Walk the product design chain end to end and say which link is broken.

The sibling of ``smoke_vintage.py``, written for the same reason and after the
same lesson. Phase 1 of ``DESIGN_FLOW_PLAN.md`` shipped with two defects that
every unit test, type check and lint pass was happy with:

* ``/api/concepts/rubric`` was declared after ``/api/concepts/{concept_id}``, so
  FastAPI parsed "rubric" as a concept UUID and the scorecard endpoint was
  unreachable. No unit test can see this -- they call the handler directly and
  never route.
* the backlog listed one library, so a concept created from Research was
  invisible in Designs and the chain broke one step after it started.

Both were found by opening the app. This is that check, automated, so the next
one is found by a deploy rather than by a person.

What it does *not* do: create rows. The vintage smoke can be read-only because
research runs already exist; this is read-only for the same reason and one
more -- a smoke test that writes into production leaves numbered concepts
behind, and concept numbering is permanent by design.

    python scripts/smoke_design_chain.py                       # against production
    python scripts/smoke_design_chain.py --base http://localhost:8000

Exit code is the number of failed links, so CI or a cron can read it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE = "https://studio.shirtfaced.wtf"
TIMEOUT = 60

# Studio now sits behind the same session auth admin does (app/session_auth.py,
# 21 August 2026) -- a request with no valid session cookie gets a redirect or
# a 401, not the real response this script is checking for. CI mints a
# short-lived token from the same SESSION_SECRET both boxes already have and
# passes it here; a local run against a dev server with auth disabled just
# leaves this unset.
SESSION_TOKEN = os.environ.get("SMOKE_SESSION_TOKEN")


def _headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT, **(extra or {})}
    if SESSION_TOKEN:
        headers["Cookie"] = f"sf_admin_session={SESSION_TOKEN}"
    return headers

# Cloudflare fronts the studio and refuses Python-urllib's default agent with a
# 403, which reads exactly like the app being broken.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

# The rubric's own shape, from DESIGN_REVIEW_SCORECARD.md and the constitution.
# Asserted here as numbers rather than read from the response and compared to
# itself, because "the endpoint returned some gates" is exactly the check that
# would have passed while the endpoint was unreachable.
EXPECTED_GATES = 13
EXPECTED_CATEGORIES = 9
EXPECTED_GROUPS = ("validate_recognition", "validate_production", "review_against_collection")


class Link:
    """One step, its result, and what it proves."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.ok = False
        self.detail = ""


def _get(url: str) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers=_headers({"Accept": "*/*"}))
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return 0, str(error).encode()


def _json(url: str) -> tuple[int, Any]:
    status, body = _get(url)
    if status != 200:
        return status, body[:120].decode("utf-8", "replace")
    try:
        return status, json.loads(body)
    except json.JSONDecodeError:
        return status, None


def run(base: str) -> list[Link]:
    links: list[Link] = []
    base = base.rstrip("/")

    # 1. The scorecard is reachable at all. This is the link that was broken by
    #    route ordering, and the one everything downstream depends on: without
    #    it no form can render and no design can ever be judged.
    rubric = Link("the scorecard is reachable and complete")
    status, payload = _json(f"{base}/api/concepts/rubric")
    if status != 200 or not isinstance(payload, dict):
        rubric.detail = f"HTTP {status} — {payload}"
    else:
        gates = payload.get("gates") or []
        categories = payload.get("categories") or []
        groups = tuple(group.get("id") for group in payload.get("groups") or [])
        problems = []
        if len(gates) != EXPECTED_GATES:
            problems.append(f"{len(gates)} gates, expected {EXPECTED_GATES}")
        if len(categories) != EXPECTED_CATEGORIES:
            problems.append(f"{len(categories)} categories, expected {EXPECTED_CATEGORIES}")
        if groups != EXPECTED_GROUPS:
            problems.append(f"groups are {groups}")
        # A control with no question is a field name a person cannot answer.
        unasked = [gate["id"] for gate in gates if not gate.get("question")]
        if unasked:
            problems.append(f"{len(unasked)} gates carry no question")
        rubric.ok = not problems
        rubric.detail = (
            "; ".join(problems)
            if problems
            else f"{len(gates)} gates and {len(categories)} categories in 3 groups"
        )
    links.append(rubric)

    # 2. The backlog answers across libraries. Defaulting to the tee library
    #    made a concept created from Research invisible here, which broke the
    #    chain one step after it started while every screen still rendered.
    backlog = Link("the backlog lists every library")
    status, payload = _json(f"{base}/api/concepts")
    concepts: list[dict[str, Any]] = payload if isinstance(payload, list) else []
    if status != 200:
        backlog.detail = f"HTTP {status} — {payload}"
    else:
        libraries = sorted({str(concept.get("library")) for concept in concepts})
        backlog.ok = len(concepts) > 0
        backlog.detail = f"{len(concepts)} concepts across {libraries or 'no'} libraries"
    links.append(backlog)

    # 3. Work answers what to do, and every row says what. A row with no
    #    sentence sends somebody hunting through six screens, which is the
    #    exact failure Phase 3 exists to remove.
    work = Link("work states a next action for every item")
    status, payload = _json(f"{base}/api/concepts/work")
    if status != 200 or not isinstance(payload, list):
        work.detail = f"HTTP {status} — {payload}"
    else:
        silent = [item for item in payload if not str(item.get("next_action") or "").strip()]
        stageless = [item for item in payload if not str(item.get("stage") or "").strip()]
        if silent:
            work.detail = f"{len(silent)} of {len(payload)} items state no next action"
        elif stageless:
            work.detail = f"{len(stageless)} items carry no stage"
        else:
            stages = sorted({str(item.get("stage")) for item in payload})
            work.ok = True
            work.detail = f"{len(payload)} items, stages {stages or 'none'}"
    links.append(work)

    # 4. Garment zones are readable, because Print has nothing to place into
    #    without them and an approval cannot record a zone that is not offered.
    garments = Link("garments declare printable zones")
    status, payload = _json(f"{base}/api/concepts/garments")
    if status != 200 or not isinstance(payload, dict):
        garments.detail = f"HTTP {status} — {payload}"
    else:
        zones = sum(len(value) for value in payload.values())
        garments.ok = zones > 0
        garments.detail = f"{len(payload)} garments, {zones} zones"
    links.append(garments)

    # 5. An attempt's review is fetchable and evaluates. Reported per attempt
    #    rather than in aggregate: one broken review is the whole chain for the
    #    person holding that design.
    review = Link("an attempt's review evaluates")
    attempt_id = _first_attempt(base, concepts)
    if attempt_id is None:
        review.detail = "no attempt exists yet to review"
        # Not a failure: an empty backlog is a state, not a broken link.
        review.ok = True
    else:
        status, payload = _json(f"{base}/api/concepts/attempts/{attempt_id}/review")
        if status != 200 or not isinstance(payload, dict):
            review.detail = f"HTTP {status} — {payload}"
        else:
            evaluation = payload.get("evaluation") or {}
            action = payload.get("next_action") or ""
            if not action:
                review.detail = "the review states no next action"
            elif "percentage" not in evaluation:
                review.detail = "the review carries no evaluation"
            else:
                review.ok = True
                review.detail = (
                    f"{evaluation['percentage']:.0f}/100, "
                    f"{len(evaluation.get('blockers') or [])} blockers, "
                    f"next action stated"
                )
    links.append(review)

    # 6. An approved version prints. The audit's finding was that printing.py
    #    held no reference to approved_designs at all, so this link is the whole
    #    point of item 5 and the far end of the chain.
    printed = Link("an approved version renders into its zone")
    version_id = _first_version(base, concepts)
    if version_id is None:
        printed.detail = "no approved version exists yet to print"
        printed.ok = True
    else:
        status, body = _get(f"{base}/api/concepts/versions/{version_id}/print.svg")
        text = body[:400].decode("utf-8", "replace")
        if status != 200:
            printed.detail = f"HTTP {status} — {text}"
        elif not text.lstrip().startswith("<svg"):
            printed.detail = "200 but not an SVG document"
        elif "<path" not in body[:20000].decode("utf-8", "replace"):
            printed.detail = "an SVG with no garment outline in it"
        else:
            printed.ok = True
            printed.detail = f"{len(body)} bytes of SVG, garment outline present"
    links.append(printed)

    return links


def _first_attempt(base: str, concepts: list[dict[str, Any]]) -> str | None:
    """The newest attempt anywhere, by asking the concepts that have one."""
    for concept in sorted(concepts, key=lambda c: c.get("attempt_count", 0), reverse=True):
        if not concept.get("attempt_count"):
            return None
        status, payload = _json(f"{base}/api/concepts/{concept['id']}")
        if status == 200 and isinstance(payload, dict) and payload.get("attempts"):
            return str(payload["attempts"][-1]["id"])
    return None


def _first_version(base: str, concepts: list[dict[str, Any]]) -> str | None:
    for concept in concepts:
        if not concept.get("approved_versions"):
            continue
        status, payload = _json(f"{base}/api/concepts/{concept['id']}")
        if status == 200 and isinstance(payload, dict) and payload.get("versions"):
            return str(payload["versions"][-1]["id"])
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE)
    arguments = parser.parse_args()

    links = run(arguments.base)
    failed = [link for link in links if not link.ok]

    print(f"design chain — {arguments.base}\n")
    for link in links:
        mark = "ok  " if link.ok else "FAIL"
        print(f"  {mark}  {link.name}")
        if link.detail:
            print(f"        {link.detail}")

    print()
    if failed:
        print(f"{len(failed)} of {len(links)} links broken.")
    else:
        print(f"all {len(links)} links intact.")
    return len(failed)


if __name__ == "__main__":
    sys.exit(main())
