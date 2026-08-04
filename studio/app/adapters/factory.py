"""Choosing adapter implementations from configuration.

The real OpenAI client is constructed only when a key and a model are both configured.
With either missing, the fake is used: development without a key works, and a test that
forgets to inject a double cannot accidentally spend money.
"""

from __future__ import annotations

import logging

from app.adapters.image_generation import (
    FakeImageGenerationClient,
    ImageGenerationClient,
    OpenAIImageGenerationClient,
)
from app.adapters.planning import (
    FakePromptPlanningClient,
    OpenAIPromptPlanningClient,
    PromptPlanningClient,
)
from app.adapters.review import (
    FakeImageReviewClient,
    ImageReviewClient,
    OpenAIImageReviewClient,
)
from app.config import Settings

logger = logging.getLogger(__name__)


def planning_client_is_live(settings: Settings) -> bool:
    """Whether a real, billable planning client would be built."""
    return bool(settings.openai_api_key and settings.openai_text_model)


def build_planning_client(settings: Settings) -> PromptPlanningClient:
    """The planning client for these settings."""
    if not planning_client_is_live(settings):
        logger.info(
            "Using the fake planning client: OPENAI_API_KEY and OPENAI_TEXT_MODEL are "
            "not both set. No request will be billed."
        )
        return FakePromptPlanningClient()

    # Imported here so the SDK is not required to run the application without a key.
    from openai import OpenAI

    assert settings.openai_api_key is not None
    return OpenAIPromptPlanningClient(
        client=OpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout_seconds,
        ),
        model=settings.openai_text_model,
        timeout_seconds=settings.openai_timeout_seconds,
    )


def image_client_is_live(settings: Settings) -> bool:
    """Whether a real, billable image client would be built."""
    return bool(settings.openai_api_key and settings.openai_image_model)


def build_image_client(settings: Settings) -> ImageGenerationClient:
    """The image generation client for these settings.

    Image calls are the expensive ones, so the same rule applies as for planning:
    without both a key and an explicitly configured model, the fake runs instead.
    """
    if not image_client_is_live(settings):
        logger.info(
            "Using the fake image client: OPENAI_API_KEY and OPENAI_IMAGE_MODEL are "
            "not both set. No image will be billed."
        )
        return FakeImageGenerationClient()

    from openai import OpenAI

    assert settings.openai_api_key is not None
    return OpenAIImageGenerationClient(
        client=OpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout_seconds,
        ),
        model=settings.openai_image_model,
        timeout_seconds=settings.openai_timeout_seconds,
    )


def review_client_is_live(settings: Settings) -> bool:
    """Whether a real, billable review client would be built."""
    return bool(settings.openai_api_key and settings.openai_review_model)


def build_review_client(settings: Settings) -> ImageReviewClient:
    """The image review client for these settings."""
    if not review_client_is_live(settings):
        logger.info(
            "Using the fake review client: OPENAI_API_KEY and OPENAI_REVIEW_MODEL are "
            "not both set. No review will be billed."
        )
        return FakeImageReviewClient()

    from openai import OpenAI

    assert settings.openai_api_key is not None
    return OpenAIImageReviewClient(
        client=OpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout_seconds,
        ),
        model=settings.openai_review_model,
        timeout_seconds=settings.openai_timeout_seconds,
    )
