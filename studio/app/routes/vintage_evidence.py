# ruff: noqa: E501
"""Private browser for the vintage marketplace evidence cache."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

router = APIRouter()

DEFAULT_ROOT = Path("/home/ubuntu/shirtfaced-research/vintage-ebay-images")


def _root() -> Path:
    return Path(os.environ.get("VINTAGE_EVIDENCE_ROOT", str(DEFAULT_ROOT))).resolve()


def _safe_listing_dir(listing_id: str) -> Path:
    """The directory for one listing, or 400/404.

    Traversal is already impossible before any path work: ``isdigit()`` admits
    no slash, no dot, no separator, so ``root / listing_id`` is always a direct
    child of root and cannot escape it.

    Deliberately does NOT call ``resolve()``. A merged evidence root is built
    from symlinks to more than one collector's tree, and resolving follows those
    links out to their real location -- whose parents are not the root, so a
    resolve-then-compare check rejects every legitimate image. That is not
    hypothetical: it 400'd all 11,544 of them, the eBay ones included.
    """
    if not listing_id.isdigit():
        raise HTTPException(status_code=400, detail="Invalid listing id")
    candidate = _root() / listing_id
    if not candidate.is_dir():
        raise HTTPException(status_code=404, detail="Listing not found")
    return candidate


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _records() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    root = _root()
    manifest = _read_json(root / "manifest.json", {})
    rows: list[dict[str, Any]] = []
    if not root.is_dir():
        return manifest, rows
    for child in sorted(root.iterdir(), reverse=True):
        if not child.is_dir() or not child.name.isdigit():
            continue
        record = _read_json(child / "record.json", {})
        if not record:
            continue
        images = sorted(
            p.name
            for p in child.iterdir()
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        )
        rows.append(
            {
                **record,
                "listing_id": str(record.get("listing_id") or child.name),
                "images": [f"/vintage-evidence/image/{child.name}/{name}" for name in images],
            }
        )

    # Counts are derived from the walk just done, not read from manifest.json.
    # The file is written once by whichever collector ran last, so it went stale
    # the moment a second source appeared under the same root -- and a merged
    # root reported "0 with images" while serving eleven thousand of them.
    # These two are free here; ``failed`` stays from the file because it is
    # collector state that cannot be derived from what landed on disk.
    manifest = {
        **manifest,
        "listings_with_images": sum(1 for row in rows if row["images"]),
        "image_count": sum(len(row["images"]) for row in rows),
    }
    return manifest, rows


@router.get("/api/vintage-evidence")
def vintage_evidence_api() -> JSONResponse:
    manifest, rows = _records()
    return JSONResponse({"manifest": manifest, "records": rows})


@router.get("/vintage-evidence/image/{listing_id}/{filename}")
def vintage_evidence_image(listing_id: str, filename: str) -> FileResponse:
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    # Same reasoning: the filename is already constrained to a bare name above,
    # so joining it cannot escape the listing directory, and resolving would
    # again break on a symlinked root.
    path = _safe_listing_dir(listing_id) / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)


@router.get("/vintage-evidence")
def vintage_evidence_page() -> HTMLResponse:
    return HTMLResponse(_PAGE, headers={"Cache-Control": "no-store"})


_PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vintage Evidence — Shirtfaced Studio</title>
<style>
:root{font-family:Inter,system-ui,sans-serif;color:#111;background:#f5f3ee}*{box-sizing:border-box}body{margin:0}.shell{max-width:1500px;margin:auto;padding:24px}.top{padding:16px 0 12px;border-bottom:1px solid #ccc}
h1{margin:0;font-size:30px}.sub{color:#666;margin:4px 0 12px}.stats{display:flex;gap:16px;flex-wrap:wrap;font-size:13px}.controls{display:grid;grid-template-columns:2fr repeat(3,1fr);gap:8px;margin-top:14px}input,select{width:100%;padding:11px 12px;border:1px solid #bbb;border-radius:10px;background:white}
.agent-panel{margin:18px 0 6px;padding:16px;background:#111;color:#fff;border-radius:16px}.agent-panel h2{margin:0 0 4px;font-size:18px}.agent-sub{font-size:12px;color:#bbb;margin-bottom:12px}.agent-actions{display:flex;gap:8px;margin-bottom:10px}.agent-actions button{border:1px solid #555;background:#222;color:#fff;border-radius:9px;padding:9px 12px;font-weight:700}.agent-actions button.primary{background:#fff;color:#111}.agent-grid{display:grid;gap:7px}.agent{background:#1e1e1e;border:1px solid #343434;border-radius:11px;overflow:hidden}.agent[open]{border-color:#555}.agent-summary{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:10px;align-items:center;padding:11px 12px;cursor:pointer;list-style:none}.agent-summary::-webkit-details-marker{display:none}.agent-summary:after{content:'+';font-size:20px;line-height:1;color:#888}.agent[open] .agent-summary:after{content:'\2212'}.agent-name{font-weight:800}.agent-state{font-size:12px;color:#bbb;text-transform:capitalize}.agent-progress{font-size:12px;font-weight:800;white-space:nowrap}.agent-body{padding:0 12px 12px;border-top:1px solid #343434}.agent-toggle{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:11px 0 2px;font-size:12px;color:#bbb}.switch{position:relative;width:48px;height:27px;flex:none}.switch input{display:none}.track{position:absolute;inset:0;border-radius:99px;background:#555;cursor:pointer}.track:after{content:'';position:absolute;width:21px;height:21px;left:3px;top:3px;border-radius:50%;background:#fff;transition:.18s}.switch input:checked+.track{background:#8ee000}.switch input:checked+.track:after{transform:translateX(21px)}.aprogress{height:6px;background:#383838;border-radius:99px;overflow:hidden;margin-top:11px}.abar{height:100%;background:#fff}.agent-row{display:flex;justify-content:space-between;gap:8px;font-size:11px;margin-top:7px;color:#bbb}.agent-row b{color:#fff;text-align:right;overflow-wrap:anywhere}.agent-error{font-size:11px;color:#ff8585;margin-top:8px;overflow-wrap:anywhere}.agent-error:empty{display:none}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px;padding-top:20px}.card{background:white;border:1px solid #d8d5ce;border-radius:14px;overflow:hidden;box-shadow:0 1px 3px #0000000d}.hero{aspect-ratio:1/1;background:#e8e5de;display:grid;place-items:center;overflow:hidden}.hero img{width:100%;height:100%;object-fit:contain}.meta{padding:12px}.brand{font-weight:800;font-size:13px;text-transform:uppercase}.title{font-size:14px;line-height:1.3;margin:6px 0;min-height:36px}.chips{display:flex;gap:6px;flex-wrap:wrap}.chip{font-size:11px;padding:4px 7px;border-radius:999px;background:#efede7}.foot{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-top:10px;font-size:12px}.foot a{color:inherit}.thumbs{display:flex;gap:5px;overflow-x:auto;padding:0 12px 12px}.thumbs img{width:54px;height:54px;object-fit:cover;border-radius:7px;border:1px solid #ddd;cursor:pointer}.empty{padding:40px;text-align:center;color:#777}
@media(max-width:700px){.shell{padding:14px}.controls{grid-template-columns:1fr 1fr}.controls input{grid-column:1/-1}.agent-panel{margin-top:14px;padding:13px}.agent-actions button{flex:1;min-height:42px}.agent-summary{grid-template-columns:minmax(0,1fr) auto auto;padding:12px 11px}.agent-state,.agent-progress{font-size:11px}}
</style>
</head>
<body><div class="shell"><div class="top"><h1>Vintage Evidence</h1><div class="sub">Sold surf / skate / street references with retained listing photography.</div><div class="stats" id="stats"></div><section class="agent-panel"><h2>Collectors</h2><div class="agent-sub">Independent 15-record workers. Open a collector for controls and details; status refreshes every 5 seconds.</div><div class="agent-actions"><button class="primary" onclick="setAll(true)">Start all</button><button onclick="setAll(false)">Stop all</button></div><div id="agents" class="agent-grid"></div></section><div class="controls"><input id="q" placeholder="Search brand, title, tags…"><select id="brand"><option value="">All brands</option></select><select id="era"><option value="">All eras</option></select><select id="trad"><option value="">All traditions</option></select></div></div><main id="grid" class="grid"></main></div>
<script>
let rows=[];const $=id=>document.getElementById(id);const uniq=(k)=>[...new Set(rows.map(r=>r[k]).filter(Boolean))].sort();
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function fill(id,key){for(const v of uniq(key)){const o=document.createElement('option');o.value=v;o.textContent=v;$(id).append(o)}}
function render(){const q=$('q').value.toLowerCase(),b=$('brand').value,e=$('era').value,t=$('trad').value;const f=rows.filter(r=>{const hay=[r.brand,r.title,r.era_claim,r.tradition,...(r.graphic_tags||[])].join(' ').toLowerCase();return(!q||hay.includes(q))&&(!b||r.brand===b)&&(!e||r.era_claim===e)&&(!t||r.tradition===t)});$('grid').innerHTML=f.length?f.map((r,i)=>{const imgs=r.images||[];const hero=imgs[0]?`<img id="hero-${i}" src="${esc(imgs[0])}" loading="lazy">`:'<span>No image</span>';const thumbs=imgs.slice(0,12).map(u=>`<img src="${esc(u)}" loading="lazy" onclick="document.getElementById('hero-${i}').src=this.src">`).join('');return`<article class="card"><div class="hero">${hero}</div><div class="meta"><div class="brand">${esc(r.brand||'—')}</div><div class="title">${esc(r.title||'Untitled')}</div><div class="chips"><span class="chip">${esc(r.era_claim||'')}</span><span class="chip">${esc(r.tradition||'')}</span><span class="chip">${imgs.length} images</span></div><div class="foot"><span>${esc(r.currency||'')} ${esc(r.sold_price??r.listed_price??'')}</span><a href="${esc(r.source_url||'#')}" target="_blank" rel="noreferrer">${r.marketplace==='archive'?'Source':'eBay'} ↗</a></div></div>${thumbs?`<div class="thumbs">${thumbs}</div>`:''}</article>`}).join(''):'<div class="empty">No matching records.</div>'}
async function toggleAgent(id,on){await fetch('/api/vintage-agents/'+id,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({enabled:on})});await loadAgents()}
async function setAll(on){const d=await fetch('/api/vintage-agents').then(r=>r.json());await Promise.all((d.agents||[]).map(a=>fetch('/api/vintage-agents/'+a.id,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({enabled:on})})));await loadAgents()}
async function loadAgents(){try{const openId=$('agents').querySelector('.agent[open]')?.dataset.id;const d=await fetch('/api/vintage-agents').then(r=>r.json());$('agents').innerHTML=(d.agents||[]).map(a=>{const target=a.batch_target||15,progress=a.batch_progress||0,pct=Math.min(100,Math.round((progress/target)*100));return `<details class="agent" name="collector-accordion" data-id="${a.id}" ${openId===String(a.id)?'open':''}><summary class="agent-summary"><span class="agent-name">Agent ${a.id}</span><span class="agent-state">${a.running?'running':'stopped'}</span><span class="agent-progress">${progress}/${target}</span></summary><div class="agent-body"><div class="agent-toggle"><span>Collector ${a.enabled?'on':'off'} · ${esc(a.status)}</span><label class="switch"><input type="checkbox" aria-label="Toggle Agent ${a.id}" ${a.enabled?'checked':''} onchange="toggleAgent(${a.id},this.checked)"><span class="track"></span></label></div><div class="aprogress"><div class="abar" style="width:${pct}%"></div></div><div class="agent-row"><span>Current checkpoint</span><b>${progress}/${target}</b></div><div class="agent-row"><span>Completed batches</span><b>${a.completed_batches||0}</b></div><div class="agent-row"><span>Completed records</span><b>${a.completed_records||0}</b></div><div class="agent-row"><span>Last listing</span><b>${esc(a.last_listing_id||'—')}</b></div><div class="agent-row"><span>Last error</span><b>${esc(a.last_error||'—')}</b></div></div></details>`}).join('')||'<div class="agent-error">Agent API unavailable.</div>';for(const el of $('agents').querySelectorAll('.agent'))el.addEventListener('toggle',()=>{if(el.open)for(const other of $('agents').querySelectorAll('.agent[open]'))if(other!==el)other.open=false})}catch(e){$('agents').innerHTML='<div class="agent-error">Agent controls unavailable.</div>'}}
fetch('/api/vintage-evidence').then(r=>r.json()).then(d=>{rows=d.records||[];const m=d.manifest||{};$('stats').innerHTML=`<span><b>${rows.length}</b> cached listings</span><span><b>${m.listings_with_images??0}</b> with images</span><span><b>${m.image_count??0}</b> image files</span><span><b>${m.failed??0}</b> failed</span>`;fill('brand','brand');fill('era','era_claim');fill('trad','tradition');render()}).catch(()=>{$('grid').innerHTML='<div class="empty">Evidence cache unavailable.</div>'});
loadAgents();setInterval(loadAgents,5000);for(const id of ['q','brand','era','trad'])$(id).addEventListener(id==='q'?'input':'change',render);
</script></body></html>"""
