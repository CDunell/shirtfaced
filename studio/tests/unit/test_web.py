"""Serving the built interface."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app
from app.web import mount_interface


def _build_dist(root: Path) -> Path:
    """A stand-in for a Vite build.

    Bundles go in ``static/``, not ``assets/``: ``/assets`` serves generated images
    from the API, and a bundle at ``/assets/index-*.js`` would be shadowed by that
    route. Vite's ``build.assetsDir`` is set to match.
    """
    dist = root / "dist"
    (dist / "static").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><div id=root></div>", encoding="utf-8")
    (dist / "static" / "app.js").write_text("console.log('studio')", encoding="utf-8")
    return dist


def test_absent_build_is_not_an_error(tmp_path: Path) -> None:
    """A developer running the Vite dev server has no dist directory."""
    assert mount_interface(FastAPI(), tmp_path / "dist") is False


def test_build_is_mounted_when_present(tmp_path: Path) -> None:
    assert mount_interface(FastAPI(), _build_dist(tmp_path)) is True


def test_interface_is_served_at_the_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dist = _build_dist(tmp_path)
    monkeypatch.setenv("WEB_DIST_ROOT", str(dist))

    with TestClient(create_app()) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "id=root" in response.text


def test_deep_links_return_the_app_shell(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A single-page application must not 404 on its own routes."""
    dist = _build_dist(tmp_path)
    monkeypatch.setenv("WEB_DIST_ROOT", str(dist))

    with TestClient(create_app()) as client:
        response = client.get("/worlds/world-01")

    assert response.status_code == 200
    assert "id=root" in response.text


def test_api_routes_are_not_shadowed_by_the_root_mount(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dist = _build_dist(tmp_path)
    monkeypatch.setenv("WEB_DIST_ROOT", str(dist))

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_built_bundles_are_served_from_static(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dist = _build_dist(tmp_path)
    monkeypatch.setenv("WEB_DIST_ROOT", str(dist))

    with TestClient(create_app()) as client:
        response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "studio" in response.text
