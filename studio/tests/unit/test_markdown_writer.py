"""Constructing canonical Markdown safely.

The injection cases matter most: a rejection reason is arbitrary human text, and it
must never be able to change the structure of a document the planner later reads.
"""

from __future__ import annotations

import pytest

from app.services import markdown_writer as writer
from app.services.markdown_sections import find_section, split_sections, subsections_of
from app.services.world_loader import headings_of
from tests.fixtures.worlds import VALID_CONTINUITY, VALID_SHOTLIST


def _drift(reason: str = "The group reads as resigned.", lesson: str | None = None):  # type: ignore[no-untyped-def]
    return writer.DriftEntry(
        shot_external_id="W01-011",
        label="Car interior transition",
        reason=reason,
        lesson=lesson,
    )


# --- sanitisation ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("dangerous", "must_not_contain"),
    [
        ("# Purpose\nEverything is fine", "\n"),
        ("### Rejected Drift", "###"),
        ("a | b | c", "|"),
        ("```python\nimport os\n```", "```"),
        ("- item\n- item", "\n"),
        ("> quote", ">"),
    ],
)
def test_structure_characters_are_neutralised(dangerous: str, must_not_contain: str) -> None:
    assert must_not_contain not in writer.sanitise_inline(dangerous)


def test_a_heading_in_a_reason_cannot_create_a_heading() -> None:
    entry = _drift(reason="# Purpose is now this")

    rendered = entry.render()

    # Exactly one heading: the one the writer created.
    assert [line for line in rendered.splitlines() if line.startswith("#")] == [
        "### W01-011 — Car interior transition"
    ]


def test_a_reason_cannot_break_out_of_a_table_cell() -> None:
    row = writer.append_rotation_row(
        VALID_CONTINUITY,
        writer.HERO_PRODUCT_ROTATION_HEADING,
        ["W01-011", "Scene | injected | cells", "Tote bag", "APPROVED"],
    )
    added = next(line for line in row.splitlines() if "injected" in line)

    # Four cells asked for, four cells produced.
    assert added.count("|") == 5


def test_long_text_is_truncated_rather_than_refused() -> None:
    result = writer.sanitise_inline("x" * 900)

    assert len(result) <= writer.MAX_REASON_CHARACTERS
    assert result.endswith("…")


def test_text_that_is_only_structure_is_refused() -> None:
    with pytest.raises(writer.MarkdownWriteError):
        writer.sanitise_inline("###   ")


# --- drift entries -----------------------------------------------------------------


def test_a_drift_entry_has_the_agreed_shape() -> None:
    rendered = _drift(lesson="Quiet scenes still need momentum.").render()

    assert rendered.startswith("### W01-011 — Car interior transition")
    assert "**Status:** REJECTED" in rendered
    assert "**Reason:** The group reads as resigned." in rendered
    assert "**Permanent lesson:** Quiet scenes still need momentum." in rendered


def test_a_drift_entry_without_a_lesson_says_so() -> None:
    """A one-off artefact must not become a permanent rule by accident."""
    assert "No new permanent lesson." in _drift().render()


def test_the_newest_drift_goes_to_the_top() -> None:
    """The planner reads the first three, so newest must be first."""
    updated = writer.insert_drift_entry(VALID_CONTINUITY, _drift())

    entries = subsections_of(updated, writer.REJECTED_DRIFT_HEADING)
    assert entries[0].heading == "W01-011 — Car interior transition"


def test_older_drift_is_kept_below() -> None:
    original = subsections_of(VALID_CONTINUITY, writer.REJECTED_DRIFT_HEADING)

    updated = writer.insert_drift_entry(VALID_CONTINUITY, _drift())

    entries = subsections_of(updated, writer.REJECTED_DRIFT_HEADING)
    assert len(entries) == len(original) + 1
    assert [e.heading for e in entries[1:]] == [e.heading for e in original]


def test_inserting_drift_leaves_every_required_heading_intact() -> None:
    """The loader validates these; losing one would break the next import."""
    updated = writer.insert_drift_entry(VALID_CONTINUITY, _drift())

    before = headings_of(VALID_CONTINUITY)
    after = headings_of(updated)

    assert set(before) < set(after)
    # Order is preserved; exactly one heading was added.
    assert [h for h in after if h in set(before)] == before
    assert len(after) == len(before) + 1


def test_a_missing_section_is_reported_rather_than_guessed() -> None:
    with pytest.raises(writer.MarkdownWriteError, match="Rejected Drift"):
        writer.insert_drift_entry("# Status Key\n\nnothing else\n", _drift())


# --- approved entries --------------------------------------------------------------


def _approved(**overrides):  # type: ignore[no-untyped-def]
    fields = {
        "shot_external_id": "W01-011",
        "scene": "Car interior transition",
        "hero_product": "Tote bag",
        "camera_position": "Rear seat",
        "strongest_success": "The moment reads as taken.",
        "note": None,
        "is_reference": False,
    }
    fields.update(overrides)
    return writer.ApprovedEntry(**fields)  # type: ignore[arg-type]


def test_an_approved_entry_records_facts_not_narrative() -> None:
    rendered = _approved().render()

    assert "**Status:** APPROVED" in rendered
    assert "**Hero product:** Tote bag" in rendered
    assert "**Camera position:** Rear seat" in rendered


def test_the_owners_note_is_why_a_frame_works_and_the_reviewer_is_attributed() -> None:
    """The owner says why an approved frame works. The reviewer is quoted, not adopted.

    "Why it works" is load-bearing: once a frame is promoted to a reference, that
    string is sent to the planner with every request, so it steers what comes next.
    Letting an unreliable reviewer's sentence occupy it puts model opinion into canon
    and then into future prompts, which AGENTS.md rule 7 exists to prevent.
    """
    rendered = _approved(note="Keep this framing.").render()

    assert "**Why it works:** Keep this framing." in rendered
    assert "**Reviewer said:** The moment reads as taken." in rendered
    assert "**Why it works:** The moment reads as taken." not in rendered


def test_without_an_owner_note_the_reviewer_is_still_only_quoted() -> None:
    rendered = _approved().render()

    assert "**Reviewer said:**" in rendered
    assert "**Why it works:**" not in rendered


def test_a_reference_promotion_is_recorded() -> None:
    assert "**Reference:**" in _approved(is_reference=True).render()


def test_an_approved_entry_lands_under_approved_reference_frames() -> None:
    updated = writer.append_approved_entry(VALID_CONTINUITY, _approved())

    section = find_section(updated, writer.APPROVED_REFERENCES_HEADING)
    assert section is not None
    assert "W01-011" in "".join(
        s.heading for s in subsections_of(updated, writer.APPROVED_REFERENCES_HEADING)
    )


def test_appending_does_not_disturb_later_sections() -> None:
    updated = writer.append_approved_entry(VALID_CONTINUITY, _approved())

    assert set(headings_of(VALID_CONTINUITY)) <= set(headings_of(updated))
    assert find_section(updated, "Next Prompt Brief") is not None


# --- rotation tables ---------------------------------------------------------------


def test_a_rotation_row_is_appended_without_changing_the_table_headings() -> None:
    before = find_section(VALID_CONTINUITY, writer.HERO_PRODUCT_ROTATION_HEADING)
    assert before is not None

    updated = writer.append_rotation_row(
        VALID_CONTINUITY,
        writer.HERO_PRODUCT_ROTATION_HEADING,
        ["W01-011", "Car interior", "Tote bag", "APPROVED"],
    )

    after = find_section(updated, writer.HERO_PRODUCT_ROTATION_HEADING)
    assert after is not None
    assert after.body.splitlines()[0] == before.body.splitlines()[0]
    assert "W01-011" in after.body


# --- shotlist markers --------------------------------------------------------------


def test_a_shot_marker_becomes_approved() -> None:
    updated = writer.set_shot_status_marker(VALID_SHOTLIST, "W01-011", writer.APPROVED_MARKER)

    row = next(line for line in updated.splitlines() if line.strip().startswith("W01-011"))
    assert row.rstrip().endswith(writer.APPROVED_MARKER)


def test_other_rows_are_untouched() -> None:
    updated = writer.set_shot_status_marker(VALID_SHOTLIST, "W01-011", writer.APPROVED_MARKER)

    before = [line for line in VALID_SHOTLIST.splitlines() if "W01-012" in line]
    after = [line for line in updated.splitlines() if "W01-012" in line]
    assert before == after


def test_the_updated_shotlist_still_parses() -> None:
    from app.services.markdown_tables import find_table

    updated = writer.set_shot_status_marker(VALID_SHOTLIST, "W01-011", writer.APPROVED_MARKER)

    table = find_table(updated, ["ID", "Scene", "Hero Product", "Camera", "Status"])
    assert table is not None
    row = next(r for r in table.rows if r.cells["id"] == "W01-011")
    assert row.cells["status"] == writer.APPROVED_MARKER
    assert row.cells["hero product"] == "Tote bag"


def test_a_pipe_table_row_is_also_supported() -> None:
    pipe = "| ID | Scene | Status |\n|---|---|---|\n| W01-011 | Car interior | ⬜ |\n"

    updated = writer.set_shot_status_marker(pipe, "W01-011", writer.APPROVED_MARKER)

    assert "| W01-011 | Car interior | ✅ |" in updated


def test_an_unknown_shot_is_reported() -> None:
    with pytest.raises(writer.MarkdownWriteError, match="W01-999"):
        writer.set_shot_status_marker(VALID_SHOTLIST, "W01-999", writer.APPROVED_MARKER)


def test_an_unknown_marker_is_refused() -> None:
    with pytest.raises(writer.MarkdownWriteError):
        writer.set_shot_status_marker(VALID_SHOTLIST, "W01-011", "DONE")


def test_the_document_keeps_its_trailing_newline() -> None:
    updated = writer.set_shot_status_marker(VALID_SHOTLIST, "W01-011", writer.APPROVED_MARKER)

    assert updated.endswith("\n") == VALID_SHOTLIST.endswith("\n")


def test_section_count_is_unchanged_by_a_marker_edit() -> None:
    updated = writer.set_shot_status_marker(VALID_SHOTLIST, "W01-011", writer.APPROVED_MARKER)

    assert len(split_sections(updated)) == len(split_sections(VALID_SHOTLIST))
