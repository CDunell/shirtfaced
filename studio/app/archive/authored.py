"""The authored elements: parametric geometry with declared slots and licences.

Ten of the archive's fourteen families cannot be ingested -- they are geometry
and render recipes rather than artwork. This is where they are written.

Every element here carries a licence marked verified with Shirtfaced as the
source, which is not paperwork: the composer only reaches verified elements, and
authored geometry is the one category whose rights are not in question. Ingested
material will carry a real external source and will be checked per item.

Slots are what make these composable. An element with slots takes supplied words
and puts them somewhere specific at a specific size; one without can only be
placed. Nothing here contains a word -- the content is always the owner's.
"""

from __future__ import annotations

from datetime import date

from app.domain.element import Element, Licence, Slot
from app.domain.enums import LicenceStatus

# Authored in this repository, so the rights are ours and the record says so
# plainly rather than leaving a blank for someone to read as permission.
AUTHORED = Licence(
    status=LicenceStatus.VERIFIED,
    terms="Proprietary - Shirtfaced",
    source="shirtfaced",
    source_id="app/archive/authored.py",
    checked_at=date(2026, 8, 8),
    commercial_use=True,
    note="Parametric geometry authored in this repository. No third-party rights.",
)


def _frame(
    key: str,
    subtype: str,
    recipe: str,
    *,
    slots: tuple[Slot, ...] = (),
    symmetry: str = "vertical",
    complexity: float = 0.2,
    ink_min: int = 1,
    ink_max: int = 3,
    style_tags: tuple[str, ...] = (),
    treatments: tuple[str, ...] = ("clean", "distressed"),
    exclusions: tuple[str, ...] = (),
    **parameters: float,
) -> Element:
    return Element(
        id=key,
        family=recipe.split(".", 1)[0],
        subtype=subtype,
        licence=AUTHORED,
        slots=slots,
        symmetry=symmetry,
        ink_min=ink_min,
        ink_max=ink_max,
        complexity=complexity,
        style_tags=style_tags,
        compatible_treatments=treatments,
        exclusions=exclusions,
        recipe=recipe,
        parameters=parameters,
    )


# --- Slot shapes reused across elements. Proportions of the element's own box,
# never of a garment, so one element serves any placement. ---

PRIMARY_ARCH = Slot(
    name="primary_text",
    top=0.06,
    height=0.19,
    width=0.82,
    centre_x=0.5,
    path="upper_arc",
    tracking=-0.015,
)

SECONDARY_BOTTOM = Slot(name="secondary_text", top=0.72, height=0.10, width=0.44, centre_x=0.5)

CENTRE_LEAD = Slot(name="primary_text", top=0.38, height=0.24, width=0.72, centre_x=0.5)

BADGE_TOP = Slot(
    name="primary_text", top=0.10, height=0.13, width=0.62, centre_x=0.5, path="upper_arc"
)

BADGE_BOTTOM = Slot(name="secondary_text", top=0.70, height=0.11, width=0.54, centre_x=0.5)


FRAMES: tuple[Element, ...] = (
    _frame(
        "frame_rect_0001",
        "plain_rectangle",
        "frame.rectangle",
        style_tags=("utilitarian", "modern"),
        radius=0.0,
        stroke=1.6,
        complexity=0.08,
    ),
    _frame(
        "frame_rect_0002",
        "rounded_rectangle",
        "frame.rectangle",
        style_tags=("utilitarian",),
        radius=8.0,
        stroke=1.6,
        complexity=0.10,
    ),
    _frame(
        "frame_capsule_0001",
        "capsule",
        "frame.capsule",
        style_tags=("sport", "modern"),
        stroke=1.6,
        complexity=0.10,
        aspect=3.0,
    ),
    _frame(
        "frame_shield_0001",
        "workwear_shield",
        "frame.shield",
        style_tags=("institutional", "workwear", "utilitarian"),
        shoulder=0.26,
        point=0.34,
        complexity=0.28,
    ),
    _frame(
        "frame_shield_0002",
        "narrow_shield",
        "frame.shield",
        style_tags=("institutional", "heraldic"),
        shoulder=0.34,
        point=0.44,
        complexity=0.30,
        aspect=0.72,
    ),
    _frame(
        "frame_circle_0001",
        "roundel",
        "frame.circle",
        symmetry="radial",
        style_tags=("institutional", "club"),
        complexity=0.12,
    ),
    _frame(
        "frame_arch_0001",
        "arch",
        "frame.arch",
        style_tags=("vintage", "memorial"),
        spring=0.55,
        complexity=0.18,
    ),
    _frame(
        "frame_ticket_0001",
        "ticket_stub",
        "frame.ticket",
        style_tags=("ephemera", "vintage"),
        notch=0.12,
        complexity=0.22,
        aspect=2.4,
    ),
    _frame(
        "frame_plaque_0001",
        "cartouche",
        "frame.plaque",
        style_tags=("vintage", "ornamental"),
        inset=0.14,
        complexity=0.24,
    ),
)


BADGES: tuple[Element, ...] = (
    _frame(
        "badge_shield_0001",
        "workwear_shield",
        "frame.shield",
        slots=(BADGE_TOP, BADGE_BOTTOM),
        style_tags=("institutional", "workwear", "utilitarian"),
        treatments=("clean", "distressed", "embroidered"),
        exclusions=("photographic",),
        complexity=0.34,
        shoulder=0.26,
        point=0.34,
        stroke=1.4,
    ),
    _frame(
        "badge_roundel_0001",
        "club_roundel",
        "frame.circle",
        slots=(BADGE_TOP, BADGE_BOTTOM),
        symmetry="radial",
        style_tags=("club", "institutional", "sport"),
        treatments=("clean", "distressed", "embroidered"),
        exclusions=("photographic",),
        complexity=0.36,
        stroke=1.4,
    ),
    _frame(
        "badge_arch_0001",
        "institutional_arch",
        "frame.arch",
        slots=(BADGE_TOP, BADGE_BOTTOM),
        style_tags=("institutional", "vintage"),
        treatments=("clean", "distressed"),
        complexity=0.32,
        spring=0.55,
        stroke=1.4,
    ),
)


TYPE_LAYOUTS: tuple[Element, ...] = (
    _frame(
        "type_collegiate_arch_0001",
        "collegiate_arch",
        "type_layout.plain",
        slots=(PRIMARY_ARCH, SECONDARY_BOTTOM),
        style_tags=("collegiate", "athletic", "varsity"),
        treatments=("clean", "distressed"),
        ink_min=1,
        ink_max=3,
        complexity=0.22,
    ),
    _frame(
        "type_stack_0001",
        "condensed_stack",
        "type_layout.plain",
        slots=(
            Slot(name="primary_text", top=0.20, height=0.22, width=0.86, centre_x=0.5),
            Slot(name="secondary_text", top=0.50, height=0.14, width=0.62, centre_x=0.5),
        ),
        style_tags=("modern", "streetwear"),
        ink_min=1,
        ink_max=2,
        complexity=0.14,
    ),
    _frame(
        "type_oversized_0001",
        "oversized_word_microcopy",
        "type_layout.plain",
        slots=(
            CENTRE_LEAD,
            Slot(name="secondary_text", top=0.68, height=0.06, width=0.38, centre_x=0.5),
        ),
        style_tags=("modern", "streetwear", "bold"),
        ink_min=1,
        ink_max=2,
        complexity=0.12,
    ),
)


SYMBOLS: tuple[Element, ...] = (
    _frame(
        "symbol_star_0001",
        "five_point_star",
        "symbol.star",
        symmetry="vertical",
        style_tags=("classic",),
        points=5,
        inner=0.40,
        complexity=0.16,
    ),
    _frame(
        "symbol_star_0002",
        "six_point_star",
        "symbol.star",
        symmetry="radial",
        style_tags=("classic",),
        points=6,
        inner=0.52,
        complexity=0.16,
    ),
    _frame(
        "symbol_bolt_0001",
        "lightning_bolt",
        "symbol.bolt",
        symmetry="none",
        style_tags=("energy", "sport"),
        complexity=0.18,
    ),
    _frame(
        "symbol_arrow_0001",
        "block_arrow",
        "symbol.arrow",
        symmetry="horizontal",
        style_tags=("utilitarian",),
        complexity=0.14,
    ),
    _frame(
        "symbol_cross_0001",
        "equal_cross",
        "symbol.cross",
        symmetry="radial",
        style_tags=("utilitarian", "medical"),
        complexity=0.12,
    ),
    _frame(
        "symbol_burst_0001",
        "sunburst",
        "symbol.burst",
        symmetry="radial",
        style_tags=("vintage", "energy"),
        spikes=12,
        complexity=0.26,
    ),
    _frame(
        "symbol_chevron_0001",
        "rank_chevron",
        "symbol.chevron",
        symmetry="vertical",
        style_tags=("military", "utilitarian"),
        complexity=0.12,
    ),
)


ORNAMENTS: tuple[Element, ...] = (
    _frame(
        "ornament_divider_0001",
        "tapered_rule",
        "ornament.divider",
        symmetry="horizontal",
        style_tags=("vintage", "printers"),
        complexity=0.08,
        aspect=8.0,
    ),
    _frame(
        "ornament_corner_0001",
        "corner_mark",
        "ornament.corner",
        symmetry="none",
        style_tags=("utilitarian", "modern"),
        complexity=0.06,
    ),
    _frame(
        "ornament_bracket_0001",
        "square_bracket",
        "ornament.bracket",
        symmetry="horizontal",
        style_tags=("utilitarian",),
        complexity=0.06,
    ),
)


ALL: tuple[Element, ...] = FRAMES + BADGES + TYPE_LAYOUTS + SYMBOLS + ORNAMENTS

BY_ID: dict[str, Element] = {element.id: element for element in ALL}


def element(key: str) -> Element:
    try:
        return BY_ID[key]
    except KeyError as error:
        raise KeyError(f"no authored element {key!r}") from error
