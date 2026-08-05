"""Which reference images get sent, and in what order.

The rule this file protects: ``locked/`` is the benchmark and is never displaced by
``approved/``. If the pipeline's own output could crowd out the anchor, the anchor
stops being one — each frame would train on the last frame's drift, and the world
would slide away from its standard one plausible step at a time.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import ClassVar

import pytest
from PIL import Image

from app.adapters.image_generation import (
    ImageGenerationRequest,
    OpenAIImageGenerationClient,
)
from app.adapters.reference_images import (
    MAX_REFERENCE_BYTES,
    FilesystemReferenceImageStore,
    NoReferenceImageStore,
    ReferenceImageError,
)


def _write_image(path: Path, name: str, colour: tuple[int, int, int] = (10, 20, 30)) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    file = path / name
    buffer = BytesIO()
    Image.new("RGB", (8, 8), colour).save(buffer, format="PNG")
    file.write_bytes(buffer.getvalue())
    return file


@pytest.fixture
def worlds_root(tmp_path: Path) -> Path:
    return tmp_path / "worlds"


def _store(worlds_root: Path) -> FilesystemReferenceImageStore:
    return FilesystemReferenceImageStore(worlds_root)


# --- what gets loaded ---------------------------------------------------------------


def test_a_world_with_no_references_loads_nothing(worlds_root: Path) -> None:
    """Not an error. A world with no references generates from text, as before."""
    assert _store(worlds_root).load("world-01", limit=4) == []


def test_locked_images_load(worlds_root: Path) -> None:
    _write_image(worlds_root / "world-01" / "references" / "locked", "seed-01.png")
    _write_image(worlds_root / "world-01" / "references" / "locked", "seed-02.png")

    images = _store(worlds_root).load("world-01", limit=4)

    assert [image.name for image in images] == ["seed-01.png", "seed-02.png"]
    assert all(image.locked for image in images)
    assert all(image.mime_type == "image/png" for image in images)


def test_non_images_are_ignored(worlds_root: Path) -> None:
    """A README beside the images must not be uploaded as one."""
    locked = worlds_root / "world-01" / "references" / "locked"
    _write_image(locked, "seed-01.png")
    (locked / "NOTES.md").write_text("not an image", encoding="utf-8")

    images = _store(worlds_root).load("world-01", limit=4)

    assert [image.name for image in images] == ["seed-01.png"]


def test_the_order_is_stable(worlds_root: Path) -> None:
    """Two identical requests are only comparable if the reference set is identical."""
    locked = worlds_root / "world-01" / "references" / "locked"
    for name in ("seed-03.png", "seed-01.png", "seed-02.png"):
        _write_image(locked, name)

    first = [i.name for i in _store(worlds_root).load("world-01", limit=8)]
    second = [i.name for i in _store(worlds_root).load("world-01", limit=8)]

    assert first == second == ["seed-01.png", "seed-02.png", "seed-03.png"]


# --- locked never loses its place ---------------------------------------------------


def test_locked_comes_before_approved(worlds_root: Path) -> None:
    _write_image(worlds_root / "world-01" / "references" / "locked", "seed-01.png")
    _write_image(worlds_root / "world-01" / "references" / "approved", "frame-01.png")

    images = _store(worlds_root).load("world-01", limit=4)

    assert images[0].name == "seed-01.png"
    assert images[0].locked is True
    assert images[1].locked is False


def test_approved_frames_never_displace_locked_ones(worlds_root: Path) -> None:
    """The anchor is not negotiable, even when the limit is tight."""
    locked = worlds_root / "world-01" / "references" / "locked"
    approved = worlds_root / "world-01" / "references" / "approved"
    for index in range(3):
        _write_image(locked, f"seed-{index:02d}.png")
    for index in range(5):
        _write_image(approved, f"frame-{index:02d}.png")

    images = _store(worlds_root).load("world-01", limit=3)

    assert len(images) == 3
    assert all(image.locked for image in images)


def test_the_limit_is_respected(worlds_root: Path) -> None:
    locked = worlds_root / "world-01" / "references" / "locked"
    for index in range(10):
        _write_image(locked, f"seed-{index:02d}.png")

    assert len(_store(worlds_root).load("world-01", limit=4)) == 4


def test_a_zero_limit_disables_references(worlds_root: Path) -> None:
    _write_image(worlds_root / "world-01" / "references" / "locked", "seed-01.png")

    assert _store(worlds_root).load("world-01", limit=0) == []


# --- unusable files -----------------------------------------------------------------


def test_an_empty_file_is_rejected_by_name(worlds_root: Path) -> None:
    locked = worlds_root / "world-01" / "references" / "locked"
    locked.mkdir(parents=True)
    (locked / "broken.png").write_bytes(b"")

    with pytest.raises(ReferenceImageError, match=r"broken\.png"):
        _store(worlds_root).load("world-01", limit=4)


def test_an_oversized_file_is_rejected_before_the_call(worlds_root: Path) -> None:
    """A local error naming the file beats a provider 400 mid-run."""
    locked = worlds_root / "world-01" / "references" / "locked"
    locked.mkdir(parents=True)
    (locked / "huge.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * MAX_REFERENCE_BYTES)

    with pytest.raises(ReferenceImageError, match=r"huge\.png"):
        _store(worlds_root).load("world-01", limit=4)


# --- which endpoint gets called -----------------------------------------------------


class _RecordingImages:
    def __init__(self) -> None:
        self.generate_calls: list[dict[str, object]] = []
        self.edit_calls: list[dict[str, object]] = []

    def _response(self) -> object:
        buffer = BytesIO()
        Image.new("RGB", (8, 8), (1, 2, 3)).save(buffer, format="PNG")
        import base64

        class _Datum:
            b64_json = base64.b64encode(buffer.getvalue()).decode()

        class _Response:
            id = "resp-test"
            data: ClassVar[list[object]] = [_Datum()]

        return _Response()

    def generate(self, **kwargs: object) -> object:
        self.generate_calls.append(kwargs)
        return self._response()

    def edit(self, **kwargs: object) -> object:
        self.edit_calls.append(kwargs)
        return self._response()


class _RecordingClient:
    def __init__(self) -> None:
        self.images = _RecordingImages()


def test_without_references_the_generate_endpoint_is_used() -> None:
    client = _RecordingClient()
    OpenAIImageGenerationClient(client=client, model="gpt-image-2", timeout_seconds=5).generate(
        ImageGenerationRequest(prompt="p", model="gpt-image-2", size="1024x1024", quality="high")
    )

    assert len(client.images.generate_calls) == 1
    assert client.images.edit_calls == []


def test_with_references_the_edit_endpoint_is_used(worlds_root: Path) -> None:
    """Text can describe a look. Only the edits endpoint can carry one."""
    _write_image(worlds_root / "world-01" / "references" / "locked", "seed-01.png")
    references = _store(worlds_root).load("world-01", limit=4)

    client = _RecordingClient()
    OpenAIImageGenerationClient(client=client, model="gpt-image-2", timeout_seconds=5).generate(
        ImageGenerationRequest(
            prompt="p",
            model="gpt-image-2",
            size="1024x1024",
            quality="high",
            reference_images=tuple(references),
        )
    )

    assert client.images.generate_calls == []
    assert len(client.images.edit_calls) == 1
    sent = client.images.edit_calls[0]["image"]
    assert isinstance(sent, list)
    assert len(sent) == 1
    assert sent[0][0] == "seed-01.png"
    assert sent[0][2] == "image/png"


def test_the_null_store_sends_nothing() -> None:
    assert NoReferenceImageStore().load("world-01", limit=8) == []
