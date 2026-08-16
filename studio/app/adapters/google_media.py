"""Google Gemini image + Veo video adapters for renderer validation.

The adapters are inert unless a Gemini key is configured. They intentionally keep
provider calls behind small request/response contracts so Studio can swap models
without rewriting scene logic.
"""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from pathlib import Path

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
            inputs.append(
                {
                    "type": "image",
                    "data": base64.b64encode(ref.data).decode("ascii"),
                    "mime_type": ref.mime_type,
                }
            )
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
