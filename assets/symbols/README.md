# Symbols

Drawn artwork, loaded as archive elements by `studio/app/archive/library.py`.

Each file is normalised into a 100-unit box on the way in. Files arrive in
whatever coordinate space their author used, and a grammar places a part as a
share of its box, so an element carrying its own scale would come out a
different size in every composition.

`library.json` holds what we know about each file — subtype, style tags, ink
range, where it came from, and whether it is standing in for something better.
Keeping it out of the SVG means artwork can be replaced without losing the
metadata, and a supplier can send a plain file without editing a manifest.

## Standing in for better artwork

| File | What is wrong |
|---|---|
| `symbol_wings_0001` | Reads as a bat rather than feathers. Wants stepped trailing edges. |
| `symbol_boomerang_0001` | A thin curve with a ball at each end. Wants thickness through the elbow. |
| `symbol_spanner_0001` | No open jaw, so it reads as a dumbbell. The jaw is what makes it a spanner. |
| `symbol_thong_0001` | Two rounded blobs. No toe post and no sole shape. |
| `symbol_can_0001` | Legible but characterless. Wants a tab and a chamfer. |

The other eight — anchor, breaking wave, crown, flame, heart, mountain range,
palm, stubby bottle — are good, and supersede the parametric versions that
stood in for them.

## Checking a delivery

Straight lines and curves both fill the same way, and the geometry loads
whatever it is given, so a file can be structurally valid and still be wrong.
Look at it rendered before accepting it. Two faults have arrived more than once
and neither shows up in the path data:

**Counters wound the same way as the outer path.** Default fill is nonzero
winding, so a subpath wound in the same direction as the outline adds mass
instead of cutting a hole. A ring, a strap gap or a rim drawn this way vanishes
into the silhouette. Either wind the counter in reverse or set
`fill-rule="evenodd"` on the path.

**Detached subpaths.** A lid, a tab or a spray drawn clear of the body reads as
a separate mark at any size and as debris at a small one.
