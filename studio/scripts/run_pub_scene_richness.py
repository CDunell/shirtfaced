#!/usr/bin/env python3
"""Generate one master-locked Nano Pro pub candidate from the persistent GPT scene master."""
from __future__ import annotations
import hashlib, io, json, sys
from datetime import UTC, datetime
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.adapters.reference_images import ReferenceImage
from app.config import get_settings

PROMPT="""IMAGE 1 IS THE MASTER. PRESERVE IT. DO NOT REDESIGN, REINTERPRET, RESTAGE, REGENERATE OR IMPROVE THE SCENE.

This is a MASTER-LOCKED EDIT, not a fresh generation.

The event already exists correctly in IMAGE 1. Every person is already doing their own thing. The camera merely happened to observe this part of the room. Named characters do not cause the world to arrange itself around them.

ABSOLUTE PRESERVATION CONTRACT:
- preserve every existing person and crowd position;
- preserve every existing body pose, interaction, collision, gaze direction and social cluster;
- preserve foreground obstruction, awkward crops, occlusions and all depth planes;
- preserve crowd density and attention distribution exactly;
- preserve pool table geometry and position;
- preserve the wooden pub stool and full beer exactly as incidental objects;
- preserve lighting, shadows, red practical spill, dark areas, exposure imperfections and photographic ugliness;
- preserve camera viewpoint, perspective, framing relationships and accidental documentary character;
- preserve the central man's action geometry as present in the master;
- preserve all secondary and tertiary events;
- do not add supporters, cheerers, spectators or reactions to the central man;
- do not remove, duplicate, relocate or invent people;
- do not create a semicircle, audience formation, protected silhouette, clean negative space or hero lighting;
- do not make anyone acknowledge the camera;
- do not turn the central man into a performer or organising principle.

CHANGE ONLY THIS:
Produce a vertical 9:16 output while retaining as much of the original master pixels/composition as possible. Where portrait canvas extension is unavoidable, extend only peripheral room/crowd texture in a way that is visually subordinate and does not alter the existing event. Do not reconstruct the central scene to achieve the aspect ratio. Cropping is preferable to redesigning the event. Do not duplicate or stitch any portion of the original scene.

This is NOT an identity pass. Do not change faces, wardrobe, bodies or character identity. Do not beautify or clarify anyone.

Success means the output feels like the same photograph/camera observation, merely delivered on a 9:16 canvas. If preservation conflicts with making a cleaner or more legible image, PRESERVATION WINS.

Return one 9:16 image."""

def main():
 refs=list((ROOT/'var/scene-references/pub-1105').glob('composition-gpt.*'))
 if len(refs)!=1: raise SystemExit(f'expected one persistent GPT master, found {len(refs)}; no provider call made')
 p=refs[0]; raw=p.read_bytes()
 with Image.open(io.BytesIO(raw)) as opened:
  opened.load(); dims=opened.size; fmt=opened.format; im=ImageOps.exif_transpose(opened).convert('RGB'); buf=io.BytesIO(); im.save(buf,'JPEG',quality=98,subsampling=0); data=buf.getvalue()
 ref=ReferenceImage(name='locked-whole-scene-master',data=data,mime_type='image/jpeg',locked=True)
 settings=get_settings()
 if not settings.google_media_live or settings.gemini_api_key is None: raise SystemExit('Google media not live; no provider call made')
 stamp=datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ'); out=ROOT/'var/renderer-validation/pub-1105'/stamp; out.mkdir(parents=True,exist_ok=True)
 model='gemini-3-pro-image'; client=GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(),model=model)
 result=client.generate(GoogleImageRequest(prompt=PROMPT,references=(ref,),aspect_ratio='9:16',image_size='2K'))
 suffix='.png' if result.mime_type=='image/png' else '.jpg'; output=out/('seed-1'+suffix); output.write_bytes(result.data)
 manifest={'scene':'pub-1105','experiment':'master-locked-scene-preservation-v2','generated_at':stamp,'model':model,'aspect_ratio':'9:16','image_size':'2K','composition_reference_used':True,'source_master':str(p.relative_to(ROOT)),'source_master_sha256':hashlib.sha256(raw).hexdigest(),'source_dimensions':list(dims),'source_format':fmt,'continuity_layer':'scene','preservation_contract':'master_locked','preserve':['all_existing_people','positions','poses','interactions','gazes','crowd_density','attention_distribution','foreground_obstruction','occlusion','depth','lighting','camera_viewpoint','pool_table','stool','beer','central_action_geometry','secondary_tertiary_events'],'change':['9:16_canvas_only','peripheral_extension_only_if_unavoidable'],'candidate_count':1,'manual_gate':'scene_richness_review_before_identity'}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)); (out/'prompt.txt').write_text(PROMPT); print(f'RESULT_DIR={out}')
if __name__=='__main__': main()
