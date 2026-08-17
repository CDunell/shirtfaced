"""The prompts are the supplied masters, and the sheet is whatever shape it comes back.

Two failures on 18 August 2026, neither of which the numbers would have caught,
because nothing was out of range: the sheet was a valid 16:9 image and the
extracted panel was a valid 9:16 one. Looking at them caught it — nine landscape
cells for a vertical delivery, and a "standalone" panel that was three landscape
frames stacked down the canvas.

The first of those was self-inflicted in a way worth pinning. The extraction
prompt in code was a paraphrase of the supplied master: seven lines standing in
for eleven, and among the four it dropped were "combine it with another panel"
and "no contact-sheet grid, borders, labels or other panels are visible" — the
two that describe precisely what came back. A paraphrase of a prompt is a
rewrite of it, and nothing recorded which words had gone.
"""

from __future__ import annotations

import inspect
from pathlib import Path

from app.config import PROJECT_ROOT, Settings
from app.services.nano_pipeline import EXTRACTION_PROMPT, generate_coverage_sheet

MASTER = (
    PROJECT_ROOT.parent
    / "docs"
    / "stage-2"
    / "social-ai-production"
    / "NANO_BANANA_CONTACT_SHEET_EXTRACTION_PROMPT.md"
)


def test_the_extraction_prompt_is_the_supplied_master_word_for_word() -> None:
    """The copy in code and the document it came from, compared outright.

    Held as a constant rather than read at call time so a provider call does not
    depend on a documentation path staying put — which is the reason a copy
    exists, and the reason it needs checking.
    """
    supplied = MASTER.read_text(encoding="utf-8").strip()
    expected = supplied.replace("{{panel_number_or_description}}", "{panel}").replace(
        "{{target_aspect_ratio}}", "{aspect_ratio}"
    )

    assert EXTRACTION_PROMPT.strip() == expected


def test_the_lines_the_paraphrase_dropped_are_present() -> None:
    """Named outright, because these two are what the failure looked like."""
    prompt = EXTRACTION_PROMPT.format(panel=2, aspect_ratio="9:16")

    assert "combine it with another panel" in prompt
    assert "No contact-sheet grid, borders, labels or other panels are visible" in prompt


def test_the_world_prompt_is_an_adaptation_of_the_supplied_coverage_master() -> None:
    """Scene prompts are specialised per scene, so this checks shape, not words.

    The coverage master is written to be adapted — it says so — and W01-P28's
    fills in the actual room. What must survive adaptation is its structure.
    """
    scene = Path(PROJECT_ROOT / "worlds/world-01/shots/W01-P28.nano-banana-coverage.txt").read_text(
        encoding="utf-8"
    )

    for heading in (
        "<instruction>",
        "**Row 1 (World / Event):**",
        "**Row 2 (Core Human Coverage):**",
        "**Row 3 (Details & Alternate Observations):**",
        'Generate a cohesive 3x3 grid "Documentary Contact Sheet"',
        "The scene exists independently of the camera.",
    ):
        assert heading in scene


def test_the_sheet_asks_for_no_aspect_ratio() -> None:
    """The sheet comes back the shape the model decides.

    Forcing one was an invented constraint, and it did not do what it was
    supposed to. The theory was that a 3x3 grid divides its canvas into nine
    cells of the canvas's ratio, so a 9:16 canvas would make the panels
    vertical. The model composes a layout instead of dividing a canvas: asked
    for a 3x3 grid at 9:16 it returned 3072x5504 holding twelve cells in two
    columns of six, still landscape, while the sheet record said nine.

    The frame shape is chosen per panel at extraction, which is where the
    supplied master puts it: TARGET ASPECT RATIO.
    """
    default = inspect.signature(generate_coverage_sheet).parameters["aspect_ratio"].default

    assert default is None


def test_a_sheet_is_generated_larger_than_a_single_frame() -> None:
    """Nine images in one file. 1K makes each panel a 459-pixel thumbnail.

    Not a preference: the supplied extraction master itself allows for "where the
    small contact-sheet panel lacks fine pixel detail", and the first sheet came
    back 1376x768.
    """
    settings = Settings()

    assert settings.google_sheet_image_size == "4K"
    assert settings.google_image_size != "1K"
