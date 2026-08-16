#!/usr/bin/env python3
"""One-shot Pro still using the persistent pub composition reference plus cast refs."""
from __future__ import annotations
import hashlib, io, json, sys
from datetime import UTC, datetime
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.adapters.reference_images import ReferenceImage
from app.config import get_settings

PROMPT="""Create a new photorealistic native 9:16 vertical phone photograph of this pub instant. Image 1 controls composition, crowd energy, physical interaction, occlusion, depth, accidental camera placement and dark practical-light atmosphere only. Do not copy identities, tattoos, signage or wardrobe from image 1. Recompose its uncontrolled documentary energy vertically.

Images 2 and 3 are Damo, full body then face. They override image 1 for his identity and build. Images 4 and 5 are Brock. Images 6 and 7 are Emma. Preserve those identities. Damo has no tattoos, jewellery, piercings or invented marks.

Damo is an audience member physically standing on top of the pool table. BOTH boots contact the green playing surface itself. Neither boot touches the stool, rail, floor or another person. His stance is unstable and asymmetric: one knee bent, torso twisted, hips displaced, with a mate allowed to grab his waist or leg to steady him. Damo holds ONE pool cue HORIZONTAL ABOVE HIS HEAD in BOTH FISTS with both arms raised. The cue never drops to chest height and never becomes a microphone. Head back, eyes shut, mouth open, roaring along toward a SEPARATE singer and four-piece band on a distant low stage. Damo never becomes the performer.

A plain wooden pub stool stands independently on the pool table, separated from Damo's feet. One full pint of beer is on top of the stool. Do not put a foot on the stool and do not move the beer.

Crowd physics should follow image 1: foreground heads, shoulders, arms and backs obscure meaningful parts of the frame; people collide, lean, duck, grab friends, squeeze past and react independently. No semicircle, no evenly spaced faces and no protected hero silhouette. Brock and Emma are secondary crowd members.

It is 11:05pm in a genuinely dark Australian pub back room. General house lights are off. Black ceiling, crushed shadows, localized pool-table pendant light and localized red or coloured stage spill. Most background patrons are silhouettes or partial faces. No HDR or broad ambient fill.

Camera is an accidental one-handed phone capture from inside the crowd, 24mm equivalent, portrait 9:16. Foreground bodies may obstruct the action. Slight motion blur, close distortion and awkward framing are desirable. Nobody notices the camera. Damo wears a black cap, faded olive tee, dark denim and worn trainers, all plain. The result must feel like an uncontrolled real event, not a posed hero, singer or advertising photograph."""

CAST=[("damo-full","var/cast/damo/a-full-length.png"),("damo-head","var/cast/damo/b-head-shoulders.png"),("brock-full","var/cast/brock/a-full-length.png"),("brock-head","var/cast/brock/b-head-shoulders.png"),("emma-head","var/cast/emma/b-head-shoulders.png"),("emma-full","var/cast/emma/a-full-length.png")]

def ref(name,path,role):
 p=ROOT/path; raw=p.read_bytes()
 with Image.open(io.BytesIO(raw)) as im:
  im.load(); fmt=im.format; dims=im.size; im=ImageOps.exif_transpose(im).convert("RGB"); im.thumbnail((2048,2048),Image.Resampling.LANCZOS); buf=io.BytesIO(); im.save(buf,"JPEG",quality=92); data=buf.getvalue()
 return ReferenceImage(name=name,data=data,mime_type="image/jpeg",locked=True),{"name":name,"role":role,"path":path,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"format":fmt,"dimensions":list(dims)}

def main():
 scene=list((ROOT/"var/scene-references/pub-1105").glob("composition-gpt.*"))
 if len(scene)!=1: raise SystemExit(f"expected one persistent composition reference; found {len(scene)}; no provider call made")
 ordered=[("gpt-composition",str(scene[0].relative_to(ROOT)),"composition-energy-camera")]+[(n,p,"canonical-identity") for n,p in CAST]
 prepared=[ref(*x) for x in ordered]; refs=tuple(x[0] for x in prepared); meta=[x[1] for x in prepared]
 settings=get_settings()
 if not settings.google_media_live or settings.gemini_api_key is None: raise SystemExit("Google media not live; no provider call made")
 model="gemini-3-pro-image"; stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"); out=ROOT/"var/renderer-validation/pub-1105"/stamp; out.mkdir(parents=True,exist_ok=True)
 manifest={"scene":"pub-1105","generated_at":stamp,"model":model,"aspect_ratio":"9:16","image_size":"2K","composition_reference_used":True,"references":meta,"candidate_count":1,"manual_gate":"seed_review_required_before_video"}; (out/"manifest.json").write_text(json.dumps(manifest,indent=2)); (out/"prompt.txt").write_text(PROMPT)
 client=GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(),model=model); result=client.generate(GoogleImageRequest(prompt=PROMPT,references=refs,aspect_ratio="9:16",image_size="2K")); suffix=".png" if result.mime_type=="image/png" else ".jpg"; (out/("seed-1"+suffix)).write_bytes(result.data); print(f"RESULT_DIR={out}")
if __name__=="__main__": main()
