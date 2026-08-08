"""Serving the archive's own artwork files.

A composed design that uses a texture or a piece of drawn flash refers to it:

    <image href="/archive/flash/illustration_part_wolf_0001.jpg" .../>

Nothing served those. `/assets/{uuid}` returns *generated* images recorded in the
database, and the archive's files are neither generated nor recorded there --
they are checked into the repository. So every raster element in every composed
design was a broken reference, in the browser and in production, while the
measurements happily reported them as used.

The alternative was embedding each one as a data URI. That keeps a design
self-contained, which a printer will eventually want, and it also turns a
200KB photograph into 270KB of base64 inside every design that touches it.
References stay small and stay deterministic; inlining is a job for print
export, where it is worth the size.

Path handling is the whole risk here, because unlike the asset store the path
does come from the request. Anything that does not resolve to a real file
underneath the archive root is refused before it is opened.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response, status

router = APIRouter(prefix="/archive", tags=["archive"])

ARCHIVE_ROOT = Path(__file__).resolve().parents[3] / "assets"

# The archive holds artwork and its manifests. Serving anything else from a
# repository directory over HTTP is how a licence file or a key gets published.
SERVABLE = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff"}

# Checked into the repository and addressed by a path that names its content, so
# a given URL is the same bytes for as long as the file is unchanged. Cached for
# a day rather than forever, because unlike a generated asset it *can* change.
CACHE_CONTROL = "public, max-age=86400"


@router.get("/{path:path}", summary="Fetch an archive artwork file")
def get_archive_file(path: str) -> Response:
    """One file from `assets/`, by its path relative to that folder."""
    candidate = (ARCHIVE_ROOT / path).resolve()

    # Resolved before comparing, so `..` and symlinks are already collapsed.
    # Checking the raw string instead would let `flash/../../.env` through.
    if not candidate.is_relative_to(ARCHIVE_ROOT.resolve()):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such file")
    if candidate.suffix.lower() not in SERVABLE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such file")
    if not candidate.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such file")

    media_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
    return Response(
        content=candidate.read_bytes(),
        media_type=media_type,
        headers={"Cache-Control": CACHE_CONTROL},
    )
