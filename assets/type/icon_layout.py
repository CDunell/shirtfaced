import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, "icon_manifest.json")) as f:
    icons = json.load(f)

with open(os.path.join(BASE, "font_plan.json")) as f:
    plan = json.load(f)

SCALE = None
for entry in plan["glyphs"]:
    if entry["char"] == "H":  # reference: use letter-scale (px->unit) consistency
        pass

# recompute the same px->unit scale used for letters, from crop_manifest.json
with open(os.path.join(BASE, "crop_manifest.json")) as f:
    crop_manifest = json.load(f)

import statistics
cap_heights_px = [m["orig_bottom"] - m["orig_top"] for m in crop_manifest if m["sheet"] == "upper"]
cap_height_px = statistics.median(cap_heights_px)
TARGET_CAP_HEIGHT = 700
LETTER_SCALE = TARGET_CAP_HEIGHT / cap_height_px

# Icons are drawn at a different native size in their source sheet than the
# letters, so reusing LETTER_SCALE directly would make icons a random size
# relative to text. Instead: normalize each icon so its own height maps to
# ICON_HEIGHT (icons sit baseline-aligned like a tall cap, e.g. slightly over
# cap-height so they read clearly next to text), preserving aspect ratio.
ICON_HEIGHT_UNITS = 760  # a bit taller than letter cap-height (700) — icons read small otherwise
SIDE_BEARING = 30
PUA_START = 0xE000

icon_glyphs = []
for m in icons:
    h_px = m["orig_bottom"] - m["orig_top"]
    w_px = m["orig_right"] - m["orig_left"]
    scale = ICON_HEIGHT_UNITS / h_px

    tgt_x0 = SIDE_BEARING
    tgt_x1 = SIDE_BEARING + w_px * scale
    tgt_y0 = 0
    tgt_y1 = ICON_HEIGHT_UNITS

    icon_glyphs.append({
        "sheet": "icon", "row": 0, "col": m["index"],
        "svg": m["svg"],
        "uni": PUA_START + m["index"],
        "name": m["name"],
        "char": None,
        "tgt_x0": tgt_x0, "tgt_y0": tgt_y0, "tgt_x1": tgt_x1, "tgt_y1": tgt_y1,
        "advance": tgt_x1 + SIDE_BEARING,
    })

plan["glyphs"].extend(icon_glyphs)
plan["ascent"] = max(plan["ascent"], ICON_HEIGHT_UNITS + 20)

with open(os.path.join(BASE, "font_plan.json"), "w") as f:
    json.dump(plan, f, indent=2)

print(f"added {len(icon_glyphs)} icon glyphs (U+{PUA_START:04X}..U+{PUA_START+len(icon_glyphs)-1:04X})")
for g in icon_glyphs:
    print(f"  U+{g['uni']:04X}  {g['name']}")
