"""Asset storage.

Domain services depend on :class:`AssetStore`, never on a filesystem path, so Oracle
Object Storage can replace the filesystem later without touching them.

Keys are relative and POSIX-style. The database stores the key; the store decides
where the bytes live.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol, runtime_checkable

from app.domain.errors import StudioError, UnsafePathError


class AssetStoreError(StudioError):
    """Storage failed."""


@dataclass(frozen=True)
class StoredAsset:
    """What was written."""

    key: str
    sha256: str
    byte_size: int
    mime_type: str


@runtime_checkable
class AssetStore(Protocol):
    """Durable storage for generated images."""

    def save(self, key: str, data: bytes, mime_type: str) -> StoredAsset: ...

    def load(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...

    def path_for(self, key: str) -> Path | None:
        """A local path when one exists, for serving directly. ``None`` otherwise."""
        ...


def validate_key(key: str) -> str:
    """Reject anything that is not a plain relative key.

    Keys are built from database identifiers rather than user input, but this is the
    boundary that writes files, so it does not take that on trust.
    """
    cleaned = key.strip().replace("\\", "/")
    if not cleaned:
        raise UnsafePathError("An asset key must not be empty.")
    if cleaned.startswith("/") or ":" in cleaned:
        raise UnsafePathError(f"{key!r} is not a relative asset key.")
    normalised = PurePosixPath(cleaned)
    if ".." in normalised.parts:
        raise UnsafePathError(f"{key!r} must not contain relative path segments.")
    # PurePosixPath drops harmless "." segments; ".." is the one that matters.
    return normalised.as_posix()


class FilesystemAssetStore:
    """Stores assets under a root directory.

    Writes are atomic: a temporary file in the destination directory is fsynced and
    then renamed, so a crash leaves either the old file or the new one, never a
    half-written image.
    """

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    @property
    def root(self) -> Path:
        return self._root

    def _resolve(self, key: str) -> Path:
        destination = (self._root / validate_key(key)).resolve()
        if self._root not in destination.parents:
            raise UnsafePathError(f"{key!r} resolves outside the asset root.")
        return destination

    def save(self, key: str, data: bytes, mime_type: str) -> StoredAsset:
        destination = self._resolve(key)
        destination.parent.mkdir(parents=True, exist_ok=True)

        try:
            handle, temporary_name = tempfile.mkstemp(
                dir=destination.parent, prefix=".partial-", suffix=".tmp"
            )
            try:
                with os.fdopen(handle, "wb") as file:
                    file.write(data)
                    file.flush()
                    os.fsync(file.fileno())
                os.replace(temporary_name, destination)
            except BaseException:
                Path(temporary_name).unlink(missing_ok=True)
                raise
        except OSError as error:
            raise AssetStoreError(f"Could not write {key!r}: {error}") from error

        return StoredAsset(
            key=validate_key(key),
            sha256=hashlib.sha256(data).hexdigest(),
            byte_size=len(data),
            mime_type=mime_type,
        )

    def load(self, key: str) -> bytes:
        destination = self._resolve(key)
        if not destination.is_file():
            raise AssetStoreError(f"No asset stored at {key!r}.")
        try:
            return destination.read_bytes()
        except OSError as error:
            raise AssetStoreError(f"Could not read {key!r}: {error}") from error

    def exists(self, key: str) -> bool:
        try:
            return self._resolve(key).is_file()
        except UnsafePathError:
            return False

    def path_for(self, key: str) -> Path | None:
        destination = self._resolve(key)
        return destination if destination.is_file() else None

    def writable(self) -> bool:
        """Whether the root can be written to. Used by readiness checks."""
        try:
            self._root.mkdir(parents=True, exist_ok=True)
            probe = self._root / ".write-probe"
            probe.write_bytes(b"")
            probe.unlink()
        except OSError:
            return False
        return True


def attempt_key(world_slug: str, attempt_id: str, name: str) -> str:
    """The key for one of an attempt's files."""
    return validate_key(f"worlds/{world_slug}/attempts/{attempt_id}/{name}")


def design_attempt_key(library: str, concept_number: int, attempt_id: str, name: str) -> str:
    """The key for one of a design attempt's files.

    The library is part of the namespace because concept numbers are only
    unique within a library: tee concept 5 and headwear H05 must never share a
    directory.
    """
    return validate_key(f"designs/{library}/{concept_number:03d}/attempts/{attempt_id}/{name}")
