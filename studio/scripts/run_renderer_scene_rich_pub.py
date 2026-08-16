#!/usr/bin/env python3
"""One paid Nano Pro pub pass: approved master locked, Damo identity only."""
from __future__ import annotations
import hashlib, io, json, sys
from datetime import UTC, datetime
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.adapters.reference_images import ReferenceImage
from app.config import get_settings
PROMPT="""IMAGE 1 IS THE APPROVED FINAL SCENE MASTER. IMAGE 2 IS DAMO IDENTITY ONLY.

This is a SURGICAL CHARACTER CONTINUITY EDIT. Do not regenerate, reinterpret, improve, restage, reframe, extend, crop or redesign IMAGE 1.

PRESERVE IMAGE 1 PIXEL-LEVEL SCENE SEMANTICS AS CLOSELY AS POSSIBLE: every other person, face, body, pose, gaze, interaction, collision, occlusion, crop, foreground obstruction, crowd density, depth plane, pool table, cue geometry, wooden pub stool, full beer, band, signage, room architecture, lighting, shadows, exposure, camera position, lens perspective, motion blur, framing and attention distribution.

CHANGE ONLY THE MAN ALREADY STANDING ON THE POOL TABLE WITH THE CUE OVERHEAD. Make that existing man recognisably the same person as IMAGE 2: DAMO. Transfer only his facial identity, head shape, hair and natural approximately five-day beard/stubble. Keep the master man's exact head angle, eyes-shut roaring expression, body pose, arm position, hands, cue position, clothing, scale, lighting and occlusion. Do not make his face cleaner, brighter, sharper or more prominent than in IMAGE 1.

Damo has NO TATTOOS and NO JEWELLERY. If the master man has any visible tattoos or jewellery, remove them only on Damo while preserving skin lighting and texture.

DO NOT alter anyone reacting to him. DO NOT add or remove people. DO NOT create hero lighting, halo, negative space, audience formation or cleaner silhouette. DO NOT move Damo. DO NOT move the cue, stool, beer or pool table. DO NOT change the aspect ratio. The room hierarchy must remain exactly as approved.

If identity fidelity conflicts with scene preservation, SCENE PRESERVATION WINS. Return one edited photorealistic 9:16 image."""
def load_ref(path:Path,name:str,role:str):
 raw=path.read_bytes()
 with Image.open(io.BytesIO(raw)) as im:
  im.load(); dims=im.size; fmt=im.format; im=ImageOps.exif_transpose(im).convert('RGB'); im.thumbnail((3072,3072),Image.Resampling.LANCZOS); b=io.BytesIO(); im.save(b,'JPEG',quality=98,subsampling=0); data=b.getvalue()
 return ReferenceImage(name=name,data=data,mime_type='image/jpeg',locked=True),{'name':name,'role':role,'path':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(raw).hexdigest(),'dimensions':list(dims),'format':fmt}
def composition_path():
 files=[p for p in (ROOT/'var/scene-references/pub-1105').glob('composition-gpt.*') if p.is_file() and p.stat().st_size>0]
 if not files: raise SystemExit('approved composition master missing; no provider call made')
 return max(files,key=lambda p:p.stat().st_mtime_ns)
def main():
 scene=composition_path(); damo=ROOT/'var/cast/damo/b-head-shoulders.png'
 if not damo.is_file(): raise SystemExit('canonical Damo head missing; no provider call made')
 scene_ref,scene_meta=load_ref(scene,'approved-scene-master','locked-whole-scene-master'); damo_ref,damo_meta=load_ref(damo,'damo-head','identity-only')
 settings=get_settings()
 if not settings.google_media_live or settings.gemini_api_key is None: raise SystemExit('Google media not live; no provider call made')
 stamp=datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ'); out=ROOT/'var/renderer-validation/pub-1105'/stamp; out.mkdir(parents=True,exist_ok=True)
 model='gemini-3-pro-image'; client=GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(),model=model)
 result=client.generate(GoogleImageRequest(prompt=PROMPT,references=(scene_ref,damo_ref),aspect_ratio='9:16',image_size='2K'))
 (out/'seed-1.jpg').write_bytes(result.data)
 manifest={'scene':'pub-1105','experiment':'approved-master-damo-surgical-identity','generated_at':stamp,'model':model,'aspect_ratio':'9:16','image_size':'2K','references':[scene_meta,damo_meta],'preserve':['entire-approved-scene','all-non-damo-people','crowd-behaviour','attention-distribution','camera','lighting','props','damo-action-geometry'],'change':['damo-facial-identity','damo-hair','damo-five-day-stubble','remove-damo-tattoos-or-jewellery-if-present'],'candidate_count':1,'manual_gate':'scene_preservation_and_identity_review_required_before_video'}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)); (out/'prompt.txt').write_text(PROMPT); print(f'RESULT_DIR={out}')
if __name__=='__main__': main()
