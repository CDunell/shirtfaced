#!/usr/bin/env python3
"""One-shot Pro preservation test using only the persistent GPT pub master image."""
from __future__ import annotations
import hashlib, io, json, sys
from datetime import UTC, datetime
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.adapters.reference_images import ReferenceImage
from app.config import get_settings

PROMPT="""IMAGE 1 IS THE MASTER IMAGE. This is an image-preservation/edit test, NOT a request to redesign, reinterpret, improve, clean up or recompose the photograph.

Reproduce IMAGE 1 as faithfully as possible as a native 9:16 vertical output. Preserve the photographed event itself: camera position, perspective, depth, crowd density, crowd overlap, physical contact between people, body poses, asymmetry, pool-table geometry, cue position, stool position, beer position, stage/bar geography, lighting distribution, deep shadows, foreground obstruction, awkward framing, motion blur, facial expressions, uncontrolled energy and accidental documentary character.

Do NOT arrange the crowd. Do NOT isolate or beautify the central man. Do NOT make the photograph cleaner. Do NOT brighten the room. Do NOT turn anyone into a performer. Do NOT alter wardrobe, identities, body geometry or object placement. Do NOT add or remove people, props, tattoos, signage or lights.

The ugly photographic properties are intentional and locked: foreground bodies obscure meaningful parts of the scene; people collide and grab one another; visibility is uneven; the ceiling is dark; practical lighting falls off hard; the frame feels caught rather than composed.

ONLY PERMITTED CHANGE: adapt the canvas from the source aspect ratio into a native 9:16 portrait social frame by extending/cropping peripheral crowd/environment as necessary. Keep the central event, people, pool table, cue, stool and beer at the same relative scale and spatial relationships. Do not invent a new central composition to fill the vertical frame.

This test succeeds only if a viewer would describe the result as the same photograph/event with the same visual chaos, not a newly generated interpretation of it."""

def ref(name,path,role):
 p=ROOT/path; raw=p.read_bytes()
 with Image.open(io.BytesIO(raw)) as im:
  im.load(); fmt=im.format; dims=im.size; im=ImageOps.exif_transpose(im).convert("RGB"); im.thumbnail((2048,2048),Image.Resampling.LANCZOS); buf=io.BytesIO(); im.save(buf,"JPEG",quality=95); data=buf.getvalue()
 return ReferenceImage(name=name,data=data,mime_type="image/jpeg",locked=True),{"name":name,"role":role,"path":path,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"format":fmt,"dimensions":list(dims)}

def main():
 scene=list((ROOT/"var/scene-references/pub-1105").glob("composition-gpt.*"))
 if len(scene)!=1: raise SystemExit(f"expected one persistent master reference; found {len(scene)}; no provider call made")
 master,meta=ref("gpt-master",str(scene[0].relative_to(ROOT)),"locked-master-image")
 settings=get_settings()
 if not settings.google_media_live or settings.gemini_api_key is None: raise SystemExit("Google media not live; no provider call made")
 model="gemini-3-pro-image"; stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"); out=ROOT/"var/renderer-validation/pub-1105"/stamp; out.mkdir(parents=True,exist_ok=True)
 manifest={"scene":"pub-1105","experiment":"gpt-master-only-preservation","generated_at":stamp,"model":model,"aspect_ratio":"9:16","image_size":"2K","composition_reference_used":True,"master_reference_only":True,"references":[meta],"candidate_count":1,"manual_gate":"seed_review_required_before_video"}; (out/"manifest.json").write_text(json.dumps(manifest,indent=2)); (out/"prompt.txt").write_text(PROMPT)
 client=GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(),model=model); result=client.generate(GoogleImageRequest(prompt=PROMPT,references=(master,),aspect_ratio="9:16",image_size="2K")); suffix=".png" if result.mime_type=="image/png" else ".jpg"; (out/("seed-1"+suffix)).write_bytes(result.data); print(f"RESULT_DIR={out}")
if __name__=="__main__": main()
