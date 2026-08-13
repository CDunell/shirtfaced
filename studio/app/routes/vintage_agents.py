# ruff: noqa: E501 -- this module embeds a browser page as a string literal.
# Its HTML, CSS and JS are minified onto single lines and cannot be wrapped
# without changing what is served. Same exemption vintage_evidence.py carries.
"""Studio controls for vintage evidence collection workers."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from app.services.vintage_agents import all_status, set_enabled

router = APIRouter()


class Toggle(BaseModel):
    enabled: bool


@router.get("/api/vintage-agents")
def api_status() -> JSONResponse:
    return JSONResponse({"agents": all_status()})


@router.post("/api/vintage-agents/{agent_id}")
def api_toggle(agent_id: int, body: Toggle) -> JSONResponse:
    try:
        result = set_enabled(agent_id, body.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return JSONResponse(result)


@router.get("/vintage-agents")
def page() -> HTMLResponse:
    return HTMLResponse(PAGE)


PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Vintage Agents — Shirtfaced Studio</title><style>
:root{font-family:Inter,system-ui,sans-serif;background:#f5f3ee;color:#111}*{box-sizing:border-box}body{margin:0}.shell{max-width:1100px;margin:auto;padding:24px}h1{margin:0 0 5px}.sub{color:#666;margin-bottom:22px}.nav a{color:#111}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}.card{background:white;border:1px solid #d5d1c8;border-radius:16px;padding:18px}.head{display:flex;justify-content:space-between;align-items:center}.dot{width:10px;height:10px;border-radius:50%;background:#aaa}.dot.on{background:#19a15f}.stat{font-size:13px;color:#666;margin:12px 0}.progress{height:8px;background:#ece9e2;border-radius:99px;overflow:hidden}.bar{height:100%;background:#111}.row{display:flex;justify-content:space-between;margin-top:8px;font-size:12px}.switch{position:relative;width:50px;height:28px}.switch input{display:none}.track{position:absolute;inset:0;border-radius:99px;background:#ccc;cursor:pointer}.track:after{content:'';position:absolute;width:22px;height:22px;left:3px;top:3px;border-radius:50%;background:white;transition:.18s}.switch input:checked+.track{background:#111}.switch input:checked+.track:after{transform:translateX(22px)}.error{color:#a00;font-size:12px;margin-top:10px;min-height:16px}.topline{display:flex;justify-content:space-between;gap:10px;align-items:end;margin-bottom:18px}@media(max-width:600px){.shell{padding:15px}.topline{display:block}}
</style></head><body><div class="shell"><div class="topline"><div><h1>Vintage Agents</h1><div class="sub">Independent 15-record end-to-end collectors. Toggle each worker on or off.</div></div><div class="nav"><a href="/vintage-evidence">Evidence viewer →</a></div></div><main id="grid" class="grid"></main></div><script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function toggle(id,on){await fetch('/api/vintage-agents/'+id,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({enabled:on})});await load()}
async function load(){const d=await fetch('/api/vintage-agents').then(r=>r.json());document.getElementById('grid').innerHTML=d.agents.map(a=>{const pct=Math.min(100,Math.round((a.batch_progress/a.batch_target)*100));return `<section class="card"><div class="head"><div><b>Agent ${a.id}</b><div class="stat">${esc(a.status)} · ${a.running?'process running':'process stopped'}</div></div><label class="switch"><input type="checkbox" ${a.enabled?'checked':''} onchange="toggle(${a.id},this.checked)"><span class="track"></span></label></div><div class="progress"><div class="bar" style="width:${pct}%"></div></div><div class="row"><span>Current checkpoint</span><b>${a.batch_progress}/${a.batch_target}</b></div><div class="row"><span>Completed batches</span><b>${a.completed_batches}</b></div><div class="row"><span>Completed records</span><b>${a.completed_records}</b></div><div class="row"><span>Last listing</span><b>${esc(a.last_listing_id||'—')}</b></div><div class="error">${esc(a.last_error||'')}</div></section>`}).join('')}
load();setInterval(load,5000);
</script></body></html>"""
