# CURB STAMPS — World and Play Plan

Status: implementation plan and content authority

Audience: children 3–8 first; parents remain the buyer

Principle: every activity must work immediately, with no account, reading wall, tutorial or data collection.

## 1. Purpose

The shop should feel like the entrance to a small creature world, not a catalogue with games taped onto it. Children should be able to meet a creature, make it do something, discover one funny fact and return later for a different tiny task. Shopping remains available but never interrupts play.

Success means:

- a child can understand the main interaction from its picture and button;
- useful play begins within one tap;
- sessions work in two minutes but reward repeat visits;
- creature names, artwork and personalities stay consistent everywhere;
- parents are not asked to create accounts or surrender children's information;
- every activity works on a phone with touch targets of at least 48px.

## 2. The world

The world is called **The Curb**. It is an ordinary little strip of pavement made enormous through creature scale. Its recurring places are deliberately simple enough to illustrate with the locked thin-line system.

| Place | What it is | Activity use |
|---|---|---|
| Crooked Curb | The main meeting place | Creature index and daily arrival |
| Long Puddle | A puddle that feels like an ocean | Find-a-creature scenes and stories |
| Crumb Hill | A dangerous mountain of toast crumbs | Snack missions and tiny stories |
| Under-the-Bin | Warm, dark and full of rumours | Mystery creature reveals |
| Moonlight Drain | Where Murk and the night weirdos live | Bedtime stories and night scenes |
| Never-Open Shop | A tiny shop whose sign always says back soon | Silly episodic story location |

Every creature receives the same compact character model:

- **home** — one recurring place;
- **favourite thing** — concrete and child-readable;
- **tiny problem** — funny, harmless and reusable in stories;
- **sound** — a short invented noise;
- **friend** — another existing creature;
- **movement** — one simple animation such as wobble, blink or shuffle.

This is enough to build continuity without producing a lore encyclopaedia for children who would rather press the noisy button.

## 3. Product roadmap

### Release 1 — Play on the Curb

Build now:

1. **Play hub** at `/play` with three instantly understandable activities.
2. **Make a Picture** — choose a real creature and tap a bright play board to place stamps. Undo and clear are always visible.
3. **Creature Noises** — six large creature buttons, each with a distinct short synthesised sound and visible sound word. Audio only begins after a tap.
4. **Tiny Mission** — one offline activity prompt that changes daily, with no login or tracking.
5. **Homepage invitation** — a dedicated play block after Meet the Curb Crew.
6. **Navigation entry** — PLAY is a first-class desktop and mobile destination.

Why first: it uses approved artwork, creates immediate entertainment, needs no backend, adds almost no privacy burden and establishes `/play` as the permanent home for later activities.

### Release 2 — Meet Their World

1. Creature profile pages separate from product pages.
2. Home, favourite thing, tiny problem, noise and friend for every released creature.
3. Three-to-six-panel wordless Tiny Stories.
4. Expanded hidden-creature scenes set in recurring locations.
5. A simple stamp book stored only on the device.

### Release 3 — Make Your Own Weirdo

1. Pick one of a small number of body silhouettes.
2. Add eyes, feet and one strange feature using curated parts.
3. Choose a short generated name from safe syllables.
4. Produce a CURB STAMPS-style card for saving or printing.

This must be a constrained builder, not free text plus image generation. That keeps the output attractive, safe and recognisably Curb Stamps.

### Release 4 — Return and Discover

1. Mystery creature voting with three pre-approved names.
2. Printable colouring, matching, maze and finish-the-creature packs.
3. Seasonal Curb scenes and story drops.
4. Optional parent-controlled email notification for new activity packs.

## 4. Interaction rules

- No sign-in to play.
- No child names, photos, location, microphone or camera access.
- No streaks, countdown pressure, random paid rewards or purchase-gated play.
- No external advertising inside the play area.
- Sound is off until the child taps a sound control.
- Controls use words plus a visual cue; colour is never the only indicator.
- Motion lasts 180–420ms and respects reduced-motion.
- Play screens remain usable without sound.
- Each activity has a clear reset and cannot reach a dead end.

## 5. Content tone

Copy is short, literal and gently ridiculous. Prefer “Tap the curb to add Blip” over instructions such as “Create your own unique composition.” Avoid adult sarcasm, knowing streetwear language and explanations of the joke.

Good character facts:

- Plod lives by the Long Puddle, likes warm toast and is always five minutes late.
- Nib lives behind the Never-Open Shop, likes corners and keeps nibbling the map.
- Zot lives Under-the-Bin, likes racing leaves and forgets where the finish line is.

## 6. Measurement without child profiling

Useful anonymous events:

- play hub opened;
- activity started;
- number of stamps placed per session;
- sound buttons used;
- mission reshuffled;
- printable pack downloaded.

Do not attach these events to a child identity or retain the pictures they make.

## 7. Definition of done for Release 1

- `/play` builds and works at 320px through desktop widths.
- A stamp can be placed, changed, undone and cleared using touch or mouse.
- Six sound buttons make distinct sounds after direct user interaction.
- The daily mission remains stable for the calendar day.
- All interactive controls are keyboard accessible and visibly focused.
- The existing shop and homepage build without regression.
- Lint, tests and production build pass.
