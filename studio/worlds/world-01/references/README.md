# Reference images for World 01

`WORLD.md` names a Locked Reference — "the six-friends Friday night street
photograph" — as the visual benchmark for the whole world. Until these folders
had contents, that benchmark existed only as prose, and prose cannot hold a
look: it can ask for warm sodium light and 35mm grain, but not for these faces,
this car, this grade.

Formats: PNG, JPEG or WebP, under 50MB each.

## `locked/` — the benchmark

The standard every frame is measured against. Seeded from `BigNight.zip`; see
`MANIFEST.md` for what came in, what was rejected and why.

One thing to be honest about: these are **generations, not photographs**. Every
one is 1536x1024, exactly gpt-image-1's landscape output, and they came from an
earlier workflow outside this pipeline. The original intention was that this
folder hold real photography, because a photograph cannot drift. It holds the
best available standard instead. If a real photograph of the six-friends
reference ever surfaces, it outranks everything here.

## `approved/` — frames this pipeline produced

Frames the owner approved, kept so later frames can match earlier ones: same
cast, same wardrobe, same vehicle, same night.

## Why the two are kept apart

A generated frame carries the model's own habits — skin a little too clean, a
composition a little too tidy, everyone lit a little too well. Feed this
pipeline's output back as its own anchor and those habits compound: each frame
trains on the last one's drift, and the world slides away from the standard it
was supposed to match, one plausible step at a time. Nobody notices, because
every frame resembles the one before it.

So `locked/` rides along in every request and `approved/` supplements it for
continuity. If the two ever disagree, `locked/` wins. That the seed is itself
generated weakens the anchor but does not change the rule: `locked/` is a fixed
target that this pipeline never writes to, and only a human adds to.

## Branding

Canon is absolute here: "No readable third-party branding or commercial logos
may appear anywhere in the image. If any third-party branding appears, the image
has failed the brief."

Four of the 21 seed candidates were rejected on that rule alone. Anything added
to `locked/` gets the same check first — a reference teaches whatever it shows,
so one McDonald's arch in the anchor set becomes a McDonald's arch in the
output.
