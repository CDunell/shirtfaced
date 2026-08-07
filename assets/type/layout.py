import json
import os
import statistics

BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, "crop_manifest.json")) as f:
    manifest = json.load(f)

idx = {(m["sheet"], m["row"], m["col"]): m for m in manifest}

UPPER_ROWS = [list("ABCDEFGHI"), list("JKLMNOPQR"), list("STUVWXYZ")]
LOWER_ROWS = [list("abcdefghi"), list("jklmnopqr"), list("stuvwxyz")]
EXTRA_ROW0 = list("0123456789")
EXTRA_ROW1 = list("!?#&%*.,'-+=/@")
EXTRA_ROW2_NAMES = ["A.alt1", "A.alt2", "R.alt1", "R.alt2", "K.alt", "G.alt", "Q.alt"]

DESCENDERS = set("gjpqy,")  # chars whose bottom legitimately sits below baseline

labels = {}  # (sheet,row,col) -> label dict {char or name, unicode or None}

for ri, row in enumerate(UPPER_ROWS):
    for ci, ch in enumerate(row):
        labels[("upper", ri, ci)] = {"char": ch, "uni": ord(ch)}

for ri, row in enumerate(LOWER_ROWS):
    for ci, ch in enumerate(row):
        labels[("lower", ri, ci)] = {"char": ch, "uni": ord(ch)}

for ci, ch in enumerate(EXTRA_ROW0):
    labels[("extra", 0, ci)] = {"char": ch, "uni": ord(ch)}

for ci, ch in enumerate(EXTRA_ROW1):
    labels[("extra", 1, ci)] = {"char": ch, "uni": ord(ch)}

for ci, name in enumerate(EXTRA_ROW2_NAMES):
    labels[("extra", 2, ci)] = {"char": None, "uni": -1, "name": name}

# sanity check: every crop got a label, every label has a crop
missing = [k for k in idx if k not in labels]
extra = [k for k in labels if k not in idx]
assert not missing, f"unlabeled crops: {missing}"
assert not extra, f"labels with no crop: {extra}"
print(f"labeled {len(labels)} glyphs, all matched")

UPM = 1000
TARGET_CAP_HEIGHT = 700
LSB = 42   # left side bearing, font units
RSB = 42   # right side bearing, font units

# global px->unit scale from median uppercase cap height
cap_heights_px = [idx[k]["orig_bottom"] - idx[k]["orig_top"]
                   for k in idx if k[0] == "upper"]
cap_height_px = statistics.median(cap_heights_px)
SCALE = TARGET_CAP_HEIGHT / cap_height_px
print(f"uppercase median height: {cap_height_px}px -> scale {SCALE:.4f} units/px")

# baseline per row: median 'orig_bottom' among glyphs in that row that are
# NOT descenders (so their bottom edge should sit exactly on the baseline)
row_groups = {}
for (sheet, row, col), m in idx.items():
    row_groups.setdefault((sheet, row), []).append((col, m))

baselines = {}
for (sheet, row), items in row_groups.items():
    bottoms = []
    for col, m in items:
        lab = labels[(sheet, row, col)]
        ch = lab["char"]
        if ch is not None and ch in DESCENDERS:
            continue
        if lab.get("name", "").startswith(("Q.alt",)):
            continue
        bottoms.append(m["orig_bottom"])
    baseline_px = statistics.median(bottoms) if bottoms else statistics.median(
        [m["orig_bottom"] for _, m in items])
    baselines[(sheet, row)] = baseline_px
    print(f"  baseline {sheet} row{row}: {baseline_px}px  (from {len(bottoms)} refs)")

plan = []
max_top_units = 0
min_bottom_units = 0
for (sheet, row, col), m in idx.items():
    lab = labels[(sheet, row, col)]
    baseline_px = baselines[(sheet, row)]

    w_px = m["orig_right"] - m["orig_left"]
    tgt_x0 = LSB
    tgt_x1 = LSB + w_px * SCALE
    tgt_y0 = (baseline_px - m["orig_bottom"]) * SCALE
    tgt_y1 = (baseline_px - m["orig_top"]) * SCALE

    max_top_units = max(max_top_units, tgt_y1)
    min_bottom_units = min(min_bottom_units, tgt_y0)

    svg_path = m["file"].replace(".png", ".svg")
    entry = {
        "sheet": sheet, "row": row, "col": col,
        "svg": svg_path,
        "uni": lab["uni"],
        "name": lab.get("name") or lab["char"],
        "char": lab["char"],
        "tgt_x0": tgt_x0, "tgt_y0": tgt_y0, "tgt_x1": tgt_x1, "tgt_y1": tgt_y1,
        "advance": tgt_x1 + RSB,
    }
    plan.append(entry)

print(f"\nfont vertical extremes: top={max_top_units:.1f} bottom={min_bottom_units:.1f} (UPM={UPM})")

out = {
    "upm": UPM,
    "ascent": int(max_top_units + 20),
    "descent": int(-min_bottom_units + 20),
    "glyphs": plan,
}
with open(os.path.join(BASE, "font_plan.json"), "w") as f:
    json.dump(out, f, indent=2)

print(f"wrote font_plan.json with {len(plan)} glyphs")
