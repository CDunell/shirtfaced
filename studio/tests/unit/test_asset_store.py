"""Filesystem asset storage."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from app.adapters.asset_store import (
    AssetStoreError,
    FilesystemAssetStore,
    attempt_key,
    validate_key,
)
from app.domain.errors import UnsafePathError

DATA = b"\x89PNG\r\n\x1a\nfake image bytes"


def test_saves_and_reads_back(tmp_path: Path) -> None:
    store = FilesystemAssetStore(tmp_path)

    stored = store.save("worlds/world-01/attempts/a/original.png", DATA, "image/png")

    assert store.load(stored.key) == DATA
    assert store.exists(stored.key)


def test_records_hash_and_size(tmp_path: Path) -> None:
    stored = FilesystemAssetStore(tmp_path).save("a/b.png", DATA, "image/png")

    assert stored.sha256 == hashlib.sha256(DATA).hexdigest()
    assert stored.byte_size == len(DATA)
    assert stored.mime_type == "image/png"


def test_creates_intermediate_directories(tmp_path: Path) -> None:
    FilesystemAssetStore(tmp_path).save("deeply/nested/path/image.png", DATA, "image/png")

    assert (tmp_path / "deeply" / "nested" / "path" / "image.png").is_file()


def test_leaves_no_partial_file_behind(tmp_path: Path) -> None:
    """Writes go to a temporary file and are renamed into place."""
    store = FilesystemAssetStore(tmp_path)
    store.save("a/b.png", DATA, "image/png")

    leftovers = list(tmp_path.rglob(".partial-*"))
    assert leftovers == []


def test_overwriting_is_atomic(tmp_path: Path) -> None:
    store = FilesystemAssetStore(tmp_path)
    store.save("a/b.png", DATA, "image/png")

    store.save("a/b.png", b"replacement", "image/png")

    assert store.load("a/b.png") == b"replacement"


@pytest.mark.parametrize(
    "key",
    ["../escape.png", "a/../../escape.png", "/absolute.png", "", "   ", "C:/x.png"],
)
def test_unsafe_keys_are_refused(key: str) -> None:
    with pytest.raises(UnsafePathError):
        validate_key(key)


def test_a_traversing_key_cannot_be_written(tmp_path: Path) -> None:
    store = FilesystemAssetStore(tmp_path / "root")

    with pytest.raises(UnsafePathError):
        store.save("../outside.png", DATA, "image/png")

    assert not (tmp_path / "outside.png").exists()


def test_backslashes_are_normalised() -> None:
    assert validate_key("a\\b\\c.png") == "a/b/c.png"


def test_reading_a_missing_asset_is_reported(tmp_path: Path) -> None:
    with pytest.raises(AssetStoreError, match="No asset stored"):
        FilesystemAssetStore(tmp_path).load("nothing/here.png")


def test_exists_is_false_for_unsafe_keys(tmp_path: Path) -> None:
    assert FilesystemAssetStore(tmp_path).exists("../escape.png") is False


def test_path_for_returns_none_when_absent(tmp_path: Path) -> None:
    assert FilesystemAssetStore(tmp_path).path_for("nothing.png") is None


def test_writable_creates_the_root(tmp_path: Path) -> None:
    store = FilesystemAssetStore(tmp_path / "assets")

    assert store.writable() is True
    assert (tmp_path / "assets").is_dir()


def test_attempt_keys_are_grouped_by_world_and_attempt() -> None:
    key = attempt_key("world-01", "abc-123", "original.png")

    assert key == "worlds/world-01/attempts/abc-123/original.png"
