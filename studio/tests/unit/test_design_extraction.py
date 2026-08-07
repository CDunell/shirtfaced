"""Measuring a design image into a rubric-ready review.

What is pinned here is that the measurements discriminate (a small chest hit
does not read like a full front print), and -- more importantly -- that the
extractor never claims to have judged something it cannot judge. An extractor
that quietly passed the gates it can't see would be worse than no extractor.
"""

from __future__ import annotations

import numpy as np
import pytest
from PIL import Image, ImageDraw

from app.domain.design_review import GateStatus, HardGate, ScoreCategory
from app.services.design_extraction import extract, measure, to_review
from app.services.design_scoring import score_design


def _garment(tmp_path, print_box=None, ink=(240, 240, 240), colours=1):  # type: ignore[no-untyped-def]
    """A synthetic black garment shot with an optional print on the torso."""
    image = Image.new("RGB", (600, 600), (18, 18, 20))
    draw = ImageDraw.Draw(image)
    if print_box:
        draw.rectangle(print_box, fill=ink)
        if colours > 1:
            x0, y0, x1, y1 = print_box
            span = (x1 - x0) // max(colours, 1)
            for i in range(1, colours):
                shade = (40 + i * 45, 200 - i * 40, 90 + i * 30)
                draw.rectangle([x0 + i * span, y0, x0 + (i + 1) * span, y1], fill=shade)
    path = tmp_path / "design.jpg"
    image.save(path)
    return path


def test_a_garment_with_no_print_is_reported_as_such(tmp_path) -> None:  # type: ignore[no-untyped-def]
    m = measure(_garment(tmp_path))

    assert m.has_print is False
    assert m.print_coverage < 0.01


def test_a_large_print_measures_larger_than_a_small_one(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The measurement that matters most: coverage has to discriminate.

    An early version scored a small left-chest print at 44% because its
    analysis box caught the model's head and the background.
    """
    small_dir = tmp_path / "small"
    small_dir.mkdir()
    small = measure(_garment(small_dir, print_box=[250, 240, 290, 280]))
    big = measure(_garment(tmp_path, print_box=[210, 230, 390, 430]))

    assert big.print_coverage > small.print_coverage * 3


def test_light_on_dark_is_detected(tmp_path) -> None:  # type: ignore[no-untyped-def]
    m = measure(_garment(tmp_path, print_box=[210, 230, 390, 430], ink=(245, 245, 245)))

    assert m.light_on_dark is True


def test_a_bold_print_survives_the_reduction_tests(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """T1/T2/T3: a large high-contrast mass must survive all three."""
    m = measure(_garment(tmp_path, print_box=[200, 220, 400, 440]))

    assert m.thumbnail_survives is True
    assert m.blur_survives is True
    assert m.greyscale_survives is True


def test_gates_needing_judgement_are_never_marked_passed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The load-bearing guarantee of this module.

    A measurement cannot tell whether a design has one dominant proposition or
    whether it duplicates the range. Claiming otherwise would let an unreviewed
    design through the one filter meant to stop it.
    """
    review = extract("d1", "Test", _garment(tmp_path, print_box=[210, 230, 390, 430]))
    by_gate = {g.gate: g.status for g in review.gate_results}

    for gate in (
        HardGate.NO_DOMINANT_PROPOSITION,
        HardGate.HIERARCHY_COLLAPSE,
        HardGate.NO_COLLECTION_ROLE,
        HardGate.COLLECTION_REDUNDANCY,
        HardGate.IDENTITY_SUBSTITUTION,
        HardGate.WEAK_WITHOUT_THE_LOGO,
        HardGate.MOCK_UP_ONLY_SUCCESS,
        HardGate.UNRESOLVED_RIGHTS_RISK,
        HardGate.NO_CLEAR_PRODUCT_DEFINITION,
        HardGate.GARMENT_CONFLICT,
    ):
        assert by_gate[gate] is GateStatus.NOT_TESTED, f"{gate} was claimed without evidence"


def test_every_gate_result_carries_evidence(tmp_path) -> None:  # type: ignore[no-untyped-def]
    review = extract("d1", "Test", _garment(tmp_path, print_box=[210, 230, 390, 430]))

    assert len(review.gate_results) == len(HardGate)
    for result in review.gate_results:
        assert result.evidence.strip()


def test_an_extracted_review_always_blocks(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Extraction alone can never approve a design.

    DESIGN_REVIEW_SCORECARD.md §2: a design cannot be approved from one floating
    artwork file. Untested gates block exactly as failed ones do, so the
    extractor's output is a starting point for a human, not a verdict.
    """
    review = extract("d1", "Test", _garment(tmp_path, print_box=[210, 230, 390, 430]))
    outcome = score_design(review)

    assert outcome.blocked is True
    assert outcome.untested_gates


def test_too_many_inks_fails_production(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Print kept clear of the torso edges, as a real chest print is.

    A print reaching the torso margins is read as the garment -- see
    _garment_colour's docstring on the jumbo limit.
    """
    m = measure(_garment(tmp_path, print_box=[240, 230, 360, 420], colours=4))
    review = to_review(
        "d1",
        "Test",
        m,
        thresholds={"ink_colours_p90": 1, "print_coverage_p10": 0.02, "print_coverage_p90": 0.35},
    )
    by_gate = {g.gate: g.status for g in review.gate_results}

    assert m.ink_colours >= 2
    assert by_gate[HardGate.PRODUCTION_FAILURE] is GateStatus.FAIL


def test_distance_category_is_rated_from_the_visual_tests(tmp_path) -> None:  # type: ignore[no-untyped-def]
    review = extract("d1", "Test", _garment(tmp_path, print_box=[200, 220, 400, 440]))
    rating = next(
        r for r in review.category_ratings if r.category is ScoreCategory.DISTANCE_AND_SILHOUETTE
    )

    assert rating.rating >= 4
    assert "thumbnail" in rating.evidence
