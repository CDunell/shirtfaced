"""Printing an approved design into a defined zone on a garment.

The gap this closes, from the 14 August audit: ``printing.py`` and
``print_service.py`` contain no reference to ``approved_designs``. Print's input
was a file name found in ``assets/designs/``, which meant the one thing the
pipeline exists to produce -- an approved version -- was not the thing Print
printed. Anything dropped in a folder was.

**Zones, not corners.** ``printing.py`` places artwork on a *photograph* by a
hand-dragged quadrilateral. That path never got off the ground and was replaced
by defined zones: ``app/archive/placements.py`` holds fourteen printable zones
per fit in real millimetres with maximum bounds and seam clearance, and
``app/archive/garment.py`` hangs a design from a named zone's top edge. This
module is the join between an approved design and that machinery.

**Why the size is carried rather than measured.** Artwork made in a paid
interface comes back as pixels, and pixels have no physical size. A 2048px PNG
is 170mm or 340mm depending on nothing in the file. So the print width is a
decision, recorded on the approved version in ``production_spec`` -- which is
what that column exists for: *"print method, colours, sizing, whatever
production needs frozen with the approval rather than recalled later"*.

**It refuses rather than shrinking.** ``garment.place`` raises
``DESIGN_EXCEEDS_ZONE`` when a design will not fit, and nothing here catches
that to scale it down. A print that does not fit its zone is a decision to
revisit, and silently resizing it would mean the garment that arrives is not
the one that was approved.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass

from PIL import Image

from app.adapters.asset_store import AssetStore, AssetStoreError
from app.archive import garment as garment_module
from app.archive.svg import num
from app.config import GARMENTS_DIR as GARMENT_DIR
from app.db.concept_models import ApprovedDesign
from app.domain.errors import StudioError

__all__ = [
    "PrintRefused",
    "ZoneChoice",
    "available_garments",
    "print_approved",
]

# Raster artwork is embedded rather than referenced: the rendered document has
# to survive being saved, mailed and opened somewhere with no access to this
# server. These are the types a paid interface actually returns.
RASTER_MIME = {"image/png": "png", "image/jpeg": "jpeg", "image/webp": "webp"}


class PrintRefused(StudioError):
    """The approved design cannot be printed as asked. HTTP 422."""


@dataclass(frozen=True)
class ZoneChoice:
    """One printable zone on one garment, as the screen needs to offer it."""

    key: str
    width_mm: float
    height_mm: float


def available_garments() -> dict[str, list[ZoneChoice]]:
    """Every garment file and the zones it declares.

    Read off the SVGs rather than listed in code, so adding a garment is
    dropping a file in. A file that cannot be parsed is skipped rather than
    failing the whole list -- one malformed garment should not empty the menu.

    Garments come from ``GARMENT_DIR`` -- the repository's own ``assets/garments``
    -- and deliberately not from ``ASSETS_ROOT``. They are checked-in source, the
    same for every deployment, and ``design_composition`` has always read them
    from there. ``ASSETS_ROOT`` is the writable store for things this
    application produced: uploaded artwork, generated photographs, renders. The
    first version of this module took an ``assets_root`` argument and looked in
    the wrong place; it passed its test only because the test copied a garment
    into a scratch root, and it would have found nothing in production.
    """
    if not GARMENT_DIR.is_dir():
        return {}

    found: dict[str, list[ZoneChoice]] = {}
    for path in sorted(GARMENT_DIR.glob("*.svg")):
        try:
            loaded = garment_module.load(path)
        except (garment_module.GarmentError, OSError, ValueError):
            continue
        if not loaded.zones:
            continue
        found[path.stem] = [
            ZoneChoice(key=zone.key, width_mm=zone.width, height_mm=zone.height)
            for zone in loaded.zones.values()
        ]
    return found


def print_approved(
    store: AssetStore,
    version: ApprovedDesign,
    *,
    show_zones: bool = False,
) -> str:
    """Render one approved version onto its garment, in its zone, at its size.

    Everything comes from the approved row. Nothing about what gets printed is
    taken from the request, because the point of an approved version is that it
    is the same every time it is asked for.
    """
    spec = version.production_spec or {}
    garment_key = str(spec.get("garment_key") or "").strip()
    zone_key = str(spec.get("zone_key") or "").strip()
    raw_width = spec.get("print_width_mm")
    width_mm = float(raw_width) if isinstance(raw_width, int | float) else None
    colour = str(spec.get("garment_colour") or "").strip() or "#1A1A1A"

    if not garment_key or not zone_key or width_mm is None or width_mm <= 0:
        missing = [
            name
            for name, present in (
                ("garment", bool(garment_key)),
                ("print zone", bool(zone_key)),
                ("print width", width_mm is not None and width_mm > 0),
            )
            if not present
        ]
        raise PrintRefused(
            f"v{version.version} has no {' and no '.join(missing)} recorded. "
            "Record them on the approved version before printing it."
        )

    garment_path = GARMENT_DIR / f"{garment_key}.svg"
    if garment_path.name != f"{garment_key}.svg" or not garment_path.is_file():
        raise PrintRefused(f"There is no garment called {garment_key!r}.")

    try:
        loaded = garment_module.load(garment_path)
    except garment_module.GarmentError as error:
        raise PrintRefused(f"{garment_key} could not be read: {error}") from error

    if zone_key not in loaded.zones:
        offered = ", ".join(sorted(loaded.zones)) or "none"
        raise PrintRefused(f"{garment_key} has no {zone_key!r} zone. It has: {offered}.")

    master = version.master_asset
    try:
        data = store.load(master.relative_path)
    except AssetStoreError as error:
        raise PrintRefused(
            f"The approved artwork is recorded but its file could not be read. {error}"
        ) from error

    design_svg, design_width, design_height = _as_svg(data, master.mime_type, width_mm)

    try:
        return garment_module.place(
            loaded,
            zone_key,
            design_svg,
            design_width,
            design_height,
            garment_colour=colour,
            show_zones=show_zones,
        )
    except garment_module.GarmentError as error:
        raise PrintRefused(
            f"{error.detail or error}. Reduce the print width on the approved version, "
            "or choose a zone with more room."
        ) from error


def _as_svg(data: bytes, mime_type: str, width_mm: float) -> tuple[str, float, float]:
    """The artwork as an SVG document at a real millimetre size.

    Vector artwork is used as it stands and only measured. Raster artwork is
    wrapped: its height follows from its own aspect ratio, so the print is
    never distorted to fill a zone -- the width is the decision and the height
    is arithmetic.
    """
    if mime_type == "image/svg+xml" or data.lstrip()[:5] in (b"<svg ", b"<?xml"):
        text = data.decode("utf-8", errors="replace")
        return text, width_mm, _svg_height(text, width_mm)

    suffix = RASTER_MIME.get(mime_type)
    if suffix is None:
        raise PrintRefused(
            f"{mime_type} cannot be placed on a garment. "
            f"Approved artwork must be SVG, {', '.join(sorted(RASTER_MIME))}."
        )

    from io import BytesIO

    try:
        with Image.open(BytesIO(data)) as image:
            pixel_width, pixel_height = image.size
    except OSError as error:
        raise PrintRefused(f"The approved artwork is not a readable image: {error}") from error
    if not pixel_width or not pixel_height:
        raise PrintRefused("The approved artwork has no dimensions.")

    height_mm = width_mm * pixel_height / pixel_width
    encoded = base64.b64encode(data).decode("ascii")
    document = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{num(width_mm)}" height="{num(height_mm)}" '
        f'viewBox="0 0 {num(width_mm)} {num(height_mm)}">'
        f'<image href="data:{mime_type};base64,{encoded}" x="0" y="0" '
        f'width="{num(width_mm)}" height="{num(height_mm)}"/>'
        f"</svg>"
    )
    return document, width_mm, height_mm


def _svg_height(document: str, width_mm: float) -> float:
    """A vector design's height at the requested width, from its viewBox.

    Falls back to square rather than guessing: a design whose viewBox cannot be
    read is one whose proportions are unknown, and a wrong aspect ratio is a
    distorted print rather than a visible error.
    """
    match = garment_module.VIEWBOX.search(document)
    if match is None:
        return width_mm
    _x, _y, box_width, box_height = (float(value) for value in match.groups())
    if box_width <= 0:
        return width_mm
    return width_mm * box_height / box_width
