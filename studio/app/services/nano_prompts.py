"""The Nano prompt masters, held verbatim.

``docs/stage-2/social-ai-production/`` holds the prompts the owner wrote. This
module is a copy of the generic ones, so a provider call does not depend on a
documentation path staying put, and ``tests/unit/test_nano_pipeline_shape.py``
compares the copy against the master so the two cannot drift.

Its own module for one reason: these are somebody else's words, and wrapping a
line changes the text sent to the provider. E501 is switched off here, the same
way and for the same reason it is off for ``scripts/``, and stays on everywhere
the code actually lives.

It used to be a paraphrase — seven lines standing in for eleven — and among the
four it dropped were "combine it with another panel" and "no contact-sheet grid,
borders, labels or other panels are visible". On 18 August 2026 an extraction
came back as three landscape frames stacked down a 9:16 canvas, which is exactly
what those two forbid. The paraphrase was not shorter, it was weaker, and
nothing recorded which words had gone.
"""

from __future__ import annotations

EXTRACTION_PROMPT = (
    "<instruction>\n"
    "Analyze the supplied approved contact sheet and identify the requested panel exactly.\n"
    "Return that selected view as one standalone full-resolution image.\n"
    "Use the contact sheet as the visual authority for identity, appearance, camera angle, framing intent, spatial relationships and scene state.\n"
    "Do not reinterpret the selected panel, redesign it, combine it with another panel or invent a new angle.\n"
    "Preserve the same subject(s), face(s), body proportions, clothing, props, environment, lighting, geometry and interaction shown in the requested panel.\n"
    "Expand the requested panel cleanly into a standalone image while maintaining its established composition and visual relationships.\n"
    "Where the small contact-sheet panel lacks fine pixel detail, resolve detail conservatively from the rest of the same contact sheet and any supplied canonical reference images. Do not invent identity-changing features or new scene content.\n"
    "Do not add, remove, duplicate, relocate or restage people or objects.\n"
    "Do not change camera position, lens intent, crop logic or subject relationship unless explicitly requested.\n"
    "REQUESTED PANEL: {panel}\n"
    "TARGET ASPECT RATIO: {aspect_ratio}\n"
    "</instruction>\n"
    "A single standalone photorealistic image reproducing the requested approved contact-sheet panel at full usable resolution and the requested aspect ratio.\n"
    "The output preserves the exact established identity, appearance, framing, spatial relationships, environment and lighting of the selected panel. No contact-sheet grid, borders, labels or other panels are visible.\n"
)
