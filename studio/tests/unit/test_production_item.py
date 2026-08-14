"""The work queue: what is outstanding, in the order it should be picked up.

These are pure — transient rows, no session — because the whole point of a
derived item is that it is a function of the rows and nothing else.
"""

from __future__ import annotations

import datetime as dt

import pytest

from app.db.concept_models import (
    ApprovedDesign,
    DesignAsset,
    DesignAttempt,
    DesignConcept,
    DesignReviewRecord,
)
from app.domain.design_review import CATEGORY_LIMITS, GATE_LABELS, HARD_GATE_IDS, ScoreCategory
from app.domain.enums import (
    ConceptLibrary,
    ConceptStatus,
    DesignAssetKind,
    DesignAttemptMethod,
    DesignAttemptState,
)
from app.services.production_item import _item, work_queue


def concept(
    number: int = 1,
    status: ConceptStatus = ConceptStatus.BACKLOG,
    attempts: list[DesignAttempt] | None = None,
    versions: list[ApprovedDesign] | None = None,
    parsed: dict[str, object] | None = None,
) -> DesignConcept:
    row = DesignConcept(
        library=ConceptLibrary.TSHIRT,
        external_number=number,
        slug=f"{number:04d}-a-concept",
        title=f"CONCEPT {number}",
        concept_text="words",
        round=0,
        source_path="x",
        source_document_hash="0" * 64,
        parsed_json=parsed or {},
        status=status,
    )
    row.attempts = attempts or []
    row.approved_versions = versions or []
    return row


def attempt(
    number: int = 1,
    state: DesignAttemptState = DesignAttemptState.PLANNED,
    *,
    artwork: bool = False,
    review: DesignReviewRecord | None = None,
) -> DesignAttempt:
    row = DesignAttempt(
        attempt_number=number,
        method=DesignAttemptMethod.MANUAL_IMPORT,
        state=state,
    )
    row.assets = (
        [
            DesignAsset(
                kind=DesignAssetKind.ARTWORK,
                relative_path="a.png",
                sha256="0" * 64,
                mime_type="image/png",
                byte_size=1,
            )
        ]
        if artwork
        else []
    )
    row.review = review
    row.decision = None
    row.approved_design = None
    return row


def review(percentage: float, *, complete: bool = True) -> DesignReviewRecord:
    """A stored review that evaluates to roughly the given percentage."""
    rating = round(percentage / 20)
    categories = [ScoreCategory.from_rating(c, rating) for c in CATEGORY_LIMITS]
    gates = [
        {"id": gate_id, "label": GATE_LABELS[gate_id], "result": "pass", "evidence": ""}
        for gate_id in (HARD_GATE_IDS if complete else HARD_GATE_IDS[:5])
    ]
    return DesignReviewRecord(
        reviewer="owner",
        hard_gates=gates,
        score_categories=[c.to_dict() for c in categories],
        rationale="",
        requested_decision="design_approved",
        measurements={},
        evaluation={},
    )


def version(number: int = 1, superseded: bool = False) -> ApprovedDesign:
    return ApprovedDesign(
        version=number,
        approved_by="owner",
        production_spec={
            "garment_key": "garment_tee_crew_front",
            "zone_key": "centre_chest",
            "print_width_mm": 180,
        },
        superseded_at=dt.datetime(2026, 8, 1, tzinfo=dt.UTC) if superseded else None,
    )


# --- stages ------------------------------------------------------------------


def test_an_untouched_backlog_concept_is_unstarted_and_says_where_the_brief_is() -> None:
    item = _item(concept())

    assert item.stage == "unstarted"
    assert item.attempt_id is None
    assert "start an attempt" in item.next_action
    assert "brief" in item.next_action


def test_an_attempt_with_no_artwork_needs_artwork() -> None:
    item = _item(concept(attempts=[attempt(state=DesignAttemptState.PLANNED)]))

    assert item.stage == "needs_artwork"
    assert item.has_artwork is False


def test_artwork_attached_opens_the_review() -> None:
    item = _item(concept(attempts=[attempt(state=DesignAttemptState.GENERATED, artwork=True)]))

    assert item.stage == "review_open"
    assert item.has_artwork is True


def test_a_generated_attempt_that_lost_its_artwork_still_needs_artwork() -> None:
    """State says generated, assets say otherwise. Believe the assets."""
    item = _item(concept(attempts=[attempt(state=DesignAttemptState.GENERATED, artwork=False)]))

    assert item.stage == "needs_artwork"


def test_awaiting_a_decision_carries_the_score_and_the_blockers() -> None:
    item = _item(
        concept(
            attempts=[
                attempt(
                    state=DesignAttemptState.AWAITING_DECISION,
                    artwork=True,
                    review=review(80),
                )
            ]
        )
    )

    assert item.stage == "awaiting_decision"
    assert item.percentage == 80
    assert item.eligible is True
    assert item.blockers == []


def test_an_incomplete_review_reports_what_is_outstanding() -> None:
    item = _item(
        concept(
            attempts=[
                attempt(
                    state=DesignAttemptState.AWAITING_DECISION,
                    artwork=True,
                    review=review(80, complete=False),
                )
            ]
        )
    )

    assert item.eligible is False
    assert any("not answered" in blocker for blocker in item.blockers)


def test_approved_but_unversioned_is_its_own_stage() -> None:
    item = _item(concept(attempts=[attempt(state=DesignAttemptState.APPROVED, artwork=True)]))

    assert item.stage == "approved_unversioned"
    assert "Record it as a version" in item.next_action


def test_a_version_makes_it_printable_and_says_what_will_print() -> None:
    live = attempt(state=DesignAttemptState.APPROVED, artwork=True)
    standing = version(1)
    live.approved_design = standing
    item = _item(concept(attempts=[live], versions=[standing]))

    assert item.stage == "ready_to_print"
    assert item.approved_version == 1
    assert "180mm" in item.next_action
    assert "centre chest" in item.next_action


def test_a_superseded_version_does_not_count_as_the_standing_one() -> None:
    item = _item(
        concept(
            attempts=[attempt(state=DesignAttemptState.APPROVED, artwork=True)],
            versions=[version(1, superseded=True)],
        )
    )

    assert item.approved_version is None
    assert item.stage == "approved_unversioned"


def test_the_live_attempt_is_the_latest_not_the_latest_undecided() -> None:
    """A rejected latest attempt means start another, not carry on with the
    one before it."""
    item = _item(
        concept(
            attempts=[
                attempt(1, DesignAttemptState.AWAITING_DECISION, artwork=True),
                attempt(2, DesignAttemptState.REJECTED, artwork=True),
            ]
        )
    )

    assert item.attempt_number == 2
    assert item.stage == "settled"


# --- provenance --------------------------------------------------------------


def test_a_research_born_concept_carries_where_it_came_from() -> None:
    item = _item(concept(parsed={"vintage_research_run_id": "run-1", "research_concept_number": 3}))

    assert item.research_run_id == "run-1"
    assert item.research_concept_number == 3


def test_a_markdown_concept_carries_no_research_provenance() -> None:
    item = _item(concept())

    assert item.research_run_id == ""
    assert item.research_concept_number is None


# --- ordering ----------------------------------------------------------------


class _Session:
    """Just enough session to hand work_queue a fixed set of concepts."""

    def __init__(self, concepts: list[DesignConcept]) -> None:
        self._concepts = concepts

    def execute(self, _statement: object) -> _Session:
        return self

    def scalars(self) -> _Session:
        return self

    def all(self) -> list[DesignConcept]:
        return self._concepts


def test_the_queue_puts_what_is_blocked_on_a_person_first() -> None:
    """The top of the list has to be the right place to start, or the list is
    just the backlog again."""
    rows = [
        concept(1),  # unstarted
        concept(2, attempts=[attempt(state=DesignAttemptState.PLANNED)]),  # needs artwork
        concept(
            3,
            attempts=[
                attempt(state=DesignAttemptState.AWAITING_DECISION, artwork=True, review=review(80))
            ],
        ),
        concept(4, attempts=[attempt(state=DesignAttemptState.GENERATED, artwork=True)]),
    ]

    ordered = work_queue(_Session(rows))  # type: ignore[arg-type]

    assert [item.external_number for item in ordered] == [3, 4, 2, 1]


def test_within_a_stage_the_furthest_along_comes_first() -> None:
    rows = [
        concept(
            1,
            attempts=[
                attempt(state=DesignAttemptState.AWAITING_DECISION, artwork=True, review=review(40))
            ],
        ),
        concept(
            2,
            attempts=[
                attempt(state=DesignAttemptState.AWAITING_DECISION, artwork=True, review=review(80))
            ],
        ),
    ]

    ordered = work_queue(_Session(rows))  # type: ignore[arg-type]

    assert [item.external_number for item in ordered] == [2, 1]


def test_settled_work_is_out_of_the_way_unless_asked_for() -> None:
    rows = [
        concept(1),
        concept(2, attempts=[attempt(state=DesignAttemptState.REJECTED, artwork=True)]),
    ]

    assert [i.external_number for i in work_queue(_Session(rows))] == [1]  # type: ignore[arg-type]
    assert [
        i.external_number
        for i in work_queue(_Session(rows), include_settled=True)  # type: ignore[arg-type]
    ] == [1, 2]


def test_every_item_states_a_next_action() -> None:
    """A row with nothing to say is a row that sends somebody hunting."""
    rows = [
        concept(1),
        concept(2, attempts=[attempt(state=DesignAttemptState.PLANNED)]),
        concept(3, attempts=[attempt(state=DesignAttemptState.APPROVED, artwork=True)]),
    ]

    for item in work_queue(_Session(rows)):  # type: ignore[arg-type]
        assert item.next_action.endswith("."), item.next_action
        assert len(item.next_action.split()) >= 6, item.next_action


@pytest.mark.parametrize("include", [True, False])
def test_the_dict_shape_is_json_safe(include: bool) -> None:
    """It goes straight out of a FastAPI route, so uuids must already be strings."""
    import json

    rows = [concept(1, attempts=[attempt(state=DesignAttemptState.PLANNED)])]
    payload = [item.to_dict() for item in work_queue(_Session(rows), include_settled=include)]  # type: ignore[arg-type]

    json.dumps(payload)
