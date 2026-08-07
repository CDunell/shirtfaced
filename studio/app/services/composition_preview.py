"""Drawing a composition so it can be judged by eye.

A layout spec is a list of proportions, and proportions are not reviewable. The
owner's standing instruction is that decisions get made by looking at the
thing, not by reading a description of it, and an arrangement is exactly the
kind of claim that reads fine and looks wrong.

So each option the engine offers is drawn onto a garment at the proportions it
actually specifies, with the supplied words set in the brand face. This is a
*placement* preview and deliberately not finished artwork: it shows where
things sit and how large they are relative to each other, which is what the
engine is claiming. Type treatment, weight, texture and colour choices are the
generation step that section 7 gates behind approvals, and drawing them here
would show a design the engine has not earned the right to propose.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.services.composition_engine import Composition, Option

REPO_ROOT = Path(__file__).resolve().parents[3]
BRAND_FONT = REPO_ROOT / "assets" / "type" / "Shirtfaced-Regular.ttf"

# The print area on a tee front, as a share of the garment box. The engine's
# slot proportions are relative to this, never to the image.
PRINT_TOP = 0.20
PRINT_BOTTOM = 0.72
PRINT_LEFT = 0.22
PRINT_RIGHT = 0.78

GARMENT_FILL = (28, 28, 30)
GARMENT_EDGE = (70, 70, 74)
INK = (232, 232, 228)
LOGO_INK = (198, 255, 0)
CARD_BG = (18, 18, 19)
MUTED = (132, 132, 138)


# The brand face is a display face with a narrow character set -- it has no
# colon and no em dash, which rendered interface chrome as "BRIEF[]" and
# "two even bands [] paired lines". It belongs on the print, where the brand
# actually speaks; labels and captions get a plain UI face.
UI_FONT_CANDIDATES = (
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)


def _print_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """The brand face, for words that are actually printed on the garment."""
    if BRAND_FONT.is_file():
        try:
            return ImageFont.truetype(str(BRAND_FONT), size)
        except OSError:
            pass
    return _font(size)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """A plain face for labels, captions and any other interface chrome."""
    for candidate in UI_FONT_CANDIDATES:
        if candidate.is_file():
            try:
                return ImageFont.truetype(str(candidate), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _garment(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    """A plain tee silhouette. Enough to read placement against, no more."""
    left, top, right, bottom = box
    width = right - left
    height = bottom - top
    shoulder = top + int(height * 0.10)
    body_left = left + int(width * 0.16)
    body_right = right - int(width * 0.16)

    draw.polygon(
        [
            (body_left, shoulder),
            (left + int(width * 0.05), top + int(height * 0.06)),
            (left, top + int(height * 0.30)),
            (body_left, top + int(height * 0.36)),
            (body_left, bottom),
            (body_right, bottom),
            (body_right, top + int(height * 0.36)),
            (right, top + int(height * 0.30)),
            (right - int(width * 0.05), top + int(height * 0.06)),
            (body_right, shoulder),
        ],
        fill=GARMENT_FILL,
        outline=GARMENT_EDGE,
    )
    # Collar.
    draw.arc(
        [
            left + int(width * 0.38),
            top + int(height * 0.02),
            right - int(width * 0.38),
            top + int(height * 0.14),
        ],
        start=0,
        end=180,
        fill=GARMENT_EDGE,
        width=2,
    )


def _fit_text(
    text: str, target_width: int, target_height: int
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Largest brand-face size that fits the slot the engine specified."""
    size = max(8, target_height)
    while size > 7:
        font = _print_font(size)
        box = font.getbbox(text)
        if (box[2] - box[0]) <= target_width and (box[3] - box[1]) <= target_height:
            return font
        size -= 1
    return _print_font(8)


def draw_option(option: Option, size: tuple[int, int] = (300, 380)) -> Image.Image:
    """One option, drawn at the proportions it specifies."""
    canvas = Image.new("RGB", size, CARD_BG)
    draw = ImageDraw.Draw(canvas)

    margin = int(size[0] * 0.06)
    garment_box = (margin, margin, size[0] - margin, size[1] - margin - 26)
    _garment(draw, garment_box)

    gl, gt, gr, gb = garment_box
    gw, gh = gr - gl, gb - gt
    print_left = gl + int(gw * PRINT_LEFT)
    print_right = gl + int(gw * PRINT_RIGHT)
    print_top = gt + int(gh * PRINT_TOP)
    print_bottom = gt + int(gh * PRINT_BOTTOM)
    print_width = print_right - print_left
    print_height = print_bottom - print_top

    for slot in option.slots:
        slot_width = max(6, int(print_width * slot.width))
        slot_height = max(5, int(print_height * slot.height))
        centre = print_left + int(print_width * slot.centre_x)
        left = centre - slot_width // 2
        top = print_top + int(print_height * slot.top)

        if slot.element_kind in ("image", "logo"):
            # Placeholder mass, because no artwork has been supplied or earned.
            draw.rectangle(
                [left, top, left + slot_width, top + slot_height],
                outline=LOGO_INK,
                width=2,
            )
            label = slot.element_kind.upper()
            font = _fit_text(label, slot_width - 8, max(9, slot_height - 8))
            box = font.getbbox(label)
            draw.text(
                (
                    left + (slot_width - (box[2] - box[0])) // 2,
                    top + (slot_height - (box[3] - box[1])) // 2 - box[1],
                ),
                label,
                font=font,
                fill=LOGO_INK,
            )
        else:
            text = (slot.content or "").strip() or "—"
            font = _fit_text(text, slot_width, slot_height)
            box = font.getbbox(text)
            draw.text(
                (
                    left + (slot_width - (box[2] - box[0])) // 2,
                    top + (slot_height - (box[3] - box[1])) // 2 - box[1],
                ),
                text,
                font=font,
                fill=INK,
            )

    caption = _font(13)
    small = _font(11)
    draw.text((margin, size[1] - 24), option.template_name[:34], font=caption, fill=INK)
    draw.text(
        (margin, size[1] - 12),
        f"confidence {option.confidence:.2f} · {option.corpus_designs} designs",
        font=small,
        fill=MUTED,
    )
    return canvas


def draw_composition(
    composition: Composition, heading: str, size: tuple[int, int] = (300, 380)
) -> Image.Image:
    """Every option side by side, with the refusal shown when there is one."""
    header = 58
    if not composition.composable:
        canvas = Image.new("RGB", (size[0] * 2, header + 90), CARD_BG)
        draw = ImageDraw.Draw(canvas)
        draw.text((18, 16), heading, font=_font(15), fill=INK)
        draw.text((18, header), composition.refusal_reason, font=_font(15), fill=(255, 110, 110))
        draw.text((18, header + 22), composition.refusal_detail[:88], font=_font(11), fill=MUTED)
        return canvas

    count = len(composition.options)
    gap_lines = composition.gaps
    footer = 20 + 14 * len(gap_lines)
    canvas = Image.new("RGB", (size[0] * count, header + size[1] + footer), CARD_BG)
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 16), heading, font=_font(15), fill=INK)
    draw.text(
        (18, 36),
        f"{count} arrangement(s) the corpus supports",
        font=_font(11),
        fill=MUTED,
    )

    for index, option in enumerate(composition.options):
        canvas.paste(draw_option(option, size), (index * size[0], header))

    for line, gap in enumerate(gap_lines):
        draw.text(
            (18, header + size[1] + 6 + line * 14),
            f"gap — {gap[:110]}",
            font=_font(11),
            fill=(226, 170, 90),
        )
    return canvas
