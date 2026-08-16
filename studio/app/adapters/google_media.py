"""Google Gemini image + Veo video adapters for renderer validation.

The adapters are inert unless a Gemini key is configured. They intentionally keep
provider calls behind small request/response contracts so Studio can swap models
without rewriting scene logic.
"""

from __future__ import annotations

import base64
import io
import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageFile, ImageOps

from app.adapters.reference_images import ReferenceImage


class GoogleMediaError(RuntimeError):
    pass


@dataclass(frozen=True)
class GoogleImageRequest:
    prompt: str
    references: tuple[ReferenceImage, ...] = ()
    aspect_ratio: str = "16:9"
    image_size: str = "1K"


@dataclass(frozen=True)
class GoogleImageResult:
    data: bytes
    mime_type: str
    model: str


@dataclass(frozen=True)
class GoogleVideoRequest:
    prompt: str
    first_frame: bytes
    first_frame_mime: str = "image/jpeg"
    aspect_ratio: str = "16:9"
    resolution: str = "1080p"


@dataclass(frozen=True)
class GoogleVideoResult:
    data: bytes
    mime_type: str
    model: str
    operation_name: str | None


def _normalise_reference_for_gemini(ref: ReferenceImage) -> tuple[str, str]:
    """Return a clean base64 JPEG for Gemini's inline image input.

    The first production cast bootstrap exposed that some legacy JPEGs are truncated:
    browsers display them, but strict decoders and Gemini reject them. Pillow can salvage
    those streams when explicitly allowed. We immediately re-encode the decoded pixels
    to a fresh baseline RGB JPEG, so the provider never receives the damaged source bytes.

    This is a compatibility bridge for legacy references, not permission to keep creating
    damaged assets. New canonical files should pass strict decode before storage.
    """

    previous = ImageFile.LOAD_TRUNCATED_IMAGES
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    try:
        with Image.open(io.BytesIO(ref.data)) as source:
            source.load()
            image = ImageOps.exif_transpose(source)
            if image.mode in {"RGBA", "LA"} or (
                image.mode == "P" and "transparency" in image.info
            ):
                rgba = image.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")

            max_side = 2048
            if max(image.size) > max_side:
                image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

            output = io.BytesIO()
            image.save(
                output,
                format="JPEG",
                quality=92,
                optimize=True,
                progressive=False,
            )
    except Exception as exc:
        raise GoogleMediaError(f"Reference image {ref.name!r} cannot be decoded") from exc
    finally:
        ImageFile.LOAD_TRUNCATED_IMAGES = previous

    return base64.b64encode(output.getvalue()).decode("ascii"), "image/jpeg"


class GoogleImageClient:
    def __init__(self, *, api_key: str, model: str) -> None:
        if not api_key or not model:
            raise GoogleMediaError("Gemini image client requires explicit API key and model")
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(self, request: GoogleImageRequest) -> GoogleImageResult:
        inputs: list[dict[str, str]] = []
        for ref in request.references:
            data, mime_type = _normalise_reference_for_gemini(ref)
            inputs.append({"type": "image", "data": data, "mime_type": mime_type})
        inputs.append({"type": "text", "text": request.prompt})

        interaction = self._client.interactions.create(
            model=self._model,
            input=inputs,
            response_format={
                "type": "image",
                "aspect_ratio": request.aspect_ratio,
                "image_size": request.image_size,
            },
        )
        output = getattr(interaction, "output_image", None)
        if output is None or not getattr(output, "data", None):
            raise GoogleMediaError("Gemini returned no image")
        return GoogleImageResult(
            data=base64.b64decode(output.data),
            mime_type=getattr(output, "mime_type", None) or "image/png",
            model=self._model,
        )


class GoogleVideoClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        poll_seconds: float = 10.0,
        timeout_seconds: float = 900.0,
    ) -> None:
        if not api_key or not model:
            raise GoogleMediaError("Veo client requires explicit API key and model")
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._poll = max(1.0, poll_seconds)
        self._timeout = max(self._poll, timeout_seconds)

    def generate(self, request: GoogleVideoRequest) -> GoogleVideoResult:
        from google.genai import types

        image = types.Image(image_bytes=request.first_frame, mime_type=request.first_frame_mime)
        operation = self._client.models.generate_videos(
            model=self._model,
            prompt=request.prompt,
            image=image,
            config=types.GenerateVideosConfig(
                aspect_ratio=request.aspect_ratio,
                resolution=request.resolution,
            ),
        )
        operation_name = getattr(operation, "name", None)
        deadline = time.monotonic() + self._timeout
        while not operation.done:
            if time.monotonic() >= deadline:
                raise GoogleMediaError(f"Veo operation timed out after {self._timeout:.0f}s")
            time.sleep(self._poll)
            operation = self._client.operations.get(operation)

        response = getattr(operation, "response", None)
        videos = getattr(response, "generated_videos", None) if response is not None else None
        if not videos:
            raise GoogleMediaError("Veo returned no video")
        generated = videos[0]
        video = generated.video
        self._client.files.download(file=video)
        raw = getattr(video, "video_bytes", None)
        if raw is None:
            import tempfile

            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "generated.mp4"
                video.save(str(path))
                raw = path.read_bytes()
        return GoogleVideoResult(
            data=bytes(raw),
            mime_type="video/mp4",
            model=self._model,
            operation_name=str(operation_name) if operation_name else None,
        )
