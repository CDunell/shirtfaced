"""Taking outside artwork into the archive.

Four of the fourteen families cannot be authored. A drawing of a hand has to be
drawn or found, and finding it means someone else made it. That changes what
ingestion is: mostly a rights problem wearing a file-format problem's clothes.

Everything comes in. Reference material is how design has always worked, and an
archive that can only hold what has already been cleared is an archive that
cannot learn from anything. The corpus already holds thousands of competitors'
product photographs on exactly that basis.

What this module does record is **where each thing came from** -- source, item
identifier, URL -- because that is what makes the rights question answerable
later, when it is actually asked. It is a record, not a gate.

The rights question is asked once, about a finished design, before release. See
``rights_cleared_for_sale`` in the design workflow.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.archive.convert import colours_in, combined_path, has_raster, shapes_in
from app.domain.element import Element, Licence
from app.domain.enums import LicenceStatus

# Path commands, for measuring how involved a piece of artwork is.
COMMAND = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")
PATH_TAG = re.compile(r'<path[^>]*\sd="([^"]+)"', re.IGNORECASE | re.DOTALL)
VIEWBOX = re.compile(r'viewBox="\s*([-\d.]+)[\s,]+([-\d.]+)[\s,]+([-\d.]+)[\s,]+([-\d.]+)"')

# The scale complexity is measured against. Not a limit -- a reference point,
# so "how involved is this" is a number the composer can weigh against the size
# of the print it is considering.
BUSY_COMMANDS = 400


class NotIngestible(Exception):
    """The file cannot become an element, with a durable reason code."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Source:
    """Where a piece of artwork came from.

    Every field is required. A source with a blank identifier cannot be checked
    again later, which makes it indistinguishable from something nobody
    recorded -- and an unrecorded source is the one that gets used by accident.
    """

    name: str
    item_id: str
    url: str
    note: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise NotIngestible("SOURCE_NOT_NAMED", "a source must say where it came from")
        if not self.item_id.strip():
            raise NotIngestible(
                "SOURCE_HAS_NO_IDENTIFIER",
                f"{self.name} artwork needs the identifier it has there, so the "
                "terms can be checked against the item rather than the collection",
            )


def _geometry(svg: str) -> tuple[str, tuple[str, ...]]:
    """The file's geometry as one path, and the palette it arrived in.

    Primitives -- rect, circle, ellipse, polygon, polyline, line -- are
    converted here rather than refused. Asking whoever sent the file to convert
    them first is asking someone else to do work that belongs on this side, and
    turning material away in the meantime.
    """
    shapes = shapes_in(svg)
    if not shapes:
        raise NotIngestible(
            "NO_GEOMETRY",
            "nothing drawable in the file"
            + (
                " -- it appears to be an embedded bitmap, which has no geometry to read"
                if has_raster(svg)
                else ""
            ),
        )
    return combined_path(shapes), colours_in(shapes)


def complexity_of(path_data: str) -> float:
    """How involved this artwork is, as a number the composer can weigh.

    Counted from drawing commands rather than file size, because file size
    mostly measures how the exporter felt about decimal places.

    This is a signal, not a limit. Something intricate is wrong for a 76mm yoke
    print and right for a 305mm front, and the density budget already makes that
    call per placement. Refusing it here would throw it away for both.
    """
    commands = len(COMMAND.findall(path_data))
    return min(commands / BUSY_COMMANDS, 1.0)


def ingest_svg(
    file: Path,
    *,
    element_key: str,
    recipe_family: str,
    subtype: str,
    source: Source,
    style_tags: tuple[str, ...] = (),
    ink_min: int = 1,
    ink_max: int = 2,
    symmetry: str = "none",
) -> Element:
    """Read one SVG into an archive element.

    Provenance is recorded and nothing is blocked. What is known about where it
    came from travels with it, so the release review has something to work from.
    """
    try:
        svg = file.read_text(encoding="utf-8")
    except OSError as error:
        raise NotIngestible("UNREADABLE_FILE", str(error)) from error

    path_data, source_colours = _geometry(svg)

    return Element(
        id=element_key,
        family=recipe_family,
        subtype=subtype,
        licence=Licence(
            # Not a placeholder to be filled in by a script. The whole point is
            # that a person reads the terms for this item.
            status=LicenceStatus.UNVERIFIED,
            source=source.name,
            source_id=source.item_id,
            source_url=source.url,
            note=source.note,
        ),
        slots=(),
        symmetry=symmetry,
        ink_min=ink_min,
        ink_max=ink_max,
        complexity=complexity_of(path_data),
        style_tags=style_tags,
        compatible_treatments=("clean", "distressed"),
        recipe="",
        geometry=path_data,
        source_colours=source_colours,
        source_file=str(file),
    )


def verify(
    element: Element,
    *,
    terms: str,
    checked_at: object,
    commercial_use: bool,
    note: str = "",
) -> Element:
    """Record that a person checked this item's terms.

    Deliberately explicit about `commercial_use`. Passing False keeps the
    element stored and refused rather than deleting it, so the same artwork is
    not found and re-checked in six months.
    """
    from dataclasses import replace

    if not terms.strip():
        raise NotIngestible(
            "TERMS_NOT_RECORDED",
            "verifying means recording what the terms actually say, not that someone looked",
        )
    if not element.licence.source or not element.licence.source_id:
        raise NotIngestible(
            "SOURCE_INCOMPLETE",
            "an element with no recorded source cannot be verified, because "
            "there is nothing to check it against",
        )

    return replace(
        element,
        licence=Licence(
            status=LicenceStatus.VERIFIED if commercial_use else LicenceStatus.REFUSED,
            terms=terms,
            source=element.licence.source,
            source_id=element.licence.source_id,
            source_url=element.licence.source_url,
            checked_at=checked_at,  # type: ignore[arg-type]
            commercial_use=commercial_use,
            note=note or element.licence.note,
        ),
    )
