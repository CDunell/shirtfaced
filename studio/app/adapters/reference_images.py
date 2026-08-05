"""Loading the reference images a world is measured against.

`WORLD.md` names a Locked Reference as the visual benchmark, but until now that
benchmark only ever reached the planner as prose. Prose can ask for warm sodium light
and 35mm grain; it cannot ask for *these faces, this car, this grade*. Two runs of the
same shot produced four different people both times, because nothing carried across
except words.

This reads the images themselves so they can be sent to the image model.

Two directories, and the order matters:

* ``locked/`` — the benchmark. A fixed target the pipeline never writes to.
* ``approved/`` — frames this pipeline produced and the owner approved, for continuity
  between one night's frames and the next.

``locked/`` always goes first and is never crowded out, because the anchor losing its
place to the pipeline's own output is exactly the drift the split exists to prevent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from app.domain.errors import StudioError

logger = logging.getLogger(__name__)

LOCKED_DIRECTORY = "locked"
APPROVED_DIRECTORY = "approved"
REFERENCES_DIRECTORY = "references"

SUFFIX_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

# The provider rejects anything larger. Checked here so an oversized file is a clear
# local error naming the file, rather than a 400 halfway through a paid run.
MAX_REFERENCE_BYTES = 50 * 1024 * 1024


class ReferenceImageError(StudioError):
    """A reference image could not be read or is unusable."""


@dataclass(frozen=True)
class ReferenceImage:
    """One reference image, ready to send."""

    name: str
    data: bytes
    mime_type: str
    locked: bool

    @property
    def byte_size(self) -> int:
        return len(self.data)


@runtime_checkable
class ReferenceImageStore(Protocol):
    """Supplies the reference images for a world."""

    def load(self, world_slug: str, *, limit: int) -> list[ReferenceImage]: ...


class FilesystemReferenceImageStore:
    """Reference images under ``<worlds_root>/<slug>/references/``."""

    def __init__(self, worlds_root: Path) -> None:
        self._root = Path(worlds_root)

    def directory(self, world_slug: str, kind: str) -> Path:
        return self._root / world_slug / REFERENCES_DIRECTORY / kind

    def _read_directory(self, path: Path, *, locked: bool) -> list[ReferenceImage]:
        if not path.is_dir():
            return []

        images: list[ReferenceImage] = []
        # Sorted so the set sent to the model is stable between runs: an unstable
        # reference set makes two identical requests incomparable.
        for file in sorted(path.iterdir()):
            if not file.is_file():
                continue
            mime = SUFFIX_MIME.get(file.suffix.lower())
            if mime is None:
                logger.debug("Skipping %s: not an image the provider accepts", file.name)
                continue

            size = file.stat().st_size
            if size > MAX_REFERENCE_BYTES:
                raise ReferenceImageError(
                    f"{file.name} is {size:,} bytes, over the {MAX_REFERENCE_BYTES:,} "
                    "byte limit for a reference image."
                )
            if size == 0:
                raise ReferenceImageError(f"{file.name} is empty.")

            images.append(
                ReferenceImage(
                    name=file.name, data=file.read_bytes(), mime_type=mime, locked=locked
                )
            )
        return images

    def load(self, world_slug: str, *, limit: int) -> list[ReferenceImage]:
        """The reference images for a world, locked first, capped at ``limit``.

        Locked images are never displaced by approved ones. If the locked set alone
        exceeds the limit it is truncated, and nothing approved is sent: the benchmark
        outranks continuity, because continuity with a drifting frame is not worth
        having.
        """
        if limit <= 0:
            return []

        locked = self._read_directory(self.directory(world_slug, LOCKED_DIRECTORY), locked=True)
        if len(locked) >= limit:
            if len(locked) > limit:
                logger.info(
                    "Sending %d of %d locked references; the limit leaves no room for "
                    "approved frames",
                    limit,
                    len(locked),
                )
            return locked[:limit]

        approved = self._read_directory(
            self.directory(world_slug, APPROVED_DIRECTORY), locked=False
        )
        # Newest approved frames first: they are the closest thing to the current look.
        approved.reverse()
        return locked + approved[: limit - len(locked)]


class NoReferenceImageStore:
    """No reference images. Used where sending them is not wanted."""

    def load(self, world_slug: str, *, limit: int) -> list[ReferenceImage]:
        return []


__all__ = [
    "APPROVED_DIRECTORY",
    "LOCKED_DIRECTORY",
    "MAX_REFERENCE_BYTES",
    "FilesystemReferenceImageStore",
    "NoReferenceImageStore",
    "ReferenceImage",
    "ReferenceImageError",
    "ReferenceImageStore",
]
