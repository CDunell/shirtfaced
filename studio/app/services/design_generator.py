"""Composing supplied elements into designs, using layouts the corpus actually uses.

Give it elements -- a phrase, a subhead, a logo, an image -- and it returns
rendered designs. The arrangements are not invented: ``mine_design_structure.py``
reads the vertical stack of every printed design in the corpus (bands of ink
separated by clear garment, with their positions, heights and widths), and this
places the supplied elements into those measured slots.

So "three elements" is laid out the way three-element designs in the corpus are
actually laid out, at their median proportions, rather than however looked right
at the time.

What it does not do: write the phrase, draw the artwork, or judge whether the
idea is any good. It answers *where things go and how big*, which is the part
2,868 measured designs can actually speak to.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

from PIL import Image, ImageDraw, ImageFont

CORPUS_ROOT = Path(__file__).resolve().parents[2] / "var" / "design_corpus"
BRAND_FONT = Path(__file__).resolve().parents[3] / "public" / "fonts" / "Shirtfaced-Regular.ttf"

# The print area, in pixels. Square, generous, and independent of any garment --
# placement onto a photograph is the compositor's job, not this module's.
CANVAS = 1000

ElementKind = Literal["text", "image", "logo"]


@dataclass
class Element:
    """One thing to place."""

    kind: ElementKind
    text: str = ""
    image_bytes: bytes | None = None
    # Bigger weight claims more of the composition's height.
    weight: float = 1.0


@dataclass
class Layout:
    """A measured arrangement: one slot per element, top to bottom."""

    name: str
    slots: list[dict[str, float]]
    designs_seen: int
    evidence: str

    @property
    def element_count(self) -> int:
        return len(self.slots)


@dataclass
class GeneratedDesign:
    """One rendered option."""

    layout_name: str
    evidence: str
    ink: str
    garment: str
    png: bytes
    notes: list[str] = field(default_factory=list)

    def to_dict(self, include_png: bool = False) -> dict[str, Any]:
        import base64

        data: dict[str, Any] = {
            "layout": self.layout_name,
            "evidence": self.evidence,
            "ink": self.ink,
            "garment": self.garment,
            "notes": self.notes,
        }
        if include_png:
            data["png_base64"] = base64.b64encode(self.png).decode()
        return data


# Brand colourways. globals.css: black is the documented seller for the tee,
# hoodie and cap, and the corpus agrees -- black is the commonest garment and
# 60% of designs run light ink on dark.
COLOURWAYS: list[tuple[str, str, str, str]] = [
    ("washed black", "#1c1c1a", "bone", "#e8e2d5"),
    ("vintage white", "#e8e2d5", "ink", "#1c1c1a"),
    ("washed black", "#1c1c1a", "acid lime", "#c6ff33"),
]

FALLBACK_LAYOUTS: dict[int, Layout] = {
    1: Layout(
        "single mass",
        [{"top": 0.18, "height": 0.60, "width": 0.86, "centre_x": 0.5}],
        0,
        "default — corpus not mined",
    ),
    2: Layout(
        "lead above, support below",
        [
            {"top": 0.16, "height": 0.42, "width": 0.88, "centre_x": 0.5},
            {"top": 0.64, "height": 0.16, "width": 0.62, "centre_x": 0.5},
        ],
        0,
        "default — corpus not mined",
    ),
    3: Layout(
        "lead on top, stacked support",
        [
            {"top": 0.10, "height": 0.16, "width": 0.90, "centre_x": 0.5},
            {"top": 0.30, "height": 0.44, "width": 0.80, "centre_x": 0.5},
            {"top": 0.80, "height": 0.10, "width": 0.55, "centre_x": 0.5},
        ],
        0,
        "default — corpus not mined",
    ),
}


def load_layouts() -> dict[int, Layout]:
    """Measured layouts from the corpus, falling back to documented defaults."""
    report = CORPUS_ROOT / "design_structure.json"
    if not report.is_file():
        return dict(FALLBACK_LAYOUTS)

    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except ValueError:
        return dict(FALLBACK_LAYOUTS)

    layouts: dict[int, Layout] = {}
    for count_key, entry in (data.get("layouts") or {}).items():
        count = int(count_key)
        shapes = entry.get("shapes") or {}
        name = next(iter(shapes), f"{count}-element stack")
        layouts[count] = Layout(
            name=name,
            slots=entry["slots"],
            designs_seen=entry.get("designs", 0),
            evidence=(
                f"{entry.get('designs', 0)} corpus designs use {count} element"
                f"{'s' if count != 1 else ''}; slots are their median proportions."
            ),
        )
    for count, fallback in FALLBACK_LAYOUTS.items():
        layouts.setdefault(count, fallback)
    return layouts


def _normalise(slots: list[dict[str, float]], margin: float = 0.08) -> list[dict[str, float]]:
    """Rescale measured slots so the print fills the canvas.

    The corpus slots are fractions of the *torso box*, which includes bare
    garment above and below the print. Rendering them straight onto a canvas
    reproduces that empty space and the elements drift apart into three floating
    words. Re-basing them on the print's own extent keeps the relative
    proportions and gaps the corpus found, which is the part worth copying,
    while filling the artboard.

    Slots are also grown into the gaps between them. A measured band is the
    rows where ink is *dense*, not the element's full extent -- the sparse top
    of an arch or the thin base of an illustration fall below the detection
    threshold -- so the raw gaps overstate the real ones. Each slot expands to
    take its share of the gap on either side, less a consistent gutter, which
    keeps the corpus's relative sizes while composing the elements as a block.
    """
    if not slots:
        return slots
    top = min(s["top"] for s in slots)
    bottom = max(s["top"] + s["height"] for s in slots)
    span = bottom - top
    if span <= 0:
        return slots

    usable = 1.0 - margin * 2
    scaled = [
        {
            **s,
            "top": margin + (s["top"] - top) / span * usable,
            "height": s["height"] / span * usable,
        }
        for s in slots
    ]
    if len(scaled) == 1:
        return scaled

    gutter = 0.03
    grown: list[dict[str, float]] = []
    for index, slot in enumerate(scaled):
        new_top = slot["top"]
        new_bottom = slot["top"] + slot["height"]
        if index > 0:
            previous = scaled[index - 1]
            gap = slot["top"] - (previous["top"] + previous["height"])
            new_top -= max(gap - gutter, 0) / 2
        if index < len(scaled) - 1:
            gap = scaled[index + 1]["top"] - new_bottom
            new_bottom += max(gap - gutter, 0) / 2
        grown.append({**slot, "top": new_top, "height": new_bottom - new_top})
    return grown


def _font(size: int) -> ImageFont.FreeTypeFont:
    if BRAND_FONT.is_file():
        return ImageFont.truetype(str(BRAND_FONT), size)
    return ImageFont.load_default()


def _fit_text(draw: ImageDraw.ImageDraw, text: str, box_w: int, box_h: int) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Largest size that fits, wrapping onto as many lines as the slot allows."""
    words = text.split()
    best: tuple[ImageFont.FreeTypeFont, list[str]] | None = None
    for lines_wanted in (1, 2, 3):
        if lines_wanted > len(words):
            break
        # Split as evenly as possible across the wanted number of lines.
        per = -(-len(words) // lines_wanted)
        lines = [" ".join(words[i : i + per]) for i in range(0, len(words), per)]
        size = 8
        while size < 400:
            font = _font(size + 4)
            widest = max(draw.textlength(line, font=font) for line in lines)
            total_h = (size + 4) * 1.06 * len(lines)
            if widest > box_w or total_h > box_h:
                break
            size += 4
        font = _font(max(size, 8))
        area = draw.textlength(max(lines, key=len), font=font) * size * len(lines)
        if best is None or area > best[2]:  # type: ignore[misc]
            best = (font, lines, area)  # type: ignore[assignment]
    assert best is not None
    return best[0], best[1]  # type: ignore[return-value]


def _draw_element(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    element: Element,
    slot: dict[str, float],
    ink: str,
) -> None:
    box_w = int(slot["width"] * CANVAS)
    box_h = int(slot["height"] * CANVAS)
    cx = int(slot["centre_x"] * CANVAS)
    top = int(slot["top"] * CANVAS)

    if element.kind in {"image", "logo"} and element.image_bytes:
        art = Image.open(BytesIO(element.image_bytes)).convert("RGBA")
        art.thumbnail((box_w, box_h), Image.LANCZOS)
        canvas.paste(art, (cx - art.width // 2, top + (box_h - art.height) // 2), art)
        return

    if not element.text.strip():
        return

    font, lines = _fit_text(draw, element.text.upper(), box_w, box_h)
    ascent, descent = font.getmetrics()
    line_h = (ascent + descent) * 1.06
    block_h = line_h * len(lines)
    y = top + (box_h - block_h) / 2
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text((cx - w / 2, y), line, font=font, fill=ink)
        y += line_h


def generate(
    elements: list[Element],
    layouts: dict[int, Layout] | None = None,
    max_options: int = 3,
) -> list[GeneratedDesign]:
    """Compose the supplied elements into rendered design options."""
    if not elements:
        return []

    available = layouts if layouts is not None else load_layouts()
    count = len(elements)

    # The layout for this element count, plus neighbours as alternatives: a
    # three-element idea often reads better as two if the third is small.
    candidates: list[Layout] = []
    if count in available:
        candidates.append(available[count])
    for offset in (1, -1):
        neighbour = available.get(count + offset)
        if neighbour and len(candidates) < 2:
            candidates.append(neighbour)
    if not candidates:
        candidates = [FALLBACK_LAYOUTS.get(min(count, 3), FALLBACK_LAYOUTS[1])]

    designs: list[GeneratedDesign] = []
    for layout in candidates:
        for garment_name, garment_hex, ink_name, ink_hex in COLOURWAYS:
            if len(designs) >= max_options:
                break
            canvas = Image.new("RGB", (CANVAS, CANVAS), garment_hex)
            draw = ImageDraw.Draw(canvas)

            slots = _normalise(layout.slots)
            notes: list[str] = []
            if len(elements) > len(slots):
                notes.append(
                    f"{len(elements)} elements into {len(slots)} measured slots — "
                    "the last ones share the final slot. Consider dropping one: the "
                    "constitution allows no more than three hierarchy levels."
                )
            for index, element in enumerate(elements):
                slot = slots[min(index, len(slots) - 1)]
                _draw_element(canvas, draw, element, slot, ink_hex)

            buffer = BytesIO()
            canvas.save(buffer, format="PNG")
            designs.append(
                GeneratedDesign(
                    layout_name=layout.name,
                    evidence=layout.evidence,
                    ink=ink_name,
                    garment=garment_name,
                    png=buffer.getvalue(),
                    notes=notes,
                )
            )
    return designs[:max_options]
