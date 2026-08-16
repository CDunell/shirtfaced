# ruff: noqa: E501, RUF001
"""Deterministic virtual-camera coverage from approved scene masters.

Coverage frames are crops of existing source pixels only. This route never calls an
image or video provider and refuses to operate unless the caller supplies the exact
current source SHA256.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from PIL import Image
from pydantic import BaseModel, Field

from app.config import PROJECT_ROOT

router = APIRouter(prefix="/api/renderer", tags=["renderer"])
SCENE_REFERENCE_ROOT = PROJECT_ROOT / "var" / "scene-references"
SHOT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _master(scene_id: str) -> Path:
    root = SCENE_REFERENCE_ROOT / scene_id
    for name in ("composition-gpt.png", "composition-gpt.jpg", "composition-gpt.jpeg"):
        candidate = root / name
        if candidate.is_file():
            return candidate
    raise HTTPException(404, f"No approved composition master for {scene_id}")


class CoverageFrameRequest(BaseModel):
    scene_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    shot_name: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    x: int = Field(ge=0)
    y: int = Field(default=0, ge=0)
    height: int = Field(default=0, ge=0)


@router.get("/coverage-master/{scene_id}", include_in_schema=False)
def coverage_master(scene_id: str):
    master = _master(scene_id)
    media = "image/png" if master.suffix.lower() == ".png" else "image/jpeg"
    return FileResponse(
        master,
        media_type=media,
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@router.post("/coverage-frame")
def save_coverage_frame(request: CoverageFrameRequest):
    if not SHOT_RE.fullmatch(request.shot_name):
        raise HTTPException(400, "Invalid shot name")
    source = _master(request.scene_id)
    source_sha = _sha256(source)
    if source_sha != request.source_sha256:
        raise HTTPException(
            409,
            f"Source changed: expected {request.source_sha256}, current {source_sha}",
        )

    with Image.open(source) as image:
        image.load()
        sw, sh = image.size
        crop_h = request.height or sh
        crop_h = (crop_h // 16) * 16
        if crop_h < 16:
            raise HTTPException(400, "Coverage crop is too small")
        crop_w = crop_h * 9 // 16
        x0, y0 = request.x, request.y
        x1, y1 = x0 + crop_w, y0 + crop_h
        if x1 > sw or y1 > sh:
            raise HTTPException(
                400,
                f"Crop outside source: source={sw}x{sh}, crop=({x0},{y0})-({x1},{y1})",
            )
        crop = image.crop((x0, y0, x1, y1))

    out_dir = SCENE_REFERENCE_ROOT / request.scene_id / "coverage" / request.shot_name
    out_dir.mkdir(parents=True, exist_ok=True)
    frame = out_dir / "frame.png"
    crop.save(frame, format="PNG")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    manifest = {
        "scene": request.scene_id,
        "shot": request.shot_name,
        "generated_at": stamp,
        "operation": "original_pixels_crop_only",
        "source_path": str(source.relative_to(PROJECT_ROOT)),
        "source_sha256": source_sha,
        "source_dimensions": [sw, sh],
        "crop_box": [x0, y0, x1, y1],
        "crop_dimensions": [crop_w, crop_h],
        "aspect_ratio": "9:16",
        "frame_sha256": _sha256(frame),
        "resized": False,
        "provider_called": False,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return {
        "status": "saved",
        "frame_path": str(frame.relative_to(PROJECT_ROOT)),
        **manifest,
    }


@router.get("/coverage-tool/{scene_id}", response_class=HTMLResponse, include_in_schema=False)
def coverage_tool(scene_id: str):
    master = _master(scene_id)
    source_sha = _sha256(master)
    with Image.open(master) as image:
        sw, sh = image.size
    crop_h = (sh // 16) * 16
    crop_w = crop_h * 9 // 16
    if crop_w > sw:
        raise HTTPException(400, "Master is too narrow for a full-height 9:16 viewport")

    html = f"""<!doctype html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{scene_id} coverage</title>
<style>
body{{font-family:system-ui;background:#111;color:#eee;margin:0;padding:18px}}
main{{max-width:1100px;margin:auto}} .stage{{position:relative;display:inline-block;max-width:100%;touch-action:none;user-select:none}}
.stage img{{display:block;max-width:100%;height:auto}} .viewport{{position:absolute;top:0;height:100%;border:3px solid #fff;box-sizing:border-box;background:rgba(255,255,255,.06);cursor:grab}}
.controls{{display:grid;grid-template-columns:1fr auto;gap:10px;margin-top:14px}} input,button{{font:inherit;padding:12px;border-radius:8px;border:1px solid #555;background:#1c1c1c;color:#fff}} button{{font-weight:800;padding-inline:22px}} code{{word-break:break-all}} .meta{{opacity:.75;font-size:.9rem}} #status{{min-height:1.5em;margin-top:10px}}
</style></head><body><main>
<h1>9:16 virtual camera — {scene_id}</h1>
<p>Drag the white viewport across the approved master. Saving creates an original-pixel crop only. No generation, no resize.</p>
<div id="stage" class="stage"><img id="master" src="/api/renderer/coverage-master/{scene_id}?sha={source_sha}"><div id="viewport" class="viewport"></div></div>
<div class="controls"><input id="shot" value="coverage-01" pattern="[a-z0-9][a-z0-9_-]{{0,63}}" placeholder="shot name"><button id="save">Save coverage frame</button></div>
<div id="status"></div>
<p class="meta">Master {sw}×{sh} · SHA <code>{source_sha}</code> · crop {crop_w}×{crop_h}</p>
<script>
const sourceW={sw}, sourceH={sh}, cropW={crop_w}, cropH={crop_h};
const stage=document.getElementById('stage'), img=document.getElementById('master'), vp=document.getElementById('viewport'), status=document.getElementById('status');
let x=0, dragging=false, grab=0;
function metrics(){{const r=img.getBoundingClientRect(); return {{w:r.width,h:r.height,scale:r.width/sourceW}}}}
function render(){{const m=metrics(); vp.style.width=(cropW*m.scale)+'px'; vp.style.height=(cropH*m.scale)+'px'; vp.style.left=(x*m.scale)+'px'; vp.style.top='0px'}}
function clamp(v){{return Math.max(0,Math.min(sourceW-cropW,v))}}
function pointX(e){{const r=img.getBoundingClientRect(); return (e.clientX-r.left)/r.width*sourceW}}
vp.addEventListener('pointerdown',e=>{{dragging=true;vp.setPointerCapture(e.pointerId);grab=pointX(e)-x;vp.style.cursor='grabbing'}});
vp.addEventListener('pointermove',e=>{{if(!dragging)return;x=clamp(Math.round(pointX(e)-grab));render()}});
vp.addEventListener('pointerup',e=>{{dragging=false;vp.style.cursor='grab'}});
stage.addEventListener('pointerdown',e=>{{if(e.target===vp)return;const p=pointX(e);x=clamp(Math.round(p-cropW/2));render()}});
window.addEventListener('resize',render); img.addEventListener('load',render); render();
document.getElementById('save').addEventListener('click',async()=>{{
 const shot=document.getElementById('shot').value.trim(); status.textContent='Saving…';
 const res=await fetch('/api/renderer/coverage-frame',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{scene_id:'{scene_id}',shot_name:shot,source_sha256:'{source_sha}',x:x,y:0,height:cropH}})}});
 const body=await res.json(); status.textContent=res.ok ? `Saved ${{body.frame_path}} · SHA ${{body.frame_sha256}} · x=${{x}}` : (body.detail||'Save failed');
}});
</script></main></body></html>"""
    return HTMLResponse(html, headers={"Cache-Control": "no-store, max-age=0"})
