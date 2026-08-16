#!/usr/bin/env python3
"""One-shot Pro localized crop edit: refine Damo identity, then composite back into the preserved pub master."""
from __future__ import annotations
import hashlib, io, json, sys
from datetime import UTC, datetime
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.adapters.reference_images import ReferenceImage
from app.config import get_settings

PROMPT="""IMAGE 1 is a LOCAL CROP from the current working photograph around the central man's head, neck and upper torso. IMAGE 2 is the canonical head-and-shoulders identity reference for DAMO.

Edit IMAGE 1, do not create a new photograph.

Replace the central man's entire HEAD AND VISIBLE NECK identity so he unmistakably matches DAMO in IMAGE 2. IMAGE 2 has full authority for skull shape, face proportions, brow, eyes, nose, cheekbones, jaw, mouth, ears, hairline, hair texture, stubble and visible neck identity.

Preserve the exact pose and expression from IMAGE 1: same head-back angle, eyes shut, mouth open roaring the chorus. Preserve both raised arms where they enter the crop, the same shirt, shoulder positions, lighting, red/black background, grain, exposure and motion character.

DO NOT change the crop composition. DO NOT move the shoulders or arms. DO NOT alter the shirt. DO NOT clean up or beautify the image. DO NOT brighten the face beyond the existing practical lighting. DO NOT create a portrait look. DO NOT add tattoos, jewellery, scars or piercings. Damo has no tattoos.

The source man's identity must not survive. Do not average identities. The edited head/neck must clearly be the same person as IMAGE 2 while everything else in IMAGE 1 remains the same photographed moment.

Return the edited crop only, preserving its 4:5 composition."""

def ref_from_image(name,im,role,quality=98):
 buf=io.BytesIO(); im.convert("RGB").save(buf,"JPEG",quality=quality,subsampling=0); data=buf.getvalue()
 return ReferenceImage(name=name,data=data,mime_type="image/jpeg",locked=True),{"name":name,"role":role,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"dimensions":list(im.size),"format":"JPEG"}

def ref_from_path(name,path,role,quality=98):
 p=ROOT/path; raw=p.read_bytes()
 with Image.open(io.BytesIO(raw)) as im:
  im.load(); fmt=im.format; dims=im.size; im=ImageOps.exif_transpose(im).convert("RGB"); im.thumbnail((2048,2048),Image.Resampling.LANCZOS); buf=io.BytesIO(); im.save(buf,"JPEG",quality=quality,subsampling=0); data=buf.getvalue()
 return ReferenceImage(name=name,data=data,mime_type="image/jpeg",locked=True),{"name":name,"role":role,"path":path,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"format":fmt,"dimensions":list(dims)}

def latest_working_master() -> Path:
 root=ROOT/"var/renderer-validation/pub-1105"; candidates=[]
 accepted_experiments={"damo-head-neck-iterative-refinement","gpt-master-plus-damo-head-neck-authoritative"}
 for manifest in root.glob("*/manifest.json"):
  try: data=json.loads(manifest.read_text())
  except Exception: continue
  if data.get("experiment") not in accepted_experiments: continue
  for seed in manifest.parent.glob("seed-1.*"):
   if seed.is_file() and seed.stat().st_size>0: candidates.append((seed.stat().st_mtime,seed))
 if not candidates: raise SystemExit("no preserved Damo working master found; no provider call made")
 return max(candidates,key=lambda x:x[0])[1]

def main():
 master_path=latest_working_master(); damo_head=ROOT/"var/cast/damo/b-head-shoulders.png"
 if not damo_head.is_file(): raise SystemExit(f"missing canonical Damo head ref: {damo_head}; no provider call made")
 with Image.open(master_path) as opened:
  opened.load(); master=ImageOps.exif_transpose(opened).convert("RGB")
 if master.size != (1536,2752): raise SystemExit(f"unexpected working master dimensions {master.size}; no provider call made")
 # Tight 4:5 edit window around Damo's head/neck/upper torso. Everything outside remains byte-derived from the working master.
 crop_box=(320,160,960,960); source_crop=master.crop(crop_box)
 crop_ref,crop_meta=ref_from_image("localized-master-crop",source_crop,"locked-local-edit-master")
 head_ref,head_meta=ref_from_path("damo-head",str(damo_head.relative_to(ROOT)),"authoritative-head-neck-identity")
 settings=get_settings()
 if not settings.google_media_live or settings.gemini_api_key is None: raise SystemExit("Google media not live; no provider call made")
 model="gemini-3-pro-image"; stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"); out=ROOT/"var/renderer-validation/pub-1105"/stamp; out.mkdir(parents=True,exist_ok=True)
 client=GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(),model=model)
 result=client.generate(GoogleImageRequest(prompt=PROMPT,references=(crop_ref,head_ref),aspect_ratio="4:5",image_size="2K"))
 with Image.open(io.BytesIO(result.data)) as edited_opened:
  edited_opened.load(); edited=ImageOps.exif_transpose(edited_opened).convert("RGB").resize(source_crop.size,Image.Resampling.LANCZOS)
 # Feathered local composite prevents the model from touching the wider event while allowing the head/neck edit to blend naturally.
 mask=Image.new("L",source_crop.size,0)
 inner=Image.new("L",(520,680),255); inner=inner.filter(ImageFilter.GaussianBlur(28)); mask.paste(inner,(60,60))
 composite_crop=Image.composite(edited,source_crop,mask)
 final=master.copy(); final.paste(composite_crop,(crop_box[0],crop_box[1]))
 output_path=out/"seed-1.jpg"; final.save(output_path,"JPEG",quality=96,subsampling=0)
 manifest={"scene":"pub-1105","experiment":"damo-localized-crop-identity-edit","generated_at":stamp,"model":model,"aspect_ratio":"9:16-final / 4:5-edit-crop","image_size":"2K-provider-crop","source_master":str(master_path.relative_to(ROOT)),"source_master_sha256":hashlib.sha256(master_path.read_bytes()).hexdigest(),"crop_box":list(crop_box),"crop_dimensions":list(source_crop.size),"preserve":["all_pixels_outside_local_crop","scene_geometry","camera","crowd","body_below_upper_torso","props","lighting_distribution"],"change":["damo_head_neck_identity_localized"],"references":[crop_meta,head_meta],"candidate_count":1,"manual_gate":"seed_review_required_before_video"}; (out/"manifest.json").write_text(json.dumps(manifest,indent=2)); (out/"prompt.txt").write_text(PROMPT)
 print(f"MASTER={master_path}"); print(f"RESULT_DIR={out}")
if __name__=="__main__": main()
