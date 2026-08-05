"""Image generation adapters.

Services depend on the :class:`ImageGenerationClient` protocol, never on the OpenAI
SDK. Generation and review are separate operations and separate adapters.

Every provider failure is classified, because retry has to know the difference
between a timeout worth repeating and a refusal that will never succeed.

Tests must never construct the OpenAI client.
"""

from __future__ import annotations

import base64
import binascii
import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Protocol, runtime_checkable

from app.adapters.reference_images import ReferenceImage
from app.domain.enums import FailureCode
from app.domain.errors import StudioError

logger = logging.getLogger(__name__)

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
WEBP_PREFIX = b"RIFF"

MIME_TYPES = {"png": "image/png", "jpeg": "image/jpeg", "jpg": "image/jpeg", "webp": "image/webp"}


class ImageGenerationError(StudioError):
    """Generation failed, with the reason classified."""

    def __init__(self, message: str, code: FailureCode = FailureCode.PROVIDER_ERROR) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ImageGenerationRequest:
    """One image request."""

    prompt: str
    model: str
    size: str
    quality: str
    output_format: str = "png"
    # The images the frame should look like it came from. Empty means text alone,
    # which is what produced four different casts for the same shot.
    reference_images: tuple[ReferenceImage, ...] = ()

    @property
    def has_references(self) -> bool:
        return bool(self.reference_images)


@dataclass(frozen=True)
class GeneratedImage:
    """The bytes and everything worth recording about how they were made."""

    data: bytes
    mime_type: str
    model: str
    size: str
    quality: str
    output_format: str
    provider_request_id: str | None = None


@runtime_checkable
class ImageGenerationClient(Protocol):
    """Produces one image."""

    def generate(self, request: ImageGenerationRequest) -> GeneratedImage: ...


def detect_mime_type(data: bytes) -> str | None:
    """The image type from its magic bytes, or ``None`` if it is not an image.

    The provider states a format, but bytes that are not an image must never be
    stored as one.
    """
    if data.startswith(PNG_MAGIC):
        return "image/png"
    if data.startswith(JPEG_MAGIC):
        return "image/jpeg"
    if data.startswith(WEBP_PREFIX) and data[8:12] == b"WEBP":
        return "image/webp"
    return None


class FakeImageGenerationClient:
    """A deterministic generator that costs nothing and never leaves the process.

    It draws a real image so the whole pipeline — hashing, thumbnailing, storage,
    serving — is exercised for real. The same request always produces the same bytes.
    """

    def __init__(self, *, fail_with: ImageGenerationError | None = None) -> None:
        self._fail_with = fail_with
        self.requests: list[ImageGenerationRequest] = []

    def generate(self, request: ImageGenerationRequest) -> GeneratedImage:
        self.requests.append(request)
        if self._fail_with is not None:
            raise self._fail_with

        width, height = _parse_size(request.size)
        data = _draw_placeholder(width, height, request.prompt)

        return GeneratedImage(
            data=data,
            mime_type="image/png",
            model=request.model or "fake-image-model",
            size=request.size,
            quality=request.quality,
            output_format="png",
            provider_request_id="fake-request",
        )


def _parse_size(size: str) -> tuple[int, int]:
    try:
        width, height = (int(part) for part in size.lower().split("x", 1))
    except ValueError:
        return 1536, 1024
    return max(1, width), max(1, height)


def _draw_placeholder(width: int, height: int, prompt: str) -> bytes:
    """A deterministic image derived from the prompt.

    Two different prompts produce visibly different images, so a test that asserts an
    image changed is asserting something real.
    """
    import hashlib
    from io import BytesIO

    from PIL import Image, ImageDraw

    digest = hashlib.sha256(prompt.encode("utf-8")).digest()
    background = (digest[0] // 3 + 20, digest[1] // 3 + 20, digest[2] // 3 + 30)

    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    step = max(24, width // 24)
    for index in range(0, width, step):
        shade = digest[(index // step) % len(digest)]
        draw.line(
            [(index, 0), (index + step // 2, height)],
            fill=(shade, shade // 2 + 40, 60),
            width=max(1, step // 8),
        )
    draw.rectangle(
        [width // 8, height // 8, width - width // 8, height - height // 8],
        outline=(240, 240, 240),
        width=max(2, width // 300),
    )

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class OpenAIImageGenerationClient:
    """Image generation through the OpenAI images interface."""

    def __init__(self, client: Any, model: str, timeout_seconds: float) -> None:
        if not model:
            raise ImageGenerationError(
                "OPENAI_IMAGE_MODEL is not set. Configure it explicitly: guessing a "
                "model name can cause unexpected cost.",
                FailureCode.CONFIGURATION,
            )
        self._client = client
        self._model = model
        self._timeout = timeout_seconds

    def generate(self, request: ImageGenerationRequest) -> GeneratedImage:
        try:
            if request.has_references:
                # The edits endpoint is the only way to put an image in front of the
                # model. Text can describe a look; only this can carry one.
                logger.info(
                    "Generating with %d reference image(s): %s",
                    len(request.reference_images),
                    ", ".join(image.name for image in request.reference_images),
                )
                response = self._client.images.edit(
                    model=self._model,
                    image=[
                        (image.name, BytesIO(image.data), image.mime_type)
                        for image in request.reference_images
                    ],
                    prompt=request.prompt,
                    size=request.size,
                    quality=request.quality,
                    n=1,
                    timeout=self._timeout,
                )
            else:
                response = self._client.images.generate(
                    model=self._model,
                    prompt=request.prompt,
                    size=request.size,
                    quality=request.quality,
                    n=1,
                    timeout=self._timeout,
                )
        except Exception as error:
            raise _classify(error) from error

        data = _first_image_bytes(response)
        mime_type = detect_mime_type(data)
        if mime_type is None:
            raise ImageGenerationError(
                "The provider returned data that is not a recognisable image.",
                FailureCode.INVALID_IMAGE,
            )

        request_id = getattr(response, "id", None)
        if request_id:
            # Provider request IDs are logged for support; payloads are not.
            logger.info("Image response %s from %s", request_id, self._model)

        return GeneratedImage(
            data=data,
            mime_type=mime_type,
            model=self._model,
            size=request.size,
            quality=request.quality,
            output_format=mime_type.removeprefix("image/"),
            provider_request_id=str(request_id) if request_id else None,
        )


def _first_image_bytes(response: Any) -> bytes:
    entries = getattr(response, "data", None)
    if not entries:
        raise ImageGenerationError("The provider returned no image.", FailureCode.INVALID_IMAGE)

    encoded = getattr(entries[0], "b64_json", None)
    if not encoded:
        # A temporary URL is not durable storage, and the specification requires the
        # exact bytes to be kept.
        raise ImageGenerationError(
            "The provider returned no image data. Base64 output is required so the "
            "exact bytes can be stored.",
            FailureCode.INVALID_IMAGE,
        )

    try:
        return base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ImageGenerationError(
            "The provider returned image data that could not be decoded.",
            FailureCode.INVALID_IMAGE,
        ) from error


def _classify(error: Exception) -> ImageGenerationError:
    """Map a provider exception onto a failure code.

    Matching is on the exception's class name so the SDK's exception hierarchy is not
    imported into this module.
    """
    name = type(error).__name__
    text = str(error)

    if "Timeout" in name:
        return ImageGenerationError(
            f"The image request timed out: {text}", FailureCode.PROVIDER_TIMEOUT
        )
    if name in {"AuthenticationError", "PermissionDeniedError", "NotFoundError"}:
        return ImageGenerationError(
            f"The image request was refused and will not succeed on retry: {text}",
            FailureCode.CONFIGURATION,
        )
    if name in {"BadRequestError", "UnprocessableEntityError"}:
        return ImageGenerationError(
            f"The provider rejected the prompt or settings: {text}",
            FailureCode.PROVIDER_REFUSED,
        )
    return ImageGenerationError(f"The image request failed: {text}", FailureCode.PROVIDER_ERROR)
