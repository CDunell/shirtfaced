# SHIRTFACED — VIDEO PIPELINE ARCHITECTURE

**Status:** Proposed Canon

## Principle

The photography prompt is **not** the source of every downstream asset.

The **Scene Specification** is.

A scene is the canonical source. Every renderer consumes the same scene.

```text
WORLD
│
├── SCENE
│   ├── Narrative
│   ├── Cast
│   ├── Lighting
│   ├── Emotional State
│   ├── Continuity
│   ├── Canon Rules
│   └── Motion Intent
│
└── Renderers
    ├── Photography
    ├── Video
    ├── Instagram
    ├── TikTok
    ├── Website
    ├── Paid Ads
    └── Product Placement
```

## Motion Intent

Every scene defines how it naturally moves before any renderer is used.

### Primary Motion

The dominant subject movement.

### Secondary Motion

Gestures, conversation, clothing, expressions and interactions.

### Environmental Motion

Traffic, lighting, weather, crowds and atmosphere.

### Camera Behaviour

The camera observes. It never becomes the performance.

## Renderer Contracts

Renderers contain production settings only.

### Photography

- Landscape master
- Aspect ratio
- Image prompt

### Seedance

- Model: Seedance 2.0 Fast
- Resolution: 720p
- Aspect ratio: 9:16
- Duration: 5 seconds
- Audio: Off
- Motion Intent consumed directly

### Instagram

- Crop
- Caption
- Alt text
- Filename

### TikTok

- Hook
- Caption
- Hashtags
- Suggested ambient audio

## Creative vs Production

### Creative — Human Authored

- Narrative
- Mood
- Cast
- Lighting
- Motion Intent
- Continuity
- Canon Rules

### Production — Generated

- Photography prompt
- Video prompt
- Camera instructions
- Social copy
- Metadata
- Filenames
- Export package

## Continuity Block

Every scene records:

- Previous scene
- Next scene
- Continuing characters
- Continuing props
- Time
- Weather
- Emotional trajectory

This allows image and video generations to feel like consecutive documentary moments rather than isolated creations.

## Canon Decision

WORLD and SCENE remain the single source of truth.

Renderers generate all downstream production assets automatically.

Creative intent is authored once.

Everything else is production.
