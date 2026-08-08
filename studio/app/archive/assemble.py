"""Building one design out of several parts.

The renderer draws one element. This draws a grammar: a frame with a mark inside
it and a word arched over the top, as one piece of artwork with one set of inks.

Two things it does that single-element rendering never had to:

*It decides what fills each role.* A grammar asks for "a frame" and the archive
offers nine. Which one is chosen comes from the brief's style, the density
budget, and a seeded draw for the rest -- so the same brief with a different
seed gives a genuinely different design rather than the same one twice.

*It spends a budget.* Each part costs some of what the placement can carry, and
optional parts are dropped when the money runs out. This is what stops four
intricate things landing in a left-chest print because each one passed its own
check separately.

The output is still one deterministic SVG. Same brief, same seed, same bytes.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field

from app.archive.grammar import Grammar, Part, density_budget
from app.archive.placements import Placement
from app.archive.render import Palette, RefusedToRender, _frame_path
from app.archive.svg import Canvas, num, rng_for
from app.archive.typeset import MissingGlyph, set_arc, set_line
from app.domain.element import Element

ASSEMBLER_VERSION = "1.0.0"

# What each kind of part costs against the density budget. Type is cheap because
# it is what people came to read; a busy mark is dear because it competes.
TITLE_COST = 0.22
FOOTER_COST = 0.10
RULE_COST = 0.06


@dataclass
class AssembledDesign:
    """One finished design and how it was arrived at."""

    svg: str
    width_mm: float
    height_mm: float
    content_hash: str
    grammar_key: str
    grammar_name: str
    reads_as: str
    # role -> element key, for the parts that came from the archive.
    chosen: dict[str, str] = field(default_factory=dict)
    dropped: list[str] = field(default_factory=list)
    density_spent: float = 0.0
    density_allowed: float = 0.0
    warnings: list[str] = field(default_factory=list)
    assembler_version: str = ASSEMBLER_VERSION


def _candidates(part: Part, elements: tuple[Element, ...]) -> list[Element]:
    """Archive elements that could fill this role.

    A part asking for a frame gets frames; a part asking for nothing in
    particular gets anything without slots of its own, because an element with
    its own slots is a design rather than a component.
    """
    found = []
    for element in elements:
        family = element.recipe.split(".", 1)[0] if element.recipe else element.family
        if part.families and family not in part.families:
            continue
        if part.slot:
            continue
        found.append(element)
    return found


def _pick(
    part: Part,
    elements: tuple[Element, ...],
    style_tags: tuple[str, ...],
    generator: random.Random,
) -> Element | None:
    """Choose one element for a role.

    Weighted by style rather than filtered by it, then drawn. Filtering on style
    makes an archive of thousands behave like an archive of ten; weighting keeps
    the unexpected reachable, which is most of the point of having thousands.
    """
    candidates = _candidates(part, elements)
    if not candidates:
        return None

    weights = []
    for element in candidates:
        overlap = len(set(style_tags) & set(element.style_tags))
        # A style match is worth about four times an ordinary candidate, so it
        # usually wins and occasionally does not.
        weights.append(1.0 + 4.0 * overlap)

    total = sum(weights)
    draw = generator.random() * total
    running = 0.0
    for element, weight in zip(candidates, weights, strict=True):
        running += weight
        if draw <= running:
            return element
    return candidates[-1]


def _place_text(
    canvas: Canvas,
    part: Part,
    text: str,
    width: float,
    height: float,
    colour: str,
    arc: bool,
) -> None:
    box_width = width * part.width
    box_height = height * part.height
    left = width * part.left
    top = height * part.top

    if arc:
        radius = max(box_width * 0.66, box_height)
        setting = set_arc(text, radius=radius, cap_height=box_height, tracking=-0.015)
        canvas.add(
            f'<g transform="translate({num(left + box_width / 2)} {num(top + radius)})">'
            f'<path d="{setting.path}" fill="{colour}"/></g>'
        )
        return

    setting = set_line(text, cap_height=box_height)
    scale = min(1.0, box_width / setting.width) if setting.width > 0 else 1.0
    drawn = setting.width * scale
    canvas.add(
        f'<g transform="translate({num(left + (box_width - drawn) / 2)} '
        f'{num(top + box_height)}) scale({num(scale)})">'
        f'<path d="{setting.path}" fill="{colour}"/></g>'
    )


def assemble(
    grammar: Grammar,
    content: dict[str, str],
    elements: tuple[Element, ...],
    palette: Palette,
    placement: Placement,
    seed: int,
    width_mm: float,
    height_mm: float,
) -> AssembledDesign:
    """Build one design from a grammar. Same inputs, same bytes."""
    generator = rng_for(seed, grammar.key, "assemble")
    allowed = density_budget(placement)
    spent = 0.0

    chosen: dict[str, str] = {}
    dropped: list[str] = []
    warnings: list[str] = []
    # Whether something solid has already been laid down underneath. Anything
    # drawn on top of a solid shape in the same ink is invisible, so it knocks
    # out to the garment colour instead -- which is what a printer would do
    # rather than spend a second screen saying the same thing.
    solid_ground = False
    # (layer, order, markup) so drawing order is explicit rather than incidental.
    drawn: list[tuple[int, int, str]] = []

    # What each part will cost, worked out before anything is spent. Charging as
    # we go let required parts through unchecked, so only optional ones ever
    # respected the budget and a crest on a left chest quietly overspent it.
    resolved: list[tuple[int, Part, Element | None, float]] = []
    for order, part in enumerate(grammar.parts):
        if part.slot:
            if not content.get(part.slot, "").strip():
                if not part.optional:
                    raise RefusedToRender("MISSING_REQUIRED_CONTENT", part.slot)
                dropped.append(part.role)
                continue
            cost = TITLE_COST if part.role in ("title", "banner") else FOOTER_COST
            resolved.append((order, part, None, cost))
            continue

        element = _pick(part, elements, grammar.style_tags, generator)
        if element is None:
            if not part.optional:
                raise RefusedToRender("NO_ELEMENT_FOR_ROLE", part.role)
            dropped.append(part.role)
            continue
        cost = element.complexity if part.role != "rule" else RULE_COST
        resolved.append((order, part, element, cost))

    # If the parts that cannot be dropped already cost more than the placement
    # can carry, the grammar is wrong for this placement. That is an answer, not
    # a reason to crowd the print.
    required = sum(cost for _, part, _, cost in resolved if not part.optional)
    if required > allowed:
        raise RefusedToRender(
            "DENSITY_BUDGET_EXCEEDED",
            f"{grammar.key} needs {required:.2f} on a {placement.label.lower()} "
            f"that carries {allowed:.2f}",
        )

    # Required parts first, then optional ones while the budget lasts.
    keep = [entry for entry in resolved if not entry[1].optional]
    spent = required
    for entry in resolved:
        if not entry[1].optional:
            continue
        _, part, element, cost = entry
        if spent + cost > allowed:
            dropped.append(part.role)
            warnings.append(f"{part.role} dropped: it would overload a {placement.label.lower()}")
            continue
        spent += cost
        keep.append(entry)
    keep.sort(key=lambda entry: entry[0])

    for order, part, element, _cost in keep:
        if part.slot:
            text = content[part.slot].strip()
            ink = palette.garment if solid_ground else palette.ink(1 if palette.count > 1 else 0)
            frame_canvas = Canvas(width_mm, height_mm)
            try:
                _place_text(
                    frame_canvas,
                    part,
                    text,
                    width_mm,
                    height_mm,
                    ink,
                    arc=part.role in ("title", "banner")
                    and grammar.key in ("crest", "flanked_word"),
                )
            except MissingGlyph as error:
                raise RefusedToRender("MISSING_GLYPH", str(error)) from error
            drawn.append((part.layer, order, "".join(frame_canvas.elements)))
            continue

        if element is None:
            continue
        chosen[part.role] = element.id

        box_width = width_mm * part.width
        box_height = height_mm * part.height
        path = _frame_path(element, box_width, box_height)
        if not path:
            continue
        stroke = element.parameters.get("stroke", 0.0)
        filled = stroke <= 0
        ink = palette.garment if (solid_ground and filled) else palette.ink(0)
        attributes = (
            f'fill="none" stroke="{ink}" '
            f'stroke-width="{num(stroke * min(box_width, box_height) / 100)}"'
            if stroke > 0
            else f'fill="{ink}"'
        )
        # A filled shape covering most of the design becomes the ground that
        # everything after it has to knock out of.
        if filled and part.width * part.height > 0.5:
            solid_ground = True
        drawn.append(
            (
                part.layer,
                order,
                f'<g transform="translate({num(width_mm * part.left)} '
                f'{num(height_mm * part.top)})"><path d="{path}" {attributes}/></g>',
            )
        )

    canvas = Canvas(width_mm, height_mm)
    for _, _, markup in sorted(drawn, key=lambda item: (item[0], item[1])):
        canvas.add(markup)

    svg = canvas.to_svg()
    return AssembledDesign(
        svg=svg,
        width_mm=width_mm,
        height_mm=height_mm,
        content_hash=hashlib.sha256(svg.encode("utf-8")).hexdigest(),
        grammar_key=grammar.key,
        grammar_name=grammar.name,
        reads_as=grammar.reads_as,
        chosen=chosen,
        dropped=dropped,
        density_spent=round(spent, 3),
        density_allowed=allowed,
        warnings=warnings,
    )
