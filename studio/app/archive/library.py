"""Loading ingested artwork from the asset library.

`authored.py` holds elements written as parametric geometry. This holds the
ones that arrived as files -- drawn by someone, converted, and stored under
`assets/`. Both become the same `Element`, so a grammar filling a role does not
care which kind it gets.

Drawn artwork is normalised into a unit box on the way in. Files arrive in
whatever coordinate space their author used -- one is 80x160, another 220x100 --
and a grammar sizes a part as a share of the design, so an element that
silently carries its own scale would be a different size in every composition.

Metadata comes from a sidecar `library.json`. Keeping it out of the SVG means
the artwork can be replaced without losing what we know about it, and a
supplier can send a plain file without also having to edit a manifest.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.archive.convert import combined_path, fit_to_box, shapes_in
from app.domain.element import Element, Licence
from app.domain.enums import LicenceStatus

REPO_ROOT = Path(__file__).resolve().parents[3]
LIBRARY = REPO_ROOT / "assets"

# The box drawn artwork is normalised into. Arbitrary, and it does not matter
# what it is: every part is placed as a share of its box, so what matters is
# that every element agrees on one.
UNIT = 100.0


@dataclass(frozen=True)
class Entry:
    """What the manifest records about one file."""

    subtype: str = ""
    style_tags: tuple[str, ...] = ()
    symmetry: str = "none"
    ink_min: int = 1
    ink_max: int = 2
    complexity: float | None = None
    exclusions: tuple[str, ...] = ()
    treatments: tuple[str, ...] = ("clean", "distressed")
    provisional: str = ""
    source: str = ""
    source_id: str = ""
    source_url: str = ""
    terms: str = ""


def _manifest(folder: Path) -> dict[str, Entry]:
    file = folder / "library.json"
    if not file.is_file():
        return {}
    try:
        raw = json.loads(file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # A broken manifest means no metadata, not no artwork. The files are
        # still worth loading with defaults.
        return {}
    return {
        key: Entry(
            subtype=value.get("subtype", ""),
            style_tags=tuple(value.get("style_tags", ())),
            symmetry=value.get("symmetry", "none"),
            ink_min=int(value.get("ink_min", 1)),
            ink_max=int(value.get("ink_max", 2)),
            complexity=value.get("complexity"),
            exclusions=tuple(value.get("exclusions", ())),
            treatments=tuple(value.get("treatments", ("clean", "distressed"))),
            provisional=value.get("provisional", ""),
            source=value.get("source", ""),
            source_id=value.get("source_id", ""),
            source_url=value.get("source_url", ""),
            terms=value.get("terms", ""),
        )
        for key, value in raw.items()
    }


def load_folder(folder: Path, family: str) -> tuple[Element, ...]:
    """Every SVG in a folder, as elements of one family."""
    if not folder.is_dir():
        return ()

    entries = _manifest(folder)
    found: list[Element] = []
    for file in sorted(folder.glob("*.svg")):
        key = file.stem
        entry = entries.get(key, Entry())
        try:
            svg = file.read_text(encoding="utf-8")
        except OSError:
            continue

        shapes = shapes_in(svg)
        if not shapes:
            continue
        geometry = fit_to_box(combined_path(shapes), UNIT)

        import re

        commands = len(re.findall(r"[MmLlHhVvCcSsQqTtAaZz]", geometry))
        found.append(
            Element(
                id=key,
                family=family,
                subtype=entry.subtype or key.replace(f"{family}_", "").rsplit("_", 1)[0],
                licence=Licence(
                    status=LicenceStatus.VERIFIED if entry.terms else LicenceStatus.UNVERIFIED,
                    terms=entry.terms,
                    source=entry.source,
                    source_id=entry.source_id or key,
                    source_url=entry.source_url,
                    commercial_use=bool(entry.terms),
                ),
                symmetry=entry.symmetry,
                ink_min=entry.ink_min,
                ink_max=entry.ink_max,
                complexity=(
                    entry.complexity if entry.complexity is not None else min(commands / 400.0, 1.0)
                ),
                style_tags=entry.style_tags,
                compatible_treatments=entry.treatments,
                exclusions=entry.exclusions,
                provisional=entry.provisional,
                recipe="",
                geometry=geometry,
                source_file=str(file.relative_to(REPO_ROOT)),
            )
        )
    return tuple(found)


RASTER_SUFFIXES = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp")


def load_raster_folder(folder: Path, family: str) -> tuple[Element, ...]:
    """Every raster in a folder, as elements of one family.

    A texture, a halftone field, a bandana repeat and a scanned flash sheet are
    all raster by nature, and three of the archive's families held nothing at
    all because the loader only globbed for SVG. The database has allowed an
    element without geometry since migration 0016 for exactly this; nothing was
    reading it.

    These carry no path data. They are placed by the composer the same way and
    drawn as an image reference, so what is stored is where the file is rather
    than what shape it makes.
    """
    if not folder.is_dir():
        return ()

    entries = _manifest(folder)
    found: list[Element] = []
    files = sorted(f for f in folder.iterdir() if f.suffix.lower() in RASTER_SUFFIXES)
    for file in files:
        key = file.stem
        entry = entries.get(key, Entry())
        found.append(
            Element(
                id=key,
                family=family,
                subtype=entry.subtype or key.replace(f"{family}_", "").rsplit("_", 1)[0],
                licence=Licence(
                    status=LicenceStatus.VERIFIED if entry.terms else LicenceStatus.UNVERIFIED,
                    terms=entry.terms,
                    source=entry.source,
                    source_id=entry.source_id or key,
                    source_url=entry.source_url,
                    commercial_use=bool(entry.terms),
                ),
                symmetry=entry.symmetry,
                ink_min=entry.ink_min,
                ink_max=entry.ink_max,
                # A raster's complexity cannot be counted from path commands, so
                # it is taken from the manifest or left mid-range rather than
                # guessed from the file size, which measures compression.
                complexity=entry.complexity if entry.complexity is not None else 0.5,
                style_tags=entry.style_tags,
                compatible_treatments=entry.treatments,
                exclusions=entry.exclusions,
                provisional=entry.provisional,
                recipe="",
                geometry="",
                source_file=str(file.relative_to(REPO_ROOT)),
            )
        )
    return tuple(found)


def symbols() -> tuple[Element, ...]:
    return load_folder(LIBRARY / "symbols", "symbol")


def ornaments() -> tuple[Element, ...]:
    return load_folder(LIBRARY / "ornaments", "ornament")


def frames() -> tuple[Element, ...]:
    return load_folder(LIBRARY / "frames", "frame")


def illustrations() -> tuple[Element, ...]:
    return load_folder(LIBRARY / "illustration_parts", "illustration_part")


def textures() -> tuple[Element, ...]:
    return load_raster_folder(LIBRARY / "textures", "texture")


def patterns() -> tuple[Element, ...]:
    return load_raster_folder(LIBRARY / "patterns", "pattern")


def print_effects() -> tuple[Element, ...]:
    return load_raster_folder(LIBRARY / "print_effects", "print_effect")


def badges() -> tuple[Element, ...]:
    return load_folder(LIBRARY / "badges", "badge")


def flash() -> tuple[Element, ...]:
    """Tattoo and occult flash, which arrives raster and is vectorised later."""
    return load_raster_folder(LIBRARY / "flash", "illustration_part")


def all_drawn() -> tuple[Element, ...]:
    """Everything in the asset library, whatever family, vector or raster."""
    return (
        symbols()
        + ornaments()
        + frames()
        + illustrations()
        + textures()
        + patterns()
        + print_effects()
        + flash()
        + badges()
    )
