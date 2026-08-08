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

from app.archive import geometry
from app.archive.grammar import Grammar, Part, density_budget_for
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


# One-colour separation, as a filter.
#
# Supplied flash arrives as JPEG, which has no transparency, so a mark placed on
# a black garment brought a white rectangle with it and a texture laid over a
# design washed the whole panel grey. Both are the same fault: the file is a
# picture and a print is ink or no ink.
#
# So luminance becomes alpha -- white transparent, black opaque -- and the
# result is flooded with a single colour. That is what a printer does to
# one-colour artwork, and it is why these files are black on white in the first
# place.
SEPARATION_FILTER = (
    '<filter id="{id}" x="0" y="0" width="100%" height="100%" '
    'color-interpolation-filters="sRGB">'
    '<feColorMatrix type="matrix" values="'
    "0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  "
    # Alpha from inverted luminance: a white pixel lands at 0, a black one at 1.
    '-0.2126 -0.7152 -0.0722 0 1"/>'
    '<feComponentTransfer><feFuncA type="linear" slope="{slope}" intercept="0"/>'
    "</feComponentTransfer>"
    '<feFlood flood-color="{ink}" result="ink"/>'
    '<feComposite in="ink" in2="SourceGraphic" operator="in"/>'
    "</filter>"
)


def _archive_url(source_file: str) -> str:
    """Where a stored artwork file is served from.

    `source_file` is repository-relative -- `assets/flash/wolf.jpg` -- and the
    route that serves it is mounted at /archive, so the leading folder is
    replaced rather than kept. Referring to /assets/... instead pointed at the
    generated-image store, which addresses by UUID and answered every one of
    these with a 404.
    """
    path = source_file.replace("\\", "/").lstrip("/")
    if path.startswith("assets/"):
        path = path[len("assets/") :]
    return f"archive/{path}"


def _candidates(part: Part, elements: tuple[Element, ...]) -> list[Element]:
    """Archive elements that could fill this role.

    A part asking for a frame gets frames; a part asking for nothing in
    particular gets anything.

    An element that declares its own text slots is not excluded. A badge used as
    a crest's frame simply has its own slots ignored while the grammar puts its
    title where the grammar says -- which is more useful than refusing a shape
    for carrying a feature nobody asked it to use.
    """
    found = []
    for element in elements:
        family = element.recipe.split(".", 1)[0] if element.recipe else element.family
        if part.families and family not in part.families:
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
        weight = 1.0 + 4.0 * overlap

        # Drawn artwork outranks parametric geometry for the same role. Both are
        # legitimate and a formula makes a better octagon than anyone can draw,
        # but across two hundred seeds the most-used parts were a label bar, a
        # row of dots and a droplet, while sixty-nine pieces of drawn flash
        # filled eight per cent of slots. The archive was reaching its weakest
        # material most often, which is the opposite of what having it is for.
        if element.source_file:
            weight *= 3.0

        # And a placeholder loses to anything else that fits. It is in the
        # archive so a role can be filled at all, not so it can be chosen.
        if element.provisional:
            weight *= 0.25

        weights.append(weight)

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
    treatment: str = "clean",
    wear: Element | None = None,
    wear_strength: float = 0.55,
) -> AssembledDesign:
    """Build one design from a grammar. Same inputs, same bytes.

    ``wear`` is a texture or print effect laid over the finished design rather
    than composed into it. It is not a part and no grammar asks for one: cracked
    plastisol does not sit beside the mark, it happens to it.
    """
    generator = rng_for(seed, grammar.key, "assemble")
    # From the box actually being drawn into, not from the table.
    allowed = density_budget_for(width_mm)
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

        # Raster elements -- textures, halftones, scanned flash -- carry no path
        # data at all. They were ingested and then unreachable: 145 of 226
        # elements had neither geometry nor a recipe, so the assembler skipped
        # every one of them. Drawn as an image reference rather than converted,
        # because tracing a scan of a wolf's head produces a worse wolf.
        if not element.geometry and not element.recipe and element.source_file:
            ink = palette.garment if solid_ground else palette.ink(0)
            filter_id = f"sep{order}"
            drawn.append(
                (
                    part.layer,
                    order,
                    SEPARATION_FILTER.format(id=filter_id, ink=ink, slope=1.0)
                    + f'<g transform="translate({num(width_mm * part.left)} '
                    f'{num(height_mm * part.top)})">'
                    f'<image href="/{_archive_url(element.source_file)}" '
                    f'width="{num(box_width)}" height="{num(box_height)}" '
                    f'preserveAspectRatio="xMidYMid meet" '
                    f'filter="url(#{filter_id})"/></g>',
                )
            )
            chosen[part.role] = element.id
            continue

        path = _frame_path(element, box_width, box_height)
        if not path:
            continue
        stroke = element.parameters.get("stroke", 0.0)
        filled = stroke <= 0
        ink = palette.garment if (solid_ground and filled) else palette.ink(0)
        # Ingested artwork fills even-odd, authored geometry fills nonzero.
        # Under nonzero a hole has to be wound against the shape around it, and
        # supplied artwork frequently is not -- a ring, an eye, a rim wound the
        # same way silently fills solid. Even-odd makes nesting decide, so a
        # file that would have arrived "wrong" is simply right. The rule is ours
        # to get correct, not a condition on what we are allowed to accept.
        rule = ' fill-rule="evenodd"' if element.source_file else ""
        attributes = (
            f'fill="none" stroke="{ink}" '
            f'stroke-width="{num(stroke * min(box_width, box_height) / 100)}"'
            if stroke > 0
            else f'fill="{ink}"{rule}'
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

    if treatment == "distressed":
        # Drilled out in the garment colour, over everything, so the wear reads
        # across the whole design rather than one part at a time.
        generator = rng_for(seed, grammar.key, "distress")
        for mark in geometry.distress(width_mm, height_mm, generator):
            canvas.path(mark, fill=palette.garment)

    if wear is not None and wear.source_file:
        # A texture or print effect worn over the finished design.
        #
        # These were the largest stranded group in the archive: no grammar asks
        # for a texture because a texture is not a part. Cracked plastisol does
        # not sit beside the mark, it happens *to* it, and a role in a grammar
        # cannot express that.
        #
        # Drawn in the garment colour rather than as a mask, because a mask
        # needs the texture inverted and every renderer between here and a
        # separator disagrees about how. Painting the wear in the colour of the
        # cloth is what an eroded print actually looks like, and it survives
        # being flattened.
        # Separated the same way and flooded with the *garment* colour, so the
        # texture eats holes in the ink instead of laying a grey film over the
        # whole panel. Screen blending did the latter and looked like fog.
        canvas.add(
            SEPARATION_FILTER.format(id="wear", ink=palette.garment, slope=1.0)
            + f'<image href="/{_archive_url(wear.source_file)}" '
            f'x="0" y="0" width="{num(width_mm)}" height="{num(height_mm)}" '
            f'preserveAspectRatio="none" filter="url(#wear)" '
            f'opacity="{num(wear_strength)}"/>'
        )

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
