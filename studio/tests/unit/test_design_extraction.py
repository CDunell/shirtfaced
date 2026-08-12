"""Measuring a design image into a rubric-ready review.

What is pinned here is that the measurements discriminate (a small chest hit
does not read like a full front print), and -- more importantly -- that the
extractor never claims to have judged something it cannot judge. An extractor
that quietly passed the gates it can't see would be worse than no extractor.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from app.services.design_extraction import HARD_GATE_IDS, extract, measure, points_floor, to_review


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
    by_gate = {g["id"]: g["result"] for g in review["hardGates"]}

    for gate_id in (
        "dominant_proposition_clear",
        "collection_role_defined",
        "identity_geometry_preserved",
        "logo_removal_recognition_survives",
        "competitor_substitution_survives",
        "worn_body_review_completed",
        "rights_cleared_for_sale",
        "product_blank_defined",
        "construction_conflicts_resolved",
        "production_files_match_art",
    ):
        assert by_gate[gate_id] == "not_tested", f"{gate_id} was claimed without evidence"


def test_every_gate_result_carries_evidence(tmp_path) -> None:  # type: ignore[no-untyped-def]
    review = extract("d1", "Test", _garment(tmp_path, print_box=[210, 230, 390, 430]))

    assert len(review["hardGates"]) == len(HARD_GATE_IDS)
    for result in review["hardGates"]:
        assert result["evidence"].strip()


def test_an_extracted_review_always_leaves_gates_untested(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Extraction alone can never fully clear a design.

    DESIGN_REVIEW_SCORECARD.md Section 2: a design cannot be approved from one
    floating artwork file. ``workflow.ts``'s ``evaluateReview`` treats an
    untested gate exactly as a failed one, so leaving these ``not_tested`` is
    what keeps the extractor's output a starting point for a human, not a
    verdict.
    """
    review = extract("d1", "Test", _garment(tmp_path, print_box=[210, 230, 390, 430]))
    untested = [g for g in review["hardGates"] if g["result"] == "not_tested"]

    assert untested


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
    by_gate = {g["id"]: g["result"] for g in review["hardGates"]}

    assert m.ink_colours >= 2
    assert by_gate["production_detail_feasible"] == "fail"


def test_distance_category_is_rated_from_the_visual_tests(tmp_path) -> None:  # type: ignore[no-untyped-def]
    review = extract("d1", "Test", _garment(tmp_path, print_box=[200, 220, 400, 440]))
    rating = next(c for c in review["scoreCategories"] if c["id"] == "distance_and_silhouette")

    assert rating["score"] >= 8  # 4/5 of 10 points
    assert "thumbnail" in rating["notes"]


def test_minimum_required_is_on_the_points_scale_not_the_five_point_rating(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """A real bug this pins: ``domain.ts``'s ``scoreCategorySchema`` compares
    ``score`` and ``minimumRequired`` directly, both in points out of
    ``maximum``. Emitting the scorecard's raw 0-5 floor (e.g. 3) as
    ``minimumRequired`` against a points ``score`` (e.g. 8/10) would make the
    floor comparison ``8 < 3`` -- never true, silently defeating every floor
    check downstream in ``workflow.ts``'s ``evaluateReview``.
    """
    # Distance and Silhouette: maximum 10, scorecard floor 3/5 -> 6 points.
    assert points_floor("distance_and_silhouette") == 6.0

    review = extract("d1", "Test", _garment(tmp_path, print_box=[200, 220, 400, 440]))
    rating = next(c for c in review["scoreCategories"] if c["id"] == "distance_and_silhouette")

    assert rating["minimumRequired"] == 6.0
    assert rating["score"] > rating["minimumRequired"]
