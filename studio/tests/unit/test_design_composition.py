"""Composing a design through the service the routes call.

These cover the parts that need no database: what the composer is asked, what
comes back, and how a brief that cannot be answered is refused. The refusals
matter as much as the successes -- a reason code travels to whoever wrote the
brief, and "500" tells them nothing.
"""

from __future__ import annotations

import pytest

from app.services.design_composition import CompositionRefused, Request, compose, garment_for


def test_a_brief_composes_against_a_real_garment() -> None:
    garment, options = compose(
        Request(
            seed=7,
            garment_key="garment_tee_crew_front",
            primary_text="SHIRTFACED",
            secondary_text="EST 2026",
        )
    )

    assert garment.zones, "the garment carried no print zones"
    assert options, "nothing was composed"
    assert all(option.design.svg for option in options)


def test_the_same_brief_composes_to_the_same_bytes() -> None:
    """The whole point of the seed. Different bytes here means a reprint drifts."""
    brief = Request(seed=99, garment_key="garment_tee_crew_front", primary_text="SHIRTFACED")

    first = compose(brief)[1]
    second = compose(brief)[1]

    assert [o.design.content_hash for o in first] == [o.design.content_hash for o in second]
    assert [o.design.svg for o in first] == [o.design.svg for o in second]


def test_a_different_seed_composes_something_else() -> None:
    """Otherwise the seed is decoration and every brief has one answer."""
    one = compose(Request(seed=1, garment_key="garment_tee_crew_front", primary_text="SHIRTFACED"))[
        1
    ]
    two = compose(Request(seed=2, garment_key="garment_tee_crew_front", primary_text="SHIRTFACED"))[
        1
    ]

    assert {o.design.content_hash for o in one} != {o.design.content_hash for o in two}


def test_designs_are_sized_to_the_garments_own_zone() -> None:
    """The placement table is a default; the garment in front of you is the fact."""
    garment, options = compose(
        Request(
            seed=3,
            garment_key="garment_tee_crew_front",
            primary_text="SHIRTFACED",
            placement="centre_chest",
        )
    )
    zone = garment.zones["centre_chest"]

    for option in options:
        assert option.design.width_mm <= zone.width + 0.01
        assert option.design.height_mm <= zone.height + 0.01


def test_an_unknown_garment_is_refused_not_substituted() -> None:
    """Falling back to a tee would place the design in the wrong zones."""
    with pytest.raises(CompositionRefused) as caught:
        garment_for("garment_that_does_not_exist")

    assert caught.value.reason == "UNKNOWN_GARMENT"


def test_a_garment_key_cannot_climb_out_of_its_folder() -> None:
    """The key names a file. It is not a path, and it comes over HTTP."""
    for key in ("../secrets", "..\\secrets", ".hidden"):
        with pytest.raises(CompositionRefused) as caught:
            garment_for(key)
        assert caught.value.reason == "BAD_GARMENT_KEY", key


def test_a_brief_with_no_words_is_refused_with_a_reason() -> None:
    """The archive never invents content, so an empty brief has no answer."""
    with pytest.raises(CompositionRefused) as caught:
        compose(Request(seed=1, garment_key="garment_tee_crew_front"))

    assert caught.value.reason == "NO_CONTENT"


def test_an_unknown_placement_is_refused() -> None:
    with pytest.raises(CompositionRefused) as caught:
        compose(
            Request(
                seed=1,
                garment_key="garment_tee_crew_front",
                primary_text="SHIRTFACED",
                placement="left_elbow",
            )
        )

    assert caught.value.reason == "UNKNOWN_PLACEMENT"


# --- The learning loop -------------------------------------------------------
#
# The approve control is the composer's training signal. These pin the wire
# that was missing for the system's whole life: every decision updated the row
# and taught the engine nothing, so every option carried ``decisions: 0``.


class _StubSession:
    """Just enough session for code that only flushes or reads rows back."""

    def __init__(self, rows: list[tuple[str, str]] | None = None) -> None:
        self._rows = rows or []

    def flush(self) -> None:  # pragma: no cover - nothing to do
        pass

    def execute(self, _query):
        rows = self._rows

        class _Result:
            def all(self) -> list[tuple[str, str]]:
                return rows

        return _Result()


def _read_store(path):
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def test_deciding_a_design_teaches_the_composer(tmp_path, monkeypatch) -> None:
    """An approval must move the number, or the loop is decorative."""
    import types

    from app.services import design_composition

    store_path = tmp_path / "approvals.json"
    monkeypatch.setattr(design_composition, "APPROVALS_PATH", store_path)

    design = types.SimpleNamespace(
        state="awaiting_decision",
        grammar_key="stamp",
        decided_by="",
        decided_at=None,
        decision_note="",
    )
    design_composition.decide(_StubSession(), design, approved=True, decided_by="owner")

    assert _read_store(store_path) == {"stamp": {"approved": 1, "decisions": 1}}


def test_a_rejection_counts_as_a_decision_but_not_an_approval(tmp_path, monkeypatch) -> None:
    from app.services import design_composition

    store_path = tmp_path / "approvals.json"
    monkeypatch.setattr(design_composition, "APPROVALS_PATH", store_path)

    design_composition.record_learning("banner", approved=False)
    design_composition.record_learning("banner", approved=True)

    assert _read_store(store_path) == {"banner": {"approved": 1, "decisions": 2}}


def test_the_store_rebuilds_from_the_decisions_table(tmp_path, monkeypatch) -> None:
    """The table is the record; the store is a regenerable view of it.

    A store lost with a box, corrupted, or predating the learning wire comes
    back from the rows -- variation requests excluded by the query itself.
    """
    from app.services import design_composition

    store_path = tmp_path / "approvals.json"
    store_path.write_text('{"stale": {"approved": 9, "decisions": 9}}', encoding="utf-8")
    monkeypatch.setattr(design_composition, "APPROVALS_PATH", store_path)

    rows = [("stamp", "approved"), ("stamp", "rejected"), ("banner", "approved")]
    data = design_composition.rebuild_approvals(_StubSession(rows))

    assert data == {
        "stamp": {"approved": 1, "decisions": 2},
        "banner": {"approved": 1, "decisions": 1},
    }
    assert _read_store(store_path) == data, "the stale store must be replaced, not merged"


def test_settling_a_linked_design_feeds_learning_except_for_variations(monkeypatch) -> None:
    """The concepts surface is the main decision path; it must teach too.

    A variation request stays out: it judges the content, not the construction.
    """
    import types

    from app.domain.enums import DesignDecisionKind
    from app.services import design_composition, design_pipeline

    design = types.SimpleNamespace(
        grammar_key="stamp", state="awaiting_decision", decided_by="", decided_at=None,
        decision_note="",
    )

    class _SettleSession:
        def execute(self, _query):
            class _Result:
                def scalar_one_or_none(self) -> object:
                    return design

            return _Result()

    recorded: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        design_composition,
        "record_learning",
        lambda key, approved: recorded.append((key, approved)),
    )

    attempt = types.SimpleNamespace(id="attempt-1")
    for kind in (
        DesignDecisionKind.APPROVED,
        DesignDecisionKind.REJECTED,
        DesignDecisionKind.VARIATION_REQUESTED,
    ):
        design_pipeline._settle_linked_composition(_SettleSession(), attempt, kind, "owner", None)

    assert recorded == [("stamp", True), ("stamp", False)]
