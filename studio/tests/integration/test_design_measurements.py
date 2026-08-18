"""The measured corpus and the learning loop, against the real database.

Two claims worth proving on PostgreSQL rather than a stub. The advisor and
the thresholds read ``design_measurements`` -- so rows written the way the
CLI writes them must come back in the advisor's vocabulary, and an empty
table must fall back to the documented defaults rather than invent numbers.
And the composer's confidence derives from ``composed_designs`` at compose
time -- so deciding a stored design must move what the next compose offers,
with no store in between to drift or go missing.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.design_advisor import measurement_rows
from app.services.design_composition import (
    Request,
    compose,
    decide,
    grammar_history,
    store,
)
from app.services.design_extraction import DEFAULT_THRESHOLDS, load_thresholds


def test_measured_rows_feed_the_advisor_and_the_thresholds(session: Session) -> None:
    from app.db.measurement_models import DesignMeasurement

    session.add_all(
        [
            DesignMeasurement(
                corpus="design_corpus",
                brand_slug="brand-a",
                product_slug=f"tee-{index}",
                image_path="image-01.jpg",
                tradition="skate",
                phrase_words=2,
                print_coverage=coverage,
                ink_colours=inks,
                placement_band="middle",
                light_on_dark=True,
                analyser_version="test",
            )
            for index, (coverage, inks) in enumerate([(0.10, 2), (0.20, 3), (0.30, 4)])
        ]
    )
    # A refused frame must count for neither consumer.
    session.add(
        DesignMeasurement(
            corpus="design_corpus",
            brand_slug="brand-a",
            product_slug="worn-shot",
            image_path="image-01.jpg",
            tradition="skate",
            refusal_reason="no torso band",
            analyser_version="test",
        )
    )
    session.flush()

    rows = measurement_rows(session)
    assert len(rows) == 3
    assert rows[0] == {"t": "skate", "w": 2, "cov": 0.10, "ink": 2, "band": "middle", "lod": True}

    thresholds = load_thresholds(session)
    assert thresholds["print_coverage_p10"] < thresholds["print_coverage_p90"]
    assert thresholds["ink_colours_p90"] >= 3


def test_an_empty_table_means_documented_defaults(session: Session) -> None:
    assert load_thresholds(session) == dict(DEFAULT_THRESHOLDS)
    assert measurement_rows(session) == []


def test_deciding_a_stored_design_moves_the_next_compose(session: Session) -> None:
    """The one thread the architecture said to prove first, on real tables:
    compose, keep, decide -- and the decision measurably reweights the next
    compose, read straight from composed_designs."""
    brief = Request(seed=8374, garment_key="garment_tee_crew_front", primary_text="SHIRTFACED")
    _, options = compose(brief, grammar_history(session))
    leader = options[0]
    assert leader.decisions == 0

    kept = store(session, brief, leader)
    decide(session, kept, approved=False, decided_by="owner")

    history = grammar_history(session)
    assert history[leader.grammar_key] == (0, 1)

    _, after = compose(brief, history)
    demoted = next(o for o in after if o.grammar_key == leader.grammar_key)
    assert demoted.decisions == 1
    assert demoted.confidence < leader.confidence
