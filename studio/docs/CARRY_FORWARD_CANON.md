# Carry-forward canon

Rules proven in World 01 that are **not specific to World 01**, and must be
reproduced in the `WORLD.md` of any new world.

This file changes nothing on its own. Like everything outside a world's own
documents, no code reads it and the planner never sees it. It exists so that a
rule learned expensively in one world is not relearned expensively in the next.

To put a rule here into effect in a new world, follow the promotion steps in
`stage-2/README.md`: it has to live in that world's `WORLD.md`, under a heading
listed in `PLANNING_CANON_HEADINGS`, and be validated and imported before it is
real.

---

## The camera observes, so it stands outside

The most general rule here, and the one the vehicle rule turns out to be a special
case of. Copy it into every world before anything else.

We are observers. An observer is outside the thing being observed — that is what
the word means, not a stylistic preference. So the camera is never in the box with
the subjects: not in the lift with them, not in the car with them. It is in the
next room, the hallway, the footpath, the far table, looking in through the
doorway. Close enough to be there, outside enough to be watching. Somebody inside
the moment cannot record it.

Being in an interior is fine. Being inside the container the subjects occupy is
not. A kitchen photographed from the dining room is an observer; a lift
photographed from inside the lift is a passenger.

This arrived late and from the wrong direction. The vehicle rule was written first,
as a fix for cabins that came back with no seats, and treated as being about cars.
It is not about cars. When a lift shot was then framed from inside the lift, the
question was raised as a per-shot camera choice — and corrected: it is canon,
because we are observers and that inherently means outside. Write the general rule
first in a new world and the vehicle case follows from it.

Practical bonus: doorways, windows and open lift doors are where an observer
naturally stands, which is also where the best foreground obstructions live.

## Vehicles

**The rule.** Never shot inside. The camera never sits inside a vehicle, and
nobody is ever entering or leaving one. People are photographed on or around a
vehicle, never in transit into or out of it. The vehicle is a prop, never the
hero.

Recorded in `worlds/world-01/WORLD.md` under `Product Rotation & Vehicle Canon`.
Copy it forward whole; the World 01 wording also covers the near vehicle's own
window frame, the seated-passenger posture, and the foreground-obstruction trap,
each of which was a separate failed attempt.

**Why it generalises.** The failure is structural, not stylistic. A vehicle is
built geometry with a fixed number of seats and a fixed amount of room, and when
a body is asked to occupy space the structure does not have, the model deletes or
bends the structure rather than leaving the body out. World 01 produced, in
order: a car with no front seats, a man seated in mid-air, three people across a
front row built for two, a van with no back end, and a passenger whose seat had
been silently rotated ninety degrees to face the door. Nothing about that
sequence is particular to a night out in a city. It will happen at a beach, on a
back road, and on a dune.

**The harder cases are the ones coming.** Beach trips, four-wheel driving and
road trips all make the vehicle the means of the activity, and that is exactly
when it is most tempting to make it the subject. It does not become the subject.
The activity being *about* the car does not make the frame *about* the car:
photograph the trip, not the transport.

That leaves plenty. Boards and eskies coming off a tray onto sand. People
standing around a parked 4WD with the doors shut. A bonnet used as a table. Wet
towels over a side rail. Someone at an open window talking to whoever stayed
behind. A vehicle parked in the middle distance while the frame belongs to the
people. What is out is the shot that needs someone climbing in, climbing out,
riding along, or leaning through an opening.

**"Never in the car" means never shot inside.** Settled by the owner on 5 August
2026, and it carries to every world.

The ban is on the camera and on the act, not on the existence of an occupant. A
passenger already sitting in the vehicle is fine, and the exchange through an
open window remains a good frame — it was the first frame in World 01 that held
together structurally, with the cast on the footpath and the seated woman's arm
out through a window sill at shoulder height.

What is out is: the camera inside the cabin; anyone entering or leaving; anyone
half in and half out, climbing in, mid-transfer, or leaning through a door
opening; and anyone riding along. If the photographer would have to be sitting in
the vehicle to take the shot, it is the wrong shot, however the brief describes
it.

---

## Products

**The rule.** What we sell is t-shirts, crops, hoodies, jumpers and hats — caps,
beanies and bucket hats. Everything else is cart filler: it may appear, but it is
never the hero of a frame and no composition is built around making it legible.

The range is the current one, not a closed set, and will expand. Read the list in
any world as a snapshot, and expect to add to it rather than rewrite the rule.

Black is the documented seller for the t-shirt, the hoodie and the cap, so those
stay black. It is not established for anything else, and the colour of a filler
item is free. Do not let the surrounding black-heavy wardrobe canon quietly make
everything black by default.

---

## Physical correctness is checked by the owner, not by the reviewer

Carry this to every world, and do not let a green review talk you out of looking.

The automated reviewer does not verify that what it is looking at could exist. This
was tested rather than assumed: a frame containing an orphaned car door — a panel and
a window frame with no vehicle behind them, at the wrong scale, at footpath level —
was passed as structurally sound by both `gpt-4o-mini` and `gpt-5.5`, the stronger of
the two volunteering that "the vehicle and parking meter read as physically coherent"
about a frame with no vehicle in it.

There is a `structural_plausibility` gate. It is advisory. `PASS` means nothing was
noticed, not that anything was checked.

So the owner looks at every frame for structure before anything else: is everything
present, is everyone supported, do the counts add up. Zoom in. The failures of this
kind are usually in a corner, behind a person, or below the waistline of the frame,
because that is where the model puts what it could not resolve.

## The automated review is evidence, not a verdict

Carry this with the vehicle rule. Across seven frames in one day the reviewer
rejected every single one, including the structurally soundest, and its stated
reasons were verifiably wrong often enough that the recommendation cannot be used
as a filter.

What proved trustworthy: Australian authenticity, and documentary credibility as a
judgement of staging. What did not: branding, vehicle continuity, structural
plausibility, and mood and story, which did not move at all in response to prompts
written specifically to move them.

Read the gate evidence. It is frequently sharper than the verdict it is attached to
— "the road is visible through the opening beneath the tailgate" is useful whatever
score accompanies it. Then decide from the photograph.

And do not tune prompts against the scores. Measure a prompt against the seeded
reference set instead: it is a fixed human artefact, it does not drift, and it is
the only yardstick in this project that improved anything.

## Two traps worth carrying forward

**A rule only one document agrees with is not in force.** World 01 banned vehicle
interiors in `WORLD.md` and left `CONTINUITY.md` telling the planner to shoot
from inside a car, in a list that is parsed and sent on every request. The
planner went on being instructed to do the banned thing by a document nobody
thought to re-read. When a rule changes, grep every world document for the thing
it used to allow.

**Canon excerpts are capped per section, and truncation is silent by default.**
The cap dropped the last line of the branding rule for the entire life of the
project — the clause stopping the Shirtfaced exception being read as permission
to brand a garment. Neither model ever saw it. Truncation takes the *end* of a
section, and the end of a rule is where the qualifier lives, so a trimmed rule
looks exactly like a rule that is working. There is now a warning and a test;
keep both, and keep sections short enough not to need them.
