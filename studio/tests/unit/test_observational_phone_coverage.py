"""World 01 coverage is observed by real vertical-phone operators, not a film crew.

The scene sheet still uses a 16:9 *container* because measured Nano behaviour says
that is what reliably holds a 3x3 grid. That technical sheet shape must never be
mistaken for the camera inside each panel: W01 observations are conceived through
a vertical phone from a plausible human position, and the tested structural
extraction path remains unchanged.
"""

from __future__ import annotations

import inspect

from app.config import PROJECT_ROOT
from app.services.nano_pipeline import generate_coverage_sheet, panel_plan_from_prompt

DOCS = PROJECT_ROOT.parent / "docs" / "stage-2" / "social-ai-production"
LAW = DOCS / "WORLD_01_OBSERVATIONAL_PHONE_CAMERA_LAW.md"
MASTER = DOCS / "NANO_BANANA_SCENE_COVERAGE_PROMPT.md"
W01_P28 = PROJECT_ROOT / "worlds" / "world-01" / "shots" / "W01-P28.nano-banana-coverage.txt"


def test_observational_phone_law_is_production_data() -> None:
    text = LAW.read_text(encoding="utf-8")
    assert "A real person is physically inside the event holding a phone vertically" in text
    assert "OBSERVER POSITION" in text
    assert "AVAILABLE SIGHTLINE" in text
    assert "a believable view somebody who was there could have captured" in text


def test_generic_scene_coverage_is_observer_led() -> None:
    text = MASTER.read_text(encoding="utf-8")
    assert "vertically held 9:16 phone viewfinder" in text
    assert "Prefer 2-3 observer positions" in text
    assert "Foreground obstruction is desirable" in text
    assert "No panoramic coverage" in text
    assert len(panel_plan_from_prompt(text)) == 9


def test_pub_coverage_reuses_three_physical_observers() -> None:
    text = W01_P28.read_text(encoding="utf-8")
    for observer in (
        "OBSERVER A — POOL-TABLE CROWD",
        "OBSERVER B — BAR-SIDE CROWD",
        "OBSERVER C — STAGE SIGHTLINE",
    ):
        assert observer in text

    assert "No overheads, no panoramic crowd views" in text
    assert "Prefer believable interference over complete subject visibility" in text
    assert len(panel_plan_from_prompt(text)) == 9


def test_pub_panels_are_literal_vertical_phone_sightlines() -> None:
    """W01-P28 names physical views, not cinematography coverage categories."""
    panels = panel_plan_from_prompt(W01_P28.read_text(encoding="utf-8"))

    assert len(panels) == 9
    for panel in panels:
        sightline = f"{panel['title']} {panel['summary']}".lower()
        assert "phone" in sightline
        assert "vertically" in sightline or "vertical phone" in sightline
        assert "height" in sightline
        assert "9:16" in sightline
        assert "1x" in sightline or "2x" in sightline
        assert any(
            obstruction in sightline
            for obstruction in ("head", "shoulder", "back", "arm", "torso", "hair")
        )

    forbidden_categories = (
        "damo discovery",
        "damo incident",
        "damo tighter",
        "emma + brock sightline",
        "band through crowd",
        "available table detail",
        "return to the incident",
    )
    titles = " ".join(panel["title"].lower() for panel in panels)
    assert not any(category in titles for category in forbidden_categories)


def test_pub_prompt_rejects_the_latest_sheet_and_composition_failures() -> None:
    """The 18 August candidate returned portrait cells but a 5-over-4 hero montage."""
    text = W01_P28.read_text(encoding="utf-8")

    for required in (
        "exactly THREE COLUMNS and exactly THREE ROWS",
        "one complete tall 9:16 portrait phone photograph",
        "neutral side gutters inside its grid slot",
        "roughly one-third to one-half",
        "must overlap Damo or the table",
        "never show a complete clean stage",
        "adult wooden stool standing on the table",
    ):
        assert required in text

    for rejected in (
        "five-over-four",
        "five columns",
        "two rows",
        "unobstructed centred full-body figure",
        "clean front-facing concert photograph",
        "isolated close-up",
    ):
        assert rejected in text


def test_sheet_container_stays_landscape_for_known_3x3_reliability() -> None:
    """Native vertical observation does not reopen the failed 9:16-sheet experiment."""
    default = inspect.signature(generate_coverage_sheet).parameters["aspect_ratio"].default
    assert default == "16:9"
