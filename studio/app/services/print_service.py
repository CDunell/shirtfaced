"""Putting a design on an approved photograph.

The compositor does the picture; this decides what it is given and keeps the answer.
A placement is saved against the photograph so that moving the design is done once,
and every later print -- another design, another ink, a re-export at a different
size -- is free.

Designs are files. There is no artwork in this repository yet, so anything with an
alpha channel dropped into the designs directory is a design, and the name of the
file is its name.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ImageAsset, PrintPlacement
from app.domain.errors import StudioError
from app.services.compositing import Placement, PrintSettings, print_design

# Enough to be an intentional print, small enough to reject a stray screenshot.
DESIGN_SUFFIXES = frozenset({".png", ".webp"})


class NoSuchPhoto(StudioError):
    """The photograph is not in the library."""


class NoSuchDesign(StudioError):
    """No design by that name, or the file is not usable as one."""


class NotPlaced(StudioError):
    """Nobody has said where the design goes on this photograph."""


@dataclass(frozen=True)
class Design:
    """A design file on disk."""

    name: str
    path: Path


def designs_root(assets_root: Path) -> Path:
    return assets_root / "designs"


def available_designs(assets_root: Path) -> list[Design]:
    """Every design file, by name. Empty until somebody puts one there."""
    root = designs_root(assets_root)
    if not root.is_dir():
        return []
    return sorted(
        (Design(name=path.name, path=path) for path in root.iterdir() if _is_design(path)),
        key=lambda design: design.name.lower(),
    )


def _is_design(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in DESIGN_SUFFIXES


def load_design(assets_root: Path, name: str) -> Image.Image:
    """Open one design.

    The name is treated as a file name and nothing else -- no directories, no
    traversal -- because it arrives from a request.
    """
    if name != Path(name).name:
        raise NoSuchDesign(f"{name!r} is not a design name.")

    path = designs_root(assets_root) / name
    if not _is_design(path):
        raise NoSuchDesign(f"There is no design called {name!r}.")

    # Loaded inside the context manager: Pillow keeps the file open until the image
    # data is read, and raising here would otherwise leave the handle dangling.
    with Image.open(path) as image:
        if "A" not in image.getbands():
            raise NoSuchDesign(
                f"{name!r} has no transparency, so it would print as a rectangle. "
                "Designs need an alpha channel."
            )
        return image.convert("RGBA")


def _to_placement(corners: list[list[float]], size: tuple[int, int]) -> Placement:
    """Fractions to pixels, in the order a person drags them."""
    width, height = size
    points = [(x * width, y * height) for x, y in corners]
    return Placement(points[0], points[1], points[2], points[3])


def read_placement(session: Session, asset_id: UUID) -> PrintPlacement | None:
    return session.execute(
        select(PrintPlacement).where(PrintPlacement.asset_id == asset_id)
    ).scalar_one_or_none()


def save_placement(
    session: Session,
    *,
    asset_id: UUID,
    corners: list[list[float]],
    settings: dict[str, float] | None = None,
    design: str | None = None,
) -> PrintPlacement:
    """Record where the design goes, replacing whatever was there.

    Moving a design is an edit rather than a new opinion, so there is one row per
    photograph and it is overwritten.
    """
    asset = session.get(ImageAsset, asset_id)
    if asset is None:
        raise NoSuchPhoto(f"No photograph with id {asset_id}.")

    existing = read_placement(session, asset_id)
    if existing is None:
        existing = PrintPlacement(asset_id=asset_id)
        session.add(existing)

    existing.corners = corners
    existing.settings = settings or {}
    if design is not None:
        existing.design = design

    session.commit()
    return existing


def print_on_photo(
    session: Session,
    *,
    assets_root: Path,
    photo_path: Path,
    asset_id: UUID,
    design_name: str,
) -> Image.Image:
    """The photograph with the saved placement's design printed on it."""
    placement_row = read_placement(session, asset_id)
    if placement_row is None:
        raise NotPlaced("Say where the design goes on this photograph first.")

    design = load_design(assets_root, design_name)
    stored = placement_row.settings
    settings = PrintSettings(**stored) if stored else PrintSettings()

    with Image.open(photo_path) as photo:
        placement = _to_placement(placement_row.corners, photo.size)
        return print_design(photo, design, placement, settings)
