#!/usr/bin/env python3
"""One-shot Pro edit: preserve GPT pub master and replace only central man's head identity with Damo."""
from __future__ import annotations
import hashlib, io, json, sys
from datetime import UTC, datetime
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.adapters.reference_images import ReferenceImage
from app.config import get_settings

PROMPT="""IMAGE 1 IS THE LOCKED MASTER PHOTOGRAPH. IMAGE 2 is the canonical head-and-shoulders reference for DAMO.

Perform ONE surgical edit only: replace the FACE / HEAD IDENTITY of the central man standing on the pool table in IMAGE 1 so he unmistakably matches DAMO in IMAGE 2.

Do not regenerate the scene. Do not redesign the man. Do not reinterpret the event. Keep the central man's existing body, clothing, pose, hands, arms, cue, torso, hips, legs and feet exactly as photographed in IMAGE 1. The only allowed visual changes are those necessary to make his face, hairline, hair, facial proportions and stubble match DAMO. Blend the replacement naturally into the existing head angle, expression, skin exposure, motion, lighting and grain of IMAGE 1.

EVERYTHING ELSE IS LOCKED: camera position, perspective, 9:16 crop, crowd density, every other person's identity and pose, the man physically holding Damo, foreground obstruction, occlusion, pool-table geometry, both feet positions, asymmetric stance, cue horizontal above his head in both fists, stool, full beer, band/bar geography, dark ceiling, practical lighting, red background spill, shadow depth, motion blur, photographic imperfections and uncontrolled crowd energy.

Do NOT alter body build or proportions in this pass. Do NOT use IMAGE 2 to influence clothing, pose, lighting, framing or scene geometry. Do NOT clean up the photo, brighten faces, isolate Damo, move people, fix awkward overlaps, improve composition or create a hero portrait. Do NOT add tattoos, jewellery, scars, piercings or other marks. Damo has no tattoos.

Preserve the exact head pose and expression from IMAGE 1: head back, eyes shut, mouth open, roaring along as an audience member. Change identity, not performance.

The result succeeds only if IMAGE 1 still reads as the same photograph at the same instant and the central man's head now clearly reads as canonical Damo. If any requested identity change would require changing scene geometry, preserve scene geometry instead."""

def ref(name,path,role,quality=95):
 p=ROOT/path; raw=p.read_bytes()
 with Image.open(io.BytesIO(raw)) as im:
  im.load(); fmt=im.format; dims=im.size; im=ImageOps.exif_transpose(im).convert("RGB"); im.thumbnail((2048,2048),Image.Resampling.LANCZOS); buf=io.BytesIO(); im.save(buf,"JPEG",quality=quality); data=buf.getvalue()
 return ReferenceImage(name=name,data=data,mime_type="image/jpeg",locked=True),{"name":name,"role":role,"path":path,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"format":fmt,"dimensions":list(dims)}

def main():
 scene=list((ROOT/"var/scene-references/pub-1105").glob("composition-gpt.*"))
 if len(scene)!=1: raise SystemExit(f"expected one persistent master reference; found {len(scene)}; no provider call made")
 damo_head=ROOT/"var/cast/damo/b-head-shoulders.png"
 if not damo_head.is_file(): raise SystemExit(f"missing canonical Damo head ref: {damo_head}; no provider call made")
 ordered=[
  ("gpt-master",str(scene[0].relative_to(ROOT)),"locked-master-image"),
  ("damo-head",str(damo_head.relative_to(ROOT)),"head-identity-only"),
 ]
 prepared=[ref(*x) for x in ordered]; refs=tuple(x[0] for x in prepared); meta=[x[1] for x in prepared]
 settings=get_settings()
 if not settings.google_media_live or settings.gemini_api_key is None: raise SystemExit("Google media not live; no provider call made")
 model="gemini-3-pro-image"; stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"); out=ROOT/"var/renderer-validation/pub-1105"/stamp; out.mkdir(parents=True,exist_ok=True)
 manifest={"scene":"pub-1105","experiment":"gpt-master-plus-damo-head-only","generated_at":stamp,"model":model,"aspect_ratio":"9:16","image_size":"2K","composition_reference_used":True,"master_reference_only":False,"identity_edit":"damo-head-only","preserve":["composition","camera","lighting","crowd","pose","body","wardrobe","props","geography"],"change":["damo_head_identity"],"references":meta,"candidate_count":1,"manual_gate":"seed_review_required_before_video"}; (out/"manifest.json").write_text(json.dumps(manifest,indent=2)); (out/"prompt.txt").write_text(PROMPT)
 client=GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(),model=model); result=client.generate(GoogleImageRequest(prompt=PROMPT,references=refs,aspect_ratio="9:16",image_size="2K")); suffix=".png" if result.mime_type=="image/png" else ".jpg"; (out/("seed-1"+suffix)).write_bytes(result.data); print(f"RESULT_DIR={out}")
if __name__=="__main__": main()
