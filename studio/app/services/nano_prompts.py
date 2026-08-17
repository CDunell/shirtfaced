"""The Nano prompt masters, held verbatim.

``docs/stage-2/social-ai-production/`` holds the prompts the owner wrote. This
module is a copy of the generic ones, so a provider call does not depend on a
documentation path staying put, and ``tests/unit/test_nano_pipeline_shape.py``
compares the copy against the master so the two cannot drift.

Its own module for one reason: these are somebody else's words, and wrapping a
line changes the text sent to the provider. E501 is switched off here, the same
way and for the same reason it is off for ``scripts/``, and stays on everywhere
the code actually lives.

Two rewrites cost real generations to find, and both are the same mistake:

* The extraction prompt was a paraphrase — seven lines standing in for eleven,
  with a comment claiming it was quoted. Among the four it dropped were "combine
  it with another panel" and "no contact-sheet grid, borders, labels or other
  panels are visible", which is exactly what came back.
* Then it was restored from the wrong document. ``NANO_BANANA_VEO_SCENE_
  PRODUCTION_PIPELINE.md`` §10 states the *tested* extraction method outright,
  and it is not the long master: it is short, positional and structural, and it
  names no aspect ratio. Asking for a target ratio is what made an extraction
  reframe rather than crop.
"""

from __future__ import annotations

# §9 and §10 of NANO_BANANA_VEO_SCENE_PRODUCTION_PIPELINE.md, verbatim, with the
# panel named by structural position rather than by number: "Selection should
# not require Nano to reinterpret what the panel means."
#
# There is deliberately no aspect ratio in it. §10 says "expand the selected
# image to fill the entire output canvas while preserving its exact content,
# composition, subjects, camera angle, perspective and lighting" — the frame's
# shape is the panel's shape, and stating a different one turns a crop into a
# reframe. §11 is the law it follows from: extraction is structural, never
# corrective, and a wrong panel is fixed upstream.
EXTRACTION_PROMPT = (
    "Crop out the {position} image from this {rows}x{columns} contact sheet.\n"
    "\n"
    "Return ONLY that single image as a standalone image.\n"
    "\n"
    "Remove the surrounding {siblings} panels and all grid borders.\n"
    "\n"
    "Expand the selected {position} image to fill the entire output canvas while preserving its exact content, composition, subjects, camera angle, perspective and lighting.\n"
    "\n"
    "Do not generate a new shot.\n"
    "Do not return the contact sheet.\n"
    "Do not include a grid."
)

# What §9 calls a structural position. Nano is given the words a person would
# use pointing at the sheet, not an index it has to count out.
ROW_NAMES = ("top", "middle", "bottom")
COLUMN_NAMES = ("left", "center", "right")


def position_name(panel: int, rows: int, columns: int) -> str:
    """``top-center`` for panel 2 of a 3x3, the phrase §10's example uses.

    Falls back to naming the row and column outright on any sheet that is not
    3x3, because "middle-center" means nothing on a 2x6 and a wrong word is
    worse than a plain one.
    """
    index = panel - 1
    row, column = divmod(index, columns)
    if rows == len(ROW_NAMES) and columns == len(COLUMN_NAMES):
        return f"{ROW_NAMES[row]}-{COLUMN_NAMES[column]}"
    return f"row {row + 1} / column {column + 1}"
