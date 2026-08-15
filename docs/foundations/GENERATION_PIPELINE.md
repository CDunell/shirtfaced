# Generation pipeline — how a scene actually gets made

**Status:** Production doctrine. Universe-wide, all worlds.
**Date:** 15 August 2026.
**Companions:** `CAST_REFERENCE_PROMPTS.md` holds the fourteen prompts,
`CAST_REFERENCE_USE.md` holds storage and scene use. This holds the tools.

Written after generating World 01 scene 9 three times and scene 4 four times.
Every rule below cost a failed generation to learn.

---

## 1. The constraint that shapes everything

Per the standing decision, no metered API. Generation happens in paid
subscription interfaces and the result comes back. That has not changed and is
not a limitation to route around — it decides the shape of everything here.

What it means in practice is **two tools, not one**, and they do different jobs:

| | Tool | Owns |
|---|---|---|
| **Still** | A generator that accepts multiple reference images | Everything you can see |
| **Motion** | Grok Imagine, seeded with that still | Only what changes |

They are not interchangeable and the split is not a preference.

---

## 2. The seed carries the look. Full stop.

Grok does not read look from text. This was tested directly: a prompt stating
*the room is dark, no overhead lighting, the ceiling is lost in black, crushed
blacks, underexposed* returned a brightly lit room with a visible ceiling and
daylight in the windows. The same scene seeded from a dark still came back
dark.

**Therefore every visible property belongs in the still and nowhere else:**

- Darkness, exposure, crushed blacks
- Colour temperature and which practical is where
- Wardrobe, every item
- Framing, tilt, what crops the near edge
- Grain, focus, who is sharp and who is blurred
- Who is standing where, and what is on the table

Repeating any of it in the motion prompt does not reinforce it. It dilutes the
motion signal, which is the only thing that prompt can actually control.

## 3. Without a seed, references do not bind

A text-to-video generation naming three saved character references returned
three strangers. The same three names seeded from a still held across the whole
clip with no drift.

**No seed, no faces.** There is no version of this where a scene is filmed
straight from text.

---

## 4. What the motion prompt contains

Four lines, in this order, and nothing else:

```
Use all references exactly. Maintain character consistency.

<who does what, in order, two or three physical events>

Camera: <one move>

Audio: <named sounds>
```

**"Use all references exactly"** is the documented binding phrase. It was
missing from every early attempt.

**One camera move.** Early prompts stacked five — swings, overshoots, bumps,
drops, recovers — competing inside six seconds. Name one.

**Always name the audio.** Audio generates natively and in sync, and a prompt
with no audio cue produces a weaker clip, not just a silent one. An early
prompt said `no music`, which is both a negative and the removal of the cue.

**Front-load.** The first twenty to thirty words carry disproportionate weight.

## 5. Negative prompts do not work

Grok responds to positive directives only. `no slow motion, no smooth push, no
drift, no colour grade` did nothing at best, and naming those concepts may have
invoked them.

State what you want to see. If the camera should be violent, describe violence,
do not prohibit smoothness.

## 6. Models animate what is in the frame. They do not invent events.

Scene 4 asked for a stool to tip and a beer to go over. It never happened in any
generation, because the still had the stool upright and stable and the model
animates the frame it is given.

**A physics event needs its own clip, seeded from a frame where it has already
started.** Tipping, falling, spilling, breaking — none of it can be requested,
only continued.

---

## 7. Three named characters. That is the ceiling.

The tier available here caps at three character references per generation.
Seven-image multi-reference and 1080p exist on higher paid tiers and are not
being bought.

**This is a permanent production constraint, not a workaround.** Design against
it:

- Every scene nominates three. Everyone else is crowd, which the `WORLD.md`
  Form rule already supports — unnamed people are "one bloke", "another mate".
- **Whoever wears the hero product must be one of the three.** That garment is
  why the post exists; an unnamed wearer is a drifting face on the product.
- Any scene needing four or more legible faces is a still, not a clip.

Reference-to-video is also capped at 720p where text and image-to-video reach
1080p. Using references costs resolution. Accept it — the faces are worth more
than the pixels.

## 8. Six seconds is not the ceiling

Copy the last frame of a clip, paste it as the seed of the next, continue.
Twelve, eighteen, sixty seconds. Add `maintain character consistency`, and keep
everyone inside the frame — anyone who walks out cannot come back in the next
segment.

This is how a twelve-scene arc becomes films rather than fragments, and it is
also the answer to §6: the event that cannot be requested becomes the second
clip.

**Getting the last frame.** `studio/scripts/lastframe.bat` — drag an mp4 onto
it and it writes `<name>_lastframe.png` alongside, at full resolution. Or:

```
ffmpeg -sseof -0.5 -i input.mp4 -update 1 -q:v 1 lastframe.png
```

`-sseof -0.5` seeks half a second from the end and `-update 1` keeps
overwriting until the final frame. Seeking to exactly zero can land past the
last keyframe and write nothing.

---

## 9. Known gap in our own references

Optimal character binding wants three to five references each: one face
close-up, one profile, two full-body in key poses.

**We have two each, both front-on. There is no profile frame for anybody.**
That is the cheapest available improvement to consistency and it is not done.

What is already right, by luck rather than judgement: poor lighting in
references causes most consistency failures, and all twenty-eight of ours are
evenly lit on grey seamless.

---

## 10. The order of operations

1. Write the still prompt. Everything visible goes here. Attach up to five
   references — for the character whose face carries the shot, attach both
   their frames.
2. Generate the still. Judge it as a photograph. If the composition or the
   light is wrong, fix it here — it cannot be fixed later.
3. Seed Grok with it. Name three characters.
4. Write four lines of motion.
5. For anything longer or for any event the still cannot contain, take the last
   frame and go again.
