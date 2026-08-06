# SHIRTFACED — Image-to-Video Pilot Manifest

Status: Awaiting source asset assignment  
Created: 5 August 2026  
Parent: `01-image-to-video-pilot.md`

## Rule

Only approved SHIRTFACED documentary stills may enter this manifest.

Do not substitute concept art, screen-print artwork, mockups, rejected generations or images that merely resemble the intended world.

## Required source set

| Slot | Required scene | Asset ID | Repository/storage path | Approval evidence | Native ratio | People | Garment risk | Object risk | Crop notes | Status |
|---|---|---|---|---|---|---:|---|---|---|---|
| S01 | Two-person scene with minimal interaction | — | — | — | — | 2 | Medium | Low | — | Missing |
| S02 | Mixed group walking between venues | — | — | — | — | 4–6 | High | Medium | — | Missing |
| S03 | Servo or suburban street with practical lighting | — | — | — | — | 1–4 | Medium | Medium | — | Missing |
| S04 | Pub interior with people and glassware | — | — | — | — | 3–6 | Medium | High | — | Missing |
| S05 | Product-incidental blank shirt, hoodie or cap scene | — | — | — | — | 1–4 | Critical | Medium | — | Missing |
| S06 | Empty or near-empty environmental plate | — | — | — | — | 0–1 | Low | Low | — | Missing |

## Asset acceptance checks

A source may be assigned only when all are true:

- approved as a still
- belongs to WORLD 01 — THE BIG NIGHT or an explicitly approved launch world
- no visible third-party brand or commercial logo
- no unresolved anatomy or object defect
- no baked-in typography requiring preservation
- enough resolution for vertical crop or controlled outpaint
- prompt and generation lineage can be recovered
- approval owner is known

## Risk tags

### Garment risk

- Low — no garment is commercially relevant
- Medium — blank garment visible but incidental
- High — garment silhouette or colour must remain stable
- Critical — clip is specifically testing product-incidental preservation

### Object risk

- Low — no fragile small objects
- Medium — chairs, bags, vehicles, signage or background props
- High — glasses, bottles, hands, pool cues, cigarettes, phones or interacting objects

## Source freeze

Once generation begins:

- do not replace a source midway through a platform comparison
- do not use different crops across platforms unless the platform forces it
- record every forced crop
- preserve the original source file unchanged
- create platform inputs as derivatives, never overwrite the source

## Platform input records

### Runway Gen-4.5

| Source | Input file | Ratio | Duration | FPS | Seed policy | Prompt version | Generation IDs |
|---|---|---|---:|---:|---|---|---|
| S01 | — | 9:16 | 5–8 s | 24/25 | Record | v1 | — |
| S02 | — | 9:16 | 5–8 s | 24/25 | Record | v1 | — |
| S03 | — | 9:16 | 5–8 s | 24/25 | Record | v1 | — |
| S04 | — | 9:16 | 5–8 s | 24/25 | Record | v1 | — |
| S05 | — | 9:16 | 5–8 s | 24/25 | Record | v1 | — |
| S06 | — | 9:16 | 5–8 s | 24/25 | Record | v1 | — |

### Google Veo

| Source | Input file | Model ID | Ratio | Resolution | Duration | Prompt version | Generation IDs |
|---|---|---|---|---|---:|---|---|
| S01 | — | — | 9:16 | 720p/1080p | 4–8 s | v1 | — |
| S02 | — | — | 9:16 | 720p/1080p | 4–8 s | v1 | — |
| S03 | — | — | 9:16 | 720p/1080p | 4–8 s | v1 | — |
| S04 | — | — | 9:16 | 720p/1080p | 4–8 s | v1 | — |
| S05 | — | — | 9:16 | 720p/1080p | 4–8 s | v1 | — |
| S06 | — | — | 9:16 | 720p/1080p | 4–8 s | v1 | — |

### Adobe Firefly Video

| Source | First frame | Last frame | Ratio | Duration | Motion control | Prompt version | Generation IDs |
|---|---|---|---|---:|---|---|---|
| S01 | — | None initially | 9:16 | 5 s | Recorded | v1 | — |
| S02 | — | None initially | 9:16 | 5 s | Recorded | v1 | — |
| S03 | — | None initially | 9:16 | 5 s | Recorded | v1 | — |
| S04 | — | None initially | 9:16 | 5 s | Recorded | v1 | — |
| S05 | — | None initially | 9:16 | 5 s | Recorded | v1 | — |
| S06 | — | None initially | 9:16 | 5 s | Recorded | v1 | — |

## Current blocker

The repository contains the production-system documentation but no discoverable approved source-image manifest or media paths.

The pilot cannot honestly begin until six approved stills are assigned above.
