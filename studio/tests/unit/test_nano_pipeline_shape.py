"""The shape the coverage sheet is generated at, and what extraction may return.

Both were got wrong on 18 August 2026 in a way the numbers alone would not have
caught, because nothing was out of range — the sheet was a valid 16:9 image and
the panel was a valid 9:16 one. Looking at them is what caught it: nine
landscape cells for a vertical delivery, and a "standalone" panel that was three
landscape frames stacked down the canvas to fill it.

These pin the two decisions that followed, because both are one word in a
default and one paragraph in a prompt, and both are easy to lose.
"""

from __future__ import annotations

import inspect

from app.config import Settings
from app.services.nano_pipeline import EXTRACTION_PROMPT, generate_coverage_sheet


def test_a_sheet_takes_the_shape_of_its_panels() -> None:
    """A 3x3 grid divides its canvas into nine cells of the canvas's own ratio.

    So the sheet is generated 9:16 — the shape the panels have to be — rather
    than 16:9, the shape the master is. Generating it at the master's ratio put
    the reframe onto the extraction step, which is the one place
    MASTER_FIRST_PIPELINE.md had already recorded that reframing fails.
    """
    default = inspect.signature(generate_coverage_sheet).parameters["aspect_ratio"].default

    assert default == "9:16"


def test_a_sheet_is_generated_larger_than_a_single_frame() -> None:
    """Nine images in one file. 1K makes each panel a 459-pixel thumbnail."""
    settings = Settings()

    assert settings.google_sheet_image_size == "4K"
    assert settings.google_image_size != "1K"


def test_extraction_refuses_a_collage_in_so_many_words() -> None:
    """Asked for 9:16, the model tiled three landscape frames and complied.

    It answered the question as asked, so the question now says what a single
    photograph is. Every one of these is a way it filled the canvas instead of
    reproducing the panel.
    """
    prompt = EXTRACTION_PROMPT.format(panel=2, aspect_ratio="9:16")

    for refusal in ("no grid", "no stacked", "no split screen", "no collage", "no letterbox"):
        assert refusal in prompt

    assert "exactly one continuous photograph" in prompt
    assert "without recomposing" in prompt
