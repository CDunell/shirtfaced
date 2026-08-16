#!/usr/bin/env python3
"""One-shot Pro edit: preserve GPT pub master and replace central man's head/neck identity with Damo."""
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

Perform ONE surgical replacement: replace the ENTIRE HEAD AND VISIBLE NECK REGION of the central man standing on the pool table in IMAGE 1 so that he unmistakably IS DAMO from IMAGE 2.

IDENTITY HAS FULL AUTHORITY INSIDE THE HEAD/NECK REGION. Match Damo's skull/face shape, forehead, eyebrows, eyes, nose, cheekbones, jaw, mouth, ears, hairline, hair texture, stubble pattern and neck appearance from IMAGE 2. Do not merely nudge the existing face toward Damo. Replace the original man's identity decisively while preserving the photographed head angle and expression.

The permitted edit boundary is from the shirt collar upward, plus the visible neck required for a natural blend. EVERYTHING BELOW THE COLLAR IS LOCKED PIXEL-RELATIONSHIP-WISE: shoulders, torso, body build, clothing, arms, hands, cue, hips, legs and feet remain the same geometry and same photographed event as IMAGE 1.

Preserve the performance exactly: head stays thrown back at the same angle, eyes stay shut, mouth stays open roaring the chorus. Damo is an audience member on the pool table, not the band singer.

EVERYTHING OUTSIDE THE HEAD/NECK REGION IS LOCKED: camera position, perspective, 9:16 framing, crowd density, every other person's identity and pose, the man physically holding Damo, foreground obstruction, occlusion, pool-table geometry, both feet positions, asymmetric stance, cue horizontal above his head in both fists, stool, full beer, band/bar geography, dark ceiling, practical lighting, red background spill, shadow depth, motion blur, photographic imperfections and uncontrolled crowd energy.

Do NOT regenerate the crowd. Do NOT change Damo's body or clothing in this pass. Do NOT brighten or clean up the photograph. Do NOT isolate him, move people, repair awkward overlaps, improve composition or create a hero portrait. Do NOT add tattoos, jewellery, scars, piercings or other identity marks. Damo has no tattoos.

IMPORTANT: preserving the original central man's facial structure is a FAILURE. The original face must be replaced by canonical Damo while the scene around the head remains unchanged. Preserve scene geometry outside the edit boundary; inside the head/neck boundary, prioritize Damo identity.

The result succeeds only if this still looks like the same exact chaotic photograph and a viewer familiar with IMAGE 2 immediately recognises the central man as Damo."""

def ref(name,path,role,quality=98):
 p=ROOT/path; raw=p.read_bytes()
 with Image.open(io.BytesIO(raw)) as im:
  im.load(); fmt=im.format; dims=im.size; im=ImageOps.exif_transpose(im).convert("RGB"); im.thumbnail((2048,2048),Image.Resampling.LANCZOS); buf=io.BytesIO(); im.save(buf,"JPEG",quality=quality,subsampling=0); data=buf.getvalue()
 return ReferenceImage(name=name,data=data,mime_type="image/jpeg",locked=True),{"name":name,"role":role,"path":path,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"format":fmt,"dimensions":list(dims)}

def main():
 scene=list((ROOT/"var/scene-references/pub-1105").glob("composition-gpt.*"))
 if len(scene)!=1: raise SystemExit(f"expected one persistent master reference; found {len(scene)}; no provider call made")
 damo_head=ROOT/"var/cast/damo/b-head-shoulders.png"
 if not damo_head.is_file(): raise SystemExit(f"missing canonical Damo head ref: {damo_head}; no provider call made")
 ordered=[
  ("gpt-master",str(scene[0].relative_to(ROOT)),"locked-master-image"),
  ("damo-head",str(damo_head.relative_to(ROOT)),"authoritative-head-neck-identity"),
 ]
 prepared=[ref(*x) for x in ordered]; refs=tuple(x[0] for x in prepared); meta=[x[1] for x in prepared]
 settings=get_settings()
 if not settings.google_media_live or settings.gemini_api_key is None: raise SystemExit("Google media not live; no provider call made")
 model="gemini-3-pro-image"; stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"); out=ROOT/"var/renderer-validation/pub-1105"/stamp; out.mkdir(parents=True,exist_ok=True)
 manifest={"scene":"pub-1105","experiment":"gpt-master-plus-damo-head-neck-authoritative","generated_at":stamp,"model":model,"aspect_ratio":"9:16","image_size":"2K","composition_reference_used":True,"master_reference_only":False,"identity_edit":"damo-head-neck-authoritative","preserve":["composition","camera","lighting","crowd","pose_below_collar","body","wardrobe","props","geography"],"change":["damo_head_neck_identity"],"references":meta,"candidate_count":1,"manual_gate":"seed_review_required_before_video"}; (out/"manifest.json").write_text(json.dumps(manifest,indent=2)); (out/"prompt.txt").write_text(PROMPT)
 client=GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(),model=model); result=client.generate(GoogleImageRequest(prompt=PROMPT,references=refs,aspect_ratio="9:16",image_size="2K")); suffix=".png" if result.mime_type=="image/png" else ".jpg"; (out/("seed-1"+suffix)).write_bytes(result.data); print(f"RESULT_DIR={out}")
if __name__=="__main__": main()
