"""Rendering one archive element with supplied content.

The contract this module exists to hold:

    element + content + palette + seed  ->  the same bytes, every time

Not "the same design" or "visually identical" -- the same bytes. Anything weaker
drifts, and nobody notices until a reprint does not match the original. The test
suite asserts it directly rather than trusting the discipline.

Three things make it true, and all three are easy to lose:

*No ambient randomness.* Every varying transformation draws from a generator
seeded here and salted by purpose, so adding a call to one does not shift
another.

*No ambient time.* Nothing stamps a date into the output.

*No deferred layout.* Text is outlines, not a font reference, so the file does
not become a different design on a machine with different fonts installed.

The licence gate is enforced before anything is drawn. An element whose rights
are unverified is not rendered at all -- not watermarked, not rendered with a
warning. These go on garments that are sold.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from app.archive import geometry
from app.archive.svg import Canvas, num, rng_for
from app.archive.typeset import MissingGlyph, set_arc, set_line
from app.domain.element import Element, Slot

# Bumped whenever a change here alters output for unchanged inputs. Stored
# against every render, because attributing new output to an old row is how a
# reprint quietly stops matching.
RENDERER_VERSION = "1.0.0"


class RefusedToRender(Exception):
    """The element may not be rendered, with a durable reason code."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Palette:
    """The inks available, in order of dominance.

    The garment colour is carried alongside because contrast is a property of
    the pair, not of the ink: the same green is a different decision on black
    than on natural.
    """

    garment: str = "#101010"
    inks: tuple[str, ...] = ("#F2F0EA",)

    @property
    def count(self) -> int:
        return len(self.inks)

    def ink(self, index: int) -> str:
        return self.inks[index % len(self.inks)] if self.inks else "#000000"


@dataclass
class RenderedElement:
    """The artwork, plus what is needed to prove it can be rebuilt."""

    svg: str
    width_mm: float
    height_mm: float
    content_hash: str
    renderer_version: str = RENDERER_VERSION
    warnings: list[str] = field(default_factory=list)


def _fill_slot(
    canvas: Canvas,
    slot: Slot,
    text: str,
    box_width: float,
    box_height: float,
    colour: str,
) -> None:
    """Set one slot's supplied text at the slot's own proportions."""
    slot_width = box_width * slot.width
    slot_height = box_height * slot.height
    left = box_width * slot.centre_x - slot_width / 2
    top = box_height * slot.top

    if slot.path in ("upper_arc", "lower_arc"):
        # The radius that makes the word span the slot's width at this height.
        radius = max(slot_width * 0.62, slot_height)
        setting = set_arc(
            text,
            radius=radius,
            cap_height=slot_height,
            tracking=slot.tracking,
            upper=slot.path == "upper_arc",
        )
        # set_arc centres the word on the arc's own origin, so the group is
        # moved to the slot's centre and down by the radius.
        centre_x = box_width * slot.centre_x
        centre_y = top + (radius if slot.path == "upper_arc" else 0.0)
        canvas.add(
            f'<g transform="translate({num(centre_x)} {num(centre_y)})">'
            f'<path d="{setting.path}" fill="{colour}"/></g>'
        )
        return

    setting = set_line(text, cap_height=slot_height, tracking=slot.tracking)
    # Fit to the slot rather than overrunning it: the slot is the promise the
    # element makes about how much room this content gets.
    scale = min(1.0, slot_width / setting.width) if setting.width > 0 else 1.0
    drawn_width = setting.width * scale
    if slot.alignment == "left":
        x = left
    elif slot.alignment == "right":
        x = left + slot_width - drawn_width
    else:
        x = box_width * slot.centre_x - drawn_width / 2
    y = top + slot_height

    canvas.add(
        f'<g transform="translate({num(x)} {num(y)}) scale({num(scale)})">'
        f'<path d="{setting.path}" fill="{colour}"/></g>'
    )


def _frame_path(element: Element, width: float, height: float) -> str:
    """The element's own outline, from its recipe and parameters."""
    parameters = element.parameters
    recipe = element.recipe

    if recipe == "frame.rectangle":
        return geometry.rectangle(width, height, radius=parameters.get("radius", 0.0))
    if recipe == "frame.capsule":
        return geometry.capsule(width, height)
    if recipe == "frame.shield":
        return geometry.shield(
            width,
            height,
            shoulder=parameters.get("shoulder", 0.26),
            point=parameters.get("point", 0.34),
        )
    if recipe == "frame.circle":
        return geometry.circle(min(width, height))
    if recipe == "frame.arch":
        return geometry.arch(width, height, spring=parameters.get("spring", 0.55))
    if recipe == "frame.ticket":
        return geometry.ticket(width, height, notch=parameters.get("notch", 0.12))
    if recipe == "frame.plaque":
        return geometry.plaque(width, height, inset=parameters.get("inset", 0.14))
    if recipe == "symbol.star":
        return geometry.star(
            min(width, height),
            points=int(parameters.get("points", 5)),
            inner=parameters.get("inner", 0.40),
        )
    if recipe == "symbol.bolt":
        return geometry.bolt(width, height)
    if recipe == "symbol.arrow":
        return geometry.arrow(width, height)
    if recipe == "symbol.cross":
        return geometry.cross(min(width, height))
    if recipe == "symbol.burst":
        return geometry.burst(min(width, height), spikes=int(parameters.get("spikes", 12)))
    if recipe == "symbol.chevron":
        return geometry.chevron(width, height)
    if recipe == "ornament.divider":
        return geometry.divider(width, height)
    if recipe == "ornament.corner":
        return geometry.corner_mark(min(width, height))
    if recipe == "ornament.bracket":
        return geometry.bracket(width, height)
    if recipe == "type_layout.plain":
        return ""
    raise RefusedToRender("UNKNOWN_RECIPE", recipe)


def box_for(element: Element, longest_mm: float = 180.0) -> tuple[float, float]:
    """The element's own proportions at a given longest side.

    Elements declare an aspect because their shape depends on it -- a capsule
    drawn in a square box is a circle, and a tapered rule is a blob. Callers
    that do not care get the element's intended shape rather than a square that
    silently changes what the element is.
    """
    aspect = float(element.parameters.get("aspect", 1.0))
    if aspect >= 1.0:
        return longest_mm, longest_mm / aspect
    return longest_mm * aspect, longest_mm


def render(
    element: Element,
    content: dict[str, str],
    palette: Palette,
    seed: int,
    width_mm: float | None = None,
    height_mm: float | None = None,
    treatment: str = "clean",
    longest_mm: float = 180.0,
) -> RenderedElement:
    """Render one element. The same arguments always produce the same bytes."""
    if width_mm is None or height_mm is None:
        default_width, default_height = box_for(element, longest_mm)
        width_mm = default_width if width_mm is None else width_mm
        height_mm = default_height if height_mm is None else height_mm

    usable, refusal = element.usable_with(palette.count, treatment)
    if not usable:
        raise RefusedToRender(refusal, element.id)

    canvas = Canvas(width_mm, height_mm)
    warnings: list[str] = []

    outline = _frame_path(element, width_mm, height_mm)
    if outline:
        stroke = element.parameters.get("stroke", 0.0)
        if stroke > 0:
            canvas.path(
                outline,
                fill="none",
                stroke=palette.ink(0),
                stroke_width=num(stroke * min(width_mm, height_mm) / 100),
            )
        else:
            canvas.path(outline, fill=palette.ink(0))

    # Ink index 1 onwards for content, so the frame and the words are separable
    # on press. With a single ink they collapse to the same colour, which is
    # what a one-colour job actually is.
    content_ink = palette.ink(1 if palette.count > 1 else 0)

    for slot in element.slots:
        supplied = content.get(slot.name, "").strip()
        if not supplied:
            # A slot with nothing in it is left empty rather than filled with a
            # placeholder. The archive never invents content.
            warnings.append(f"slot '{slot.name}' was left empty")
            continue
        try:
            _fill_slot(canvas, slot, supplied, width_mm, height_mm, content_ink)
        except MissingGlyph as error:
            raise RefusedToRender("MISSING_GLYPH", str(error)) from error

    if treatment == "distressed":
        generator = rng_for(seed, element.id, "distress")
        for mark in geometry.distress(width_mm, height_mm, generator):
            canvas.path(mark, fill=palette.garment)

    svg = canvas.to_svg()
    return RenderedElement(
        svg=svg,
        width_mm=width_mm,
        height_mm=height_mm,
        content_hash=hashlib.sha256(svg.encode("utf-8")).hexdigest(),
        warnings=warnings,
    )
