# SHIRTFACED — SOCIAL LAUNCH SYSTEM

## V5 — from empty accounts to a living archive

This document starts at zero.

No followers. No established feed. No audience waiting for an announcement. No need to pretend otherwise.

The first job is not to sell a drop. The first job is to make the account immediately feel like Shirtfaced already has a world worth following.

---

## 1. Launch principle

Do not introduce the brand with a corporate "hello, we are Shirtfaced" post.

Open in the middle of the story.

The first visitor should land on the profile and see ordinary Australian life photographed with enough consistency that the account already feels intentional.

Brand identity is present but restrained.

Products enter naturally after the world exists.

Commercial posts arrive after there is something for them to interrupt.

---

## 2. First nine Instagram feed positions

This is a production order, not a rigid posting calendar. Do not delay a strong post because a numbered slot says something else.

### POST 01 — THE OPEN
**Content:** strongest Friday-night documentary photograph available.

Mixed group. Nobody posing. Movement or interaction. The photograph should create immediate curiosity.

**Recipe:** Documentary Photo — clean or minimal dark corner mark.

**Purpose:** establish the world, not explain it.

**Caption:** one short observational line or nothing beyond a minimal phrase.

---

### POST 02 — MOTION
**Content:** 6–12 second Reel from the same emotional universe but not necessarily the same exact scene.

**Recipe:** Documentary Reel/TikTok.

Open directly on action. No logo intro.

Optional timestamp once. Natural finish or very short end mark.

**Cross-post:** TikTok.

---

### POST 03 — DAYLIGHT CONTRAST
**Content:** beach, 4WD, BBQ, footy, camping or another recognisably Australian daytime moment.

**Recipe:** Documentary Photo — LIGHT.

**Purpose:** immediately prove Shirtfaced is not a black-background nightlife moodboard.

---

### POST 04 — MINI STORY
**Content:** 3–5 image carousel from one event or small sequence.

**Recipe:** Photo Carousel / Mini Story.

Hero → context → moment → detail → continuation.

No title card first.

---

### POST 05 — CHARACTER
**Content:** a single human moment with personality. Someone carrying all the drinks, asleep in the wrong place, guarding the snacks, fixing something nobody asked them to fix, etc.

**Recipe:** Documentary Photo — clean/minimal.

The joke must be in the photograph. Caption does not explain it.

---

### POST 06 — SECOND MOTION
**Content:** 12–25 second Reel/TikTok with a tiny beginning/middle/end.

Examples: leaving one venue → walking → servo; packing the 4WD → beach → someone already wet; BBQ preparation → minor disaster → recovery.

**Recipe:** Documentary Reel/TikTok, LIGHT/DARK/ADAPTIVE according to footage.

**Cross-post:** TikTok.

---

### POST 07 — FIRST PRODUCT EVIDENCE
**Content:** documentary photograph where a Shirtfaced shirt/cap/hoodie appears naturally.

The product is visible enough to register but the photograph would still work without it.

**Recipe:** Documentary Photo.

Do not call it a drop yet.

---

### POST 08 — AFTERMATH / QUIET MOMENT
**Content:** dawn, empty table, servo stop, balcony, beach carpark, shoes by the door, someone making breakfast, waiting for a lift.

**Recipe:** Documentary Photo or short carousel.

**Purpose:** range. The world has quieter beats as well as chaos.

---

### POST 09 — BRAND PUNCTUATION
**Content:** strongest available image with a slightly clearer Shirtfaced identity treatment, OR a very short brand cut/end card after motion.

This is not a mission statement.

**Recipe:** identified Documentary Photo, Reel cover, or restrained brand card.

At nine posts the profile should look like an archive with a point of view, not nine launch graphics.

---

## 3. What does NOT belong in the first nine

Unless there is a real operational reason:

- no "coming soon" filler
- no founder introduction
- no mission statement tile
- no fake testimonials
- no countdown before anyone cares
- no engagement bait
- no "tag a mate" post
- no generic quote card
- no product catalogue grid
- no nine-tile logo mosaic
- no attempt to make the grid perfectly colour coordinated

---

## 4. When the first drop enters

A drop should interrupt an existing documentary rhythm rather than become the entire account.

Suggested sequence once product is genuinely ready:

1. documentary post
2. documentary motion
3. subtle product evidence
4. drop teaser
5. documentary post
6. reveal carousel
7. drop live
8. documentary continuation
9. product proof / wearer image if useful

Commercial communication remains the minority.

---

## 5. TikTok launch

Do not build a separate fake TikTok personality.

Use the same visual universe but favour sequences with a recognisable micro-story.

### First TikTok batch
Prepare at least 4 finished vertical videos before opening/publishing actively:

1. **One moment** — 6–12 sec. One action held long enough to feel real.
2. **The role** — 8–18 sec. The drinks carrier / snack thief / one-beer liar / designated navigator / person who disappears.
3. **Small journey** — 12–25 sec. Pub → walk → servo, or 4WD → beach → aftermath.
4. **Quiet payoff** — 6–15 sec. Dawn, breakfast, empty esky, beach carpark, balcony.

Cross-post suitable Reels from the clean master export. Never reuse a downloaded watermarked TikTok on Instagram.

---

## 6. Caption system

Captions are not essays and do not explain the photograph.

Use one of four modes:

### NONE
The image carries everything.

### OBSERVATION
A short line that could have been said by someone there.

### CONTEXT
Useful factual context: place, time, event, drop timing.

### PRODUCT
Only when selling: product/drop name, availability, action.

Avoid manufactured brand voice on every post. If the caption sounds like a social media manager performing irreverence, delete half of it.

---

## 7. File naming

Use predictable names before export.

### Photos
`SF_YYYYMMDD_WORLD_EVENT_001_FEED.jpg`

Example:
`SF_20260814_BIG-NIGHT_SERVO_001_FEED.jpg`

### Carousels
`SF_YYYYMMDD_WORLD_EVENT_C01_S01.jpg`
`SF_YYYYMMDD_WORLD_EVENT_C01_S02.jpg`

### Video masters
`SF_YYYYMMDD_WORLD_EVENT_R01_MASTER.mp4`

### Covers
`SF_YYYYMMDD_WORLD_EVENT_R01_COVER.jpg`

### Drop
`SF_DROP##_PRODUCT_ASSET_PURPOSE.ext`

Do not put `final-final-v3` in filenames. We are adults.

---

## 8. Export presets

### FEED PHOTO / CAROUSEL
- 1080 × 1350
- sRGB
- JPG high quality for photography
- PNG where transparency or flat graphics require it

### REEL / TIKTOK / STORY
- 1080 × 1920
- H.264 MP4
- preserve source frame rate unless there is a production reason to change it
- AAC audio
- no platform watermark

Keep an untouched clean master before adding platform-native audio/text.

---

## 9. Folder structure for produced social content

Recommended production structure outside generated template assets:

```text
social/
  incoming/
  selects/
  working/
  exports/
    instagram/
      feed/
      reels/
      stories/
    tiktok/
  covers/
  archive/
```

Do not commit huge raw photo/video libraries to the application repository. The repo stores the system, templates, specs and lightweight approved assets. Production media belongs in appropriate media storage.

---

## 10. Per-post production card

For every post answer these before editing:

```text
POST ID:
CONTENT TYPE: photo / carousel / reel / story / tiktok
WORLD / EVENT:
WHAT ACTUALLY HAPPENS:
WHY THIS IMAGE/CLIP IS WORTH POSTING WITHOUT A SHIRT:
THEME: light / dark / adaptive
RECIPE:
BRAND ASSET: clean / corner / overlay / information panel
PRODUCT VISIBILITY: none / incidental / deliberate
CAPTION MODE: none / observation / context / product
CROSS-POST: yes / no
EXPORT NAME:
STATUS: select / edit / approved / posted
```

If `WHY THIS IMAGE/CLIP IS WORTH POSTING WITHOUT A SHIRT` has no good answer, reconsider the asset.

---

## 11. Posting-day workflow

1. Choose the strongest approved content.
2. Fill the production card.
3. Edit the photograph/video first.
4. Select LIGHT/DARK/ADAPTIVE.
5. Add the minimum Shirtfaced layer required.
6. Export the clean platform master.
7. Check crop and safe areas.
8. Upload to Instagram/TikTok.
9. Add native audio, caption, location/mentions only where useful.
10. Preview once in-platform.
11. Publish.
12. Move/export record to archive and record the live post reference when useful.

---

## 12. First production queue

Before worrying about a posting schedule, build this inventory:

- 6 strong documentary feed photographs
- 2 documentary carousels
- 4 vertical motion pieces
- 4 Reel/TikTok covers
- 2 daylight/beach/4WD pieces
- 2 night/pub pieces
- 2 mixed-light/party/servo pieces
- 2 quiet/aftermath pieces
- 2 natural product-evidence photographs

There can be overlap: one beach sequence can supply a photo, carousel and motion piece.

This creates enough material to choose strong posts rather than publishing whatever happens to be finished that day.

---

## 13. Launch readiness gate

The accounts are ready to actively launch when:

- profile image and bio are set
- website link works
- at least 9 Instagram-worthy pieces are approved
- at least 4 vertical videos are approved
- covers are prepared
- LIGHT/DARK/ADAPTIVE treatments have been tested against real media
- there is enough content behind the first posts that publishing does not immediately exhaust the library

The goal is not to make the account look old. The goal is to make it look deliberate from the first post.
