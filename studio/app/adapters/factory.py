"""Choosing adapter implementations from configuration.

The real OpenAI client is constructed only when a key and a model are both configured.
With either missing, the fake is used: development without a key works, and a test that
forgets to inject a double cannot accidentally spend money.
"""

from __future__ import annotations

import logging

from app.adapters.planning import (
    FakePromptPlanningClient,
    OpenAIPromptPlanningClient,
    PromptPlanningClient,
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
