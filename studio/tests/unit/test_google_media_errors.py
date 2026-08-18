from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.adapters.google_media import GoogleImageClient, GoogleImageRequest, GoogleMediaError


class ProviderContentRejection(RuntimeError):
    pass


def test_image_sdk_errors_use_the_stable_adapter_error_contract() -> None:
    def reject(**_kwargs: object) -> object:
        raise ProviderContentRejection("Request blocked due to prohibited content guidelines")

    client = object.__new__(GoogleImageClient)
    client._model = "test-image-model"
    client._client = SimpleNamespace(interactions=SimpleNamespace(create=reject))

    with pytest.raises(GoogleMediaError) as caught:
        client.generate(GoogleImageRequest(prompt="one safe test image"))

    assert str(caught.value) == (
        "ProviderContentRejection: Request blocked due to prohibited content guidelines"
    )
