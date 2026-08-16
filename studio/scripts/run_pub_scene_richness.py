#!/usr/bin/env python3
"""Generate one scene-first Nano Pro pub master from the persistent GPT composition reference."""
from __future__ import annotations
import hashlib, io, json, sys
from datetime import UTC, datetime
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.adapters.reference_images import ReferenceImage
from app.config import get_settings

PROMPT="""IMAGE 1 IS THE LOCKED MASTER EVENT REFERENCE. Edit/reframe IMAGE 1 into a vertical 9:16 documentary photograph. Do not redesign the event and do not turn the central man into a hero portrait.

PRIMARY GOAL: preserve the WHOLE ROOM GOING OFF. The central man's pool-table incident is only one event inside an already-chaotic Friday-night Australian pub. The scene must have distributed energy and multiple simultaneous stories that would still exist if the central man were removed.

PRESERVE FROM IMAGE 1:
- packed crowd density and layered depth from bodies close to camera through the pool table to the rear of the room;
- people colliding, leaning, shouting, laughing, moving and looking in different directions independently;
- foreground heads, shoulders and bodies blocking inconvenient parts of the frame;
- multiple independent social clusters and secondary/tertiary actions unrelated to the central man;
- the sense that the photographer is trapped inside the crowd and did not compose a clean shot;
- dark ceiling, deep black areas, localized practical light, red back-bar spill, uneven face exposure, motion/exposure imperfection;
- pool table, wooden stool and full beer as incidental real objects, not display props;
- central man's unstable/asymmetric body geometry, another person physically steadying him, cue horizontal overhead in both fists, head back, eyes shut, mouth open;
- accidental cropping, occlusion, competing focal events and visual mess.

ATTENTION RULES — CRITICAL:
- do NOT create clean negative space around the central man;
- do NOT arrange people in a semicircle around him;
- do NOT make the crowd look at him, sing to him, cheer for him or treat him as the performer;
- do NOT make him the brightest, sharpest or most isolated person by design;
- do NOT simplify the room to make his pose easier to read;
- do NOT remove foreground obstruction or independent crowd action;
- the real band/performance is elsewhere in the room; the central man is an audience member/punter singing along, not the singer or leader.

VERTICAL REFRAME:
Extend/reframe naturally to 9:16 while keeping the frame FULL of event information. Do not create a large empty ceiling or empty floor merely to reach portrait format. Use additional overlapping crowd bodies, room texture and depth where extension is required. Keep the essential pool-table incident within a central 4:5-safe region but do not centre or spotlight it unnaturally.

IDENTITY:
This pass is NOT an identity pass. Preserve the people from IMAGE 1 as they are. Do not beautify faces or spend composition authority making the central man more recognisable. Character identity will be handled surgically later only if this full-scene master passes scene-richness review.

Photographic premise: accidental handheld documentary capture in a genuinely packed pub at 11:05pm. Nobody poses. Nobody acknowledges the camera. The photograph should feel difficult to take, not designed.

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
 manifest={'scene':'pub-1105','experiment':'scene-first-richness-master-v1','generated_at':stamp,'model':model,'aspect_ratio':'9:16','image_size':'2K','composition_reference_used':True,'source_master':str(p.relative_to(ROOT)),'source_master_sha256':hashlib.sha256(raw).hexdigest(),'source_dimensions':list(dims),'source_format':fmt,'continuity_layer':'scene','attention_hierarchy':['room-going-off','accidental-crowd-photograph','multiple-simultaneous-interactions','damo-pool-table-incident','damo-identity'],'preserve':['crowd_density','distributed_independent_action','foreground_obstruction','secondary_tertiary_events','depth','lighting_distribution','camera_accident','pool_table','stool','beer','central_action_geometry'],'change':['vertical_reframe_only_where_required'],'candidate_count':1,'manual_gate':'scene_richness_review_before_identity'}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)); (out/'prompt.txt').write_text(PROMPT); print(f'RESULT_DIR={out}')
if __name__=='__main__': main()
