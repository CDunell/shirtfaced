"""What an archive element is, and when it may be used.

The archive's value is that elements carry their own constraints, so a composer
can ask an element what it permits instead of a human remembering. Two of those
constraints are load-bearing enough to live in the type rather than in a
convention:

*Slots* are what make an element composable. An element that declares slots can
be filled with supplied content; one that does not can only be placed. This is
the difference between a recipe and a picture.

*Licence* is a recorded fact with a source, not a flag. These go on garments
that are sold, so an element whose rights are unverified must not be reachable
by the composer at all -- not flagged for later, not usable with a warning.
The gate fails closed: unknown means unusable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.domain.enums import LicenceStatus


@dataclass(frozen=True)
class Licence:
    """The right to use one element, as a fact that can be audited.

    `terms` alone is not enough. "CC0" with no source is an assertion by
    whoever typed it; the source and its identifier are what make it checkable
    later, and `checked_at` is what tells a future reader how stale it is.
    """

    status: LicenceStatus = LicenceStatus.UNVERIFIED
    terms: str = ""
    source: str = ""
    source_id: str = ""
    source_url: str = ""
    checked_at: date | None = None
    commercial_use: bool = False
    # Free text for the awkward cases, which are the majority of the hard ones:
    # an out-of-copyright work whose scan carries its own claim, or terms that
    # differ between the jurisdictions we sell into.
    note: str = ""

    @property
    def usable(self) -> bool:
        """Whether the composer may reach this element at all.

        Deliberately conjunctive and deliberately strict. An element is usable
        only when someone checked it, recorded what they found, and found terms
        that permit commercial use. Anything else -- including a blank record
        that nobody has got to yet -- is not usable.
        """
        return (
            self.status is LicenceStatus.VERIFIED
            and self.commercial_use
            and bool(self.terms)
            and bool(self.source)
            and self.checked_at is not None
        )

    def refusal(self) -> str:
        """Why this element may not be used, as a durable reason code."""
        if self.status is LicenceStatus.UNVERIFIED:
            return "LICENCE_UNVERIFIED"
        if self.status is LicenceStatus.REFUSED:
            return "LICENCE_REFUSED"
        if not self.commercial_use:
            return "LICENCE_NON_COMMERCIAL"
        if not self.terms or not self.source:
            return "LICENCE_INCOMPLETE"
        if self.checked_at is None:
            return "LICENCE_UNDATED"
        return ""


@dataclass(frozen=True)
class Slot:
    """A place in an element where supplied content goes.

    Geometry is proportional to the element's own box, never to a page or a
    garment, so the same element can be used at any size and on any surface.
    """

    name: str
    # Proportions of the element box: 0..1 in both axes.
    top: float
    height: float
    width: float
    centre_x: float
    # What may fill it. An empty tuple means anything.
    accepts: tuple[str, ...] = ("text",)
    # Text set along a curve rather than a baseline. "upper_arc", "lower_arc"
    # or "" for straight.
    path: str = ""
    tracking: float = 0.0
    alignment: str = "centre"


@dataclass(frozen=True)
class Element:
    """One archive element: geometry plus the rules for using it."""

    id: str
    family: str
    subtype: str
    licence: Licence
    slots: tuple[Slot, ...] = ()
    symmetry: str = "none"
    ink_min: int = 1
    ink_max: int = 3
    # 0..1, how busy the element is. Used to keep a composition from stacking
    # three intricate things on top of each other.
    complexity: float = 0.0
    style_tags: tuple[str, ...] = ()
    compatible_treatments: tuple[str, ...] = ()
    # What this element refuses. Cheaper and more honest than enumerating what
    # it permits, and it is what makes the grammar tractable.
    exclusions: tuple[str, ...] = ()
    # Authored elements name a recipe; ingested ones carry their own path data.
    # Exactly one of the two, which the database enforces as a constraint.
    recipe: str = ""
    geometry: str = ""
    source_file: str = ""
    parameters: dict[str, float] = field(default_factory=dict)

    def slot(self, name: str) -> Slot | None:
        for candidate in self.slots:
            if candidate.name == name:
                return candidate
        return None

    def usable_with(self, inks: int, treatment: str) -> tuple[bool, str]:
        """Whether this element may be used at all, and why not when it may not.

        Licence is checked first and on its own, because a licence failure is
        not a design constraint that a different palette could satisfy.
        """
        if not self.licence.usable:
            return False, self.licence.refusal()
        if inks < self.ink_min:
            return False, "INKS_BELOW_MINIMUM"
        if inks > self.ink_max:
            return False, "INKS_ABOVE_MAXIMUM"
        if treatment in self.exclusions:
            return False, "TREATMENT_EXCLUDED"
        if self.compatible_treatments and treatment not in self.compatible_treatments:
            return False, "TREATMENT_NOT_SUPPORTED"
        return True, ""
