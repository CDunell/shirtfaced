#!/usr/bin/env python3
"""Run one Veo candidate from an explicitly supplied seed for direct-vs-Nano A/B."""
from __future__ import annotations
import argparse, hashlib, json, sys
from datetime import UTC, datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.adapters.google_media import GoogleVideoClient, GoogleVideoRequest
from app.config import get_settings
PROMPT="""Continue this exact first frame as accidental handheld vertical phone footage inside a packed Australian pub. The room is already going off independently. Every person continues their own pre-existing action: talking, singing toward the band, moving through the crowd, bumping friends, looking in different directions. Nobody reorganises around the man on the pool table and nobody treats him as a performer. He remains a punter inside the event, both boots planted on the pool table, cue held horizontally overhead in both fists, head back, eyes shut, roaring along with the chorus. The band remains the performance source. Preserve the stool and full beer on the table. Small natural movement only. The phone is physically inside the crowd and gets one minor bump/reframe. Preserve ugly late-night exposure, foreground obstruction, crowd density, competing focal activity and accidental framing. No cuts, no camera teleport, no slow motion, no added people, no audience formation around him, no tattoos, no hero lighting, no halo, no text."""
def main():
 p=argparse.ArgumentParser(); p.add_argument('--seed',required=True); p.add_argument('--arm',required=True,choices=['direct-master','nano-copy']); a=p.parse_args(); seed=Path(a.seed).resolve();
 if not seed.is_file(): raise SystemExit(f'missing seed: {seed}')
 data=seed.read_bytes(); s=get_settings();
 if not s.google_media_live or s.gemini_api_key is None: raise SystemExit('Google media not live')
 mime='image/png' if seed.suffix.lower()=='.png' else 'image/jpeg'; client=GoogleVideoClient(api_key=s.gemini_api_key.get_secret_value(),model=s.google_video_model,poll_seconds=s.google_video_poll_seconds,timeout_seconds=s.google_video_timeout_seconds)
 stamp=datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ'); out=ROOT/'var/renderer-validation/pub-1105'/(stamp+'-veo-ab-'+a.arm); out.mkdir(parents=True,exist_ok=True)
 r=client.generate(GoogleVideoRequest(prompt=PROMPT,first_frame=data,first_frame_mime=mime,aspect_ratio='9:16',resolution=s.google_video_resolution)); (out/'video-1.mp4').write_bytes(r.data)
 m={'scene':'pub-1105','experiment':'direct-master-vs-nano-copy-veo','arm':a.arm,'generated_at':stamp,'model':r.model,'aspect_ratio':'9:16','resolution':s.google_video_resolution,'seed_path':str(seed),'seed_sha256':hashlib.sha256(data).hexdigest(),'video_sha256':hashlib.sha256(r.data).hexdigest(),'manual_gate':'side_by_side_keeper_review'}; (out/'manifest.json').write_text(json.dumps(m,indent=2)); (out/'motion-prompt.txt').write_text(PROMPT); print(f'RESULT_DIR={out}')
if __name__=='__main__': main()
