"""Private browser for the vintage marketplace evidence cache."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

router = APIRouter()

DEFAULT_ROOT = Path("/home/ubuntu/shirtfaced-research/vintage-ebay-images")


def _root() -> Path:
    return Path(os.environ.get("VINTAGE_EVIDENCE_ROOT", str(DEFAULT_ROOT))).resolve()


def _safe_listing_dir(listing_id: str) -> Path:
    """The directory for one listing, or 400/404.

    Traversal is already impossible before any path work: ``isdigit()`` admits
    no slash, no dot, no separator, so ``root / listing_id`` is always a direct
    child of root and cannot escape it.

    Deliberately does NOT call ``resolve()``. A merged evidence root is built
    from symlinks to more than one collector's tree, and resolving follows those
    links out to their real location -- whose parents are not the root, so a
    resolve-then-compare check rejects every legitimate image. That is not
    hypothetical: it 400'd all 11,544 of them, the eBay ones included.
    """
    if not listing_id.isdigit():
        raise HTTPException(status_code=400, detail="Invalid listing id")
    candidate = _root() / listing_id
    if not candidate.is_dir():
        raise HTTPException(status_code=404, detail="Listing not found")
    return candidate


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _records() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    root = _root()
    manifest = _read_json(root / "manifest.json", {})
    rows: list[dict[str, Any]] = []
    if not root.is_dir():
        return manifest, rows
    for child in sorted(root.iterdir(), reverse=True):
        if not child.is_dir() or not child.name.isdigit():
            continue
        record = _read_json(child / "record.json", {})
        if not record:
            continue
        images = sorted(
            p.name
            for p in child.iterdir()
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        )
        rows.append(
            {
                **record,
                "listing_id": str(record.get("listing_id") or child.name),
                "images": [f"/vintage-evidence/image/{child.name}/{name}" for name in images],
            }
        )

    # Counts are derived from the walk just done, not read from manifest.json.
    # The file is written once by whichever collector ran last, so it went stale
    # the moment a second source appeared under the same root -- and a merged
    # root reported "0 with images" while serving eleven thousand of them.
    # These two are free here; ``failed`` stays from the file because it is
    # collector state that cannot be derived from what landed on disk.
    manifest = {
        **manifest,
        "listings_with_images": sum(1 for row in rows if row["images"]),
        "image_count": sum(len(row["images"]) for row in rows),
    }
    return manifest, rows


@router.get("/api/vintage-evidence")
def vintage_evidence_api() -> JSONResponse:
    manifest, rows = _records()
    return JSONResponse({"manifest": manifest, "records": rows})


@router.get("/vintage-evidence/image/{listing_id}/{filename}")
def vintage_evidence_image(listing_id: str, filename: str) -> FileResponse:
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    # Same reasoning: the filename is already constrained to a bare name above,
    # so joining it cannot escape the listing directory, and resolving would
    # again break on a symlinked root.
    path = _safe_listing_dir(listing_id) / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)


@router.get("/vintage-evidence")
def vintage_evidence_page() -> RedirectResponse:
    """Retired: the browser now lives in the Studio shell as VintageEvidenceBench.

    The URL was bookmarked, so it redirects rather than 404s. The JSON API and
    the image route below it are unchanged -- the React bench reads both.
    """
    return RedirectResponse("/", status_code=307)
