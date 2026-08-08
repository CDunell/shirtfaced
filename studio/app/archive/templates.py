"""Layout templates, mined from what the biggest brands actually do.

The engine takes an image, a phrase and some text from the owner and decides how
to present them. This module is the "decides" half, and it is not invented: it
is fourteen layouts measured off 1,166 real designs from 188 apparel brands, in
`var/design_corpus/design_templates.json`.

Each template says where its slots sit as a share of the print area -- top,
height, width, centre -- how many of the 1,166 designs used it, which traditions
it came from, and how many words it typically carries. So a design is placed the
way a third of the streetwear corpus places a two-element design, rather than
the way somebody here guessed.

This replaces guessing, not judgement. The grammars in `grammar.py` were written
by hand, and every one of them is somebody's opinion about layout wearing the
authority of code. These are counts.

What a slot holds is deliberately not decided here. A slot is a box; the owner's
image goes in one, their words in another. The archive supplies furniture --
frames, rules, devices -- and never the subject.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

CORPUS = Path(__file__).resolve().parents[2] / "var" / "design_corpus"
TEMPLATES_FILE = CORPUS / "design_templates.json"


@dataclass(frozen=True)
class Slot:
    """One box in a layout, as a share of the print area."""

    index: int
    top: float
    height: float
    width: float
    centre_x: float

    def box(self, area_width: float, area_height: float) -> tuple[float, float, float, float]:
        """Left, top, width, height in millimetres for a given print area."""
        width = self.width * area_width
        return (
            self.centre_x * area_width - width / 2,
            self.top * area_height,
            width,
            self.height * area_height,
        )


@dataclass(frozen=True)
class Template:
    """One measured way of arranging a design."""

    id: str
    name: str
    slots: tuple[Slot, ...]
    # How many of the 1,166 designs were laid out this way, and what share of
    # designs with this many elements. Carried so a choice can be explained by
    # pointing at a count rather than a preference.
    designs: int
    share: float
    traditions: dict[str, int]
    median_words: float

    @property
    def elements(self) -> int:
        return len(self.slots)

    @property
    def reads_as(self) -> str:
        return f"{self.name} — {self.share:.0%} of {self.elements}-element designs in the corpus"


class NoTemplate(Exception):
    """No measured layout fits, with a reason rather than a silent fallback."""


@lru_cache(maxsize=1)
def all_templates() -> tuple[Template, ...]:
    """Every mined layout, or none if the corpus has not been mined here."""
    if not TEMPLATES_FILE.is_file():
        return ()
    try:
        raw = json.loads(TEMPLATES_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()

    found: list[Template] = []
    for family in raw.get("families", {}).values():
        for entry in family.get("templates", []):
            slots = tuple(
                Slot(
                    index=int(s["slot"]),
                    top=float(s["top"]),
                    height=float(s["height"]),
                    width=float(s["width"]),
                    centre_x=float(s["centre_x"]),
                )
                for s in entry.get("slots", [])
            )
            if not slots:
                continue
            found.append(
                Template(
                    id=str(entry.get("id", "")),
                    name=str(entry.get("name", "")),
                    slots=slots,
                    designs=int(entry.get("designs", 0)),
                    share=float(entry.get("share", 0.0)),
                    traditions=dict(entry.get("traditions", {})),
                    median_words=float(entry.get("median_words", 0.0)),
                )
            )
    # Commonest first, so anything that walks the list in order is walking it in
    # order of how often real brands did it.
    return tuple(sorted(found, key=lambda t: -t.designs))


def for_elements(count: int, tradition: str = "") -> tuple[Template, ...]:
    """Measured layouts that hold exactly this many things.

    Filtering by tradition narrows rather than excludes: a layout used by one
    streetwear brand and forty outdoor ones is still a layout, and the corpus is
    evidence about the market rather than a rule about us.
    """
    fits = tuple(t for t in all_templates() if t.elements == count)
    if tradition:
        preferred = tuple(t for t in fits if t.traditions.get(tradition))
        if preferred:
            return preferred
    return fits


def choose(count: int, seed: int, tradition: str = "") -> Template:
    """One layout for this many elements, picked by the seed.

    Weighted by how often the corpus used it, so the common arrangement comes up
    commonly and the rare one comes up rarely -- which is the difference between
    an engine that knows what brands do and one that picks uniformly from a list.

    Deterministic: the seed alone decides, because two designs from the same
    seed have to be the same design.
    """
    fits = for_elements(count, tradition)
    if not fits:
        raise NoTemplate(f"no measured layout holds {count} element(s)")

    total = sum(t.designs for t in fits) or len(fits)
    # Hashed rather than used directly. `seed % total` is deterministic and
    # useless: with 322 designs across the two-element layouts, every seed from
    # 0 to 91 lands in the first bucket, so the first hundred seeds all return
    # the same arrangement. The hash spreads them without losing the weighting.
    draw = int.from_bytes(sha256(f"template:{seed}".encode()).digest()[:8], "big") % total
    running = 0
    for template in fits:
        running += template.designs or 1
        if draw < running:
            return template
    return fits[-1]
