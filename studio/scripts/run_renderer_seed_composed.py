#!/usr/bin/env python3
"""One-shot Pro edit: preserve GPT pub master and replace only central man's identity with Damo."""
from __future__ import annotations
import hashlib, io, json, sys
from datetime import UTC, datetime
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.adapters.reference_images import ReferenceImage
from app.config import get_settings

PROMPT="""IMAGE 1 IS THE LOCKED MASTER IMAGE. This is a surgical identity edit, NOT a new scene generation.

Images 2 and 3 are the same person: DAMO. Image 2 is Damo full length and controls body/build/proportions. Image 3 is Damo head/shoulders and controls face, hair, stubble and identity. Replace ONLY the central man standing on the pool table in IMAGE 1 with canonical Damo from Images 2 and 3.

Everything else in IMAGE 1 is locked and must remain the same photographed event. Preserve camera position, perspective, framing, crop logic, crowd density, every body pose around Damo, physical contact, the man holding/steadying him, foreground heads and shoulders, occlusion, pool-table geometry, cue geometry and exact overhead position, stool position, full beer position, band/bar geography, lighting distribution, deep shadows, red stage/bar spill, motion blur, accidental phone-camera character and uncontrolled energy.

Do NOT rearrange the crowd. Do NOT clean up the photograph. Do NOT improve composition. Do NOT isolate Damo. Do NOT brighten the room. Do NOT alter the pose. Do NOT alter wardrobe except where required to make the central man recognisably Damo while keeping the same clothing category and fit. Do NOT move his arms, hands, cue, torso, hips, legs or feet. Do NOT change where other people touch him. Do NOT add tattoos, jewellery, scars, piercings or other marks. Damo has no tattoos.

The central man's pose is LOCKED from IMAGE 1: both feet stay where they are on the pool table; one knee remains bent; torso remains twisted; another man remains physically holding him; cue remains horizontal above his head in both hands; head stays back, eyes shut, mouth open. He is a punter singing along, not the band singer.

Identity replacement priority: make the central man's FACE, HAIR, STUBBLE, BUILD and BODY PROPORTIONS match Damo from Images 2 and 3 while preserving the exact event geometry from IMAGE 1. If identity and scene geometry conflict, preserve scene geometry and change only facial/identity characteristics necessary to make him Damo.

The result succeeds only if it looks like IMAGE 1 itself was edited so that the central man was always Damo. A viewer should not perceive a regenerated crowd or newly composed photograph."""

def ref(name,path,role,quality=95):
 p=ROOT/path; raw=p.read_bytes()
 with Image.open(io.BytesIO(raw)) as im:
  im.load(); fmt=im.format; dims=im.size; im=ImageOps.exif_transpose(im).convert("RGB"); im.thumbnail((2048,2048),Image.Resampling.LANCZOS); buf=io.BytesIO(); im.save(buf,"JPEG",quality=quality); data=buf.getvalue()
 return ReferenceImage(name=name,data=data,mime_type="image/jpeg",locked=True),{"name":name,"role":role,"path":path,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"format":fmt,"dimensions":list(dims)}

def main():
 scene=list((ROOT/"var/scene-references/pub-1105").glob("composition-gpt.*"))
 if len(scene)!=1: raise SystemExit(f"expected one persistent master reference; found {len(scene)}; no provider call made")
 damo_full=ROOT/"var/cast/damo/a-full-length.png"; damo_head=ROOT/"var/cast/damo/b-head-shoulders.png"
 missing=[str(p) for p in (damo_full,damo_head) if not p.is_file()]
 if missing: raise SystemExit("missing canonical Damo refs; no provider call made: "+", ".join(missing))
 ordered=[
  ("gpt-master",str(scene[0].relative_to(ROOT)),"locked-master-image"),
  ("damo-full",str(damo_full.relative_to(ROOT)),"identity-body-only"),
  ("damo-head",str(damo_head.relative_to(ROOT)),"identity-face-only"),
 ]
 prepared=[ref(*x) for x in ordered]; refs=tuple(x[0] for x in prepared); meta=[x[1] for x in prepared]
 settings=get_settings()
 if not settings.google_media_live or settings.gemini_api_key is None: raise SystemExit("Google media not live; no provider call made")
 model="gemini-3-pro-image"; stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"); out=ROOT/"var/renderer-validation/pub-1105"/stamp; out.mkdir(parents=True,exist_ok=True)
 manifest={"scene":"pub-1105","experiment":"gpt-master-plus-damo-identity-only","generated_at":stamp,"model":model,"aspect_ratio":"9:16","image_size":"2K","composition_reference_used":True,"master_reference_only":False,"identity_edit":"damo-only","references":meta,"candidate_count":1,"manual_gate":"seed_review_required_before_video"}; (out/"manifest.json").write_text(json.dumps(manifest,indent=2)); (out/"prompt.txt").write_text(PROMPT)
 client=GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(),model=model); result=client.generate(GoogleImageRequest(prompt=PROMPT,references=refs,aspect_ratio="9:16",image_size="2K")); suffix=".png" if result.mime_type=="image/png" else ".jpg"; (out/("seed-1"+suffix)).write_bytes(result.data); print(f"RESULT_DIR={out}")
if __name__=="__main__": main()
