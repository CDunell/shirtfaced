"""Which canon actually reaches the planning model.

A rule the model never sees is a rule that does not exist. These tests pin the
contract between WORLD.md's section headings and the planning request, against the
real document.
"""

from __future__ import annotations

import pytest

from app.adapters.markdown_store import MarkdownStore
from app.adapters.planning import FakePromptPlanningClient
from app.config import PROJECT_ROOT
from app.services.markdown_sections import section_map
from app.services.prompt_planner import (
    MAX_EXCERPT_CHARACTERS,
    PLANNING_CANON_HEADINGS,
    build_request,
    create_plan,
    with_critical_block,
)
from app.services.rotation import RotationState
from tests.unit.test_shot_selector import make_shot

WORLDS_ROOT = PROJECT_ROOT / "worlds"

pytestmark = pytest.mark.skipif(
    not (WORLDS_ROOT / "world-01" / "WORLD.md").is_file(),
    reason="World 1 documents are not present.",
)


@pytest.fixture
def world_text() -> str:
    return MarkdownStore(WORLDS_ROOT).read_document("world-01", "WORLD.md").text


@pytest.fixture
def request_for_world(world_text: str):  # type: ignore[no-untyped-def]
    return build_request(
        world_slug="world-01",
        world_name="World 01",
        shot=make_shot("W01-011", sequence=11),
        world_text=world_text,
        rotation=RotationState(),
    )


@pytest.mark.parametrize("heading", PLANNING_CANON_HEADINGS)
def test_every_named_section_exists_in_the_real_document(world_text: str, heading: str) -> None:
    """A typo here would silently drop a rule from every prompt."""
    assert heading.casefold() in section_map(world_text), (
        f"WORLD.md has no section {heading!r}. Either the document was renamed or "
        "PLANNING_CANON_HEADINGS is wrong; either way the rule stops reaching the model."
    )


def test_the_prompt_construction_protocol_is_sent(request_for_world) -> None:  # type: ignore[no-untyped-def]
    """Required by the end-to-end workflow."""
    headings = [excerpt.heading for excerpt in request_for_world.canon_excerpts]

    assert "Prompt Construction Protocol" in headings


def _flattened(request) -> str:  # type: ignore[no-untyped-def]
    """All excerpt bodies with line wrapping removed, so assertions survive rewrapping."""
    return " ".join(" ".join(excerpt.body.split()) for excerpt in request.canon_excerpts)


def test_the_branding_rules_are_sent(request_for_world) -> None:  # type: ignore[no-untyped-def]
    """The most frequently broken rule in the rejected drift.

    Both halves must travel. Sending only the apparel ban produces a sanitised
    world; sending only the hero test lets a competitor's logo onto a garment.
    """
    flattened = _flattened(request_for_world)

    # One: apparel, banned everywhere, no background exemption.
    assert "No logos" in flattened
    assert "no background exemption for apparel" in flattened.lower()

    # Two: everything else may be real, so long as it stays background.
    assert "background filler" in flattened
    assert "Never the reason the frame exists" in flattened


def test_the_vehicle_canon_is_sent(request_for_world) -> None:  # type: ignore[no-untyped-def]
    """An image was already rejected for an American pickup body.

    This content lives in a subsection, so it is only present if the whole subtree is
    sent rather than the heading's own body.
    """
    # Lowercased: these rules get reworded, and a capital letter is not the contract.
    flattened = _flattened(request_for_world).lower()

    assert "tray-back ute" in flattened
    assert "american pickup trucks" in flattened
    assert "never the hero" in flattened
    assert "getting in, getting out" in flattened
    # Colour, cab and age are deliberately open. Only the wrong body shapes are named.
    assert "cab configuration and age are open" in flattened


def test_every_plan_carries_the_branding_block(request_for_world) -> None:  # type: ignore[no-untyped-def]
    """The blank-garment rule is guaranteed, not requested.

    Three consecutive live previews dropped it. Each time a newly required element was
    added to the Prompt Construction Protocol another fell out to make room, and the
    third prompt reached the image model with no branding instruction of any kind.
    """
    plan = create_plan(FakePromptPlanningClient(), request_for_world).plan

    assert "CRITICAL." in plan.production_prompt
    assert "No logos." in plan.production_prompt


def test_the_branding_block_is_not_duplicated() -> None:
    """A model that writes its own CRITICAL block must not get a second one."""
    already = "A photograph.\nCRITICAL.\nEvery garment in frame is blank."

    assert with_critical_block(already) == already
    assert with_critical_block("A photograph.").count("CRITICAL") == 1


def test_no_canon_section_is_truncated(request_for_world) -> None:  # type: ignore[no-untyped-def]
    """Every named section reaches the model whole.

    Truncation takes the end of a section, and the end of a rule is where the
    qualifier lives. At a 2000-character cap this quietly removed the last line of
    the branding rule -- the one saying the blank-garment rule is not relaxed by the
    Shirtfaced exception -- and every other test still passed. Writing prose above an
    existing rule is enough to push it out, so length is checked, not just presence.
    """
    truncated = [
        excerpt.heading
        for excerpt in request_for_world.canon_excerpts
        if excerpt.body.endswith("…") or len(excerpt.body) >= MAX_EXCERPT_CHARACTERS
    ]

    assert not truncated, (
        f"These canon sections do not reach the model whole: {truncated}. "
        "Shorten the section or raise MAX_EXCERPT_CHARACTERS."
    )


def test_product_rotation_rules_are_sent(request_for_world) -> None:  # type: ignore[no-untyped-def]
    """Also a subsection, and the reason the shotlist rotates products at all."""
    assert "Rotate prominence between" in _flattened(request_for_world)


def test_role_instructions_are_not_sent(request_for_world) -> None:  # type: ignore[no-untyped-def]
    """The Operating System section directs humans, not the image."""
    headings = [excerpt.heading for excerpt in request_for_world.canon_excerpts]

    assert "Operating System" not in headings
    assert "Continuity Ledger" not in headings


def test_the_request_stays_bounded(request_for_world) -> None:  # type: ignore[no-untyped-def]
    """Only the relevant canon is sent, not the whole archive."""
    total = sum(len(excerpt.body) for excerpt in request_for_world.canon_excerpts)

    assert total < 20_000
