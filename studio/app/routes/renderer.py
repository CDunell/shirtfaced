# ruff: noqa: E501
"""Renderer validation endpoints."""
from __future__ import annotations
import hashlib, io, os, shutil, tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from PIL import Image
from app.config import PROJECT_ROOT, get_settings
from app.services.renderer_validation import harness_manifest, scene_package
router=APIRouter(prefix="/api/renderer",tags=["renderer"])
MAX_CANONICAL_BYTES=50*1024*1024
CANONICAL_CAST_ROOT=PROJECT_ROOT/"var"/"cast"
SCENE_REFERENCE_ROOT=PROJECT_ROOT/"var"/"scene-references"
CANONICAL_SLOTS=(("damo_full","Damo — full length",Path("damo/a-full-length.png")),("damo_head","Damo — head / shoulders",Path("damo/b-head-shoulders.png")),("brock_full","Brock — full length",Path("brock/a-full-length.png")),("brock_head","Brock — head / shoulders",Path("brock/b-head-shoulders.png")),("emma_head","Emma — head / shoulders",Path("emma/b-head-shoulders.png")),("emma_full","Emma — full length",Path("emma/a-full-length.png")))
UPLOAD_FORM='''<!doctype html><html><meta name="viewport" content="width=device-width,initial-scale=1"><body><h1>World 01 canonical cast</h1><form method="post" enctype="multipart/form-data"><input required type="file" name="damo_full"><input required type="file" name="damo_head"><input required type="file" name="brock_full"><input required type="file" name="brock_head"><input required type="file" name="emma_head"><input required type="file" name="emma_full"><button>Install six</button></form></body></html>'''
SCENE_REFERENCE_FORM='''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font-family:system-ui;max-width:680px;margin:auto;padding:24px;background:#111;color:#eee}input,button{width:100%;margin:16px 0;padding:14px}button{font-weight:800}</style></head><body><h1>pub-1105 composition reference</h1><p>Upload the approved GPT composition/energy reference once. It is stored persistently and never deployed from Git.</p><form method="post" enctype="multipart/form-data"><input required type="file" name="reference" accept="image/png,image/jpeg,.png,.jpg,.jpeg"><button>Validate and install reference</button></form><p>No Gemini or Veo call occurs here.</p></body></html>'''
async def _read_image(label,upload,png_only=False):
 data=await upload.read(MAX_CANONICAL_BYTES+1)
 if not data: raise HTTPException(400,f"{label}: empty upload")
 if len(data)>MAX_CANONICAL_BYTES: raise HTTPException(413,f"{label}: exceeds 50 MB")
 try:
  with Image.open(io.BytesIO(data)) as image:
   image.load(); fmt=image.format; width,height=image.size
   if png_only and fmt!="PNG": raise HTTPException(400,f"{label}: source must be PNG")
   if fmt not in {"PNG","JPEG"}: raise HTTPException(400,f"{label}: source must be PNG/JPEG")
   if width<256 or height<256: raise HTTPException(400,f"{label}: implausibly small {width}x{height}")
 except HTTPException: raise
 except Exception as exc: raise HTTPException(400,f"{label}: unreadable/corrupt image") from exc
 return data,{"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"width":width,"height":height,"format":fmt}
@router.get("/cast-upload",response_class=HTMLResponse,include_in_schema=False)
def cast_upload_form(): return UPLOAD_FORM
@router.post("/cast-upload")
async def cast_upload(damo_full:Annotated[UploadFile,File()],damo_head:Annotated[UploadFile,File()],brock_full:Annotated[UploadFile,File()],brock_head:Annotated[UploadFile,File()],emma_head:Annotated[UploadFile,File()],emma_full:Annotated[UploadFile,File()]):
 supplied=locals(); validated={}
 for field,label,_ in CANONICAL_SLOTS: validated[field]=await _read_image(label,supplied[field],True)
 CANONICAL_CAST_ROOT.mkdir(parents=True,exist_ok=True); backup_stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"); backup_root=PROJECT_ROOT/"var"/"cast-backups"/backup_stamp; existing=[]
 with tempfile.TemporaryDirectory(dir=PROJECT_ROOT/"var",prefix="cast-stage-") as td:
  staging=Path(td)
  for field,_,rel in CANONICAL_SLOTS: p=staging/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(validated[field][0])
  existing=[rel for _,_,rel in CANONICAL_SLOTS if (CANONICAL_CAST_ROOT/rel).is_file()]
  for rel in existing:
   b=backup_root/rel;b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(CANONICAL_CAST_ROOT/rel,b)
  installed=[]
  for field,label,rel in CANONICAL_SLOTS:
   target=CANONICAL_CAST_ROOT/rel;target.parent.mkdir(parents=True,exist_ok=True);os.replace(staging/rel,target);installed.append({"slot":field,"label":label,"path":str(target.relative_to(PROJECT_ROOT)),**validated[field][1]})
 return {"status":"installed","count":6,"canonical_root":"var/cast","backup":str(backup_root.relative_to(PROJECT_ROOT)) if existing else None,"files":installed,"provider_called":False}
@router.get("/scene-reference-upload",response_class=HTMLResponse,include_in_schema=False)
def scene_reference_upload_form(): return SCENE_REFERENCE_FORM
@router.post("/scene-reference-upload")
async def scene_reference_upload(reference:Annotated[UploadFile,File()]):
 data,meta=await _read_image("pub-1105 composition reference",reference,False); root=SCENE_REFERENCE_ROOT/"pub-1105";root.mkdir(parents=True,exist_ok=True); ext=".png" if meta["format"]=="PNG" else ".jpg"; target=root/("composition-gpt"+ext); tmp=root/(".composition-upload"+ext);tmp.write_bytes(data);os.replace(tmp,target)
 return {"status":"installed","scene":"pub-1105","role":"composition-energy-reference","path":str(target.relative_to(PROJECT_ROOT)),**meta,"provider_called":False}
@router.get("/validation")
def validation_manifest():
 s=get_settings();return harness_manifest(google_enabled=s.google_media_live,image_model=s.google_image_model,video_model=s.google_video_model)|{"billable_generation_exposed":False}
@router.get("/validation/{scene_id}")
def validation_scene(scene_id:str):
 try:return scene_package(scene_id)
 except KeyError as error:raise HTTPException(404,"Unknown validation scene") from error
