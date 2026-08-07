import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(BASE, "Shirtfaced-Regular.ttf")
OUT = os.path.join(BASE, "proof.png")

lines = [
    ("ABCDEFGHIJKLM", 90),
    ("NOPQRSTUVWXYZ", 90),
    ("abcdefghijklm", 90),
    ("nopqrstuvwxyz", 90),
    ("0123456789 !?#&%", 90),
    ("SHIRTFACED", 140),
    ("FARK  YEAH", 140),
    ("NO FUCKS GIVEN", 100),
    ("NOT TODAY, KAREN", 90),
    ("BIN CHICKEN", 100),
]

pad = 40
canvas_w = 1600
line_imgs = []
total_h = pad
for text, size in lines:
    font = ImageFont.truetype(FONT, size)
    bbox = font.getbbox(text)
    h = bbox[3] - bbox[1] + 30
    line_imgs.append((text, font, h))
    total_h += h + 10

canvas = Image.new("RGB", (canvas_w, total_h), "white")
draw = ImageDraw.Draw(canvas)
y = pad
for text, font, h in line_imgs:
    draw.text((pad, y), text, font=font, fill="black")
    y += h + 10

canvas.save(OUT)
print("saved", OUT, canvas.size)
