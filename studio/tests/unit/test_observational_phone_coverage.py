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


def test_sheet_container_stays_landscape_for_known_3x3_reliability() -> None:
    """Native vertical observation does not reopen the failed 9:16-sheet experiment."""
    default = inspect.signature(generate_coverage_sheet).parameters["aspect_ratio"].default
    assert default == "16:9"
