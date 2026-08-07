import numpy as np
from PIL import Image
from scipy import ndimage
import json
import os

SRC_DIR = r"C:\Users\User\Documents\Codex\2026-08-06\referenced-chatgpt-conversation-this-is-an\outputs\SHIRTFACED_Wordmark_Proportions_Full_Set"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

SHEETS = {
    "upper": "01_Uppercase_A-Z.png",
    "lower": "02_Lowercase_a-z.png",
    "extra": "03_Numerals_Punctuation_Alternates.png",
}

PAD = 6           # px padding around each cropped glyph
ROW_GAP_MIN = 4   # min all-background rows to treat as row separator
COL_GAP_MIN = 4   # min all-background cols to treat as glyph separator
FG_THRESH = 60    # grayscale value above which a pixel counts as foreground (glyph)


def find_bands(mask_1d, gap_min):
    """mask_1d: 1D bool array, True = has foreground.
    Returns list of (start, end) inclusive ranges of contiguous True runs,
    merging runs separated by gaps smaller than gap_min."""
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

    # merge runs separated by small gaps
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] - 1 < gap_min:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [tuple(r) for r in merged]


def process_sheet(name, filename):
    path = os.path.join(SRC_DIR, filename)
    im = Image.open(path).convert("L")
    arr = np.array(im)
    fg = arr > FG_THRESH  # True where glyph pixels (white letters on black bg)

    row_has_fg = fg.any(axis=1)
    row_bands = find_bands(row_has_fg, ROW_GAP_MIN)

    print(f"\n=== {name} ({filename}) — {len(row_bands)} row band(s) ===")

    glyph_dir = os.path.join(OUT_DIR, "glyphs", name)
    os.makedirs(glyph_dir, exist_ok=True)

    manifest = []
    for ri, (r0, r1) in enumerate(row_bands):
        row_fg = fg[r0:r1 + 1, :]
        col_has_fg = row_fg.any(axis=0)
        col_bands = find_bands(col_has_fg, COL_GAP_MIN)
        print(f"  row {ri}: {len(col_bands)} glyph(s)")

        for ci, (c0, c1) in enumerate(col_bands):
            # tight bbox within this cell using full fg array restricted to the band
            sub = fg[r0:r1 + 1, c0:c1 + 1]
            ys, xs = np.where(sub)
            gy0, gy1 = ys.min(), ys.max()
            gx0, gx1 = xs.min(), xs.max()

            top = max(0, r0 + gy0 - PAD)
            bottom = min(arr.shape[0], r0 + gy1 + 1 + PAD)
            left = max(0, c0 + gx0 - PAD)
            right = min(arr.shape[1], c0 + gx1 + 1 + PAD)

            crop = arr[top:bottom, left:right]

            # clean: denoise the grain texture, then hard-threshold to pure bitonal
            crop_img = Image.fromarray(crop)
            crop_img = crop_img.filter(__import__("PIL.ImageFilter", fromlist=["MedianFilter"]).MedianFilter(size=3))
            carr = np.array(crop_img)
            bitonal = (carr > FG_THRESH).astype(np.uint8) * 255

            # remove small speckle components (noise) that survive the median filter
            labeled, n = ndimage.label(bitonal > 0)
            if n > 0:
                sizes = ndimage.sum(bitonal > 0, labeled, range(1, n + 1))
                min_size = 25  # px area floor for a real glyph stroke/serif fragment
                keep = np.zeros_like(bitonal, dtype=bool)
                for lbl, sz in enumerate(sizes, start=1):
                    if sz >= min_size:
                        keep |= labeled == lbl
                bitonal = np.where(keep, 255, 0).astype(np.uint8)

            # invert: black glyph on white background (potrace convention)
            final = 255 - bitonal
            out_name = f"{name}_r{ri}_c{ci}"
            png_path = os.path.join(glyph_dir, out_name + ".png")
            bmp_path = os.path.join(glyph_dir, out_name + ".bmp")
            Image.fromarray(final).save(png_path)
            Image.fromarray(final).convert("1").save(bmp_path)
            manifest.append({
                "sheet": name, "row": ri, "col": ci,
                "file": f"glyphs/{name}/{out_name}.png",
                "bmp": f"glyphs/{name}/{out_name}.bmp",
                "w": final.shape[1], "h": final.shape[0],
                # tight bbox in ORIGINAL sheet pixel coords (pre-padding) — used later
                # to compute a shared baseline/scale per row band.
                "orig_top": int(r0 + gy0), "orig_bottom": int(r0 + gy1),
                "orig_left": int(c0 + gx0), "orig_right": int(c0 + gx1),
                "pad": PAD,
            })

    return manifest


all_manifest = []
for name, fname in SHEETS.items():
    all_manifest.extend(process_sheet(name, fname))

with open(os.path.join(OUT_DIR, "crop_manifest.json"), "w") as f:
    json.dump(all_manifest, f, indent=2)

print(f"\nTotal glyph crops: {len(all_manifest)}")
