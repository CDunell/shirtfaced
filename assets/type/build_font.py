import json
import os
import fontforge
import psMat

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

with open("font_plan.json") as f:
    plan = json.load(f)

UPM = plan["upm"]

f = fontforge.font()
f.familyname = "Shirtfaced"
f.fontname = "Shirtfaced-Regular"
f.fullname = "Shirtfaced Regular"
f.weight = "Regular"
f.copyright = "SHIRTFACED"
f.encoding = "UnicodeFull"
f.em = UPM
f.ascent = plan["ascent"]
f.descent = plan["descent"]

failed = []

for entry in plan["glyphs"]:
    uni = entry["uni"]
    name = entry["name"]
    svg = entry["svg"]

    if uni is not None and uni >= 0:
        g = f.createChar(uni, name)
    else:
        g = f.createChar(-1, name)

    g.importOutlines(svg)
    g.removeOverlap()
    g.correctDirection()

    xmin, ymin, xmax, ymax = g.boundingBox()
    if xmax <= xmin or ymax <= ymin:
        failed.append(name)
        continue

    sx = (entry["tgt_x1"] - entry["tgt_x0"]) / (xmax - xmin)
    sy = (entry["tgt_y1"] - entry["tgt_y0"]) / (ymax - ymin)
    tx = entry["tgt_x0"] - sx * xmin
    ty = entry["tgt_y0"] - sy * ymin

    g.transform(psMat.compose(psMat.scale(sx, sy), psMat.translate(tx, ty)))
    g.round()
    g.simplify()
    g.width = round(entry["advance"])

if failed:
    print("WARNING: empty/failed glyphs:", failed)

# basic non-letter defaults
space = f.createChar(ord(" "), "space")
space.width = round(UPM * 0.32)

f.selection.all()
f.correctDirection()

out_ttf = os.path.join(BASE, "Shirtfaced-Regular.ttf")
out_otf = os.path.join(BASE, "Shirtfaced-Regular.otf")
f.generate(out_ttf)
f.generate(out_otf)

print("generated:", out_ttf)
print("generated:", out_otf)
print("total glyphs:", len(plan["glyphs"]) + 1)
