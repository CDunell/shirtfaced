"""Presenting supplied content the way the corpus presents it.

The engine takes an image, a phrase and some text from the owner and decides how
to show them. This is that decision, made from measurements rather than opinion:

    content + garment + seed  ->  a layout, a size, a place, inks, a treatment

Everything it decides comes from something counted. The arrangement is one of
fourteen mined off 1,166 real designs. The print area is the garment's own zone
in millimetres. The inks are checked against the cloth for separation. Nothing
here holds a picture of anything: the subject is supplied, and the archive
contributes furniture -- a rule, a frame, a texture -- and never content.

Deliberately separate from ``design_composer``. That one fills hand-written
grammars from the element archive, which is the right shape for a design made
*of* archive parts and the wrong shape for presenting something the owner
brought. Both can exist; they answer different questions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.archive.garment import Garment, GarmentError
from app.archive.palettes import ColourSystem
from app.archive.palettes import choose as choose_palette
from app.archive.svg import Canvas, num, rng_for
from app.archive.templates import NoTemplate, Template
from app.archive.templates import choose as choose_template
from app.archive.typeset import MissingGlyph, set_line

# What the owner can hand over. An image is referenced rather than embedded, so
# a design stays small and the file it points at stays the record.
IMAGE = "image"
WORDS = "words"


class CannotPresent(Exception):
    """The content cannot be laid out, with a durable reason code."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Content:
    """What the owner supplied. Never invented, never edited."""

    # Ordered, because the order they gave them is information: the first thing
    # is the thing the design is about.
    items: tuple[tuple[str, str], ...] = ()

    @classmethod
    def of(cls, *, image: str = "", phrase: str = "", line: str = "") -> Content:
        supplied: list[tuple[str, str]] = []
        if image.strip():
            supplied.append((IMAGE, image.strip()))
        if phrase.strip():
            supplied.append((WORDS, phrase.strip()))
        if line.strip():
            supplied.append((WORDS, line.strip()))
        return cls(items=tuple(supplied))

    def __len__(self) -> int:
        return len(self.items)


@dataclass
class Presentation:
    """One laid-out design, and what decided it."""

    svg: str
    width_mm: float
    height_mm: float
    template: Template
    palette: ColourSystem
    inks: tuple[str, ...]
    placement_key: str
    # Why it looks like this, in counts rather than adjectives.
    rationale: str = ""
    warnings: list[str] = field(default_factory=list)


def _fit_words(text: str, box_width: float, box_height: float) -> tuple[str, float, float]:
    """Set one line to fill its box without overrunning it.

    The box comes from the corpus and the type comes from a font file, so they
    have no reason to agree. The type yields: a slot is a promise about how much
    room this content gets, and honouring the promise matters more than filling
    it exactly.
    """
    setting = set_line(text, cap_height=box_height)
    if setting.width <= 0:
        return "", 0.0, 0.0
    scale = min(1.0, box_width / setting.width)
    return setting.path, setting.width * scale, scale


def present(
    content: Content,
    garment: Garment,
    placement_key: str,
    seed: int,
    *,
    # The cloth is a brief input rather than a property of the drawing: the same
    # tee file is printed on black and on natural, and contrast is a property of
    # the pair.
    garment_colour: str = "#101010",
    colour_system: str = "",
    tradition: str = "streetwear",
    inks: int = 2,
) -> Presentation:
    """Lay supplied content out on a garment. Same inputs, same bytes."""
    if not len(content):
        raise CannotPresent("NO_CONTENT", "nothing was supplied to present")

    try:
        # Through the garment's own lookup, which resolves a request for
        # "short_sleeve" on a file that splits the zone per side.
        zone = garment.zone(placement_key)
    except GarmentError as error:
        raise CannotPresent(
            "NO_SUCH_ZONE",
            f"{placement_key} is not printable on {garment.name}; it has "
            f"{', '.join(sorted(garment.zones)) or 'no zones'}",
        ) from error

    try:
        template = choose_template(len(content), seed, tradition)
    except NoTemplate as error:
        raise CannotPresent("NO_TEMPLATE", str(error)) from error

    system = choose_palette(garment_colour, seed, colour_system)
    palette_inks = system.for_count(inks, garment_colour)

    canvas = Canvas(zone.width, zone.height)
    warnings: list[str] = []

    for (kind, value), slot in zip(content.items, template.slots, strict=False):
        left, top, box_width, box_height = slot.box(zone.width, zone.height)
        ink = palette_inks[slot.index % len(palette_inks)]

        if kind == IMAGE:
            # Referenced, not embedded. The supplied file is the record and a
            # design that carries a copy of it is a second copy to keep in step.
            canvas.add(
                f'<image href="{value}" x="{num(left)}" y="{num(top)}" '
                f'width="{num(box_width)}" height="{num(box_height)}" '
                f'preserveAspectRatio="xMidYMid meet"/>'
            )
            continue

        try:
            path, drawn_width, scale = _fit_words(value, box_width, box_height)
        except MissingGlyph as error:
            raise CannotPresent("MISSING_GLYPH", str(error)) from error
        if not path:
            warnings.append(f"nothing set for {value!r}")
            continue
        x = left + (box_width - drawn_width) / 2
        canvas.add(
            f'<g transform="translate({num(x)} {num(top + box_height)}) '
            f'scale({num(scale)})"><path d="{path}" fill="{ink}"/></g>'
        )

    words = sum(len(v.split()) for k, v in content.items if k == WORDS)
    rationale = (
        f"{template.name}: {template.designs} of 1,166 corpus designs "
        f"({template.share:.0%} of {template.elements}-element designs). "
        f"{words} word(s) against a corpus median of {template.median_words:.0f}. "
        f"{system.label} inks, checked against {garment_colour}. "
        f"{zone.width:.0f}x{zone.height:.0f}mm from the garment's own zone."
    )

    # Salted so adding a decision here cannot shift one made elsewhere.
    rng_for(seed, "present", template.id)

    return Presentation(
        svg=canvas.to_svg(),
        width_mm=zone.width,
        height_mm=zone.height,
        template=template,
        palette=system,
        inks=palette_inks,
        placement_key=placement_key,
        rationale=rationale,
        warnings=warnings,
    )
