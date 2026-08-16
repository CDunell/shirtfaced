#!/usr/bin/env python3
"""One-shot Pro iterative identity refinement using the latest preserved pub master."""
from __future__ import annotations
import hashlib, io, json, sys
from datetime import UTC, datetime
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.adapters.reference_images import ReferenceImage
from app.config import get_settings

PROMPT="""IMAGE 1 IS THE CURRENT APPROVED WORKING MASTER. IMAGE 2 is the canonical head-and-shoulders identity reference for DAMO.

This is an ITERATIVE IDENTITY REFINEMENT, not a new scene generation.

The central man on the pool table is already close to Damo. Refine ONLY his entire head and visible neck so he unmistakably matches DAMO in IMAGE 2. Strengthen identity resemblance decisively: skull shape, facial proportions, brow, eyes, nose, cheeks, jaw, mouth, ears, hairline, hair texture, stubble and neck appearance should all read as the same person as IMAGE 2.

Do NOT revert toward the original source man's face. Do NOT average the two identities. IMAGE 2 is authoritative for identity inside the head/neck boundary.

Preserve the exact photographed head orientation and performance from IMAGE 1: head thrown back at the same angle, eyes shut, mouth open roaring along with the chorus. Preserve the same lighting, exposure, grain and motion character across the replacement so it remains part of the same photograph.

EVERYTHING BELOW THE COLLAR AND EVERY PIXEL-RELATIONSHIP OUTSIDE THE HEAD/NECK EDIT BOUNDARY IS LOCKED: body, clothing, pose, arms, hands, cue, hips, legs, feet, the person holding him, every other person, crowd collisions, foreground obstruction, pool table, stool, full beer, band/bar geography, camera position, 9:16 framing, dark practical lighting, red spill, deep shadows, motion blur and accidental documentary ugliness.

No new tattoos, jewellery, scars, piercings or marks. Damo has no tattoos.

Do not clean up, beautify, recompose, brighten, isolate or simplify anything. The only goal is stronger Damo identity while preserving the current working master as the same exact event.

SUCCESS TEST: compare the central man's head to IMAGE 2. He should be immediately recognisable as the same person, while IMAGE 1 remains otherwise visually unchanged."""

def ref(name,path,role,quality=98):
 p=ROOT/path; raw=p.read_bytes()
 with Image.open(io.BytesIO(raw)) as im:
  im.load(); fmt=im.format; dims=im.size; im=ImageOps.exif_transpose(im).convert("RGB"); im.thumbnail((2048,2048),Image.Resampling.LANCZOS); buf=io.BytesIO(); im.save(buf,"JPEG",quality=quality,subsampling=0); data=buf.getvalue()
 return ReferenceImage(name=name,data=data,mime_type="image/jpeg",locked=True),{"name":name,"role":role,"path":path,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"format":fmt,"dimensions":list(dims)}

def latest_working_master() -> Path:
 root=ROOT/"var/renderer-validation/pub-1105"
 candidates=[]
 for manifest in root.glob("*/manifest.json"):
  try:
   data=json.loads(manifest.read_text())
  except Exception:
   continue
  if data.get("experiment") != "gpt-master-plus-damo-head-neck-authoritative":
   continue
  for seed in manifest.parent.glob("seed-1.*"):
   if seed.is_file() and seed.stat().st_size>0:
    candidates.append((seed.stat().st_mtime,seed))
 if not candidates:
  raise SystemExit("no prior head-neck authoritative working master found; no provider call made")
 return max(candidates,key=lambda x:x[0])[1]

def main():
 master_path=latest_working_master()
 damo_head=ROOT/"var/cast/damo/b-head-shoulders.png"
 if not damo_head.is_file(): raise SystemExit(f"missing canonical Damo head ref: {damo_head}; no provider call made")
 ordered=[
  ("working-master",str(master_path.relative_to(ROOT)),"locked-working-master"),
  ("damo-head",str(damo_head.relative_to(ROOT)),"authoritative-head-neck-identity"),
 ]
 prepared=[ref(*x) for x in ordered]; refs=tuple(x[0] for x in prepared); meta=[x[1] for x in prepared]
 settings=get_settings()
 if not settings.google_media_live or settings.gemini_api_key is None: raise SystemExit("Google media not live; no provider call made")
 model="gemini-3-pro-image"; stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"); out=ROOT/"var/renderer-validation/pub-1105"/stamp; out.mkdir(parents=True,exist_ok=True)
 manifest={"scene":"pub-1105","experiment":"damo-head-neck-iterative-refinement","generated_at":stamp,"model":model,"aspect_ratio":"9:16","image_size":"2K","composition_reference_used":True,"identity_edit":"damo-head-neck-iterative-refinement","source_master":str(master_path.relative_to(ROOT)),"preserve":["everything_outside_head_neck","head_pose","expression","lighting","camera","crowd","body","wardrobe","props","geography"],"change":["damo_head_neck_identity_strength"],"references":meta,"candidate_count":1,"manual_gate":"seed_review_required_before_video"}; (out/"manifest.json").write_text(json.dumps(manifest,indent=2)); (out/"prompt.txt").write_text(PROMPT)
 client=GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(),model=model); result=client.generate(GoogleImageRequest(prompt=PROMPT,references=refs,aspect_ratio="9:16",image_size="2K")); suffix=".png" if result.mime_type=="image/png" else ".jpg"; (out/("seed-1"+suffix)).write_bytes(result.data); print(f"MASTER={master_path}"); print(f"RESULT_DIR={out}")
if __name__=="__main__": main()
