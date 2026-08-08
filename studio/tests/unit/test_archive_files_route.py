"""Serving the archive's own artwork over HTTP.

Composed designs refer to their raster parts by path. Nothing served those:
`/assets/{uuid}` returns generated images recorded in the database, and these
are checked into the repository instead, so every raster element in every
composed design was a broken reference while the measurements reported them as
used.

Unlike the asset store, the path here comes from the request. That is the whole
risk and it is what most of these cover.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.routes.archive_files import get_archive_file


def test_a_real_artwork_file_is_served() -> None:
    response = get_archive_file("symbols/symbol_flame_0001.svg")

    assert response.status_code == 200
    assert response.body
    assert "svg" in response.media_type


@pytest.mark.parametrize(
    "path",
    [
        "../.env",
        "../../.env",
        "flash/../../.env",
        "..\\.env",
        "/etc/passwd",
        "../studio/app/config.py",
    ],
)
def test_nothing_outside_the_archive_can_be_reached(path: str) -> None:
    """The path is resolved before it is compared.

    Checking the raw string would let `flash/../../.env` through, because it
    starts with a folder that really is inside the archive.
    """
    with pytest.raises(HTTPException) as caught:
        get_archive_file(path)

    assert caught.value.status_code == 404


def test_only_artwork_is_servable() -> None:
    """The archive holds manifests beside the artwork.

    Serving whatever happens to sit in a repository directory is how a licence
    file, a manifest or a key ends up published.
    """
    with pytest.raises(HTTPException):
        get_archive_file("symbols/library.json")


def test_a_missing_file_is_a_404_not_a_crash() -> None:
    with pytest.raises(HTTPException) as caught:
        get_archive_file("flash/no_such_artwork_0001.jpg")

    assert caught.value.status_code == 404


def test_composed_designs_point_at_this_route() -> None:
    """The reference and the route have to agree, or every raster is broken.

    They did not: source_file is repository-relative and begins `assets/`, and
    emitting that verbatim pointed at the generated-image store, which addresses
    by UUID and answered every one of them with a 404.
    """
    from app.archive.assemble import _archive_url

    assert _archive_url("assets/flash/wolf.jpg") == "archive/flash/wolf.jpg"
    assert _archive_url("assets\\flash\\wolf.jpg") == "archive/flash/wolf.jpg"
