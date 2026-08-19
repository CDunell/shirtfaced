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

import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

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

    archetype_key = by_field.get("Graphic archetype", "")
    archetype_prose = _ARCHETYPE_PROSE.get(
        archetype_key, "One dominant graphic element, not several competing ideas."
    )

    ink_value = by_field.get("Ink colours", "")
    ink_count = ink_value.split(" — ")[0].strip() or "a small number of"

    placement = by_field.get("Placement", "upper")
    placement_prose = {
        "upper": "small, tight chest-placement graphic — upper chest only, not a big "
        "front-hero print",
        "centre": "centred mid-chest graphic at a self-contained, conversational scale",
        "lower": "smaller graphic sitting lower on the torso, closer to the hem",
    }.get(placement, "a compact chest-scale graphic")

    scale_value = by_field.get("Scale role", "")
    if "S1" in scale_value or "S2" in scale_value:
        scale_prose = "roughly 3-4 inches wide"
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
    phrase_line = f' "{phrase.strip()}" text.' if phrase.strip() else ""

    return (
        f"T-shirt graphic design, {tradition_label} style,{phrase_line} "
        f"{placement_prose.capitalize()} ({scale_prose}). "
        f"Screen-print aesthetic, exactly {ink_count} flat ink colors, no gradients or "
        f"photographic shading. {polarity_prose} {archetype_prose} "
        "Flat vector illustration style, ready for screen printing."
    )
