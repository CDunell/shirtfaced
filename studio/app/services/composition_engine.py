"""Deciding how supplied elements should be arranged, from how the corpus does it.

The content is not this engine's business. Someone supplies a phrase, a logo, a
photograph -- already chosen, already curated -- and the only question asked
here is *what presentation fits it*, answered from how thousands of collected
garments arrange comparable material. The engine never judges whether a phrase
is good and never invents one.

The shape follows DESIGN_ENGINE_ADAPTATION.md:

    Elements -> Feature -> Cluster -> Qualify -> Compose -> Bouncer -> Present
                              ^                                |
                              +---------- approvals -----------+

Two properties matter more than the arrangement logic itself.

*It refuses.* If the corpus cannot speak to a brief -- an element count nothing
was collected for, a template with too little behind it -- the answer is a
refusal with a reason, not three plausible-looking options. Refusal fails
closed: an exception while deciding whether we know enough resolves to "we do
not".

*Approval is the training signal.* The confidence attached to a template is
learned from which compositions the owner accepted, so the approve control is
not workflow furniture. If approving never moves the number, the loop is
decorative and the design is wrong.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

ElementKind = Literal["text", "image", "logo"]

# Shrinkage prior for *owner decisions*, carried across from the Feature Factory
# unchanged. Two approvals out of two is not twice as trustworthy as one out of
# one, and n/(n + PRIOR) says so. Ten is right here because owner decisions
# genuinely are few.
PRIOR = 10.0

# It is also right for corpus attestation, and the flat-looking confidence was
# not its fault. With 33 designs behind the thinnest template, n/(n + 10) puts
# everything above 0.77 -- and that is *correct*: ninety-two designs is a real
# pattern, and so is thirty-three. Every arrangement here is well attested.
#
# The mistake was expecting attestation to discriminate. It answers "is this a
# real pattern", to which the honest answer for all fourteen is yes. What
# separates them is whether the arrangement suits *this* brief, which is fit --
# so the confidence shown is the two multiplied. A well-attested layout that
# puts a photograph where the corpus put a line of type is not a confident
# proposal, however many brands used it for something else.
MIN_ATTESTED = 3

# A template needs at least this many corpus designs behind it to be offered.
# Matched to the learner's own cluster floor -- a higher number here would
# silently discard families the learner had already decided were worth naming,
# and the confidence attached to each already says how thin it is.
MIN_TEMPLATE_DESIGNS = 3

# Placement confidence below this is not evidence, it is noise wearing a number.
# The Feature Factory's equivalent gate is `total_samples > 0`, which lets a
# single observation count as knowledge; that is the flaw not inherited here.
MIN_CONFIDENCE = 0.35

# Most options ever offered. More than this is not choice, it is abdication.
MAX_OPTIONS = 3


@dataclass(frozen=True)
class Element:
    """One thing to place. Supplied by the owner; never generated here."""

    kind: ElementKind
    content: str = ""
    # Width over height, for images and logos. Text is measured from its words.
    aspect: float = 1.0

    @property
    def words(self) -> int:
        return len(self.content.split()) if self.content.strip() else 0

    @property
    def longest_word(self) -> int:
        return max((len(w) for w in self.content.split()), default=0)


@dataclass(frozen=True)
class Brief:
    """A set of elements to arrange, plus where they are going."""

    elements: tuple[Element, ...]
    garment: str = "tee"
    surface: str = "front"
    # Optional steer. When absent the corpus decides without one.
    tradition: str | None = None


@dataclass(frozen=True)
class PlacedSlot:
    """One element, positioned. Proportions of the print area, never pixels."""

    slot: int
    element_index: int
    element_kind: ElementKind
    content: str
    role: str
    top: float
    height: float
    width: float
    centre_x: float


@dataclass(frozen=True)
class Option:
    """One way to arrange the brief, with what stands behind it."""

    template_id: str
    template_name: str
    slots: tuple[PlacedSlot, ...]
    fit: float
    confidence: float
    corpus_designs: int
    approvals: int
    decisions: int
    traditions: dict[str, int]
    rationale: str


@dataclass(frozen=True)
class Composition:
    """The engine's answer, including when the answer is no."""

    composable: bool
    options: tuple[Option, ...] = ()
    # One durable string, so decisions can be grouped by which doubt did the work.
    refusal_reason: str = ""
    refusal_detail: str = ""
    # What the corpus cannot speak to for this brief. Never silently omitted.
    gaps: tuple[str, ...] = ()
    features: dict[str, float] = field(default_factory=dict)


def brief_features(brief: Brief) -> dict[str, float]:
    """The brief as counts and ratios only.

    Every dimension is dimensionless on purpose. Absolute sizes are what tied
    the first generator to one fixture's pixel geometry, and what the Feature
    Factory avoids so that one model serves any price level.
    """
    elements = brief.elements
    count = len(elements)
    if count == 0:
        return {"element_count": 0.0}

    kinds = [element.kind for element in elements]
    text_words = [element.words for element in elements if element.kind == "text"]
    total_words = sum(text_words)

    return {
        "element_count": float(count),
        "text_share": kinds.count("text") / count,
        "image_share": kinds.count("image") / count,
        "logo_share": kinds.count("logo") / count,
        "total_words": float(total_words),
        "words_per_text": (total_words / len(text_words)) if text_words else 0.0,
        # Share of the text taken by its longest word. Bounded to 0..1 like
        # every other dimension -- an earlier version divided characters by
        # word count, which is characters per word, unbounded, and would have
        # dominated any distance computed over these features.
        "longest_word_share": (
            max((e.longest_word for e in elements), default=0)
            / max(sum(len(e.content.replace(" ", "")) for e in elements if e.kind == "text"), 1)
        ),
        "mean_aspect": (
            sum(e.aspect for e in elements if e.kind in ("image", "logo"))
            / max(sum(1 for e in elements if e.kind in ("image", "logo")), 1)
        ),
    }


class ApprovalStore:
    """Approve/reject decisions per template, kept durable.

    This is the feedback edge. The Feature Factory rebuilds its cluster-to-outcome
    map from closed trades; this rebuilds from the owner's decisions, which is
    the only reason the approve control exists.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: dict[str, dict[str, int]] = {}
        if path.is_file():
            try:
                self._data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                # A corrupt store means no learned history, not a crash. The
                # engine falls back to corpus evidence alone.
                self._data = {}

    def record(self, template_key: str, approved: bool) -> None:
        entry = self._data.setdefault(template_key, {"approved": 0, "decisions": 0})
        entry["decisions"] += 1
        if approved:
            entry["approved"] += 1
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def history(self, template_key: str) -> tuple[int, int]:
        entry = self._data.get(template_key, {})
        return int(entry.get("approved", 0)), int(entry.get("decisions", 0))


def slot_affinity(width: float, height: float) -> ElementKind | None:
    """What a slot of these proportions held, inferred from its shape.

    The corpus records slot geometry and nothing about content, so a brief of an
    image and a phrase matched every two-element template equally -- including
    the two that are plainly two lines of type. The shape gives it away: a slot
    0.89 wide by 0.49 tall is a mass, and one 0.92 by 0.16 is a line of words.

    Returning None for the middle band is deliberate. A slot that could be
    either should not be evidence for or against anything.
    """
    if height <= 0:
        return None
    aspect = width / height
    if aspect >= 4.5:
        return "text"
    if aspect <= 2.5:
        return "image"
    return None


def _kind_fit(brief: Brief, template: dict[str, Any]) -> float:
    """How well the supplied kinds match what this template's slots held.

    Scored per slot and averaged, so a template whose shapes say image-then-
    caption is preferred for an image and a phrase, and the two-lines-of-type
    arrangement is not. A logo counts as an image: both are marks rather than
    words.
    """
    slots = template.get("slots") or []
    if not slots or len(slots) != len(brief.elements):
        return 0.5

    scored = 0.0
    counted = 0
    for element, slot in zip(brief.elements, slots, strict=False):
        wants = slot_affinity(float(slot.get("width", 0)), float(slot.get("height", 0)))
        if wants is None:
            continue
        supplied = "text" if element.kind == "text" else "image"
        scored += 1.0 if wants == supplied else 0.0
        counted += 1
    # Every slot ambiguous is not a match and not a mismatch.
    return scored / counted if counted else 0.5


def _attestation(corpus_designs: int) -> float:
    """Whether this arrangement is a real pattern rather than a coincidence."""
    if corpus_designs < MIN_ATTESTED:
        return 0.0
    return corpus_designs / (corpus_designs + PRIOR)


def _confidence(corpus_designs: int, approved: int, decisions: int, fit: float = 1.0) -> float:
    """How much to trust this template for this brief.

    Two sources, deliberately kept separate. The corpus says how well attested
    the arrangement is among brands that ship; approvals say whether it suits
    this brand specifically. Owner decisions are weighted per observation more
    heavily than corpus designs, because they are about us.
    """
    # Attested *and* suited. Either one alone overstates: a layout used by a
    # third of the corpus is not a confident answer for a brief it does not fit,
    # and a perfect fit to something nobody has ever shipped is a guess.
    corpus_weight = _attestation(corpus_designs) * fit
    if decisions == 0:
        # No decisions yet is not evidence against. It caps how far corpus
        # attestation alone can carry a template, and nothing more.
        return round(corpus_weight * 0.75, 4)

    approval_rate = approved / decisions
    owner_weight = decisions / (decisions + PRIOR)
    blended = (1 - owner_weight) * corpus_weight + owner_weight * approval_rate
    return round(blended, 4)


def _lead_index(brief: Brief) -> int:
    """Which element carries the composition.

    An image or logo leads when present -- it is the thing seen first from
    across a room. Otherwise the longest phrase leads. This is a presentation
    decision, not a judgement about the content's quality.
    """
    for index, element in enumerate(brief.elements):
        if element.kind == "image":
            return index
    for index, element in enumerate(brief.elements):
        if element.kind == "logo":
            return index
    return max(
        range(len(brief.elements)),
        key=lambda i: brief.elements[i].words,
        default=0,
    )


def _assign(brief: Brief, slots: list[dict[str, Any]]) -> tuple[PlacedSlot, ...]:
    """Put each element in a slot: the lead into the largest, the rest in order.

    Reading order is preserved for everything that is not the lead, because a
    supplied sequence of lines is a sequence the owner chose.
    """
    lead = _lead_index(brief)
    largest = max(range(len(slots)), key=lambda i: slots[i]["height"] * slots[i]["width"])

    remaining = [i for i in range(len(brief.elements)) if i != lead]
    placed: list[PlacedSlot] = []

    for slot_index, slot in enumerate(slots):
        if slot_index == largest:
            element_index = lead
            role = "lead"
        else:
            if not remaining:
                continue
            element_index = remaining.pop(0)
            role = "support"
        element = brief.elements[element_index]
        placed.append(
            PlacedSlot(
                slot=slot["slot"],
                element_index=element_index,
                element_kind=element.kind,
                content=element.content,
                role=role,
                top=float(slot["top"]),
                height=float(slot["height"]),
                width=float(slot["width"]),
                centre_x=float(slot["centre_x"]),
            )
        )
    return tuple(placed)


def _fit(brief: Brief, template: dict[str, Any]) -> float:
    """How closely this brief resembles what the template was learned from.

    Word count is the signal available on both sides: the corpus records median
    words per design, and the brief supplies its own. Compared as a ratio so a
    two-word brief against a three-word template scores like a twenty against a
    thirty.
    """
    brief_words = sum(element.words for element in brief.elements)
    template_words = float(template.get("median_words") or 0)
    if brief_words == 0 or template_words == 0:
        word_fit = 0.5
    else:
        ratio = min(brief_words, template_words) / max(brief_words, template_words)
        word_fit = ratio

    tradition_fit = 1.0
    if brief.tradition:
        traditions = template.get("traditions") or {}
        total = sum(traditions.values()) or 1
        tradition_fit = 0.5 + 0.5 * (traditions.get(brief.tradition, 0) / total)

    share = float(template.get("share") or 0)
    kind_fit = _kind_fit(brief, template)
    # Kind carries the most weight of the four. Putting a photograph where the
    # corpus put a line of type is a worse mistake than being two words off.
    return round(0.4 * kind_fit + 0.3 * word_fit + 0.2 * tradition_fit + 0.1 * share, 4)


class CompositionEngine:
    """Arranges a brief using templates learned from the corpus."""

    def __init__(self, templates_path: Path, approvals_path: Path) -> None:
        self.templates_path = templates_path
        self.approvals = ApprovalStore(approvals_path)
        self._families: dict[str, Any] = {}
        self._source_designs = 0
        if templates_path.is_file():
            try:
                report = json.loads(templates_path.read_text(encoding="utf-8"))
                self._families = report.get("families", {})
                self._source_designs = int(report.get("source_designs", 0))
            except (json.JSONDecodeError, OSError):
                self._families = {}

    @property
    def ready(self) -> bool:
        return bool(self._families)

    def template_key(self, element_count: int, template_id: str) -> str:
        """Keyed by learned identity, not by label.

        Descriptive names collide -- the corpus yields two distinct "wide band"
        centroids differing in proportion -- and keying approvals by name would
        pool two different arrangements into one score.
        """
        return f"{element_count}:{template_id}"

    def compose(self, brief: Brief) -> Composition:
        """Answer the brief, or refuse it with a reason. Never raises."""
        try:
            return self._compose(brief)
        except Exception as error:
            return Composition(
                composable=False,
                refusal_reason="ASSESSMENT_FAILED",
                refusal_detail=type(error).__name__,
            )

    def _compose(self, brief: Brief) -> Composition:
        features = brief_features(brief)

        if not brief.elements:
            return Composition(
                composable=False,
                refusal_reason="NO_ELEMENTS",
                refusal_detail="nothing was supplied to arrange",
                features=features,
            )

        if not self._families:
            return Composition(
                composable=False,
                refusal_reason="NO_CLUSTER",
                refusal_detail="no learned templates; run learn_design_templates.py",
                features=features,
            )

        count = len(brief.elements)
        family = self._families.get(str(count))
        gaps: list[str] = []

        if family is None:
            available = ", ".join(sorted(self._families, key=int))
            return Composition(
                composable=False,
                refusal_reason="NO_CLUSTER",
                refusal_detail=(
                    f"nothing in the corpus arranges {count} elements; "
                    f"element counts with evidence: {available}"
                ),
                features=features,
            )

        # --- Synthesis: which templates are eligible at all. Kept separate from
        # scoring so a threshold never leaks into a weight. ---
        eligible = [
            template
            for template in family.get("templates", [])
            if int(template.get("designs", 0)) >= MIN_TEMPLATE_DESIGNS
        ]
        if not eligible:
            return Composition(
                composable=False,
                refusal_reason="NO_ELIGIBLE_TEMPLATE",
                refusal_detail=(
                    f"{count}-element designs exist but no arrangement among them "
                    f"has {MIN_TEMPLATE_DESIGNS} designs behind it"
                ),
                features=features,
            )

        # --- Scoring: of the survivors, which fits best. ---
        scored: list[Option] = []
        for template in eligible:
            key = self.template_key(count, str(template.get("id") or template["name"]))
            approved, decisions = self.approvals.history(key)
            # Fit first: confidence is attestation times fit, so it cannot be
            # computed before the fit it depends on.
            fit = _fit(brief, template)
            confidence = _confidence(int(template["designs"]), approved, decisions, fit)
            if confidence < MIN_CONFIDENCE:
                continue
            slots = _assign(brief, template["slots"])
            if len(slots) < count:
                # The template cannot hold everything supplied. Not a refusal on
                # its own -- another template may -- but this one is out.
                continue
            scored.append(
                Option(
                    template_id=str(template.get("id") or template["name"]),
                    template_name=template["name"],
                    slots=slots,
                    fit=fit,
                    confidence=confidence,
                    corpus_designs=int(template["designs"]),
                    approvals=approved,
                    decisions=decisions,
                    traditions=dict(template.get("traditions") or {}),
                    rationale=self._rationale(template, brief, approved, decisions),
                )
            )

        if not scored:
            return Composition(
                composable=False,
                refusal_reason="INSUFFICIENT_EVIDENCE",
                refusal_detail=(
                    f"{len(eligible)} arrangement(s) for {count} elements, none above "
                    f"the confidence floor of {MIN_CONFIDENCE}"
                ),
                features=features,
            )

        scored.sort(key=lambda option: -(option.fit * option.confidence))

        if brief.tradition:
            attested = any(brief.tradition in option.traditions for option in scored)
            if not attested:
                gaps.append(
                    f"no collected design in the '{brief.tradition}' tradition uses "
                    f"a {count}-element arrangement; ranking ignored tradition"
                )
        if brief.surface != "front":
            gaps.append(
                f"templates are learned from front-of-garment prints; '{brief.surface}' "
                "placement is not separately attested"
            )

        # Everything that scored is offered, up to the cap.
        #
        # This used to shrink the list when confidence was low -- three above
        # 0.6, two above 0.45, otherwise one. With no approval history
        # confidence is capped at corpus weight x 0.75, so it rarely cleared 0.6
        # and the cap almost always bit. Confidence is already reported against
        # every option; hiding the rest decides for the reader twice.

        return Composition(
            composable=True,
            options=tuple(scored[:MAX_OPTIONS]),
            gaps=tuple(gaps),
            features=features,
        )

    def _rationale(
        self, template: dict[str, Any], brief: Brief, approved: int, decisions: int
    ) -> str:
        """Why this arrangement, in the corpus's own terms."""
        designs = int(template["designs"])
        share = float(template.get("share") or 0)
        traditions = template.get("traditions") or {}
        lead_tradition = next(iter(traditions), None)

        parts = [
            f"{designs} collected designs arrange {len(brief.elements)} elements this way",
            f"{share:.0%} of all {len(brief.elements)}-element designs in the corpus",
        ]
        if lead_tradition:
            parts.append(f"most often in {lead_tradition}")
        if decisions:
            parts.append(f"approved {approved} of {decisions} times here")
        else:
            parts.append("no decisions recorded here yet")
        return "; ".join(parts)

    def record_decision(self, element_count: int, template_id: str, approved: bool) -> None:
        """Feed a decision back. This is what moves confidence."""
        self.approvals.record(self.template_key(element_count, template_id), approved)
