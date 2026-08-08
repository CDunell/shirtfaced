"""Composing whole designs for a brief, using every part in the archive.

The element composer picks one archive element and puts the supplied words on
it. That only works for elements which declare text slots -- badges and type
layouts -- so of fifty elements it could ever offer six. Every symbol, every
plain frame, every ornament was unreachable through it.

This works the way the archive is actually built: pick a grammar, fill its roles
from the archive, and return the assembled design. A symbol has no text slots
and never needed any -- it is the mark inside a crest, and the grammar puts the
words where the grammar says. Forty-seven of the fifty are reachable this way.

The machinery around it is unchanged and was never the problem: named gates
before scoring, refusal with reason codes, and the owner's approvals feeding
back into what gets offered.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.archive import registry
from app.archive.assemble import AssembledDesign, assemble
from app.archive.garment import Garment, GarmentError
from app.archive.grammar import Grammar, grammars_for, suits
from app.archive.placements import Placement
from app.archive.placements import placement as get_placement
from app.archive.render import Palette, RefusedToRender
from app.archive.svg import rng_for
from app.domain.element import Element
from app.services.composition_engine import PRIOR, ApprovalStore

MAX_OPTIONS = 6

# Brand inks, most dominant first. The garment colour is chosen alongside and is
# not an ink; contrast is a property of the pair.
DEFAULT_INKS = ("#C6FF00", "#F2F0EA", "#101010", "#7A7A7A", "#C0452A", "#2B4B7E")


@dataclass(frozen=True)
class Brief:
    """What the owner supplied, and where it is going."""

    primary_text: str = ""
    secondary_text: str = ""
    placement: str = "centre_chest"
    fit: str = "adult"
    style_tags: tuple[str, ...] = ()
    inks: int = 2
    treatment: str = "clean"
    garment: str = "#101010"

    @property
    def content(self) -> dict[str, str]:
        return {"primary_text": self.primary_text, "secondary_text": self.secondary_text}

    @property
    def supplied_slots(self) -> set[str]:
        return {name for name, value in self.content.items() if value.strip()}


@dataclass(frozen=True)
class DesignOption:
    """One assembled design, with what stands behind it."""

    grammar_key: str
    grammar_name: str
    reads_as: str
    design: AssembledDesign
    placement: Placement
    score: float
    confidence: float
    approvals: int
    decisions: int
    rationale: str

    @property
    def svg(self) -> str:
        return self.design.svg

    @property
    def parts(self) -> dict[str, str]:
        return self.design.chosen


@dataclass(frozen=True)
class Rejection:
    """One grammar that could not be used, and why."""

    grammar_key: str
    reason: str


@dataclass
class Composition:
    """The answer, including when the answer is no."""

    composable: bool
    options: tuple[DesignOption, ...] = ()
    refusal_reason: str = ""
    refusal_detail: str = ""
    rejections: tuple[Rejection, ...] = ()
    gaps: tuple[str, ...] = field(default_factory=tuple)


def _available_families(elements: tuple[Element, ...]) -> set[str]:
    return {
        (element.recipe.split(".", 1)[0] if element.recipe else element.family)
        for element in elements
    }


def _score(grammar: Grammar, brief: Brief, design: AssembledDesign) -> tuple[float, str]:
    """Rank an assembled design, and say why in plain terms."""
    reasons: list[str] = []

    if brief.style_tags:
        overlap = set(brief.style_tags) & set(grammar.style_tags)
        affinity = len(overlap) / len(brief.style_tags)
        if overlap:
            reasons.append(f"matches {', '.join(sorted(overlap))}")
    else:
        affinity = 0.5

    # A design that used what was supplied beats one that dropped half of it.
    wanted = len(brief.supplied_slots)
    used = len([slot for slot in grammar.content_slots() if slot in brief.supplied_slots])
    completeness = used / wanted if wanted else 1.0
    if design.dropped:
        reasons.append(f"dropped {', '.join(design.dropped)}")

    # Room used, without crowding. Halfway through the budget reads as
    # comfortable; scraping the ceiling reads as busy.
    if design.density_allowed > 0:
        ratio = design.density_spent / design.density_allowed
        breathing = 1.0 - abs(ratio - 0.6)
    else:
        breathing = 0.5

    reasons.append(design.reads_as)
    score = 0.4 * affinity + 0.35 * completeness + 0.25 * breathing
    return round(max(score, 0.0), 4), "; ".join(reasons)


def _confidence(decisions: int, approved: int, score: float) -> float:
    """How much to trust this suggestion.

    Blended from the same uncertain baseline whether or not decisions exist, so
    a single approval moves it about as far as a single approval should.
    """
    baseline = score * 0.70
    if decisions == 0:
        return round(baseline, 4)
    rate = approved / decisions
    weight = decisions / (decisions + PRIOR)
    return round((1 - weight) * baseline + weight * rate, 4)


class DesignComposer:
    """Builds whole designs for a brief, from every part the archive holds."""

    def __init__(self, approvals_path: Path, elements: tuple[Element, ...] | None = None) -> None:
        self.approvals = ApprovalStore(approvals_path)
        self.elements = elements if elements is not None else registry.all_elements()

    def compose(
        self,
        brief: Brief,
        seed: int,
        limit: int = MAX_OPTIONS,
        garment: Garment | None = None,
    ) -> Composition:
        """Answer the brief, or refuse it with a reason. Never raises.

        When a garment is supplied, designs are sized to that garment's actual
        zone rather than to the placement table. The table is a default drawn
        from production guidance; the garment in front of you is the physical
        fact, and a 200mm zone cannot hold a 229mm print however typical that
        size is elsewhere.
        """
        try:
            return self._compose(brief, seed, limit, garment)
        except Exception as error:
            return Composition(
                composable=False,
                refusal_reason="ASSESSMENT_FAILED",
                refusal_detail=type(error).__name__,
            )

    def _compose(
        self, brief: Brief, seed: int, limit: int, garment: Garment | None = None
    ) -> Composition:
        if not brief.supplied_slots:
            return Composition(
                composable=False,
                refusal_reason="NO_CONTENT",
                refusal_detail="nothing was supplied to arrange",
            )

        try:
            placement = get_placement(brief.placement, brief.fit)
        except KeyError as error:
            return Composition(
                composable=False,
                refusal_reason="UNKNOWN_PLACEMENT",
                refusal_detail=str(error),
            )

        fits = grammars_for(brief.supplied_slots, _available_families(self.elements))
        if not fits:
            return Composition(
                composable=False,
                refusal_reason="NO_GRAMMAR_FITS",
                refusal_detail=(
                    "nothing in the grammar can be built from "
                    f"{', '.join(sorted(brief.supplied_slots))} with the families held"
                ),
            )

        # The garment's own zone wins where there is one.
        width_mm, height_mm = placement.typical_width_mm, placement.typical_height_mm
        if garment is not None:
            try:
                zone = garment.zone(brief.placement)
            except GarmentError as error:
                return Composition(
                    composable=False,
                    refusal_reason=error.reason,
                    refusal_detail=error.detail,
                )
            width_mm, height_mm = zone.width, zone.height

        palette = Palette(garment=brief.garment, inks=tuple(DEFAULT_INKS[: brief.inks]))
        options: list[DesignOption] = []
        rejections: list[Rejection] = []

        for fit in fits:
            grammar = fit.grammar
            if not suits(grammar, width_mm, height_mm):
                rejections.append(
                    Rejection(
                        grammar.key,
                        f"WRONG_SHAPE_FOR_ZONE:{width_mm:.0f}x{height_mm:.0f}",
                    )
                )
                continue
            try:
                design = assemble(
                    grammar,
                    brief.content,
                    self.elements,
                    palette,
                    placement,
                    seed=seed,
                    width_mm=width_mm,
                    height_mm=height_mm,
                    treatment=brief.treatment,
                )
            except RefusedToRender as error:
                rejections.append(Rejection(grammar.key, error.reason))
                continue

            score, rationale = _score(grammar, brief, design)
            approved, decisions = self.approvals.history(grammar.key)
            options.append(
                DesignOption(
                    grammar_key=grammar.key,
                    grammar_name=grammar.name,
                    reads_as=grammar.reads_as,
                    design=design,
                    placement=placement,
                    score=score,
                    confidence=_confidence(decisions, approved, score),
                    approvals=approved,
                    decisions=decisions,
                    rationale=rationale,
                )
            )

        if not options:
            grouped: dict[str, int] = {}
            for rejection in rejections:
                grouped[rejection.reason] = grouped.get(rejection.reason, 0) + 1
            summary = ", ".join(f"{key} ({count})" for key, count in sorted(grouped.items()))
            return Composition(
                composable=False,
                refusal_reason="NOTHING_BUILDS",
                refusal_detail=(
                    f"{len(rejections)} grammar(s) could not build on a "
                    f"{placement.label.lower()}: {summary}"
                ),
                rejections=tuple(rejections),
            )

        # Ties broken by a seeded draw over a stable order, so adding a grammar
        # does not silently reorder every existing suggestion.
        generator = rng_for(seed, "design-tiebreak")
        options.sort(key=lambda option: option.grammar_key)
        generator.shuffle(options)
        options.sort(key=lambda option: -(option.score * option.confidence))

        gaps: list[str] = []
        if brief.style_tags:
            known = registry.by_id()
            matched = any(
                set(brief.style_tags) & set(known[key].style_tags)
                for option in options[:limit]
                for key in option.parts.values()
                if key in known
            )
            if not matched:
                gaps.append(
                    f"nothing chosen carries {', '.join(brief.style_tags)}; "
                    "style ranked the arrangement rather than the parts"
                )

        known = registry.by_id()
        standing_in = sorted(
            {
                key
                for option in options[:limit]
                for key in option.parts.values()
                if key in known and known[key].provisional
            }
        )
        if standing_in:
            gaps.append(
                "standing in for better artwork: "
                + ", ".join(standing_in)
                + " -- see each element's note for what it is waiting for"
            )

        return Composition(
            composable=True,
            options=tuple(options[:limit]),
            rejections=tuple(rejections),
            gaps=tuple(gaps),
        )

    def record_decision(self, grammar_key: str, approved: bool) -> None:
        """Feed a decision back. This is what moves confidence."""
        self.approvals.record(grammar_key, approved)
