"""Designs made of several parts, and the rules for putting them together.

Everything before this could place one shape on a shirt. A real design is not
one shape. It is a frame with a symbol inside it and a word arched over the top
and a small line underneath, and the interesting question is which of those go
together and how they sit relative to each other.

That question is what a grammar answers. Not "is this element allowed" -- the
gates already do that -- but "given a lead, what supports it, and where does the
support go".

Three ideas do most of the work here:

*A design has one lead and everything else serves it.* Two things competing for
first look is the commonest way a shirt fails. So a composition names its lead
and sizes everything else beneath it.

*Roles, not elements.* The grammar says "a frame, then a symbol inside it, then
a word above" -- it does not name which frame. That is what lets one grammar
produce many designs, and what makes a new element immediately useful in every
grammar it fits.

*Density is a budget.* Each part spends some of a fixed allowance, and the
allowance shrinks with the placement. This is what stops the composer stacking
four intricate things into a left-chest print because each one passed its own
check.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.archive.placements import Placement

# How much visual load a design may carry, before the placement scales it. One
# unit is roughly "a plain shape with a word on it".
DENSITY_BUDGET = 1.0


def density_budget_for(width_mm: float) -> float:
    """The load a print of this width can carry.

    Taken from the print's actual width rather than from the placement table.
    Designs are sized to the garment's own zone, so reading the budget off the
    table meant a 280mm yoke zone got the allowance for the table's 76mm one
    and every grammar was refused.

    A left chest at 90mm carries a fraction of what a full front does, because
    it is seen from the same distance and is a quarter of the size.
    """
    reference = 230.0  # a centre chest, the size most designs are drawn for
    scale = min(width_mm / reference, 1.35)
    return round(DENSITY_BUDGET * max(scale, 0.35), 3)


def density_budget(placement: Placement) -> float:
    """The load this placement carries at its typical size."""
    return density_budget_for(placement.typical_width_mm)


@dataclass(frozen=True)
class Part:
    """One role in a composition, and where it sits.

    Geometry is proportional to the whole design, so a grammar holds at any
    print size. `layer` decides drawing order: lower numbers go down first, so
    a frame at 0 sits behind a symbol at 1.
    """

    role: str
    # Which families may fill this part. Empty means any.
    families: tuple[str, ...] = ()
    top: float = 0.0
    left: float = 0.0
    width: float = 1.0
    height: float = 1.0
    layer: int = 0
    # Content slot this part carries, if it carries one.
    slot: str = ""
    # A part the design can do without when the budget runs short. The lead
    # never is.
    optional: bool = False


@dataclass(frozen=True)
class Grammar:
    """One way to build a design out of parts."""

    key: str
    name: str
    # What it reads as, in plain terms, so a suggestion can explain itself.
    reads_as: str
    parts: tuple[Part, ...]
    # The shape this arrangement wants, as width over height. A crest is
    # square, a flanked word is wide, a tower is tall. Parts are proportional
    # to whatever box they are given, so a tower in a 2.5:1 zone is a squashed
    # tower and a crest in a sleeve is a stretched crest -- neither is refused
    # by anything that only counts density.
    aspect: float = 1.0
    style_tags: tuple[str, ...] = ()
    # Minimum inks. A grammar that relies on a knockout cannot be one colour.
    ink_min: int = 1
    ink_max: int = 3

    @property
    def lead(self) -> Part:
        return self.parts[0]

    def content_slots(self) -> tuple[str, ...]:
        return tuple(part.slot for part in self.parts if part.slot)


# --- The grammars.
#
# Written as arrangements rather than as designs. Each one is a way of putting
# parts together that recurs across the corpus and across the trade generally --
# a crest, a banner over a mark, a stamp, a stencil. What fills them is chosen
# per brief. ---

GRAMMARS: tuple[Grammar, ...] = (
    Grammar(
        key="crest",
        name="Crest",
        reads_as="an emblem you could stitch on a blazer",
        parts=(
            Part(role="frame", families=("frame", "badge"), layer=0),
            Part(
                role="mark",
                families=("symbol", "illustration_part"),
                top=0.34,
                left=0.34,
                width=0.32,
                height=0.32,
                layer=1,
            ),
            Part(
                role="title",
                top=0.10,
                left=0.19,
                width=0.62,
                height=0.13,
                layer=2,
                slot="primary_text",
            ),
            Part(
                role="footer",
                top=0.70,
                left=0.23,
                width=0.54,
                height=0.11,
                layer=2,
                slot="secondary_text",
                optional=True,
            ),
        ),
        aspect=0.95,  # square-ish, like a badge
        style_tags=("institutional", "club", "heraldic"),
        ink_min=1,
        ink_max=3,
    ),
    Grammar(
        key="banner_over_mark",
        name="Banner over mark",
        reads_as="a big word with the picture underneath carrying it",
        parts=(
            Part(
                role="mark",
                families=("symbol", "illustration_part"),
                top=0.34,
                left=0.22,
                width=0.56,
                height=0.46,
                layer=0,
            ),
            Part(
                role="banner",
                top=0.06,
                left=0.06,
                width=0.88,
                height=0.22,
                layer=1,
                slot="primary_text",
            ),
            Part(
                role="footer",
                top=0.84,
                left=0.28,
                width=0.44,
                height=0.09,
                layer=1,
                slot="secondary_text",
                optional=True,
            ),
        ),
        aspect=1.0,  # the mark wants room beneath the word
        style_tags=("skate", "streetwear", "band-merch"),
        ink_min=1,
        ink_max=3,
    ),
    Grammar(
        key="stamp",
        name="Stamp",
        reads_as="something official that has been used a few hundred times",
        parts=(
            Part(role="frame", families=("frame",), layer=0),
            Part(
                role="title",
                top=0.30,
                left=0.12,
                width=0.76,
                height=0.22,
                layer=1,
                slot="primary_text",
            ),
            Part(
                role="rule",
                families=("ornament",),
                top=0.58,
                left=0.24,
                width=0.52,
                height=0.05,
                layer=1,
                optional=True,
            ),
            Part(
                role="footer",
                top=0.66,
                left=0.24,
                width=0.52,
                height=0.10,
                layer=1,
                slot="secondary_text",
                optional=True,
            ),
        ),
        aspect=1.0,  # a frame around centred type
        style_tags=("utilitarian", "workwear", "vintage"),
        ink_min=1,
        ink_max=2,
    ),
    Grammar(
        key="stencil",
        name="Stencil",
        reads_as="sprayed on a crate, in a hurry",
        parts=(
            Part(
                role="title",
                top=0.24,
                left=0.04,
                width=0.92,
                height=0.30,
                layer=0,
                slot="primary_text",
            ),
            Part(
                role="footer",
                top=0.60,
                left=0.20,
                width=0.60,
                height=0.10,
                layer=0,
                slot="secondary_text",
                optional=True,
            ),
            Part(
                role="mark",
                families=("symbol", "illustration_part"),
                top=0.74,
                left=0.42,
                width=0.16,
                height=0.16,
                layer=1,
                optional=True,
            ),
        ),
        aspect=1.6,  # type-led and wide
        style_tags=("military", "utilitarian", "workwear"),
        ink_min=1,
        ink_max=2,
    ),
    Grammar(
        key="flanked_word",
        name="Flanked word",
        reads_as="a word held between two marks, like a headline with wings",
        parts=(
            Part(
                role="title",
                top=0.38,
                left=0.20,
                width=0.60,
                height=0.22,
                layer=1,
                slot="primary_text",
            ),
            Part(
                role="left_mark",
                families=("symbol", "ornament", "illustration_part"),
                top=0.40,
                left=0.02,
                width=0.16,
                height=0.18,
                layer=0,
            ),
            Part(
                role="right_mark",
                families=("symbol", "ornament", "illustration_part"),
                top=0.40,
                left=0.82,
                width=0.16,
                height=0.18,
                layer=0,
            ),
            Part(
                role="footer",
                top=0.66,
                left=0.25,
                width=0.50,
                height=0.09,
                layer=1,
                slot="secondary_text",
                optional=True,
            ),
        ),
        aspect=2.2,  # marks either side of a word
        style_tags=("collegiate", "athletic", "classic"),
        ink_min=1,
        ink_max=2,
    ),
    Grammar(
        key="tower",
        name="Tower",
        reads_as="everything stacked up the middle, tall and narrow",
        parts=(
            Part(
                role="mark",
                families=("symbol", "illustration_part"),
                top=0.04,
                left=0.36,
                width=0.28,
                height=0.24,
                layer=0,
            ),
            Part(
                role="title",
                top=0.34,
                left=0.08,
                width=0.84,
                height=0.20,
                layer=1,
                slot="primary_text",
            ),
            Part(
                role="rule",
                families=("ornament",),
                top=0.58,
                left=0.30,
                width=0.40,
                height=0.04,
                layer=1,
                optional=True,
            ),
            Part(
                role="footer",
                top=0.66,
                left=0.22,
                width=0.56,
                height=0.10,
                layer=1,
                slot="secondary_text",
                optional=True,
            ),
        ),
        aspect=0.65,  # stacked up the middle
        style_tags=("modern", "streetwear", "bold"),
        ink_min=1,
        ink_max=2,
    ),
    Grammar(
        key="lone_mark",
        name="Lone mark",
        reads_as="one shape, no words, confident about it",
        parts=(
            Part(
                role="mark",
                families=("symbol", "illustration_part"),
                top=0.14,
                left=0.14,
                width=0.72,
                height=0.72,
                layer=0,
            ),
        ),
        aspect=1.0,  # one shape
        style_tags=("modern", "minimal"),
        ink_min=1,
        ink_max=2,
    ),
    Grammar(
        key="sleeve_run",
        name="Sleeve run",
        reads_as="a word running down the arm, the way a sponsor stripe does",
        aspect=0.28,  # long and narrow, the shape of a sleeve
        parts=(
            Part(
                role="title",
                top=0.06,
                left=0.02,
                width=0.96,
                height=0.62,
                layer=0,
                slot="primary_text",
            ),
            Part(
                role="rule",
                families=("ornament",),
                top=0.72,
                left=0.15,
                width=0.70,
                height=0.05,
                layer=0,
                optional=True,
            ),
            Part(
                role="mark",
                families=("symbol", "illustration_part"),
                top=0.80,
                left=0.28,
                width=0.44,
                height=0.16,
                layer=0,
                optional=True,
            ),
        ),
        style_tags=("sport", "utilitarian", "modern"),
        ink_min=1,
        ink_max=2,
    ),
    Grammar(
        key="ticket",
        name="Ticket",
        reads_as="a stub torn off something you went to",
        parts=(
            Part(role="frame", families=("frame",), layer=0),
            Part(
                role="title",
                top=0.22,
                left=0.10,
                width=0.80,
                height=0.26,
                layer=1,
                slot="primary_text",
            ),
            Part(
                role="footer",
                top=0.58,
                left=0.16,
                width=0.68,
                height=0.14,
                layer=1,
                slot="secondary_text",
                optional=True,
            ),
        ),
        aspect=1.7,  # a stub is wider than it is tall
        style_tags=("ephemera", "vintage", "novelty"),
        ink_min=1,
        ink_max=2,
    ),
)

BY_KEY: dict[str, Grammar] = {grammar.key: grammar for grammar in GRAMMARS}


@dataclass
class Fit:
    """Whether a grammar suits a brief, and what it would cost to use it."""

    grammar: Grammar
    fills: int = 0
    unfilled: tuple[str, ...] = field(default_factory=tuple)
    missing_families: tuple[str, ...] = field(default_factory=tuple)


def grammars_for(supplied_slots: set[str], available_families: set[str]) -> list[Fit]:
    """Which grammars a brief can actually build, and how well.

    A grammar is offered when its required parts can be filled. Optional parts
    are exactly that -- a crest without a footer is still a crest, and refusing
    to build one because no second line was supplied would be the archive being
    precious about its own structure.
    """
    fits: list[Fit] = []
    for grammar in GRAMMARS:
        required = [part for part in grammar.parts if not part.optional]

        missing = tuple(
            sorted(
                {
                    part.families[0]
                    for part in required
                    if part.families and not set(part.families) & available_families
                }
            )
        )
        needed_slots = {part.slot for part in required if part.slot}
        if needed_slots - supplied_slots:
            continue
        if missing:
            continue

        filled = len([part for part in grammar.parts if part.slot in supplied_slots])
        unfilled = tuple(
            part.slot for part in grammar.parts if part.slot and part.slot not in supplied_slots
        )
        fits.append(Fit(grammar=grammar, fills=filled, unfilled=unfilled))

    # Most of the supplied content used, first. A grammar that uses both lines
    # beats one that drops the second on the floor.
    fits.sort(key=lambda fit: (-fit.fills, len(fit.unfilled), fit.grammar.key))
    return fits


# How far a zone's proportions may differ from a grammar's before the result
# stops being that arrangement. Beyond this a crest in a sleeve is not a narrow
# crest, it is a different and worse thing.
MAX_ASPECT_MISMATCH = 2.0


def suits(grammar: Grammar, width_mm: float, height_mm: float) -> bool:
    """Whether this arrangement survives a box of these proportions."""
    if height_mm <= 0 or grammar.aspect <= 0:
        return False
    ratio = (width_mm / height_mm) / grammar.aspect
    return 1 / MAX_ASPECT_MISMATCH <= ratio <= MAX_ASPECT_MISMATCH
