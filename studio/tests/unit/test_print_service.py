"""Choosing what the compositor is given.

The picture itself is covered in test_compositing. What matters here is that a name
arriving from a request cannot reach outside the designs directory, and that a file
which would print as a rectangle is refused before anybody wastes a look at it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.services.print_service import (
    NoSuchDesign,
    available_designs,
    designs_root,
    load_design,
)


@pytest.fixture
def assets_root(tmp_path: Path) -> Path:
    designs_root(tmp_path).mkdir(parents=True)
    return tmp_path


def write_design(assets_root: Path, name: str, *, alpha: bool = True) -> Path:
    path = designs_root(assets_root) / name
    mode = "RGBA" if alpha else "RGB"
    Image.new(mode, (10, 10), (255, 0, 0) + ((128,) if alpha else ())).save(path)
    return path


def test_a_missing_directory_is_not_an_error(tmp_path: Path) -> None:
    """No designs yet is the normal state until artwork exists."""
    assert available_designs(tmp_path) == []


def test_designs_are_listed_by_name(assets_root: Path) -> None:
    write_design(assets_root, "send-it.png")
    write_design(assets_root, "cold-beer.png")

    assert [design.name for design in available_designs(assets_root)] == [
        "cold-beer.png",
        "send-it.png",
    ]


def test_things_that_are_not_designs_are_ignored(assets_root: Path) -> None:
    """The directory is somewhere files get dropped, so it collects other things."""
    write_design(assets_root, "real.png")
    (designs_root(assets_root) / "notes.txt").write_text("not a design")
    (designs_root(assets_root) / "subfolder").mkdir()

    assert [design.name for design in available_designs(assets_root)] == ["real.png"]


def test_a_design_without_transparency_is_refused(assets_root: Path) -> None:
    """It would print as a solid rectangle across somebody's chest."""
    write_design(assets_root, "flat.png", alpha=False)

    with pytest.raises(NoSuchDesign, match="alpha"):
        load_design(assets_root, "flat.png")


@pytest.mark.parametrize(
    "name",
    ["../secrets.png", "..\\secrets.png", "sub/dir.png", "/etc/passwd"],
    ids=["parent", "windows-parent", "subdirectory", "absolute"],
)
def test_a_name_cannot_escape_the_designs_directory(assets_root: Path, name: str) -> None:
    """The name arrives from a request. It is a file name and nothing else."""
    with pytest.raises(NoSuchDesign):
        load_design(assets_root, name)


def test_a_design_that_is_there_loads(assets_root: Path) -> None:
    write_design(assets_root, "send-it.png")

    assert load_design(assets_root, "send-it.png").mode == "RGBA"
