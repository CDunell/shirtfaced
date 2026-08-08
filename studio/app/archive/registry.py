"""Everything the composer can reach, from both sources.

Elements come from two places. `authored.py` writes them as parametric geometry,
which is right for anything a formula gets correct: polygons, cogs, stars,
frames. `library.py` loads them from files, which is the only way to get
anything representational -- a flame, a palm, a magpie.

Drawn artwork wins where the two overlap. An authored flame that reads as a
pear is a placeholder for a drawn one, and once the drawn one exists the
placeholder has done its job.

Some replacements arrive under a different name -- our `symbol_wave_0001`
became `symbol_breaking_wave_0001` -- so the supersession is recorded
explicitly rather than left to a name collision, which would silently keep both.
"""

from __future__ import annotations

from app.archive import authored, library
from app.domain.element import Element

# Authored placeholder -> the drawn file that replaces it. Where the drawn
# version kept the same id the collision is handled without an entry here.
SUPERSEDED: dict[str, str] = {
    "symbol_wave_0001": "symbol_breaking_wave_0001",
    "symbol_mountains_0001": "symbol_mountain_range_0001",
    "symbol_stubby_0001": "symbol_stubby_bottle_0001",
    "symbol_tinnie_0001": "symbol_can_0001",
}


def all_elements() -> tuple[Element, ...]:
    """The archive as the composer sees it, drawn artwork taking precedence."""
    drawn = library.all_drawn()
    drawn_ids = {element.id for element in drawn}

    kept: list[Element] = []
    for element in authored.ALL:
        if element.id in drawn_ids:
            continue
        if SUPERSEDED.get(element.id) in drawn_ids:
            continue
        kept.append(element)

    return tuple(kept) + drawn


def by_id() -> dict[str, Element]:
    return {element.id: element for element in all_elements()}


def provisional() -> tuple[Element, ...]:
    """Elements still standing in for something better, from either source."""
    return tuple(element for element in all_elements() if element.provisional)
