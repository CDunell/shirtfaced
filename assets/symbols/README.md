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
| `symbol_breaking_wave_0001` | Reads as a decorative flourish. Wants a heavier face under the curl. |
| `symbol_spanner_0001` | No open jaw, so it reads as a dumbbell. The jaw is what makes it a spanner. |
| `symbol_thong_0001` | Two rounded blobs. No toe post and no sole shape. |
| `symbol_can_0001` | Legible but characterless. Wants a tab and a chamfer. |

The other seven — anchor, crown, flame, heart, mountain range, palm, stubby
bottle — are good, and supersede the parametric versions that stood in for them.
