"""Choosing adapter implementations from configuration.

The real OpenAI client is constructed only when a key and a model are both configured.
With either missing, the fake is used: development without a key works, and a test that
forgets to inject a double cannot accidentally spend money.
"""

from __future__ import annotations

import logging

from app.adapters.canon_classifier import (
    CanonClassifier,
    FakeCanonClassifier,
    OpenAICanonClassifier,
)
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


def image_model_for(settings: Settings, *, draft: bool = False) -> str:
    """The model a run will actually be billed for.

    The client bakes its model in at construction and ignores the one on the request,
    so this is the only thing that decides what gets called. Asking for a draft
    without OPENAI_IMAGE_DRAFT_MODEL set returns empty rather than quietly falling
    back to the full model: a silent fallback is how a draft ends up costing full
    price while the record says otherwise.
    """
    return settings.openai_image_draft_model if draft else settings.openai_image_model


def image_client_is_live(settings: Settings, *, draft: bool = False) -> bool:
    """Whether a real, billable image client would be built."""
    return bool(settings.openai_api_key and image_model_for(settings, draft=draft))


def build_image_client(settings: Settings, *, draft: bool = False) -> ImageGenerationClient:
    """The image generation client for these settings.

    Image calls are the expensive ones, so the same rule applies as for planning:
    without both a key and an explicitly configured model, the fake runs instead.

    ``draft`` selects the cheap model. It has to be decided here rather than per
    request, because the request's model field is ignored by the real client.
    """
    model = image_model_for(settings, draft=draft)
    if not image_client_is_live(settings, draft=draft):
        logger.info(
            "Using the fake image client: OPENAI_API_KEY and %s are not both set. "
            "No image will be billed.",
            "OPENAI_IMAGE_DRAFT_MODEL" if draft else "OPENAI_IMAGE_MODEL",
        )
        return FakeImageGenerationClient()

    from openai import OpenAI

    assert settings.openai_api_key is not None
    return OpenAIImageGenerationClient(
        client=OpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout_seconds,
        ),
        model=model,
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


def classifier_is_live(settings: Settings) -> bool:
    """Whether a real, billable classifier would be built."""
    return bool(settings.openai_api_key and settings.openai_text_model)


def build_canon_classifier(settings: Settings) -> CanonClassifier:
    """The canon classifier for these settings.

    Classification is advisory, so an unkeyed deployment gets the deterministic fake
    rather than an empty queue.
    """
    if not classifier_is_live(settings):
        logger.info(
            "Using the fake canon classifier: OPENAI_API_KEY and OPENAI_TEXT_MODEL are "
            "not both set. No request will be billed."
        )
        return FakeCanonClassifier()

    from openai import OpenAI

    assert settings.openai_api_key is not None
    return OpenAICanonClassifier(
        client=OpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout_seconds,
        ),
        model=settings.openai_text_model,
        timeout_seconds=settings.openai_timeout_seconds,
    )
