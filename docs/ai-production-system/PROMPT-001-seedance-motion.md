# PROMPT-001 — SHIRTFACED Motion Baseline

Status: Approved  
Date: 2026-08-05

## Generation contract

- Model: Seedance 2.0 Fast
- Aspect ratio: 9:16
- Duration: 5 seconds
- Resolution: 720p
- Native audio: Off
- Input: Approved SHIRTFACED image as first frame

## Prompt

```text
Generate one image-to-video clip using the attached image as the first frame.

Generation contract

Model: Seedance 2.0 Fast
Aspect ratio: 9:16
Duration: 5 seconds
Resolution: 720p
Native audio: Off

Motion

Continue the existing moment naturally.

The people are the primary source of motion.

The group continues walking together while chatting, laughing and naturally shifting their weight as they walk.

Use only a gentle handheld tracking shot to observe the scene.

Preserve every person's identity, clothing, body proportions, objects and lighting.

No new people.
No new objects.
No cuts.
No zoom.
No push-in.
No orbit.
No dramatic camera movement.

Before generating, show me the generation specification for approval. Do not substitute another model or change any settings unless I explicitly approve.
```

## Benchmark result

Score: 9.2/10

## Findings

- Portrait reframing is suitable for Instagram and TikTok.
- Identity preservation was excellent.
- Human-motion-first prompting performed better than camera-led prompting.
- Camera movement should remain minimal.
- Existing landscape documentary images can be converted directly into vertical social video.
- This prompt is the production baseline for future motion variants.
