import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
import json
import os

SRC = r"C:\Users\User\Documents\Codex\2026-08-06\referenced-chatgpt-conversation-this-is-an\outputs\SHIRTFACED_Wordmark_Proportions_Full_Set\05_Icon_Glyphs.png"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

PAD = 10
ROW_GAP_MIN = 6
COL_GAP_MIN = 6
FG_THRESH = 100
MIN_COMPONENT_SIZE = 15  # icons have thin strokes/small details (eyes, drips) — keep those

ICON_NAMES = [
    "icon.smiley", "icon.palm", "icon.cart", "icon.sf",
    "icon.8ball", "icon.beer", "icon.chair", "icon.lightning",
    "icon.ibis", "icon.tent", "icon.flame", "icon.wave",
]


def find_bands(mask_1d, gap_min):
    runs = []
    in_run = False
    start = 0
    for i, v in enumerate(mask_1d):
        if v and not in_run:
            start = i
            in_run = True
        elif not v and in_run:
            runs.append([start, i - 1])
            in_run = False
    if in_run:
        runs.append([start, len(mask_1d) - 1])
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] - 1 < gap_min:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [tuple(r) for r in merged]


im = Image.open(SRC).convert("L")
arr = np.array(im)
fg = arr > FG_THRESH

row_has_fg = fg.any(axis=1)
row_bands = find_bands(row_has_fg, ROW_GAP_MIN)
print(f"row bands: {len(row_bands)}")

icon_dir = os.path.join(OUT_DIR, "glyphs", "icons")
os.makedirs(icon_dir, exist_ok=True)

manifest = []
i = 0
for ri, (r0, r1) in enumerate(row_bands):
    row_fg = fg[r0:r1 + 1, :]
    col_has_fg = row_fg.any(axis=0)
    col_bands = find_bands(col_has_fg, COL_GAP_MIN)
    print(f"  row {ri}: {len(col_bands)} icon(s)")

    for ci, (c0, c1) in enumerate(col_bands):
        sub = fg[r0:r1 + 1, c0:c1 + 1]
        ys, xs = np.where(sub)
        gy0, gy1 = ys.min(), ys.max()
        gx0, gx1 = xs.min(), xs.max()

        top = max(0, r0 + gy0 - PAD)
        bottom = min(arr.shape[0], r0 + gy1 + 1 + PAD)
        left = max(0, c0 + gx0 - PAD)
        right = min(arr.shape[1], c0 + gx1 + 1 + PAD)

        crop = arr[top:bottom, left:right]
        crop_img = Image.fromarray(crop).filter(ImageFilter.MedianFilter(size=3))
        carr = np.array(crop_img)
        bitonal = (carr > FG_THRESH).astype(np.uint8) * 255

        labeled, n = ndimage.label(bitonal > 0)
        if n > 0:
            sizes = ndimage.sum(bitonal > 0, labeled, range(1, n + 1))
            keep = np.zeros_like(bitonal, dtype=bool)
            for lbl, sz in enumerate(sizes, start=1):
                if sz >= MIN_COMPONENT_SIZE:
                    keep |= labeled == lbl
            bitonal = np.where(keep, 255, 0).astype(np.uint8)

        final = 255 - bitonal
        name = ICON_NAMES[i] if i < len(ICON_NAMES) else f"icon.extra{i}"
        base = f"icon_{i:02d}"
        Image.fromarray(final).save(os.path.join(icon_dir, base + ".png"))
        Image.fromarray(final).convert("1").save(os.path.join(icon_dir, base + ".bmp"))

        manifest.append({
            "index": i, "name": name,
            "png": f"glyphs/icons/{base}.png",
            "bmp": f"glyphs/icons/{base}.bmp",
            "svg": f"glyphs/icons/{base}.svg",
            "orig_top": int(r0 + gy0), "orig_bottom": int(r0 + gy1),
            "orig_left": int(c0 + gx0), "orig_right": int(c0 + gx1),
        })
        i += 1

with open(os.path.join(OUT_DIR, "icon_manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

print(f"total icons cropped: {len(manifest)}")
for m in manifest:
    print(" ", m["index"], m["name"])
