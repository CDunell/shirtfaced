import json
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE, "crop_manifest.json")) as f:
    manifest = json.load(f)

by_sheet = {}
for m in manifest:
    by_sheet.setdefault(m["sheet"], {}).setdefault(m["row"], []).append(m)

CELL = 140
LABEL_H = 20

for sheet, rows in by_sheet.items():
    n_rows = len(rows)
    n_cols = max(len(v) for v in rows.values())
    canvas = Image.new("RGB", (n_cols * CELL, n_rows * (CELL + LABEL_H)), "white")
    draw = ImageDraw.Draw(canvas)
    for ri, items in rows.items():
        items.sort(key=lambda m: m["col"])
        for ci, m in enumerate(items):
            glyph = Image.open(os.path.join(BASE, m["file"])).convert("RGB")
            glyph.thumbnail((CELL - 10, CELL - LABEL_H - 10))
            x = ci * CELL
            y = ri * (CELL + LABEL_H)
            canvas.paste(glyph, (x + 5, y + LABEL_H))
            draw.rectangle([x, y, x + CELL - 1, y + CELL + LABEL_H - 1], outline="red")
            draw.text((x + 3, y + 2), f"r{ri}c{ci}", fill="red")
    out = os.path.join(BASE, "contact", f"{sheet}_contact.png")
    canvas.save(out)
    print("wrote", out, canvas.size)
