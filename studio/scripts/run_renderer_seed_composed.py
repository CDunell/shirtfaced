#!/usr/bin/env python3
"""One-shot Nano Banana Pro scene-first pub master pass.

Purpose: restore distributed room energy and attention balance before any further
identity refinement. The persistent GPT composition image is the locked scene
master; Damo identity is deliberately secondary in this pass.
"""
from __future__ import annotations
import hashlib, io, json, sys
from datetime import UTC, datetime
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest
from app.adapters.reference_images import ReferenceImage
from app.config import get_settings

PROMPT="""IMAGE 1 IS THE LOCKED MASTER PHOTOGRAPH AND OWNS THE WHOLE SCENE.

Edit IMAGE 1 as conservatively as possible into a native vertical 9:16 social frame. This is a SCENE-FIRST preservation pass, not a portrait, not a character showcase and not a fresh generation.

The photograph is a packed Australian pub back room already going off on a Friday night. Preserve and, where vertical extension requires invention, CONTINUE the same distributed chaos throughout the frame: overlapping bodies, foreground obstruction, people colliding, independent conversations and reactions, people facing different directions, partial faces, cropped bodies, motion, sweat, deep shadows, red bar spill, pool-table lamp, clutter and several simultaneous human events.

DAMO is the man on the pool table with the cue overhead. He is narratively important but photographically he is only ONE incident inside the room. DO NOT give him a clean halo, extra negative space, brighter key light, central-stage treatment or an audience. DO NOT arrange people around him. DO NOT make other patrons sing to him, cheer for him, watch him as a performance or synchronise around him. Some patrons may notice him; many must remain busy with unrelated Friday-night behaviour. The room's energy must still make sense if Damo were removed.

Preserve the master event facts: Damo remains on the pool table with both boots on it, cue horizontal overhead in both hands, head back, eyes shut, roaring along with the real band; the wooden pub stool and full beer remain on the table; the actual band remains a separate background event. Damo is a punter, never the singer/frontman. Damo has no tattoos.

Preserve IMAGE 1's accidental documentary qualities: inconvenient occlusion, asymmetric body geometry, physical contact, imperfect framing, uneven visibility, deep blacks, localized practical light, foreground people blocking useful information, layered depth and lack of visual cleanliness. Do not beautify, simplify, tidy, balance or make faces uniformly readable.

Vertical extension must ADD EVENT INFORMATION, not empty ceiling/headroom. Fill the 9:16 frame with believable crowd interference and layered room detail while retaining the master photograph's camera premise and visual density.

Identity is NOT the optimisation target in this pass. Do not perform a dedicated face replacement. Preserve the source man's existing appearance sufficiently for continuity, but scene richness and attention distribution have absolute priority.

Return one photorealistic 9:16 edited photograph only."""

def composition_master() -> Path:
 root=ROOT/"var/scene-references/pub-1105"
 files=[p for p in root.glob("composition-gpt.*") if p.is_file() and p.stat().st_size>0]
 if len(files)!=1: raise SystemExit(f"expected exactly one persistent GPT composition master, found {len(files)}; no provider call made")
 return files[0]

def make_ref(path:Path):
 raw=path.read_bytes()
 with Image.open(io.BytesIO(raw)) as opened:
  opened.load(); fmt=opened.format; dims=opened.size
  im=ImageOps.exif_transpose(opened).convert("RGB"); im.thumbnail((3072,3072),Image.Resampling.LANCZOS)
  buf=io.BytesIO(); im.save(buf,"JPEG",quality=98,subsampling=0); data=buf.getvalue()
 return ReferenceImage(name="locked-scene-master",data=data,mime_type="image/jpeg",locked=True),{"name":"locked-scene-master","role":"scene-truth-and-attention-hierarchy","path":str(path.relative_to(ROOT)),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"format":fmt,"dimensions":list(dims)}

def main():
 master=composition_master(); ref,meta=make_ref(master); settings=get_settings()
 if not settings.google_media_live or settings.gemini_api_key is None: raise SystemExit("Google media not live; no provider call made")
 model="gemini-3-pro-image"; stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"); out=ROOT/"var/renderer-validation/pub-1105"/stamp; out.mkdir(parents=True,exist_ok=True)
 client=GoogleImageClient(api_key=settings.gemini_api_key.get_secret_value(),model=model)
 result=client.generate(GoogleImageRequest(prompt=PROMPT,references=(ref,),aspect_ratio="9:16",image_size="2K"))
 output=out/"seed-1.jpg"; output.write_bytes(result.data)
 manifest={"scene":"pub-1105","experiment":"scene-first-distributed-chaos-reset","generated_at":stamp,"model":model,"aspect_ratio":"9:16","image_size":"2K","composition_reference_used":True,"source_master":str(master.relative_to(ROOT)),"source_master_sha256":hashlib.sha256(master.read_bytes()).hexdigest(),"candidate_count":1,"priority_hierarchy":["room-going-off","accidental-crowd-photograph","multiple-simultaneous-interactions","damo-pool-table-incident","damo-identity"],"preserve":["scene-richness","distributed-independent-action","crowd-density","occlusion","foreground-obstruction","lighting-distribution","pool-table-geometry","stool-and-beer","damo-action","band-as-separate-background-event","documentary-camera-premise"],"change":["vertical-9x16-extension-only-as-needed"],"references":[meta],"manual_gate":"scene_richness_review_required_before_identity_or_video"}; (out/"manifest.json").write_text(json.dumps(manifest,indent=2)); (out/"prompt.txt").write_text(PROMPT)
 print(f"MASTER={master}"); print(f"RESULT_DIR={out}")
if __name__=="__main__": main()
