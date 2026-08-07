"""Where a print may sit on a garment, and how large it may be.

The `placements/` family: garment coordinates and maximum print bounds. These
are constraints rather than geometry -- a placement does not draw anything, it
tells a composition where it is allowed to be and how much room it has.

Stored in millimetres. The source figures are in inches because print-on-demand
documentation is American, but the brand is Australian, its blanks are specified
in centimetres, and carrying two unit systems through a geometry pipeline is how
a print ends up 2.54 times the size it should be. Conversion happens once, here,
at the boundary.

**Provenance and its limits.** The figures come from Kittl's print-placement
guidance, supplied as reference. It is a design tool's summary of print-on-demand
convention, which makes it a good account of what the industry broadly does and
*not* a specification for any particular blank. Every real garment has its own
printable area, and a supplier's spec sheet outranks this table whenever the two
disagree. These are defaults to compose against and to check a composition has
not obviously overrun -- not permission to skip reading the blank's own spec.
"""

from __future__ import annotations

from dataclasses import dataclass

MM_PER_INCH = 25.4

# Print resolution the artwork must hold at final size. Vector output sidesteps
# this, which is one more reason the archive emits SVG; it matters when an
# ingested raster element is placed.
REQUIRED_DPI = 300

# Minimum clearance from any seam. A print closer than this either distorts
# over the seam or cannot be held flat on the platen.
DEFAULT_SEAM_CLEARANCE_MM = 1.0 * MM_PER_INCH
SLEEVE_SEAM_CLEARANCE_MM = 2.0 * MM_PER_INCH


def inches(value: float) -> float:
    """One conversion, at one boundary."""
    return round(value * MM_PER_INCH, 2)


@dataclass(frozen=True)
class Placement:
    """One printable zone, with the bounds a composition must fit inside."""

    key: str
    label: str
    # Garment panel this sits on, so a composition cannot put a back print on a
    # front-only template.
    panel: str
    # Maximum print, in millimetres. A composition may be smaller, never larger.
    max_width_mm: float
    max_height_mm: float
    # Typical print, used when nothing else decides the size. Distinct from the
    # maximum on purpose: composing to the maximum every time is what produces
    # a catalogue where every design is a jumbo front.
    typical_width_mm: float
    typical_height_mm: float
    # Distance from the reference seam, as a range. Both ends are real: the
    # narrow end is where it starts to crowd the collar, the wide end is where
    # it starts to disappear under the hem.
    offset_from_mm: float
    offset_to_mm: float
    offset_reference: str
    seam_clearance_mm: float = DEFAULT_SEAM_CLEARANCE_MM
    note: str = ""

    @property
    def aspect(self) -> float:
        return self.max_width_mm / max(self.max_height_mm, 1e-6)

    def fits(self, width_mm: float, height_mm: float) -> tuple[bool, str]:
        """Whether a composition of this size may use this placement."""
        if width_mm > self.max_width_mm:
            return False, "PRINT_WIDER_THAN_PLACEMENT"
        if height_mm > self.max_height_mm:
            return False, "PRINT_TALLER_THAN_PLACEMENT"
        return True, ""


# --- Adult. The default range; youth and toddler are scaled below. ---

ADULT_PLACEMENTS: tuple[Placement, ...] = (
    Placement(
        key="centre_chest",
        label="Centre chest",
        panel="front",
        max_width_mm=inches(11),
        max_height_mm=inches(11),
        typical_width_mm=inches(9),
        typical_height_mm=inches(9),
        offset_from_mm=inches(3),
        offset_to_mm=inches(3.5),
        offset_reference="collar",
        note="8-10in wide is the common range; 11in is the ceiling.",
    ),
    Placement(
        key="full_front",
        label="Full front",
        panel="front",
        max_width_mm=inches(12),
        max_height_mm=inches(16),
        typical_width_mm=inches(12),
        typical_height_mm=inches(14),
        offset_from_mm=inches(2),
        offset_to_mm=inches(3),
        offset_reference="collar",
        note="12-15in wide in practice; 16in tall is the ceiling.",
    ),
    Placement(
        key="left_chest",
        label="Left chest",
        panel="front",
        max_width_mm=inches(4.5),
        max_height_mm=inches(4.5),
        typical_width_mm=inches(3.5),
        typical_height_mm=inches(3.5),
        offset_from_mm=inches(5.5),
        offset_to_mm=inches(8),
        offset_reference="shoulder_seam",
        note="4-6in from the centreline. 4.5in suits horizontal lockups.",
    ),
    Placement(
        key="full_back",
        label="Full back",
        panel="back",
        max_width_mm=inches(12),
        max_height_mm=inches(14),
        typical_width_mm=inches(12),
        typical_height_mm=inches(14),
        offset_from_mm=inches(1),
        offset_to_mm=inches(3),
        offset_reference="back_collar",
    ),
    Placement(
        key="upper_back_yoke",
        label="Upper back yoke",
        panel="back",
        max_width_mm=inches(3),
        max_height_mm=inches(1.5),
        typical_width_mm=inches(2.5),
        typical_height_mm=inches(1),
        offset_from_mm=inches(1),
        offset_to_mm=inches(2),
        offset_reference="back_collar_seam",
    ),
    Placement(
        key="short_sleeve",
        label="Short sleeve",
        panel="sleeve",
        max_width_mm=inches(3),
        max_height_mm=inches(3),
        typical_width_mm=inches(2.5),
        typical_height_mm=inches(2.5),
        offset_from_mm=inches(1),
        offset_to_mm=inches(3),
        offset_reference="sleeve_hem",
        seam_clearance_mm=SLEEVE_SEAM_CLEARANCE_MM,
    ),
    Placement(
        key="long_sleeve",
        label="Long sleeve",
        panel="sleeve",
        max_width_mm=inches(2.5),
        max_height_mm=inches(14),
        typical_width_mm=inches(2),
        typical_height_mm=inches(10),
        offset_from_mm=inches(2),
        offset_to_mm=inches(3),
        offset_reference="shoulder_seam",
        seam_clearance_mm=SLEEVE_SEAM_CLEARANCE_MM,
    ),
    Placement(
        key="inner_neck_label",
        label="Inner neck label",
        panel="neck",
        max_width_mm=inches(3),
        max_height_mm=inches(3),
        typical_width_mm=inches(2.5),
        typical_height_mm=inches(2.5),
        offset_from_mm=inches(0.5),
        offset_to_mm=inches(1),
        offset_reference="back_collar_seam",
        note="Tagless label zone. Replaces a woven label rather than joining it.",
    ),
    Placement(
        key="outer_back_neck",
        label="Outer back neck",
        panel="back",
        max_width_mm=inches(4),
        max_height_mm=inches(4),
        typical_width_mm=inches(3),
        typical_height_mm=inches(1.5),
        offset_from_mm=inches(0.5),
        offset_to_mm=inches(1.5),
        offset_reference="back_collar_seam",
    ),
    Placement(
        key="pocket",
        label="Pocket",
        panel="front",
        max_width_mm=inches(3),
        max_height_mm=inches(3),
        typical_width_mm=inches(2.5),
        typical_height_mm=inches(2.5),
        offset_from_mm=inches(6),
        offset_to_mm=inches(8),
        offset_reference="shoulder_seam",
    ),
)


# --- Youth and toddler.
#
# The source gives explicit youth figures for the placements it covers and a
# proportional rule for the rest. Explicit numbers are used where they exist and
# the rule fills the gaps, rather than scaling everything and quietly
# contradicting the stated youth sizes. ---

YOUTH_OVERRIDES: dict[str, tuple[float, float]] = {
    # key -> (max width in inches, max height in inches)
    "centre_chest": (10.5, 10.5),
    "full_front": (10.5, 12.0),
    "left_chest": (3.5, 3.5),
}

YOUTH_SMALL_OVERRIDES: dict[str, tuple[float, float]] = {
    "centre_chest": (8.5, 8.5),
    "full_front": (9.0, 9.0),
    "left_chest": (3.0, 3.0),
}

# Applied only where no explicit figure is given.
YOUTH_SCALE = 0.80
TODDLER_SCALE = 0.55


def _scaled(
    placement: Placement, scale: float, overrides: dict[str, tuple[float, float]]
) -> Placement:
    override = overrides.get(placement.key)
    if override is not None:
        max_width, max_height = inches(override[0]), inches(override[1])
    else:
        max_width = round(placement.max_width_mm * scale, 2)
        max_height = round(placement.max_height_mm * scale, 2)

    ratio_w = max_width / max(placement.max_width_mm, 1e-6)
    ratio_h = max_height / max(placement.max_height_mm, 1e-6)
    return Placement(
        key=placement.key,
        label=placement.label,
        panel=placement.panel,
        max_width_mm=max_width,
        max_height_mm=max_height,
        typical_width_mm=round(placement.typical_width_mm * ratio_w, 2),
        typical_height_mm=round(placement.typical_height_mm * ratio_h, 2),
        # Offsets scale too: a print 3in below the collar on an adult tee is
        # most of the way down a toddler's chest.
        offset_from_mm=round(placement.offset_from_mm * scale, 2),
        offset_to_mm=round(placement.offset_to_mm * scale, 2),
        offset_reference=placement.offset_reference,
        seam_clearance_mm=placement.seam_clearance_mm,
        note=placement.note,
    )


YOUTH_PLACEMENTS: tuple[Placement, ...] = tuple(
    _scaled(placement, YOUTH_SCALE, YOUTH_OVERRIDES) for placement in ADULT_PLACEMENTS
)

YOUTH_SMALL_PLACEMENTS: tuple[Placement, ...] = tuple(
    _scaled(placement, YOUTH_SCALE * 0.85, YOUTH_SMALL_OVERRIDES) for placement in ADULT_PLACEMENTS
)

TODDLER_PLACEMENTS: tuple[Placement, ...] = tuple(
    _scaled(placement, TODDLER_SCALE, {}) for placement in ADULT_PLACEMENTS
)

BY_FIT: dict[str, tuple[Placement, ...]] = {
    "adult": ADULT_PLACEMENTS,
    "youth": YOUTH_PLACEMENTS,
    "youth_small": YOUTH_SMALL_PLACEMENTS,
    "toddler": TODDLER_PLACEMENTS,
}


def placement(key: str, fit: str = "adult") -> Placement:
    """One placement, or a refusal.

    An unknown fit raises rather than falling back to adult. Silently sizing a
    youth garment as an adult one because someone mistyped the fit is a printed
    mistake, not a default.
    """
    if fit not in BY_FIT:
        raise KeyError(f"no fit {fit!r}; known fits are {', '.join(sorted(BY_FIT))}")
    for candidate in BY_FIT[fit]:
        if candidate.key == key:
            return candidate
    raise KeyError(f"no placement {key!r} for fit {fit!r}")
