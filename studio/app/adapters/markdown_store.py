"""Reading canonical Markdown documents.

Responsible for loading files, hashing them and refusing to read outside the worlds
directory. It never calls OpenAI and holds no domain knowledge about what the
documents mean.

Writing is added by the phase that first changes a document; Version 1 reads only.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from app.domain.errors import UnsafePathError, WorldNotFoundError

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

    def available_slugs(self) -> list[str]:
        """World directories that contain all three documents."""
        if not self._root.is_dir():
            return []
        return sorted(
            entry.name
            for entry in self._root.iterdir()
            if entry.is_dir() and all((entry / name).is_file() for name in REQUIRED_DOCUMENTS)
        )
