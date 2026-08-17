"""Extraction is the tested structural crop, and no stage imposes a shape.

Three failures on 18 August 2026, each one a rewrite of something the owner had
already written down.

1. The extraction prompt in code was a paraphrase of a supplied master — seven
   lines standing in for eleven — and among the four it dropped were "combine it
   with another panel" and "no contact-sheet grid, borders, labels or other
   panels are visible". An extraction came back as three landscape frames
   stacked down one canvas: precisely that.

2. The fix was to force the coverage sheet to 9:16, on the theory that a 3x3
   grid divides its canvas into nine cells of the canvas's ratio. The model
   composes a layout rather than dividing a canvas: it returned 3072x5504
   holding twelve cells in two columns of six, still landscape, while the sheet
   record still said nine.

3. Then the prompt was restored from the wrong document. NANO_BANANA_VEO_SCENE_
   PRODUCTION_PIPELINE.md §10 states the tested extraction method outright, and
   it is short, positional, structural, and names no aspect ratio at all.

What all three have in common is a shape being requested somewhere the owner
never asked for one. So these pin the absence.
"""

from __future__ import annotations

import inspect

from app.config import PROJECT_ROOT, Settings
from app.services.coverage_library import measured_ratio, record_panel_extraction
from app.services.nano_pipeline import extract_panel, generate_coverage_sheet
from app.services.nano_prompts import EXTRACTION_PROMPT, position_name

PIPELINE = (
    PROJECT_ROOT.parent
    / "docs"
    / "stage-2"
    / "social-ai-production"
    / "NANO_BANANA_VEO_SCENE_PRODUCTION_PIPELINE.md"
)


def test_the_extraction_prompt_is_10s_tested_method() -> None:
    """Compared against the document's own example, line for line.

    Only the panel's position, the grid size and the sibling count are
    substituted; §9 requires the position be structural, so the numbers in the
    document's 3x3 example fall out of the same fields.
    """
    example = PIPELINE.read_text(encoding="utf-8").split("The tested extraction method")[1]
    example = example.split("```")[1].strip()
    if example.startswith("text"):
        example = example[len("text") :].strip()

    rendered = EXTRACTION_PROMPT.format(position="top-center", rows=3, columns=3, siblings=8)

    assert rendered.strip() == example


def test_a_panel_is_named_by_where_it_sits() -> None:
    """§9: selection should not require Nano to reinterpret what a panel means."""
    assert position_name(1, 3, 3) == "top-left"
    assert position_name(2, 3, 3) == "top-center"
    assert position_name(5, 3, 3) == "middle-center"
    assert position_name(9, 3, 3) == "bottom-right"
    # A sheet that is not 3x3 has no "middle-center", so it is named plainly.
    assert position_name(4, 6, 2) == "row 2 / column 2"


def test_extraction_requests_no_aspect_ratio() -> None:
    """§10 expands the panel to fill the canvas, preserving its composition.

    Requesting a ratio is what turned a crop into a reframe, which §11 forbids
    outright: extraction is structural, never corrective.
    """
    assert "aspect" not in EXTRACTION_PROMPT.lower()
    assert "aspect_ratio" not in inspect.signature(extract_panel).parameters


def test_the_sheet_requests_no_aspect_ratio_either() -> None:
    """The sheet comes back the shape the model decides. §7 states no shape."""
    assert inspect.signature(generate_coverage_sheet).parameters["aspect_ratio"].default is None


def test_a_frame_records_the_ratio_it_came_back_as() -> None:
    """Measured, not requested — and null means measure it, not assume 9:16."""
    assert inspect.signature(record_panel_extraction).parameters["aspect_ratio"].default is None
    assert measured_ratio(1080, 1920) == "9:16"
    assert measured_ratio(1376, 768) == "43:24"


def test_a_sheet_is_generated_larger_than_a_single_frame() -> None:
    """Nine images in one file. 1K makes each panel a 459-pixel thumbnail.

    Resolution is about pixels, not shape, so it survives all of the above. §10
    asks extraction to expand a panel to fill a canvas, which it can only do
    with pixels to work from.
    """
    settings = Settings()

    assert settings.google_sheet_image_size == "4K"
    assert settings.google_image_size != "1K"


def test_the_pipeline_document_is_in_the_repository() -> None:
    """It was not, until 18 August 2026, and that is why it was not followed."""
    text = PIPELINE.read_text(encoding="utf-8")

    for law in (
        "The scene exists independently of the camera.",
        "Never repair the selected shot during extraction.",
        "Extraction is structural, not corrective.",
        "Failed panels are fixed upstream.",
    ):
        assert law in text
