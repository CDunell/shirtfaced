"""Source files must not contain control characters.

This has bitten three times in one session, always the same way: a tooling
round-trip collapses a `\\b` escape and writes a raw 0x08 backspace byte into
the source. Nothing errors. The file still parses. A regex silently matches
nothing, or a pattern quietly stops working, and the failure surfaces somewhere
unrelated hours later.

The first time it killed two of six category patterns in the corpus collector.
The third time it made every SVG group transform be ignored, which put every
placed design in the top-left corner of the garment and looked like a placement
bug.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# Tab, newline and carriage return are the legitimate ones.
ALLOWED = {0x09, 0x0A, 0x0D}

SEARCHED = ("app", "scripts", "tests")


def _source_files() -> list[Path]:
    found: list[Path] = []
    for folder in SEARCHED:
        found.extend((ROOT / folder).rglob("*.py"))
    return [path for path in found if "__pycache__" not in path.parts]


@pytest.mark.parametrize("path", _source_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_no_control_characters(path: Path) -> None:
    data = path.read_bytes()
    offenders = sorted({byte for byte in data if byte < 0x20 and byte not in ALLOWED})
    assert not offenders, (
        f"{path.relative_to(ROOT)} contains control byte(s) "
        f"{', '.join(hex(b) for b in offenders)}. This is almost always a "
        "collapsed escape -- a backslash-b written as a raw backspace -- which "
        "parses fine and silently breaks whatever pattern it lands in."
    )
