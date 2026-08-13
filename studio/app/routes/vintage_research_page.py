# ruff: noqa: E501 -- this module embeds a browser page as a string literal.
# Its HTML, CSS and JS are minified onto single lines and cannot be wrapped
# without changing what is served. Same exemption vintage_evidence.py carries.
"""Server-rendered Studio workbench for Vintage Evidence research."""

from __future__ import annotations

from html import escape
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.concept_models import DesignConcept
from app.db.session import get_db_session
from app.services.vintage_research import (
    VintageResearchError,
    execute_research,
    filter_evidence,
    load_run,
    update_concept,
)

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_db_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

STYLE = """<style>body{font:14px system-ui;background:#f5f3ee;margin:0}.s{max-width:1300px;margin:auto;padding:18px}.c{background:#fff;border:1px solid #ddd;border-radius:12px;padding:14px;margin:12px 0}.f{display:flex;gap:8px;flex-wrap:wrap}input,select,button,textarea{padding:9px;border:1px solid #aaa;border-radius:8px;font:inherit}button{background:#111;color:#fff;font-weight:700}.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px}.e,.x{border:1px solid #ddd;border-radius:9px;padding:8px}.e img{width:100%;height:150px;object-fit:contain;background:#eee}.k{display:grid;grid-template-columns:1fr 1fr;gap:10px}.p{white-space:pre-wrap;background:#f2f0eb;padding:8px;font-size:12px}.src{display:flex;gap:6px;overflow:auto}.src img{width:90px;height:90px;object-fit:contain;background:#eee}.m{color:#666;font-size:12px}@media(max-width:700px){.k{grid-template-columns:1fr}}</style>"""


def _page(body: str) -> HTMLResponse:
    return HTMLResponse(
        f"<!doctype html><meta name='viewport' content='width=device-width,initial-scale=1'><title>Vintage Research</title>{STYLE}<main class='s'><h1>Vintage Evidence Research</h1><p class='m'>Actual evidence images → Pass 1 exactly 10 concepts → Pass 2 the same 10 with expanded prompts.</p>{body}</main>",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/vintage-research")
def browse(
    q: str = Query(default=""),
    brand: str = Query(default=""),
    era: str = Query(default=""),
    tradition: str = Query(default=""),
) -> HTMLResponse:
    filters = {"query": q, "brand": brand, "era": era, "tradition": tradition}
    rows = filter_evidence(filters)[:200]
    cards = "".join(
        f"<label class='e'><input type='checkbox' name='listing_ids' value='{escape(str(r['listing_id']))}'><img src='{escape(r['images'][0])}'><b>{escape(str(r.get('brand') or 'Unknown'))}</b><br><span class='m'>{escape(str(r.get('title') or ''))}</span></label>"
        for r in rows
    )
    body = f"""<section class='c'><form method='get' class='f'><input name='q' value='{escape(q)}' placeholder='Search'><input name='brand' value='{escape(brand)}' placeholder='Brand'><input name='era' value='{escape(era)}' placeholder='Era'><input name='tradition' value='{escape(tradition)}' placeholder='Tradition'><button>Filter evidence</button><a href='/vintage-evidence'>Evidence viewer</a></form></section><section class='c'><form method='post' action='/vintage-research/run'><input type='hidden' name='q' value='{escape(q)}'><input type='hidden' name='brand' value='{escape(brand)}'><input type='hidden' name='era' value='{escape(era)}'><input type='hidden' name='tradition' value='{escape(tradition)}'><div class='f'><label>Images <select name='image_limit'><option>8</option><option>12</option><option selected>16</option><option>24</option></select></label><button>Run both passes</button></div><p class='m'>{len(rows)} matching listings shown. Select the evidence listings to analyse.</p><div class='g'>{cards}</div></form></section>"""
    return _page(body)


@router.post("/vintage-research/run")
def run_research(
    settings: SettingsDep,
    q: str = Form(default=""),
    brand: str = Form(default=""),
    era: str = Form(default=""),
    tradition: str = Form(default=""),
    image_limit: int = Form(default=16),
    listing_ids: list[str] = Form(default=[]),
) -> RedirectResponse:
    run = execute_research(
        settings,
        filters={"query": q, "brand": brand, "era": era, "tradition": tradition},
        listing_ids=listing_ids or None,
        image_urls=None,
        image_limit=image_limit,
    )
    return RedirectResponse(f"/vintage-research/{run['id']}", status_code=303)


# Declared before the {run_id} route so it wins the match. Without it a GET to
# /vintage-research/run -- a reload or a back-nav after submitting the form, which
# posts to this same path -- falls into review() as run_id="run", fails the UUID
# parse and surfaces as an unexplained 500. Sending it back to the form is what
# the visitor was after.
@router.get("/vintage-research/run")
def run_get() -> RedirectResponse:
    return RedirectResponse("/vintage-research", status_code=303)


@router.get("/vintage-research/{run_id}")
def review(run_id: str, session: SessionDep) -> HTMLResponse:
    try:
        run = load_run(run_id)
    except VintageResearchError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    sources = "".join(
        f"<img src='{escape(i['image_url'])}' title='{escape(i['filename'])}'>"
        for i in run.get("evidence_images", [])
    )
    targets = session.query(DesignConcept).order_by(DesignConcept.external_number).all()
    target_options = "".join(
        f"<option value='{c.id}'>#{c.external_number} {escape(c.title)}</option>" for c in targets
    )
    concepts = []
    for c in run.get("concepts", []):
        n = c["concept_number"]
        prompt = c.get("edited_prompt") or c.get("pass2_prompt") or ""
        actions = f"<form class='f' method='post' action='/vintage-research/{run_id}/{n}/status'><button name='state' value='approved'>Approve</button><button name='state' value='rejected'>Reject</button></form>"
        edit = f"<form method='post' action='/vintage-research/{run_id}/{n}/edit'><textarea name='prompt' rows='8' style='width:100%'>{escape(prompt)}</textarea><button>Save edit</button></form>"
        pipe = ""
        if c.get("status") == "approved":
            pipe = f"<form class='f' method='post' action='/vintage-research/{run_id}/{n}/pipeline'><select name='design_concept_id'>{target_options}</select><button>Send to design pipeline</button></form>"
        concepts.append(
            f"<article class='x'><b>{n}. {escape(c['title'])}</b><p>{escape(c['idea'])}</p><div class='p'>{escape(prompt)}</div><p><b>Status:</b> {escape(c.get('status', 'pending'))}</p>{actions}{edit}{pipe}</article>"
        )
    body = f"<section class='c'><a href='/vintage-research'>New research run</a><h2>Run {escape(run_id[:8])}</h2><p class='m'>{escape(run.get('model', ''))} · {len(run.get('evidence_images', []))} exact images</p><h3>Exact source images supplied</h3><div class='src'>{sources}</div></section><section class='c'><div class='k'>{''.join(concepts)}</div></section>"
    return _page(body)


@router.post("/vintage-research/{run_id}/{number}/status")
def set_status(run_id: str, number: int, state: str = Form(...)) -> RedirectResponse:
    update_concept(run_id, number, status=state)
    return RedirectResponse(f"/vintage-research/{run_id}", status_code=303)


@router.post("/vintage-research/{run_id}/{number}/edit")
def edit_prompt(run_id: str, number: int, prompt: str = Form(...)) -> RedirectResponse:
    update_concept(run_id, number, edited_prompt=prompt)
    return RedirectResponse(f"/vintage-research/{run_id}", status_code=303)
