"""Deterministic SVG emission.

Everything the archive produces has to be byte-identical for the same inputs,
and the usual reasons output drifts are all small: floats formatted by repr,
dictionaries iterated in insertion order that changes when a caller is edited,
a timestamp in a comment, ambient randomness in a texture.

So numbers are formatted through one function, attributes are emitted in sorted
order, and nothing here reads a clock or a global random source. The seeded
generator is passed in explicitly wherever variation is wanted, which is the
same discipline the workflow scripts enforce by forbidding Math.random().
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# Decimal places kept in emitted geometry. Four is finer than any press can
# hold and coarse enough that platform float noise never reaches the output.
PRECISION = 4


def num(value: float) -> str:
    """One number, formatted one way, everywhere.

    Trailing zeros are stripped so the output is compact, and negative zero is
    normalised -- it compares equal to zero but does not render identically,
    which is exactly the kind of difference that breaks byte-identity.
    """
    rounded = round(float(value), PRECISION)
    if rounded == 0:
        return "0"
    text = f"{rounded:.{PRECISION}f}".rstrip("0").rstrip(".")
    return text or "0"


def points(pairs: list[tuple[float, float]]) -> str:
    return " ".join(f"{num(x)},{num(y)}" for x, y in pairs)


@dataclass
class Canvas:
    """An SVG document being built.

    Width and height are in millimetres because print is, and because a print
    that is 280mm across is a fact about the garment while 1024 pixels is a
    fact about a screen.
    """

    width_mm: float
    height_mm: float
    elements: list[str] = field(default_factory=list)

    def add(self, markup: str) -> None:
        self.elements.append(markup)

    def path(self, data: str, **attributes: object) -> None:
        self.add(_tag("path", d=data, **attributes))

    def circle(self, cx: float, cy: float, r: float, **attributes: object) -> None:
        self.add(_tag("circle", cx=num(cx), cy=num(cy), r=num(r), **attributes))

    def rect(
        self, x: float, y: float, width: float, height: float, **attributes: object
    ) -> None:
        self.add(
            _tag(
                "rect",
                x=num(x),
                y=num(y),
                width=num(width),
                height=num(height),
                **attributes,
            )
        )

    def group(self, markup: list[str], **attributes: object) -> None:
        inner = "".join(markup)
        self.add(f"{_open('g', **attributes)}{inner}</g>")

    def to_svg(self) -> str:
        """The finished document.

        No generator comment and no timestamp: both would defeat the property
        this whole module exists to hold.
        """
        header = (
            '<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{num(self.width_mm)}mm" height="{num(self.height_mm)}mm" '
            f'viewBox="0 0 {num(self.width_mm)} {num(self.height_mm)}">'
        )
        return header + "".join(self.elements) + "</svg>"


def _format_attributes(attributes: dict[str, object]) -> str:
    parts = []
    # Sorted, so an edit that reorders keyword arguments cannot change output.
    for key in sorted(attributes):
        value = attributes[key]
        if value is None:
            continue
        name = key.rstrip("_").replace("_", "-")
        if isinstance(value, float):
            value = num(value)
        parts.append(f'{name}="{value}"')
    return (" " + " ".join(parts)) if parts else ""


def _tag(name: str, **attributes: object) -> str:
    return f"<{name}{_format_attributes(attributes)}/>"


def _open(name: str, **attributes: object) -> str:
    return f"<{name}{_format_attributes(attributes)}>"


def rng_for(seed: int, *salt: str) -> random.Random:
    """A generator scoped to one seed and one named purpose.

    Two transformations that both want variation must not share a stream, or
    adding a call to one silently changes the other. Salting by name keeps each
    independent and reproducible on its own.
    """
    combined = f"{seed}:" + ":".join(salt)
    return random.Random(combined)


def jitter(generator: random.Random, amount: float) -> float:
    """Symmetric variation, from an explicitly supplied generator."""
    return (generator.random() * 2.0 - 1.0) * amount
