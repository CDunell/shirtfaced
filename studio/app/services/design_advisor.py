"""Deciding how to present a phrase or a graphic, from what the corpus does.

The system's own audit named this gap: *"Rules are post-hoc, not generative.
Everything in System B evaluates a design that already exists. There is no design
generator analogous to prompt_planner.py."* ``design_extraction`` is post-hoc --
it measures finished work. This is the other direction: give it a phrase or a
graphic, and it returns how that content should be presented, with the corpus
evidence behind each choice.

It prescribes **presentation, never content**. It will not write the joke, invent
the artwork, or decide whether an idea is any good. It answers the questions the
constitution requires answered before artwork begins -- which graphic archetype,
which layout, which scale role, how much of the garment, how many inks, where on
the body, light or dark -- and it answers them from 2,868 measured designs rather
than from taste.

Every recommendation carries its evidence. A number with no corpus behind it is
marked as a default, not dressed up as a finding.
"""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# scripts/mine_design_structure.py's raw per-design output: 4,125 real designs,
# each with its measured element count, band shape and band geometry. Loaded
# once and cached -- 1.3MB of JSON nobody wants re-parsed per request.
STRUCTURE_RAW_PATH = (
    Path(__file__).resolve().parents[2] / "var" / "design_corpus" / "design_structure_raw.json"
)

# Garment words are not part of the design's phrase. "Squawk 1200 Sweatshirt" is
# a two-word design, not three.
GARMENT_WORDS = re.compile(
    r"\b(tee|t-?shirts?|hoodie|sweat ?shirt|crew ?neck|jumper|cap|hat|beanie|"
    r"long ?sleeve|pullover|sweater|oversized|crop|shirt|stubby|holder|koozie)\b",
    re.IGNORECASE,
)

Intent = Literal["phrase", "graphic", "both"]


def phrase_words(text: str) -> list[str]:
    """The words that are actually the design, garment nouns removed."""
    return [w for w in re.findall(r"[A-Za-z0-9']+", GARMENT_WORDS.sub("", text)) if len(w) > 1]


def length_bucket(word_count: int) -> str:
    """Phrase-length bands. Coverage rises monotonically across these in the
    corpus (9.5 / 10.9 / 12.2 / 14.2 per cent), which is what makes them useful
    rather than arbitrary: more words genuinely need more garment."""
    if word_count <= 2:
        return "short"
    if word_count <= 4:
        return "mid"
    if word_count <= 6:
        return "long"
    return "very_long"


BUCKET_LABEL = {
    "short": "1-2 words",
    "mid": "3-4 words",
    "long": "5-6 words",
    "very_long": "7+ words",
}

# Scale roles, SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION.md §7. The constitution
# names them and says "scale is defined by function first and dimensions second",
# then never dimensions them. These bands come from the corpus's own coverage
# distribution, so a scale role finally means a measurable thing.
SCALE_BANDS: list[tuple[float, str, str]] = [
    (0.02, "S1", "chest identifier — compact, conversational distance"),
    (0.06, "S2", "emblem — self-contained, substantial surrounding blank"),
    (0.22, "S3", "hero — dominant torso composition"),
    (1.01, "S4", "jumbo — approaches seams, garment body as the field"),
]


@dataclass
class Recommendation:
    """One decision, and why."""

    field_name: str
    value: str
    evidence: str
    confidence: Literal["corpus", "weak-corpus", "default"]

    def to_dict(self) -> dict[str, str]:
        return {
            "field": self.field_name,
            "value": self.value,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }


@dataclass
class DesignDirection:
    """How to present the supplied content."""

    input_summary: str
    intent: Intent
    tradition: str
    recommendations: list[Recommendation] = field(default_factory=list)
    alternatives: list[str] = field(default_factory=list)
    not_decided: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "input": self.input_summary,
            "intent": self.intent,
            "tradition": self.tradition,
            "recommendations": [r.to_dict() for r in self.recommendations],
            "alternatives": self.alternatives,
            "not_decided": self.not_decided,
        }


def measurement_rows(session: Session) -> list[dict[str, Any]]:
    """Measured designs joined to their phrase length. Empty when unmined.

    Reads ``design_measurements`` -- the corpus measured by code, one row per
    frame, written by ``python -m app.cli design-data --refresh``. This used
    to read ``var/design_corpus/joined.json``, a file that existed only on
    whichever machine last ran the joiner, which for this advisor's whole
    life was no machine at all. The table cannot be absent from the box, and
    an empty result keeps the same honest meaning: unmined, so every
    recommendation below is a default.
    """
    from sqlalchemy import select

    from app.db.measurement_models import DesignMeasurement

    rows = session.execute(
        select(
            DesignMeasurement.tradition,
            DesignMeasurement.phrase_words,
            DesignMeasurement.print_coverage,
            DesignMeasurement.ink_colours,
            DesignMeasurement.placement_band,
            DesignMeasurement.light_on_dark,
        ).where(DesignMeasurement.refusal_reason.is_(None))
    ).all()
    return [
        {
            "t": tradition,
            "w": words,
            "cov": coverage,
            "ink": inks,
            "band": band,
            "lod": light_on_dark,
        }
        for tradition, words, coverage, inks, band, light_on_dark in rows
    ]


def _scale_role(coverage: float) -> tuple[str, str]:
    for ceiling, role, description in SCALE_BANDS:
        if coverage < ceiling:
            return role, description
    return "S4", SCALE_BANDS[-1][2]


def advise(
    phrase: str = "",
    has_graphic: bool = False,
    tradition: str = "novelty",
    rows: list[dict[str, Any]] | None = None,
) -> DesignDirection:
    """Recommend how to present this content.

    ``tradition`` selects which part of the corpus to learn from -- a brewery
    prints very differently from a skate brand, and averaging them produces a
    design that belongs to neither.
    """
    rows = [] if rows is None else rows
    words = phrase_words(phrase)
    bucket = length_bucket(len(words))

    if phrase and has_graphic:
        intent: Intent = "both"
    elif has_graphic:
        intent = "graphic"
    else:
        intent = "phrase"

    direction = DesignDirection(
        input_summary=(f'"{phrase.strip()}"' if phrase.strip() else "graphic only")
        + (f" · {len(words)} words" if words else ""),
        intent=intent,
        tradition=tradition,
    )

    def add(name: str, value: str, evidence: str, confidence: str = "corpus") -> None:
        direction.recommendations.append(
            Recommendation(name, value, evidence, confidence)  # type: ignore[arg-type]
        )

    # --- graphic archetype: constitution §8's own vocabulary -----------------
    if intent == "phrase":
        archetype = "typographic hero"
        why = (
            "Words with no supplied image. The constitution requires one dominant "
            "archetype; with nothing to look at but the phrase, the lettering has to "
            "be the thing worth looking at."
        )
    elif intent == "graphic":
        archetype = "image-led hero"
        why = (
            "A graphic with no phrase leads on the image; any type identifies rather than competes."
        )
    else:
        archetype = "image-and-title lockup"
        why = (
            "Both supplied. §8 allows supporting elements but demands one dominant "
            "archetype — a lockup makes them one object instead of two competing ones."
        )
    add("Graphic archetype", archetype, why, "default")

    # --- everything below is measured ---------------------------------------
    same_tradition = [r for r in rows if r.get("t") == tradition]
    pool = same_tradition or rows
    pool_note = (
        f"{len(same_tradition)} {tradition} designs"
        if same_tradition
        else f"{len(rows)} designs across all traditions ({tradition} not represented)"
    )
    confidence = "corpus" if len(pool) >= 40 else ("weak-corpus" if pool else "default")

    if not pool:
        direction.not_decided.append(
            "The corpus has not been measured, so nothing below is evidence-backed. "
            "Run: python -m app.cli design-data --refresh"
        )
        return direction

    matched = [r for r in pool if length_bucket(r.get("w", 0)) == bucket] or pool
    coverage = statistics.median(r["cov"] for r in matched)
    inks = int(statistics.median(r["ink"] for r in matched))
    placement = Counter(r["band"] for r in matched).most_common(1)[0][0]
    light_share = sum(1 for r in matched if r["lod"]) / len(matched)

    role, role_note = _scale_role(coverage)
    add(
        "Scale role",
        f"{role} — {role_note}",
        f"{coverage:.1%} median print coverage for {BUCKET_LABEL[bucket]} in {pool_note}. "
        "The constitution names S0-S4 without dimensioning them; this is that band measured.",
        confidence,
    )
    add(
        "Print coverage",
        f"~{coverage:.0%} of the torso",
        f"Coverage rises with phrase length across the corpus — 9.5% at 1-2 words to "
        f"14.2% at 7+. This phrase sits at {BUCKET_LABEL[bucket]}.",
        confidence,
    )
    add(
        "Ink colours",
        f"{inks} — screen-print first",
        f"Median {inks} significant inks in {pool_note}. Beyond the corpus p90 the "
        "colour count needs a documented reason, per §12.4.",
        confidence,
    )
    add(
        "Placement",
        placement,
        f"{Counter(r['band'] for r in matched)[placement]} of {len(matched)} comparable "
        f"designs place the mass {placement} on the torso.",
        confidence,
    )
    polarity = "light on dark" if light_share >= 0.5 else "dark on light"
    add(
        "Value polarity",
        polarity,
        f"{light_share:.0%} of comparable designs run light ink on a dark garment. "
        "Black is the documented seller for the tee, hoodie and cap.",
        confidence,
    )

    # --- layout: a body-side decision, so it follows scale -------------------
    layout = (
        "A3 — front hero / clean back"
        if role in {"S1", "S2"}
        else "A4 — clean or micro front / back hero"
    )
    add(
        "Layout archetype",
        layout,
        "At this scale the corpus puts the mass on one face and leaves the other quiet. "
        "§6 requires one archetype chosen before artwork begins.",
        "weak-corpus",
    )

    density = {
        "short": "D1 — sparse",
        "mid": "D2 — layered",
        "long": "D2 — layered",
        "very_long": "D3 — dense",
    }[bucket]
    add(
        "Density class",
        density,
        f"{BUCKET_LABEL[bucket]} of copy. D3 requires an explicit grid, frame or overlap "
        "system; D1 requires exceptional silhouette or typography.",
        "weak-corpus",
    )

    # --- alternatives worth trying, from neighbouring traditions -------------
    by_tradition: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if length_bucket(row.get("w", 0)) == bucket:
            by_tradition[row["t"]].append(row["cov"])
    neighbours = sorted(
        (
            (t, statistics.median(c))
            for t, c in by_tradition.items()
            if len(c) >= 25 and t != tradition
        ),
        key=lambda kv: abs(kv[1] - coverage),
    )
    for name, value in neighbours[:2]:
        direction.alternatives.append(
            f"{name} treats the same length at {value:.0%} coverage — worth a "
            f"variant if this reads too {'quiet' if value > coverage else 'loud'}."
        )

    direction.not_decided = [
        "The idea itself — whether the phrase is funny, or the graphic is good.",
        "Typeface, illustration style, and the actual artwork.",
        "Collection role and commercial tier: brief decisions, not properties of the content.",
        "Whether this duplicates something already in the range.",
    ]
    return direction


_SHAPE_PROSE = {
    "single wide mass": "one element spanning wide and shallow across the print area, not "
    "tall or narrow",
    "single tall mass": "one element running tall and narrow rather than wide",
    "single compact mark": "one small, self-contained mark rather than something spread "
    "across the print area",
    "lead above, support below": "the main element sits above a smaller supporting line, "
    "stacked top to bottom",
    "support above, lead below": "a smaller supporting line sits above the main element, "
    "which anchors the bottom",
    "lead on top, stacked support": "the main element leads at the top with supporting "
    "elements stacked beneath it",
    "framed centre — support above and below": "the main element sits centred, framed by "
    "supporting lines above and below it",
    "stacked support, lead at base": "supporting elements stack above, with the main "
    "element anchoring the base",
    "even stack — repeated bands": "several evenly-weighted bands stacked with no single "
    "dominant element",
    "two even bands — paired lines": "two lines of roughly equal weight, paired rather than "
    "one leading the other",
}


@lru_cache(maxsize=1)
def _structure_rows() -> tuple[dict[str, Any], ...]:
    """scripts/mine_design_structure.py's raw output, one entry per measured design."""
    if not STRUCTURE_RAW_PATH.is_file():
        return ()
    try:
        return tuple(json.loads(STRUCTURE_RAW_PATH.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return ()


def tradition_shape(tradition: str) -> tuple[str, int, int] | None:
    """The most common band shape actually measured for this tradition.

    Deterministic: no model, no network, same corpus in and same answer out --
    the same guarantee ``mine_design_structure.py`` makes. Returns
    ``(shape, count, tradition_total)`` or ``None`` if this tradition has no
    measured designs at all.
    """
    rows = [r for r in _structure_rows() if r.get("tradition") == tradition]
    if not rows:
        return None
    shape, count = Counter(r["shape"] for r in rows if r.get("shape")).most_common(1)[0]
    return shape, count, len(rows)


_ARCHETYPE_PROSE = {
    "typographic hero": "Bold lettering carries the whole design — no supporting image.",
    "image-led hero": "One dominant illustrated or photographic image carries the design, "
    "with no competing text element.",
    "image-and-title lockup": "Bold vintage-style lettering combined with a small icon or "
    "emblem, locked together as one unit — not text floating separately from artwork.",
    "emblem or badge": "A self-contained circular or shield-shaped badge/crest, with "
    "lettering following the emblem's own curve or border, not sitting outside it.",
    "poster or editorial": "A fully illustrated scene treated like a vintage print or poster, "
    "with the title integrated into the composition rather than added as a separate line.",
    "symbolic icon system": "A small set of simple, repeated iconographic marks rather than "
    "one large image.",
    "collage or controlled frame": "Multiple smaller elements arranged within one contained "
    "frame or border, not a single hero image.",
    "character or object portrait": "A single subject rendered in a formal portrait "
    "treatment, centred and dignified regardless of how absurd the subject is.",
    "all-over or jumbo field": "The graphic covers most of the garment's surface rather than "
    "sitting in one contained area.",
}


def render_generation_prompt(direction: DesignDirection, phrase: str = "") -> str:
    """Turn a DesignDirection into prose ready to paste into an image generator.

    ``advise()`` answers "what should this design measure" for a human reading
    a brief. Nobody pastes "print coverage: 4%" into ChatGPT, Nano Banana or
    Grok and gets a t-shirt graphic back — they need the same decisions
    written as a visual description. This is that translation, and only that:
    it still decides nothing ``advise()`` didn't already decide from the
    corpus. Wording, not judgement.
    """
    by_field = {r.field_name: r.value for r in direction.recommendations}
    if "Placement" not in by_field:
        # advise() bails out before adding any measured field once the corpus
        # pool for this request is empty -- "Graphic archetype" is the only
        # recommendation that survives that, and it is a default, not
        # evidence. Match advise()'s own refusal rather than filling the gap
        # with this function's private guesses.
        return (
            "The corpus has not been measured for this request, so there is nothing "
            "evidence-backed to build a prompt from. Run: python -m app.cli design-data --refresh"
        )

    # Prefer the real, tradition-specific measurement over the generic
    # archetype default: mine_design_structure.py measured actual composition
    # shapes from real designs in this tradition, which is a stronger claim
    # than "image-and-title lockup" (advise()'s constitutional default for
    # phrase+graphic, true of every tradition equally because it isn't
    # measured from any of them).
    shape_hit = tradition_shape(direction.tradition)
    if shape_hit is not None:
        shape, shape_count, tradition_total = shape_hit
        structure_prose = _SHAPE_PROSE.get(
            shape, f"the composition follows a '{shape}' arrangement"
        )
        archetype_prose = (
            f"Composition: {structure_prose} — the most common structure in "
            f"{shape_count} of {tradition_total} measured {direction.tradition} designs."
        )
    else:
        archetype_key = by_field.get("Graphic archetype", "")
        archetype_prose = _ARCHETYPE_PROSE.get(
            archetype_key, "One dominant graphic element, not several competing ideas."
        )

    # Placement says WHERE on the body; scale says HOW BIG. Keeping them in
    # one combined phrase produced a real contradiction -- "small, tight...
    # not a big front-hero print" followed immediately by "(a dominant,
    # large-scale graphic covering most of the torso)" whenever scale role
    # was S3. They are two separate measured facts and can disagree; say
    # both, don't let one silently overrule the other's wording.
    placement = by_field.get("Placement", "upper")
    placement_prose = {
        "upper": "positioned on the upper chest",
        "centre": "centred at mid-chest",
        "lower": "sitting lower on the torso, closer to the hem",
    }.get(placement, "positioned on the chest")

    scale_value = by_field.get("Scale role", "")
    if "S1" in scale_value or "S2" in scale_value:
        scale_prose = "small and self-contained, roughly 3-4 inches wide"
    elif "S3" in scale_value:
        scale_prose = "a dominant, large-scale graphic covering most of the torso"
    else:
        scale_prose = "an oversized graphic that runs close to the garment's seams"

    polarity = by_field.get("Value polarity", "light on dark")
    polarity_prose = (
        "Light-coloured ink on a black garment."
        if polarity == "light on dark"
        else "Dark ink on a light or white garment."
    )

    tradition_label = direction.tradition.replace("-", " ")
    # The input describes what to depict -- it is not a literal string to
    # typeset. Wrapping it in quotes and calling it "text" told the image
    # generator to print the sentence "Modern design twist on the classic
    # surf tee" onto a shirt, which is not what anyone meant by typing that.
    # If the idea names an actual short slogan, it will read as one in the
    # description; nothing here forces it to.
    idea_text = phrase.strip()
    idea_line = f" Design concept: {idea_text.rstrip('.')}." if idea_text else ""

    # Dropped: "exactly N flat ink colors, no gradients or photographic
    # shading". A hard colour-count cap combined with "no gradients" pushed
    # the image generator toward flat, thin, samey colour-blocked graphics --
    # confirmed against real Grok output, not a guess. The corpus's ink-count
    # measurement is still real and still shown in the structured
    # recommendations; it just doesn't belong as a generation constraint.
    #
    # Both guardrails below came from generating real test images and looking
    # at them, not from guessing:
    # - Without a style anchor, a dense scene concept (a diner at night)
    #   rendered as an atmospheric painterly poster bleeding past the
    #   garment edges -- not something a screen-print production run could
    #   reproduce. "Flat vector illustration style" was cut along with the
    #   ink-count cap by mistake; only the cap was the actual problem.
    # - A concept that describes an abstract quality of the lettering
    #   ("confidence carried entirely by the type") rather than its concrete
    #   form got read as the literal words to print -- "CONFIDENCE CARRED
    #   ENTIRELY BY THE TYPE", misspelling included. The instruction below
    #   is the general guard; concepts written that way should still be
    #   fixed at the source when found.
    return (
        f"T-shirt graphic design, {tradition_label} style.{idea_line} "
        f"Scale: {scale_prose}. Placement: {placement_prose}. "
        f"{polarity_prose} {archetype_prose} "
        "Flat vector illustration or clean halftone screen-print texture -- not a "
        "photorealistic or painterly scene, and not extending past the garment itself. "
        "Invent an appropriate short brand name or wordmark if the concept calls for "
        "lettering; do not render this description's own wording as the printed text, "
        "do not depict any real trademarked logo or brand name, and do not invent a name "
        "that closely echoes an existing apparel brand (e.g. nothing built from 'Rip', "
        "'Curl', 'Quik', 'Vans', 'Volcom' or similar recognisable fragments) -- invent "
        "something unrelated instead."
    )
