"""Recommending presentation from measured corpus rows.

What is pinned here: the recommendation confidence honestly reflects how much
comparable evidence exists (empty corpus, a thin pool, a real one), the intent
and archetype selection follows the constitution's own three-way split, and
``not_decided`` never quietly shrinks -- an advisor that stopped naming what it
can't decide would be worse than no advisor.
"""

from __future__ import annotations

from app.services.design_advisor import advise, length_bucket, phrase_words


def _row(tradition="skate", words=3, coverage=0.05, ink=4, band="upper", light_on_dark=True):
    return {"t": tradition, "w": words, "cov": coverage, "ink": ink, "band": band, "lod": light_on_dark}


def _pool(count, **overrides):
    return [_row(**overrides) for _ in range(count)]


def test_phrase_words_strips_garment_nouns() -> None:
    assert phrase_words("Weekend Warrior Club T-Shirt") == ["Weekend", "Warrior", "Club"]
    assert phrase_words("Squawk 1200 Sweatshirt") == ["Squawk", "1200"]


def test_length_bucket_bands() -> None:
    assert length_bucket(1) == "short"
    assert length_bucket(2) == "short"
    assert length_bucket(3) == "mid"
    assert length_bucket(4) == "mid"
    assert length_bucket(5) == "long"
    assert length_bucket(6) == "long"
    assert length_bucket(7) == "very_long"


def test_advise_with_no_corpus_only_returns_the_default_archetype() -> None:
    """No mined data means nothing below the archetype line is evidence-backed.

    An advisor that filled in numbers anyway would be dressing up a guess as
    a finding -- exactly what this module's own docstring promises not to do.
    """
    direction = advise(phrase="Weekend Warrior Club", has_graphic=True, tradition="skate", rows=[])

    assert len(direction.recommendations) == 1
    assert direction.recommendations[0].field_name == "Graphic archetype"
    assert direction.recommendations[0].confidence == "default"
    assert any("not been mined" in note for note in direction.not_decided)


def test_intent_and_archetype_follow_the_three_way_split() -> None:
    phrase_only = advise(phrase="Weekend Warrior", has_graphic=False, rows=[])
    graphic_only = advise(phrase="", has_graphic=True, rows=[])
    both = advise(phrase="Weekend Warrior", has_graphic=True, rows=[])

    assert phrase_only.intent == "phrase"
    assert phrase_only.recommendations[0].value == "typographic hero"

    assert graphic_only.intent == "graphic"
    assert graphic_only.recommendations[0].value == "image-led hero"

    assert both.intent == "both"
    assert both.recommendations[0].value == "image-and-title lockup"


def test_confidence_is_corpus_only_once_the_matching_pool_is_large_enough() -> None:
    thin = advise(phrase="Weekend Warrior Club", has_graphic=True, tradition="skate", rows=_pool(10))
    deep = advise(phrase="Weekend Warrior Club", has_graphic=True, tradition="skate", rows=_pool(60))

    def confidence_of(direction, field_name):
        return next(r for r in direction.recommendations if r.field_name == field_name).confidence

    assert confidence_of(thin, "Scale role") == "weak-corpus"
    assert confidence_of(deep, "Scale role") == "corpus"


def test_falls_back_to_the_whole_corpus_when_tradition_is_unrepresented() -> None:
    rows = _pool(50, tradition="skate")
    direction = advise(phrase="Weekend Warrior", has_graphic=True, tradition="brewery", rows=rows)

    scale = next(r for r in direction.recommendations if r.field_name == "Scale role")
    assert "not represented" in scale.evidence


def test_scale_role_reflects_measured_coverage() -> None:
    jumbo = advise(
        phrase="Weekend Warrior",
        has_graphic=True,
        tradition="skate",
        rows=_pool(50, tradition="skate", coverage=0.5),
    )
    compact = advise(
        phrase="Weekend Warrior",
        has_graphic=True,
        tradition="skate",
        rows=_pool(50, tradition="skate", coverage=0.01),
    )

    scale_jumbo = next(r for r in jumbo.recommendations if r.field_name == "Scale role")
    scale_compact = next(r for r in compact.recommendations if r.field_name == "Scale role")

    assert scale_jumbo.value.startswith("S4")
    assert scale_compact.value.startswith("S1")


def test_alternatives_surface_a_neighbouring_tradition_at_a_different_scale() -> None:
    rows = _pool(50, tradition="skate", words=3, coverage=0.05) + _pool(
        30, tradition="band-merch", words=3, coverage=0.20
    )
    direction = advise(phrase="Weekend Warrior Club", has_graphic=True, tradition="skate", rows=rows)

    assert any("band-merch" in alt for alt in direction.alternatives)


def test_not_decided_always_names_what_it_cannot_judge() -> None:
    direction = advise(phrase="Weekend Warrior Club", has_graphic=True, tradition="skate", rows=_pool(50))

    assert len(direction.not_decided) == 4
    assert any("funny" in note or "good" in note for note in direction.not_decided)
