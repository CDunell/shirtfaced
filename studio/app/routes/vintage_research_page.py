"""Redirects for the retired server-rendered Vintage Research page.

The page this module used to serve was HTML, CSS and JavaScript built inside
Python string literals -- one 2,000-character line that had to be edited to
change a link. It now lives in the Studio React shell as
``VintageResearchBench``, alongside the other benches, which is where it picks
up navigation instead of carrying its own.

What is left is the redirects. The old URLs were bookmarked and posted, and a
404 is a worse answer than the shell. Data moved to ``vintage_api``; nothing
here reads or writes anything.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/vintage-research")
def research_page() -> RedirectResponse:
    return RedirectResponse("/", status_code=307)


@router.get("/vintage-research/run")
def run_get() -> RedirectResponse:
    """A GET here used to fall into the {run_id} route and 500 on the UUID parse."""
    return RedirectResponse("/", status_code=307)


@router.get("/vintage-research/{run_id}")
def review(run_id: str) -> RedirectResponse:
    # The run id is dropped deliberately: the shell selects a run from its own
    # list, and inventing a deep link the React side cannot honour would be a
    # promise this redirect has no way to keep.
    return RedirectResponse("/", status_code=307)
