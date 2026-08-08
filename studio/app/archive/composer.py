"""Choosing archive elements for a brief, and placing them on a garment.

The layer above the renderer. Given content the owner has already chosen, this
decides which elements can carry it, ranks the ones that can, renders them at a
real placement's real size, and refuses when nothing in the archive fits.

It keeps the shape the composition engine already established, because that part
was never the thing that was wrong:

*Synthesis before scoring.* Which elements are eligible at all is decided by
named predicates, separately from how good each one is. Otherwise a threshold
leaks into a weight and neither can be reasoned about.

*Refusal is a first-class answer.* An empty result carries reason codes, so
`GROUP BY reason` says which constraint is actually doing work rather than
leaving someone to guess why the archive went quiet.

*Approval is the training signal.* Which compositions the owner accepts feeds
back into what gets offered, and it is the only signal here that is about this
brand rather than about geometry.

Nothing in this module writes content. It arranges what it is given.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.archive import authored
from app.archive.placements import Placement
from app.archive.placements import placement as get_placement
from app.archive.render import (
    Palette,
    RefusedToRender,
    RenderedElement,
    box_for,
    render,
)
from app.archive.svg import rng_for
from app.domain.element import Element
from app.services.composition_engine import PRIOR, ApprovalStore

# Most options ever offered. More than this is not choice, it is abdication.
MAX_OPTIONS = 3

# An element busier than this crowds a small placement. A left chest print is
# 90mm across; an intricate badge at that size is a smudge from two metres.
SMALL_PLACEMENT_MM = 120.0
SMALL_PLACEMENT_MAX_COMPLEXITY = 0.30


@dataclass(frozen=True)
class Brief:
    """What the owner supplied, and where it is going.

    The text fields are the content and this module never alters them. Style
    tags are a steer rather than a filter -- they rank, they do not exclude,
    because excluding on taste is how an archive of 3,000 parts behaves like an
    archive of ten.
    """

    primary_text: str = ""
    secondary_text: str = ""
    placement: str = "centre_chest"
    fit: str = "adult"
    style_tags: tuple[str, ...] = ()
    inks: int = 2
    treatment: str = "clean"

    @property
    def content(self) -> dict[str, str]:
        return {
            "primary_text": self.primary_text,
            "secondary_text": self.secondary_text,
        }

    @property
    def supplied_slots(self) -> set[str]:
        return {name for name, value in self.content.items() if value.strip()}


@dataclass(frozen=True)
class Option:
    """One composed design, with what stands behind it."""

    element_id: str
    subtype: str
    family: str
    rendered: RenderedElement
    placement: Placement
    score: float
    confidence: float
    approvals: int
    decisions: int
    rationale: str

    @property
    def svg(self) -> str:
        return self.rendered.svg


@dataclass(frozen=True)
class Rejection:
    """One element that could not be used, and the predicate that stopped it."""

    element_id: str
    reason: str


@dataclass
class ArchiveComposition:
    """The answer, including when the answer is no."""

    composable: bool
    options: tuple[Option, ...] = ()
    refusal_reason: str = ""
    refusal_detail: str = ""
    # Every element the archive holds and could not use, with why. This is what
    # makes a quiet archive diagnosable instead of mysterious.
    rejections: tuple[Rejection, ...] = ()
    gaps: tuple[str, ...] = field(default_factory=tuple)


# --- Synthesis: a registry of named predicates, ordered, rather than a cascade
# buried in one function. Each returns a reason code or an empty string. ---


def _gate_fits_the_job(element: Element, brief: Brief, placement: Placement) -> str:
    """Inks and treatment. Not rights -- those are a release question."""
    usable, reason = element.usable_with(brief.inks, brief.treatment)
    return "" if usable else reason


def _gate_has_slots(element: Element, brief: Brief, placement: Placement) -> str:
    """Content was supplied, so the element must have somewhere to put it."""
    if not brief.supplied_slots:
        return ""
    return "" if element.slots else "ELEMENT_HAS_NO_SLOTS"


def _gate_slots_are_fillable(element: Element, brief: Brief, placement: Placement) -> str:
    """Every supplied piece of content needs a slot that accepts it.

    The reverse is allowed: an element may declare more slots than the brief
    fills, and the renderer reports the empty ones rather than inventing text.
    """
    if not brief.supplied_slots:
        return ""
    names = {slot.name for slot in element.slots}
    missing = brief.supplied_slots - names
    return f"NO_SLOT_FOR:{','.join(sorted(missing))}" if missing else ""


# Whether an intricate element suits a small print is a real question, and the
# density budget in grammar.py already answers it -- proportionally, against the
# placement's actual size, and across the whole composition rather than one part
# at a time. A second absolute threshold here only rejected things the budget
# would have weighed properly.


GATES = (
    _gate_fits_the_job,
    _gate_has_slots,
    _gate_slots_are_fillable,
)


def _eligible(element: Element, brief: Brief, placement: Placement) -> str:
    for gate in GATES:
        reason = gate(element, brief, placement)
        if reason:
            return reason
    return ""


# --- Scoring: of the survivors, which fits best. ---


def _score(element: Element, brief: Brief, placement: Placement) -> tuple[float, str]:
    """Rank an eligible element, and say why in the corpus's own terms."""
    reasons: list[str] = []

    if brief.style_tags:
        overlap = len(set(brief.style_tags) & set(element.style_tags))
        affinity = overlap / len(brief.style_tags)
        if overlap:
            shared = sorted(set(brief.style_tags) & set(element.style_tags))
            reasons.append(f"matches {', '.join(shared)}")
    else:
        affinity = 0.5
        reasons.append("no style asked for, so style did not rank it")

    # Prefer an element whose slots the brief actually fills. A three-slot badge
    # holding one word is mostly empty frame.
    if element.slots:
        filled = len(brief.supplied_slots & {slot.name for slot in element.slots})
        occupancy = filled / len(element.slots)
        reasons.append(f"fills {filled} of {len(element.slots)} slots")
    else:
        occupancy = 1.0 if not brief.supplied_slots else 0.0

    # Room to breathe: at a generous placement, a little more complexity reads
    # as craft; at a small one it reads as noise.
    headroom = min(placement.max_width_mm / SMALL_PLACEMENT_MM, 2.0) / 2.0
    complexity_fit = 1.0 - abs(element.complexity - headroom * 0.4)

    score = 0.45 * affinity + 0.35 * occupancy + 0.20 * complexity_fit
    return round(score, 4), "; ".join(reasons)


def _longest_for(element: Element, placement: Placement) -> float:
    """The longest side that fits this element's shape inside the placement.

    Sizing by the placement's own longest edge is wrong: a square element in a
    305x356mm full front comes out 356mm wide against a 305mm limit, and every
    option is then rejected as too wide. The element's box has to be fitted
    inside the placement, not matched to one of its edges.

    Fitted to the *typical* box rather than the maximum. Composing to the
    ceiling every time is what produces a catalogue where every design is a
    jumbo front.
    """
    unit_width, unit_height = box_for(element, 1000.0)
    scale = min(
        placement.typical_width_mm / unit_width,
        placement.typical_height_mm / unit_height,
    )
    return 1000.0 * scale


def _confidence(decisions: int, approved: int, score: float) -> float:
    """How much to trust this suggestion.

    With no decisions recorded, the score alone carries it, capped -- geometry
    fitting a brief is not the same as the owner wanting it. Once decisions
    exist they take over under n/(n + 10) shrinkage, the same prior the
    composition engine uses, so two approvals out of two do not read as
    certainty.
    """
    # The uncertain baseline: geometry fitting a brief is not the owner wanting
    # it, so an unproven element is capped below its raw score.
    baseline = score * 0.70
    if decisions == 0:
        return round(baseline, 4)
    rate = approved / decisions
    weight = decisions / (decisions + PRIOR)
    # Blended from the baseline, not from the raw score. Blending from the raw
    # score made a single approval jump higher than five ever could, which is
    # the opposite of what shrinkage is for.
    return round((1 - weight) * baseline + weight * rate, 4)


class ArchiveComposer:
    """Selects and places archive elements for a brief."""

    def __init__(self, approvals_path: Path, elements: tuple[Element, ...] | None = None) -> None:
        self.approvals = ApprovalStore(approvals_path)
        self.elements = elements if elements is not None else authored.ALL

    def compose(self, brief: Brief, seed: int, limit: int = MAX_OPTIONS) -> ArchiveComposition:
        """Answer the brief, or refuse it with a reason. Never raises."""
        try:
            return self._compose(brief, seed, limit)
        except Exception as error:
            return ArchiveComposition(
                composable=False,
                refusal_reason="ASSESSMENT_FAILED",
                refusal_detail=type(error).__name__,
            )

    def _compose(self, brief: Brief, seed: int, limit: int) -> ArchiveComposition:
        if not brief.primary_text.strip() and not brief.secondary_text.strip():
            return ArchiveComposition(
                composable=False,
                refusal_reason="NO_CONTENT",
                refusal_detail="nothing was supplied to arrange",
            )

        try:
            placement = get_placement(brief.placement, brief.fit)
        except KeyError as error:
            return ArchiveComposition(
                composable=False,
                refusal_reason="UNKNOWN_PLACEMENT",
                refusal_detail=str(error),
            )

        rejections: list[Rejection] = []
        survivors: list[Element] = []
        for element in self.elements:
            reason = _eligible(element, brief, placement)
            if reason:
                rejections.append(Rejection(element.id, reason))
            else:
                survivors.append(element)

        if not survivors:
            grouped: dict[str, int] = {}
            for rejection in rejections:
                key = rejection.reason.split(":", 1)[0]
                grouped[key] = grouped.get(key, 0) + 1
            summary = ", ".join(f"{key} ({count})" for key, count in sorted(grouped.items()))
            return ArchiveComposition(
                composable=False,
                refusal_reason="NO_ELIGIBLE_ELEMENT",
                refusal_detail=f"{len(rejections)} element(s) rejected: {summary}",
                rejections=tuple(rejections),
            )

        palette = Palette(inks=tuple(_DEFAULT_INKS[: brief.inks]))

        options: list[Option] = []
        gaps: list[str] = []
        for element in survivors:
            try:
                rendered = render(
                    element,
                    brief.content,
                    palette,
                    seed=seed,
                    treatment=brief.treatment,
                    longest_mm=_longest_for(element, placement),
                )
            except RefusedToRender as error:
                rejections.append(Rejection(element.id, error.reason))
                continue

            fits, why = placement.fits(rendered.width_mm, rendered.height_mm)
            if not fits:
                rejections.append(Rejection(element.id, why))
                continue

            score, rationale = _score(element, brief, placement)
            approved, decisions = self.approvals.history(element.id)
            options.append(
                Option(
                    element_id=element.id,
                    subtype=element.subtype,
                    family=element.family,
                    rendered=rendered,
                    placement=placement,
                    score=score,
                    confidence=_confidence(decisions, approved, score),
                    approvals=approved,
                    decisions=decisions,
                    rationale=rationale,
                )
            )

        if not options:
            return ArchiveComposition(
                composable=False,
                refusal_reason="NOTHING_FITS_THE_PLACEMENT",
                refusal_detail=(
                    f"{len(survivors)} element(s) were eligible but none rendered "
                    f"within {placement.label} at {placement.max_width_mm:.0f}x"
                    f"{placement.max_height_mm:.0f}mm"
                ),
                rejections=tuple(rejections),
            )

        # Ties broken by a seeded shuffle rather than by archive order, so a new
        # element does not silently reorder every existing suggestion. Sorted
        # by id first so the shuffle is over a stable sequence.
        generator = rng_for(seed, "tiebreak")
        options.sort(key=lambda option: option.element_id)
        generator.shuffle(options)
        options.sort(key=lambda option: -(option.score * option.confidence))

        if brief.style_tags:
            matched = any(
                set(brief.style_tags) & set(authored.BY_ID[option.element_id].style_tags)
                for option in options
            )
            if not matched:
                in_archive = {
                    tag
                    for element in self.elements
                    for tag in element.style_tags
                    if tag in brief.style_tags
                }
                if in_archive:
                    gaps.append(
                        f"{', '.join(sorted(in_archive))} exists in the archive but not on "
                        "anything that survived the gates for this brief, so style did "
                        "not rank the options"
                    )
                else:
                    gaps.append(
                        f"nothing in the archive carries {', '.join(brief.style_tags)}; "
                        "ranking ignored style"
                    )
        offered = [_element_by_id(self.elements, option.element_id) for option in options[:limit]]
        standing_in = [
            element.id for element in offered if element is not None and element.provisional
        ]
        if standing_in:
            gaps.append(
                "standing in for better artwork: "
                + ", ".join(standing_in)
                + " -- see each element's note for what it is waiting for"
            )
        if brief.treatment == "embroidered":
            gaps.append(
                "embroidery is not simulated -- these are the placement and "
                "geometry only, not a stitch preview"
            )

        return ArchiveComposition(
            composable=True,
            options=tuple(options[:limit]),
            rejections=tuple(rejections),
            gaps=tuple(gaps),
        )

    def record_decision(self, element_id: str, approved: bool) -> None:
        """Feed a decision back. This is what moves confidence."""
        self.approvals.record(element_id, approved)


def _element_by_id(elements: tuple[Element, ...], key: str) -> Element | None:
    for element in elements:
        if element.id == key:
            return element
    return None


# Brand inks, most dominant first. The garment colour is chosen alongside and is
# not an ink; contrast is a property of the pair.
_DEFAULT_INKS = ("#C6FF00", "#F2F0EA", "#101010", "#7A7A7A", "#C0452A", "#2B4B7E")
