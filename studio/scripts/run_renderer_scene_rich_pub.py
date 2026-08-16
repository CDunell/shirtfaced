#!/usr/bin/env python3
"""One paid Nano Pro pub scene pass: scene richness first, Damo incident embedded inside it."""
from __future__ import annotations
import hashlib, io, json, sys
from datetime import UTC, datetime
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.adapters.reference_images import ReferenceImage
from app.config import get_settings

PROMPT="""IMAGE 1 is the authoritative documentary scene reference and visual hierarchy reference. IMAGE 2 is DAMO identity only.

Create a new 9:16 documentary phone photograph that preserves IMAGE 1's most important quality: THE WHOLE PUB ROOM IS ALREADY GOING OFF. Damo's pool-table incident is only one ridiculous thing happening inside a fully alive, crowded Friday-night back room. Do not build the room around Damo. Do not make him the performer, singer, leader or visual gravitational centre.

SCENE HIERARCHY, IN THIS ORDER:
1. a packed Australian pub room in uncontrolled late-night chaos;
2. accidental crowd photograph with foreground bodies obstructing the camera and several depth planes;
3. many simultaneous independent interactions unrelated to Damo;
4. Damo's pool-table incident discovered within that chaos;
5. Damo identity.

The frame must contain competing human events: people colliding, dancing, yelling to friends, turning away, squeezing past, talking, drinking, laughing, partially disappearing behind other bodies. Some people notice Damo, many do not. Nobody forms an audience around him. Nobody collectively sings to him or cheers for him. Nobody poses for the camera. The energy must still make sense if Damo were removed.

Keep the room dark like IMAGE 1: black ceiling and deep shadow, small practical pools of light, red bar spill in the rear, uneven face exposure. Preserve inconvenient foreground obstruction, cropped bodies, motion blur, awkward sightlines, sweat and photographic mess. Do not clean up the frame. Do not create protected negative space around Damo. Do not centre him neatly. Fill the vertical frame with crowd information and layered depth rather than empty headroom.

DAMO: use IMAGE 2 only for his recognisable identity: face, hair, facial proportions and stubble. He is a normal punter, no tattoos, no jewellery. His required instant: he is standing on the pool table with BOTH BOOTS on it, body unstable/asymmetric rather than heroic, cue horizontal OVERHEAD held in both fists, head back, eyes shut, roaring along with the chorus toward the actual band. A nearby mate may physically steady him. Damo is facing away from the distant stage and is not performing for the room.

The wooden pub stool remains on the pool table with a full beer. The actual band is separate and distant. Normal incidental pub signage is welcome as environmental texture only.

Use IMAGE 1 for crowd density, distributed attention, physical collisions, occlusion, darkness, camera accident and overall realism. Do not copy identities from IMAGE 1. Use IMAGE 2 for Damo identity only. Return one photorealistic 9:16 image, 2K."""

def load_ref(path:Path,name:str,role:str):
 raw=path.read_bytes()
 with Image.open(io.BytesIO(raw)) as im:
  im.load(); dims=im.size; fmt=im.format; im=ImageOps.exif_transpose(im).convert('RGB'); im.thumbnail((2048,2048),Image.Resampling.LANCZOS); b=io.BytesIO(); im.save(b,'JPEG',quality=98,subsampling=0); data=b.getvalue()
 return ReferenceImage(name=name,data=data,mime_type='image/jpeg',locked=True),{'name':name,'role':role,'path':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(raw).hexdigest(),'dimensions':list(dims),'format':fmt}

def composition_path():
 files=list((ROOT/'var/scene-references/pub-1105').glob('composition-gpt.*'))
 if len(files)!=1: raise SystemExit(f'expected one composition master, found {len(files)}; no provider call made')
 return files[0]

def main():
 scene=composition_path(); damo=ROOT/'var/cast/damo/b-head-shoulders.png'
 if not damo.is_file(): raise SystemExit('canonical Damo head missing; no provider call made')
 scene_ref,scene_meta=load_ref(scene,'scene-richness-master','authoritative-scene-hierarchy')
 damo_ref,damo_meta=load_ref(damo,'damo-head','identity-only')
 settings=get_settings()
 if not settings.google_media_live or settings.gemini_api_key is None: raise SystemExit('Google media not live; no provider call made')
 stamp=datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ'); out=ROOT/'var/renderer-validation/pub-1105'/stamp; out.mkdir(parents=True,exist_ok=True)
 model='gemini-3-pro-image'; client=GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(),model=model)
 result=client.generate(GoogleImageRequest(prompt=PROMPT,references=(scene_ref,damo_ref),aspect_ratio='9:16',image_size='2K'))
 (out/'seed-1.jpg').write_bytes(result.data)
 manifest={'scene':'pub-1105','experiment':'scene-first-richness-plus-damo-identity','generated_at':stamp,'model':model,'aspect_ratio':'9:16','image_size':'2K','composition_reference_used':True,'references':[scene_meta,damo_meta],'hierarchy':['room-going-off','accidental-crowd-photo','independent-interactions','damo-incident','damo-identity'],'hard_reject_if':['hero-centric','crowd-as-audience','scene-detail-collapse','protected-space-around-damo','insufficient-independent-action'],'candidate_count':1,'manual_gate':'scene_richness_and_identity_review_required_before_video'}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)); (out/'prompt.txt').write_text(PROMPT)
 print(f'RESULT_DIR={out}')
if __name__=='__main__': main()
