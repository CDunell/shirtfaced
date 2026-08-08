"""Ink systems, and whether one can be printed on a given garment.

Every design the engine has ever composed used the same six inks in the same
order, sliced to however many the brief asked for. A two-ink design was acid
green and off-white, every time, on whatever colour the garment happened to be.
That is why a screen full of options came back looking like one option.

This makes the choice data. What it deliberately does *not* do is decide which
palette a drop uses: subject and colour are seasonal, the archive is the
permanent layer, and a document in here choosing the season's colours is the
same mistake as filling the archive with fauna.

So what lives here is mechanism and physical fact:

*Contrast is a property of the pair.* The same green is a different decision on
black than on natural. An ink that does not separate from the cloth is not a
subtle design, it is an invisible one, and that is measurable rather than a
matter of taste.

*Ink count is money.* Each additional screen is a separate screen, a separate
pass and a separate registration risk, so a system says how many it needs and
the engine can be asked for fewer.
"""

from __future__ import annotations

from dataclasses import dataclass

# Below this the ink and the cloth are the same thing at three metres. Derived
# from relative luminance rather than chosen: it is the point where a print
# stops reading, not a preference about how bold a design should be.
MIN_SEPARATION = 0.20


def _channel(value: int) -> float:
    """One sRGB channel, linearised."""
    fraction = value / 255.0
    return fraction / 12.92 if fraction <= 0.03928 else ((fraction + 0.055) / 1.055) ** 2.4


def luminance(colour: str) -> float:
    """Relative luminance of a hex colour, 0 for black and 1 for white."""
    raw = colour.lstrip("#")
    if len(raw) == 3:
        raw = "".join(c * 2 for c in raw)
    try:
        red, green, blue = (int(raw[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return 0.0
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def separation(one: str, other: str) -> float:
    """How far apart two colours are in light. Symmetrical, 0 to 1."""
    return abs(luminance(one) - luminance(other))


@dataclass(frozen=True)
class ColourSystem:
    """A named set of inks, in order of dominance."""

    key: str
    label: str
    inks: tuple[str, ...]
    # What it is for, in the same voice as a grammar's `reads_as`: something a
    # person can judge without opening the file.
    reads_as: str = ""

    def usable_on(self, garment: str) -> bool:
        """Whether this system has any ink that reads on this cloth."""
        return any(separation(ink, garment) >= MIN_SEPARATION for ink in self.inks)

    def for_count(self, count: int, garment: str = "") -> tuple[str, ...]:
        """The first `count` inks that can be seen on this garment.

        Every ink is checked, not just the leading one. Checking only the first
        was wrong in a way that took a render to notice: the workwear system is
        amber, black and off-white, and on a black garment its *second* ink is
        the garment. A design whose mark happened to land on ink two came back
        as an empty shirt -- a correct file, printing nothing.

        The black is not removed from the system. It is skipped for this
        garment, which is what a printer would do.
        """
        inks = self.inks
        if garment:
            visible = tuple(i for i in inks if separation(i, garment) >= MIN_SEPARATION)
            inks = visible or inks
        return inks[: max(1, count)] or inks[:1]


# The system every design has used until now, named rather than assumed. Kept
# first so existing seeds compose as they did before.
HOUSE = ColourSystem(
    key="house",
    label="House",
    inks=("#C6FF00", "#F2F0EA", "#101010", "#7A7A7A", "#C0452A", "#2B4B7E"),
    reads_as="acid green leading, the one everything has been printed in so far",
)

SYSTEMS: tuple[ColourSystem, ...] = (
    HOUSE,
    ColourSystem(
        key="single_light",
        label="One light ink",
        inks=("#F2F0EA", "#C6FF00"),
        reads_as="one off-white ink on a dark garment; the cheapest thing to print",
    ),
    ColourSystem(
        key="single_dark",
        label="One dark ink",
        inks=("#101010", "#C0452A"),
        reads_as="one black ink on a pale garment",
    ),
    ColourSystem(
        key="workwear",
        label="Workwear",
        inks=("#E8A33D", "#101010", "#F2F0EA"),
        reads_as="hi-vis amber over black, the utility register",
    ),
    ColourSystem(
        key="faded",
        label="Faded",
        inks=("#B8B0A0", "#7A7A7A", "#101010"),
        reads_as="washed and low-contrast, for a print meant to look old",
    ),
)

BY_KEY = {system.key: system for system in SYSTEMS}


def usable_for(garment: str) -> tuple[ColourSystem, ...]:
    """Every system whose leading ink reads on this garment.

    Never empty: if nothing separates, the garment is mid-grey and the honest
    answer is the system with the most contrast rather than a refusal, because
    a design still has to come back.
    """
    fits = tuple(system for system in SYSTEMS if system.usable_on(garment))
    if fits:
        return fits
    return (max(SYSTEMS, key=lambda s: separation(s.inks[0], garment)),)


def choose(garment: str, seed: int, named: str = "") -> ColourSystem:
    """One system for this garment: the named one, or one picked by the seed.

    Picked from the seed rather than at random so the palette is part of what a
    seed means. Two designs from the same seed must be the same design, and
    colour is not an exception to that.
    """
    if named:
        system = BY_KEY.get(named)
        if system is not None:
            return system
    fits = usable_for(garment)
    return fits[seed % len(fits)]
