"""Image generation adapters, retry and thumbnailing.

The real OpenAI client is never constructed.
"""

from __future__ import annotations

import base64
from typing import Any

import pytest

from app.adapters.factory import build_image_client, image_client_is_live, image_model_for
from app.adapters.image_generation import (
    FakeImageGenerationClient,
    ImageGenerationError,
    ImageGenerationRequest,
    OpenAIImageGenerationClient,
    detect_mime_type,
)
from app.config import Settings
from app.domain.enums import FailureCode
from app.services import images
from app.services.retry import RetryPolicy, call_with_retry

REQUEST = ImageGenerationRequest(
    prompt="Documentary photograph of friends in a car",
    model="a-model",
    size="512x384",
    quality="high",
)


# --- the fake ----------------------------------------------------------------------


def test_the_fake_produces_a_real_decodable_image() -> None:
    generated = FakeImageGenerationClient().generate(REQUEST)

    assert detect_mime_type(generated.data) == "image/png"
    assert images.measure(generated.data) == images.ImageDimensions(512, 384)


def test_the_fake_is_deterministic() -> None:
    first = FakeImageGenerationClient().generate(REQUEST)
    second = FakeImageGenerationClient().generate(REQUEST)

    assert first.data == second.data


def test_a_different_prompt_produces_a_different_image() -> None:
    other = ImageGenerationRequest(
        prompt="A completely different scene", model="a-model", size="512x384", quality="high"
    )

    assert FakeImageGenerationClient().generate(REQUEST).data != (
        FakeImageGenerationClient().generate(other).data
    )


def test_the_fake_records_what_it_was_asked() -> None:
    client = FakeImageGenerationClient()

    client.generate(REQUEST)

    assert client.requests[0].size == "512x384"


# --- thumbnails --------------------------------------------------------------------


def test_thumbnails_preserve_aspect_ratio_and_shrink() -> None:
    generated = FakeImageGenerationClient().generate(REQUEST)

    data, size = images.make_thumbnail(generated.data, max_edge=128)

    assert max(size.width, size.height) == 128
    assert size.width / size.height == pytest.approx(512 / 384, rel=0.02)
    assert len(data) < len(generated.data)


def test_a_small_image_is_not_enlarged() -> None:
    small = FakeImageGenerationClient().generate(
        ImageGenerationRequest(prompt="p", model="m", size="64x64", quality="high")
    )

    _, size = images.make_thumbnail(small.data, max_edge=512)

    assert (size.width, size.height) == (64, 64)


def test_undecodable_data_is_rejected_rather_than_stored() -> None:
    with pytest.raises(ImageGenerationError) as caught:
        images.measure(b"this is not an image")

    assert caught.value.code is FailureCode.INVALID_IMAGE


# --- magic-byte detection ----------------------------------------------------------


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"\x89PNG\r\n\x1a\nrest", "image/png"),
        (b"\xff\xd8\xff\xe0rest", "image/jpeg"),
        (b"RIFF????WEBPrest", "image/webp"),
        (b"not an image", None),
        (b"", None),
    ],
)
def test_detects_the_image_type(data: bytes, expected: str | None) -> None:
    assert detect_mime_type(data) == expected


# --- the OpenAI adapter ------------------------------------------------------------


class StubImages:
    def __init__(self, *, payload: Any = None, error: Exception | None = None) -> None:
        self._payload = payload
        self._error = error
        self.calls: list[dict[str, Any]] = []

    def generate(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self._error is not None:
            raise self._error
        return self._payload


class StubClient:
    def __init__(self, images_api: StubImages) -> None:
        self.images = images_api


def _response(data: bytes | None, *, key: str = "b64_json") -> Any:
    entry = type("Entry", (), {key: base64.b64encode(data).decode() if data else None})()
    return type("Response", (), {"data": [entry], "id": "img_stub"})()


def _client(**kwargs: Any) -> tuple[OpenAIImageGenerationClient, StubImages]:
    api = StubImages(**kwargs)
    return OpenAIImageGenerationClient(
        StubClient(api), model="an-image-model", timeout_seconds=30
    ), api


def test_decodes_base64_output() -> None:
    png = FakeImageGenerationClient().generate(REQUEST).data
    client, _ = _client(payload=_response(png))

    generated = client.generate(REQUEST)

    assert generated.data == png
    assert generated.mime_type == "image/png"
    assert generated.provider_request_id == "img_stub"


def test_sends_the_configured_model_size_and_quality() -> None:
    png = FakeImageGenerationClient().generate(REQUEST).data
    client, api = _client(payload=_response(png))

    client.generate(REQUEST)

    assert api.calls[0]["model"] == "an-image-model"
    assert api.calls[0]["size"] == "512x384"
    assert api.calls[0]["quality"] == "high"
    assert api.calls[0]["n"] == 1


def test_an_unset_model_is_refused_before_any_request() -> None:
    with pytest.raises(ImageGenerationError) as caught:
        OpenAIImageGenerationClient(StubClient(StubImages()), model="", timeout_seconds=30)

    assert caught.value.code is FailureCode.CONFIGURATION


def test_a_url_only_response_is_rejected() -> None:
    """A temporary provider URL is not durable storage."""
    client, _ = _client(payload=_response(None))

    with pytest.raises(ImageGenerationError) as caught:
        client.generate(REQUEST)

    assert caught.value.code is FailureCode.INVALID_IMAGE


def test_non_image_bytes_are_rejected() -> None:
    client, _ = _client(payload=_response(b"definitely not an image"))

    with pytest.raises(ImageGenerationError) as caught:
        client.generate(REQUEST)

    assert caught.value.code is FailureCode.INVALID_IMAGE


@pytest.mark.parametrize(
    ("exception_name", "expected"),
    [
        ("APITimeoutError", FailureCode.PROVIDER_TIMEOUT),
        ("AuthenticationError", FailureCode.CONFIGURATION),
        ("PermissionDeniedError", FailureCode.CONFIGURATION),
        ("BadRequestError", FailureCode.PROVIDER_REFUSED),
        ("APIConnectionError", FailureCode.PROVIDER_ERROR),
    ],
)
def test_provider_errors_are_classified(exception_name: str, expected: FailureCode) -> None:
    error = type(exception_name, (Exception,), {})("upstream said no")
    client, _ = _client(error=error)

    with pytest.raises(ImageGenerationError) as caught:
        client.generate(REQUEST)

    assert caught.value.code is expected


# --- retry -------------------------------------------------------------------------

FAST = RetryPolicy(max_attempts=3, initial_delay_seconds=0.01)


def test_a_transient_failure_is_retried_and_can_succeed() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ImageGenerationError("timed out", FailureCode.PROVIDER_TIMEOUT)
        return "ok"

    assert call_with_retry(flaky, FAST, sleep=lambda _: None, random_value=lambda: 0.5) == "ok"
    assert calls["n"] == 3


def test_retries_are_bounded() -> None:
    calls = {"n": 0}

    def always_fails() -> str:
        calls["n"] += 1
        raise ImageGenerationError("timed out", FailureCode.PROVIDER_TIMEOUT)

    with pytest.raises(ImageGenerationError):
        call_with_retry(always_fails, FAST, sleep=lambda _: None, random_value=lambda: 0.5)

    assert calls["n"] == 3


@pytest.mark.parametrize("code", [FailureCode.CONFIGURATION, FailureCode.PROVIDER_REFUSED])
def test_permanent_failures_are_not_retried(code: FailureCode) -> None:
    """Each retry of an image call may cost money; these would fail identically."""
    calls = {"n": 0}

    def refused() -> str:
        calls["n"] += 1
        raise ImageGenerationError("no", code)

    with pytest.raises(ImageGenerationError):
        call_with_retry(refused, FAST, sleep=lambda _: None, random_value=lambda: 0.5)

    assert calls["n"] == 1


def test_backoff_grows_and_is_jittered() -> None:
    policy = RetryPolicy(initial_delay_seconds=1.0, multiplier=2.0, jitter=0.25)

    assert policy.delay_for(1, 0.5) == pytest.approx(1.0)
    assert policy.delay_for(2, 0.5) == pytest.approx(2.0)
    assert policy.delay_for(1, 0.0) < policy.delay_for(1, 1.0)


def test_backoff_is_capped() -> None:
    policy = RetryPolicy(initial_delay_seconds=1.0, multiplier=10.0, max_delay_seconds=5.0)

    assert policy.delay_for(5, 0.5) == pytest.approx(5.0)


# --- the factory -------------------------------------------------------------------

VALID_URL = "postgresql+psycopg://app:secret@db.example:5432/shirtfaced_studio"


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {"database_url": VALID_URL}
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


def test_the_fake_image_client_is_used_without_a_key() -> None:
    settings = _settings(openai_image_model="an-image-model")

    assert image_client_is_live(settings) is False
    assert isinstance(build_image_client(settings), FakeImageGenerationClient)


def test_the_fake_image_client_is_used_without_a_model() -> None:
    settings = _settings(openai_api_key="sk-test")

    assert image_client_is_live(settings) is False
    assert isinstance(build_image_client(settings), FakeImageGenerationClient)


def test_a_live_image_client_needs_both() -> None:
    settings = _settings(openai_api_key="sk-test", openai_image_model="an-image-model")

    assert image_client_is_live(settings) is True


# --- which model actually gets billed ------------------------------------------------
#
# The real client bakes its model in at construction and ignores the one on the
# request, so this choice is the only thing that decides the bill. Passing a draft
# model on the request alone changed the recorded value and nothing else.


def test_the_draft_model_is_chosen_only_when_a_draft_is_asked_for() -> None:
    settings = _settings(
        openai_image_model="the-expensive-one", openai_image_draft_model="the-cheap-one"
    )

    assert image_model_for(settings) == "the-expensive-one"
    assert image_model_for(settings, draft=True) == "the-cheap-one"


def test_a_draft_never_falls_back_to_the_full_model() -> None:
    """Falling back is how a draft quietly costs full price."""
    settings = _settings(openai_image_model="the-expensive-one")

    assert image_model_for(settings, draft=True) == ""
    assert image_client_is_live(settings, draft=True) is False


def test_a_live_draft_client_is_built_on_the_draft_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings(
        openai_api_key="sk-test",
        openai_image_model="the-expensive-one",
        openai_image_draft_model="the-cheap-one",
    )
    assert image_client_is_live(settings, draft=True) is True

    captured: dict[str, Any] = {}

    def _capture(*, client: Any, model: str, timeout_seconds: float) -> Any:
        captured["model"] = model
        return FakeImageGenerationClient()

    # The real OpenAI client is never constructed here; only the model it would
    # have been given is checked, because that is the value that gets billed.
    monkeypatch.setattr("app.adapters.factory.OpenAIImageGenerationClient", _capture)
    build_image_client(settings, draft=True)

    assert captured["model"] == "the-cheap-one"


def test_the_generated_image_reports_the_model_that_was_called() -> None:
    """The attempt records this, not what was requested, so a row cannot misreport."""
    client = FakeImageGenerationClient()

    generated = client.generate(
        ImageGenerationRequest(prompt="a prompt", model="asked-for", size="8x8", quality="low")
    )

    assert generated.model == "asked-for"
