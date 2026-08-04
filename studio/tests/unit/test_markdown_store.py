"""The Markdown store: reading, hashing and path safety."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.adapters.markdown_store import MarkdownStore, sha256_hex
from app.domain.errors import UnsafePathError, WorldNotFoundError


def _make_world(root: Path, slug: str = "world-01") -> Path:
    directory = root / slug
    directory.mkdir(parents=True)
    (directory / "WORLD.md").write_text("# SHIRTFACED\n", encoding="utf-8")
    (directory / "CONTINUITY.md").write_text("# Status Key\n", encoding="utf-8")
    (directory / "SHOTLIST.md").write_text("# Shotlist\n", encoding="utf-8")
    return directory


def test_reads_the_three_documents(tmp_path: Path) -> None:
    _make_world(tmp_path)

    documents = MarkdownStore(tmp_path).read_world_documents("world-01")

    assert set(documents) == {"WORLD.md", "CONTINUITY.md", "SHOTLIST.md"}
    assert documents["WORLD.md"].text == "# SHIRTFACED\n"


def test_hashes_the_content(tmp_path: Path) -> None:
    _make_world(tmp_path)

    documents = MarkdownStore(tmp_path).read_world_documents("world-01")

    assert documents["WORLD.md"].sha256 == sha256_hex("# SHIRTFACED\n")
    assert len(documents["WORLD.md"].sha256) == 64


def test_the_hash_changes_when_the_content_does(tmp_path: Path) -> None:
    directory = _make_world(tmp_path)
    store = MarkdownStore(tmp_path)
    before = store.read_document("world-01", "WORLD.md").sha256

    (directory / "WORLD.md").write_text("# SHIRTFACED\n\nedited\n", encoding="utf-8")

    assert store.read_document("world-01", "WORLD.md").sha256 != before


@pytest.mark.parametrize(
    "slug",
    ["..", "../secrets", "..\\secrets", "world-01/../..", "/etc", "", "."],
)
def test_path_traversal_is_refused(tmp_path: Path, slug: str) -> None:
    _make_world(tmp_path)

    with pytest.raises(UnsafePathError):
        MarkdownStore(tmp_path).world_directory(slug)


def test_a_missing_world_is_reported_clearly(tmp_path: Path) -> None:
    with pytest.raises(WorldNotFoundError):
        MarkdownStore(tmp_path).read_world_documents("world-99")


def test_a_missing_document_is_reported_clearly(tmp_path: Path) -> None:
    directory = _make_world(tmp_path)
    (directory / "SHOTLIST.md").unlink()

    with pytest.raises(WorldNotFoundError, match=r"SHOTLIST\.md"):
        MarkdownStore(tmp_path).read_world_documents("world-01")


def test_available_slugs_lists_only_complete_worlds(tmp_path: Path) -> None:
    _make_world(tmp_path, "world-01")
    _make_world(tmp_path, "world-02")
    (tmp_path / "world-02" / "CONTINUITY.md").unlink()
    (tmp_path / "not-a-world").mkdir()

    assert MarkdownStore(tmp_path).available_slugs() == ["world-01"]
