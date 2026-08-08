"""Reading Illustrator EPS and AI artwork.

Bought and downloaded vector packs arrive as `.eps` and `.ai`, and the converter
read neither, so a pack sat in `assets/stock/` as a file nobody could open. The
usual answer is Ghostscript or Inkscape, which means a binary on every machine
that ever rebuilds a design -- and the archive's premise is that its outputs can
always be regenerated.

So it is read directly. Illustrator writes its paths as plain-text PostScript
with a small, stable operator set, and the translation to SVG is close to
one-for-one:

    x y m                     moveto
    x y l | L                 lineto
    x1 y1 x2 y2 x3 y3 c | C   curveto
    x2 y2 x3 y3 v | V         curveto, first control at the current point
    x1 y1 x3 y3 y | Y         curveto, second control at the endpoint
    h | H                     closepath
    f F b B s S n N           paint what has been built, and start again
    *u ... *U                 one shape made of several subpaths

Two things have to be right or nothing lands in the correct place. PostScript
counts Y upwards and SVG counts it down, so every point is flipped about the
bounding box's top edge. And a compound path -- a letter O, a ring, a wheel --
paints all its subpaths together, so its parts have to be accumulated rather
than emitted one at a time, or the hole becomes a disc.

What this does not do: gradients, patterns, clipping paths, embedded images and
text are skipped. They are recorded as skipped rather than silently dropped, and
what comes back is the geometry, which is what the archive stores.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.archive.svg import num

# Numbers and bare operator tokens. Illustrator writes operators as short
# alphabetic words, sometimes prefixed with * for the compound-path pair.
TOKEN = re.compile(rb"-?\d*\.?\d+(?:[eE][-+]?\d+)?|\*?[A-Za-z]+")

BBOX = re.compile(rb"%%HiResBoundingBox:\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)")
PLAIN_BBOX = re.compile(rb"%%BoundingBox:\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)")

PAINT_FILL = {"f", "F", "b", "B"}
PAINT_STROKE = {"s", "S", "b", "B"}
PAINT_NONE = {"n", "N"}
PAINT = PAINT_FILL | PAINT_STROKE | PAINT_NONE


@dataclass
class Artwork:
    """What came out of one file."""

    paths: list[tuple[str, str]] = field(default_factory=list)
    width: float = 0.0
    height: float = 0.0
    # Named rather than counted, because "12 skipped" tells nobody what is
    # missing from the drawing they are looking at.
    skipped: list[str] = field(default_factory=list)

    @property
    def combined(self) -> str:
        return " ".join(path for path, _fill in self.paths if path)


def _cmyk(c: float, m: float, y: float, k: float) -> str:
    red = round(255 * (1 - min(c + k, 1.0)))
    green = round(255 * (1 - min(m + k, 1.0)))
    blue = round(255 * (1 - min(y + k, 1.0)))
    return f"#{red:02x}{green:02x}{blue:02x}"


def _grey(value: float) -> str:
    level = round(255 * value)
    return f"#{level:02x}{level:02x}{level:02x}"


def _rgb(red: float, green: float, blue: float) -> str:
    return f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"


def read(data: bytes) -> Artwork:
    """Every painted path in an Illustrator EPS or AI stream."""
    box = BBOX.search(data) or PLAIN_BBOX.search(data)
    if box:
        left, bottom, right, top = (float(v) for v in box.groups())
    else:
        # Without a box the flip has no reference, so the drawing would be
        # mirrored about zero and land off-canvas. Refusing here beats returning
        # geometry that is quietly upside down.
        return Artwork(skipped=["no bounding box; the y-flip has no reference"])

    art = Artwork(width=right - left, height=top - bottom)

    # The prolog *defines* these operators -- /h { closepath } def -- so parsing
    # from the top of the file reads the dictionary as if it were drawing, and
    # the first shape comes back as four closepaths and nothing else. The
    # artwork starts after the setup section.
    start = data.find(b"%%EndSetup")
    if start < 0:
        start = data.find(b"%%EndProlog")
    tokens = TOKEN.findall(data[start:] if start >= 0 else data)

    stack: list[float] = []
    segments: list[str] = []
    compound: list[str] = []
    in_compound = False
    in_gradient = False
    fill = "#000000"
    x = y = 0.0
    seen: set[str] = set()

    def flip(px: float, py: float) -> tuple[float, float]:
        return px - left, top - py

    for raw in tokens:
        token = raw.decode("latin-1")
        try:
            stack.append(float(token))
            continue
        except ValueError:
            pass

        if token == "m" and len(stack) >= 2:
            x, y = stack[-2], stack[-1]
            fx, fy = flip(x, y)
            segments.append(f"M {num(fx)} {num(fy)}")
        elif token in ("l", "L") and len(stack) >= 2:
            x, y = stack[-2], stack[-1]
            fx, fy = flip(x, y)
            segments.append(f"L {num(fx)} {num(fy)}")
        elif token in ("c", "C") and len(stack) >= 6:
            x1, y1, x2, y2, x3, y3 = stack[-6:]
            a, b = flip(x1, y1)
            c2, d = flip(x2, y2)
            e, f = flip(x3, y3)
            segments.append(f"C {num(a)} {num(b)} {num(c2)} {num(d)} {num(e)} {num(f)}")
            x, y = x3, y3
        elif token in ("v", "V") and len(stack) >= 4:
            # First control point is the current point.
            x2, y2, x3, y3 = stack[-4:]
            a, b = flip(x, y)
            c2, d = flip(x2, y2)
            e, f = flip(x3, y3)
            segments.append(f"C {num(a)} {num(b)} {num(c2)} {num(d)} {num(e)} {num(f)}")
            x, y = x3, y3
        elif token in ("y", "Y") and len(stack) >= 4:
            # Second control point is the endpoint.
            x1, y1, x3, y3 = stack[-4:]
            a, b = flip(x1, y1)
            e, f = flip(x3, y3)
            segments.append(f"C {num(a)} {num(b)} {num(e)} {num(f)} {num(e)} {num(f)}")
            x, y = x3, y3
        elif token in ("h", "H"):
            segments.append("Z")
        elif token in ("g", "G") and stack:
            fill = _grey(stack[-1])
        elif token in ("k", "K") and len(stack) >= 4:
            fill = _cmyk(*stack[-4:])
        elif token in ("Xa", "XA") and len(stack) >= 3:
            fill = _rgb(*stack[-3:])
        elif token == "*u":
            in_compound = True
            compound = []
        elif token == "*U":
            in_compound = False
            if compound:
                art.paths.append((" ".join(compound), fill))
            compound = []
        elif token in PAINT:
            built = " ".join(segments)
            # A run of closepaths with no points is not a shape. It happens
            # wherever a paint operator follows something this does not read,
            # and emitting it puts empty paths into the archive.
            if built and any(c in built for c in "MLC") and not in_gradient:
                if in_compound:
                    # Held back so every subpath paints as one shape. Emitting
                    # them separately turns a ring into a disc.
                    compound.append(built)
                elif token not in PAINT_NONE:
                    art.paths.append((built, fill))
            segments = []
        elif token == "Bb":
            # A gradient-filled shape. Its geometry is readable and its colour
            # is not, and painting it in the default ink is worse than dropping
            # it: the pack's background is a gradient rectangle the size of the
            # canvas, and filling it black buried all six hundred shapes behind
            # it. Skipped, and said so.
            in_gradient = True
            seen.add("gradients")
        elif token == "BB":
            in_gradient = False
        elif token in ("Bg", "Bm"):
            seen.add("gradients")
        elif token in ("Xh", "XH"):
            seen.add("patterns")
        elif token in ("Tf", "TX", "Tx", "Tj"):
            seen.add("text")
        elif token in ("XI", "Xi"):
            seen.add("embedded images")
        elif token == "W":
            seen.add("clipping paths")

        if (
            token in PAINT
            or token in ("m", "l", "L", "c", "C", "v", "V", "y", "Y")
            or token.isalpha()
            or token.startswith("*")
        ):
            stack.clear()

    art.skipped = sorted(f"{what} are not converted" for what in seen)
    return art
