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
    if not listing_id.isdigit():
        raise HTTPException(status_code=400, detail="Invalid listing id")
    root = _root()
    candidate = (root / listing_id).resolve()
    if root not in candidate.parents:
        raise HTTPException(status_code=400, detail="Invalid path")
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
    return manifest, rows


@router.get("/api/vintage-evidence")
def vintage_evidence_api() -> JSONResponse:
    manifest, rows = _records()
    return JSONResponse({"manifest": manifest, "records": rows})


@router.get("/vintage-evidence/image/{listing_id}/{filename}")
def vintage_evidence_image(listing_id: str, filename: str) -> FileResponse:
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = (_safe_listing_dir(listing_id) / filename).resolve()
    if path.parent != _safe_listing_dir(listing_id) or not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)


@router.get("/vintage-evidence")
def vintage_evidence_page() -> HTMLResponse:
    return HTMLResponse(_PAGE)


_PAGE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vintage Evidence — Shirtfaced Studio</title>
<style>
:root{font-family:Inter,system-ui,sans-serif;color:#111;background:#f5f3ee}*{box-sizing:border-box}
body{margin:0}.shell{max-width:1500px;margin:auto;padding:24px}.top{position:sticky;top:0;z-index:4;background:#f5f3eef2;backdrop-filter:blur(10px);padding:16px 0 12px;border-bottom:1px solid #ccc}
h1{margin:0;font-size:30px}.sub{color:#666;margin:4px 0 12px}.stats{display:flex;gap:16px;flex-wrap:wrap;font-size:13px}.controls{display:grid;grid-template-columns:2fr repeat(3,1fr);gap:8px;margin-top:14px}
input,select{width:100%;padding:11px 12px;border:1px solid #bbb;border-radius:10px;background:white}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px;padding-top:20px}.card{background:white;border:1px solid #d8d5ce;border-radius:14px;overflow:hidden;box-shadow:0 1px 3px #0000000d}.hero{aspect-ratio:1/1;background:#e8e5de;display:grid;place-items:center;overflow:hidden}.hero img{width:100%;height:100%;object-fit:contain}.meta{padding:12px}.brand{font-weight:800;font-size:13px;text-transform:uppercase}.title{font-size:14px;line-height:1.3;margin:6px 0;min-height:36px}.chips{display:flex;gap:6px;flex-wrap:wrap}.chip{font-size:11px;padding:4px 7px;border-radius:999px;background:#efede7}.foot{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-top:10px;font-size:12px}.foot a{color:inherit}.thumbs{display:flex;gap:5px;overflow-x:auto;padding:0 12px 12px}.thumbs img{width:54px;height:54px;object-fit:cover;border-radius:7px;border:1px solid #ddd;cursor:pointer}
.empty{padding:40px;text-align:center;color:#777}@media(max-width:700px){.shell{padding:14px}.controls{grid-template-columns:1fr 1fr}.controls input{grid-column:1/-1}}
</style>
</head>
<body><div class="shell"><div class="top"><h1>Vintage Evidence</h1><div class="sub">Sold surf / skate / street references with retained listing photography.</div><div class="stats" id="stats"></div><div class="controls"><input id="q" placeholder="Search brand, title, tags…"><select id="brand"><option value="">All brands</option></select><select id="era"><option value="">All eras</option></select><select id="trad"><option value="">All traditions</option></select></div></div><main id="grid" class="grid"></main></div>
<script>
let rows=[];const $=id=>document.getElementById(id);const uniq=(k)=>[...new Set(rows.map(r=>r[k]).filter(Boolean))].sort();
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function fill(id,key){for(const v of uniq(key)){const o=document.createElement('option');o.value=v;o.textContent=v;$(id).append(o)}}
function render(){const q=$('q').value.toLowerCase(),b=$('brand').value,e=$('era').value,t=$('trad').value;const f=rows.filter(r=>{const hay=[r.brand,r.title,r.era_claim,r.tradition,...(r.graphic_tags||[])].join(' ').toLowerCase();return(!q||hay.includes(q))&&(!b||r.brand===b)&&(!e||r.era_claim===e)&&(!t||r.tradition===t)});$('grid').innerHTML=f.length?f.map((r,i)=>{const imgs=r.images||[];const hero=imgs[0]?`<img id="hero-${i}" src="${esc(imgs[0])}" loading="lazy">`:'<span>No image</span>';const thumbs=imgs.slice(0,12).map(u=>`<img src="${esc(u)}" loading="lazy" onclick="document.getElementById('hero-${i}').src=this.src">`).join('');return`<article class="card"><div class="hero">${hero}</div><div class="meta"><div class="brand">${esc(r.brand||'Unknown')}</div><div class="title">${esc(r.title||'Untitled')}</div><div class="chips"><span class="chip">${esc(r.era_claim||'')}</span><span class="chip">${esc(r.tradition||'')}</span><span class="chip">${imgs.length} images</span></div><div class="foot"><span>${esc(r.currency||'')} ${esc(r.sold_price??r.listed_price??'')}</span><a href="${esc(r.source_url||'#')}" target="_blank" rel="noreferrer">eBay ↗</a></div></div>${thumbs?`<div class="thumbs">${thumbs}</div>`:''}</article>`}).join(''):'<div class="empty">No matching records.</div>'}
fetch('/api/vintage-evidence').then(r=>r.json()).then(d=>{rows=d.records||[];const m=d.manifest||{};$('stats').innerHTML=`<span><b>${rows.length}</b> cached listings</span><span><b>${m.listings_with_images??0}</b> with images</span><span><b>${m.image_count??0}</b> image files</span><span><b>${m.failed??0}</b> failed</span>`;fill('brand','brand');fill('era','era_claim');fill('trad','tradition');render()}).catch(()=>{$('grid').innerHTML='<div class="empty">Evidence cache unavailable.</div>'});
for(const id of ['q','brand','era','trad'])$(id).addEventListener(id==='q'?'input':'change',render);
</script></body></html>'''
