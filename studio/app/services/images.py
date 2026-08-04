"""Image inspection and thumbnailing.

Pillow is used only here, where local image metadata and thumbnails genuinely require
it.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from app.adapters.image_generation import ImageGenerationError
from app.domain.enums import FailureCode

THUMBNAIL_MAX_EDGE = 512
THUMBNAIL_MIME_TYPE = "image/webp"
THUMBNAIL_QUALITY = 80


@dataclass(frozen=True)
class ImageDimensions:
    width: int
    height: int


def measure(data: bytes) -> ImageDimensions:
    """Read an image's dimensions, rejecting anything that will not decode."""
    try:
        with Image.open(BytesIO(data)) as image:
            width, height = image.size
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise ImageGenerationError(
            "The generated data could not be decoded as an image.",
            FailureCode.INVALID_IMAGE,
        ) from error

    return ImageDimensions(width=width, height=height)


def make_thumbnail(
    data: bytes, max_edge: int = THUMBNAIL_MAX_EDGE
) -> tuple[bytes, ImageDimensions]:
    """A smaller copy for lists and history, in WebP.

    Aspect ratio is preserved and the image is never enlarged.
    """
    try:
        with Image.open(BytesIO(data)) as image:
            converted = image.convert("RGB")
            converted.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            converted.save(buffer, format="WEBP", quality=THUMBNAIL_QUALITY, method=4)
            size = converted.size
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise ImageGenerationError(
            "A thumbnail could not be produced from the generated image.",
            FailureCode.INVALID_IMAGE,
        ) from error

    return buffer.getvalue(), ImageDimensions(width=size[0], height=size[1])
