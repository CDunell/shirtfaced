"""Reading canonical Markdown documents.

Responsible for loading files, hashing them and refusing to read outside the worlds
directory. It never calls OpenAI and holds no domain knowledge about what the
documents mean.

Writes are atomic and validated by the caller before they reach here: a temporary
sibling on the same filesystem is fsynced and renamed, so a crash leaves either the
old document or the new one, never half of either.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.domain.errors import StudioError, UnsafePathError, WorldNotFoundError


class MarkdownWriteFailed(StudioError):
    """A canonical document could not be written."""


WORLD_DOCUMENT = "WORLD.md"
CONTINUITY_DOCUMENT = "CONTINUITY.md"
SHOTLIST_DOCUMENT = "SHOTLIST.md"

REQUIRED_DOCUMENTS = (WORLD_DOCUMENT, CONTINUITY_DOCUMENT, SHOTLIST_DOCUMENT)


def sha256_hex(text: str) -> str:
    """SHA-256 of the document text.

    Hashing the decoded text rather than the raw bytes means a line-ending change
    alone does not read as a content change, which matters on Windows.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Document:
    """A loaded canonical document."""

    name: str
    path: Path
    text: str
    sha256: str


class MarkdownStore:
    """Reads world documents from a fixed root directory."""

    def __init__(self, worlds_root: Path) -> None:
        self._root = worlds_root.resolve()

    @property
    def root(self) -> Path:
        return self._root

    def world_directory(self, slug: str) -> Path:
        """Resolve a world directory, refusing anything outside the root.

        The slug reaches this from a URL, so ``../`` and absolute paths are rejected
        rather than normalised.
        """
        if not slug or slug in {".", ".."} or "/" in slug or "\\" in slug:
            raise UnsafePathError(f"{slug!r} is not a valid world slug.")

        candidate = (self._root / slug).resolve()
        if candidate != self._root and self._root not in candidate.parents:
            raise UnsafePathError(f"{slug!r} resolves outside the worlds directory.")
        return candidate

    def read_document(self, slug: str, name: str) -> Document:
        """Read one document from a world directory."""
        directory = self.world_directory(slug)
        path = (directory / name).resolve()
        if path.parent != directory:
            raise UnsafePathError(f"{name!r} resolves outside the world directory.")
        if not path.is_file():
            raise WorldNotFoundError(f"{name} is missing from {directory}.")

        text = path.read_text(encoding="utf-8")
        return Document(name=name, path=path, text=text, sha256=sha256_hex(text))

    def read_world_documents(self, slug: str) -> dict[str, Document]:
        """Read all three canonical documents."""
        directory = self.world_directory(slug)
        if not directory.is_dir():
            raise WorldNotFoundError(f"No world directory at {directory}.")
        return {name: self.read_document(slug, name) for name in REQUIRED_DOCUMENTS}

    def write_documents(self, slug: str, documents: dict[str, str]) -> dict[str, Document]:
        """Replace one or more documents atomically.

        Each candidate is written to a temporary sibling, fsynced and renamed. The
        renames happen one after another rather than as a single transaction — the
        filesystem offers nothing stronger — so the caller validates every candidate
        before calling this, and reports reconciliation if a later rename fails.
        """
        directory = self.world_directory(slug)
        if not directory.is_dir():
            raise WorldNotFoundError(f"No world directory at {directory}.")

        staged: list[tuple[Path, Path]] = []
        try:
            for name, text in documents.items():
                target = (directory / name).resolve()
                if target.parent != directory:
                    raise UnsafePathError(f"{name!r} resolves outside the world directory.")

                handle, temporary_name = tempfile.mkstemp(
                    dir=directory, prefix=f".{name}.", suffix=".tmp"
                )
                with os.fdopen(handle, "w", encoding="utf-8", newline="") as file:
                    file.write(text)
                    file.flush()
                    os.fsync(file.fileno())
                staged.append((Path(temporary_name), target))

            for temporary, target in staged:
                os.replace(temporary, target)
        except OSError as error:
            for temporary, _ in staged:
                temporary.unlink(missing_ok=True)
            raise MarkdownWriteFailed(f"Could not write the world documents: {error}") from error

        return {name: self.read_document(slug, name) for name in documents}

    def snapshot(self, slug: str) -> dict[str, str]:
        """The current text of every canonical document, for restoring after a failure."""
        return {name: document.text for name, document in self.read_world_documents(slug).items()}

    def available_slugs(self) -> list[str]:
        """World directories that contain all three documents."""
        if not self._root.is_dir():
            return []
        return sorted(
            entry.name
            for entry in self._root.iterdir()
            if entry.is_dir() and all((entry / name).is_file() for name in REQUIRED_DOCUMENTS)
        )
