"""PROMPT_CONSTRUCTION_PRINCIPLES.md must not contradict the vehicle canon.

Level 4 used to list "Through the passenger window." and "Inside the back seat."
as valid camera positions, while WORLD.md and CARRY_FORWARD_CANON.md ban the camera
from ever being inside a vehicle. This document is not parsed by any loader — it is
read by whoever writes a prompt by hand — so nothing else would have caught the two
disagreeing. See docs/shirtfaced-audit.md Area 1.5.
"""

from __future__ import annotations

from app.config import PROJECT_ROOT

DOC_PATH = PROJECT_ROOT / "docs" / "PROMPT_CONSTRUCTION_PRINCIPLES.md"


def _text() -> str:
    return DOC_PATH.read_text(encoding="utf-8").lower()


def test_the_document_exists() -> None:
    assert DOC_PATH.is_file()


def test_level_four_no_longer_puts_the_camera_inside_a_vehicle() -> None:
    text = _text()

    banned = ("inside the back seat", "through the passenger window.")
    offenders = [phrase for phrase in banned if phrase in text]

    assert not offenders, (
        f"PROMPT_CONSTRUCTION_PRINCIPLES.md still lists these camera positions: "
        f"{offenders}. Both put the camera inside the vehicle cabin, which "
        "CARRY_FORWARD_CANON.md's vehicle rule forbids outright."
    )


def test_the_document_defers_to_world_specific_canon() -> None:
    """A generic 'permanent canon' document has to say it can be overruled.

    Otherwise the next contradiction looks exactly like this one did: two documents
    both claiming permanent authority, with no stated tiebreaker.
    """
    text = _text()

    assert "carry_forward_canon.md" in text
    assert "wins" in text
