"""Builders for world-document fixtures.

Valid documents are the smallest thing that satisfies the Markdown contract, so a
test that breaks one is unambiguous about what it broke.
"""

from __future__ import annotations

from pathlib import Path

VALID_WORLD = """\
# SHIRTFACED --- WORLD 01

## THE BIG NIGHT

# Purpose

Flagship visual universe.

# Emotional Tone

Optimism.

# Lighting

Street lights.

# Colour Palette

Amber.

# Photography Language

35mm documentary.

# Locations

Country pubs.

# People

Ordinary Australians.

# Wardrobe

Blank garments.

# Composition

Discovered, not displayed.

# An Unknown Section

Kept as it is.

# Success Test

Would someone share it?
"""

VALID_CONTINUITY = """\
# SHIRTFACED — WORLD 01 CONTINUITY LEDGER

# Status Key

- **APPROVED** — belongs in World 1.

# Hero Product Rotation

| Sequence | Scene | Hero Product | Status |
|---:|---|---|---|
| 01 | Walking between venues | Black tee | APPROVED |

# Camera Position Rotation

| Sequence | Scene | Camera Position | Status |
|---:|---|---|---|
| 01 | Walking between venues | Across street | APPROVED |

# Approved Reference Frames

## Reference 01

# Rejected Drift

## Closed Bottle Shop

# Current Canon Notes

- Optimism does not require loud behaviour.

# Next Prompt Brief

**Scene:** Interior car transition.
"""

VALID_SHOTLIST = """\
# SHIRTFACED --- WORLD 01 SHOTLIST

## Status

-   ⬜ Planned
-   ✅ Approved

  ID        Scene                     Hero Product   Camera              Status
  --------- ------------------------- -------------- ------------------- --------
  W01-001   Walking between venues    T-shirt        Across street       ✅
  W01-008   Bottle shop after close   Mixed          Across road         ❌
  W01-011   Car interior transition   Tote bag       Rear seat           ⬜
  W01-012   Apartment lift            Hoodie waist   Inside lift         ⬜

## Rotation Rules

1.  Use the highest-priority Planned scene.
"""


def write_world(
    root: Path,
    slug: str = "world-01",
    *,
    world: str = VALID_WORLD,
    continuity: str = VALID_CONTINUITY,
    shotlist: str = VALID_SHOTLIST,
) -> Path:
    """Create a world directory, optionally with a broken document."""
    directory = root / slug
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "WORLD.md").write_text(world, encoding="utf-8")
    (directory / "CONTINUITY.md").write_text(continuity, encoding="utf-8")
    (directory / "SHOTLIST.md").write_text(shotlist, encoding="utf-8")
    return directory
