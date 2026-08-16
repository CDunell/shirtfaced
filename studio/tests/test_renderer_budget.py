from __future__ import annotations

import pytest

from app.services.renderer_budget import BudgetSnapshot, RendererBudgetExceeded, assert_can_spend


def test_budget_allows_bounded_dev_spend() -> None:
    assert_can_spend(
        BudgetSnapshot(scene_limit_usd=12, validation_limit_usd=100, monthly_limit_usd=250),
        8,
    )


def test_budget_refuses_unbounded_retry() -> None:
    with pytest.raises(RendererBudgetExceeded):
        assert_can_spend(
            BudgetSnapshot(
                scene_limit_usd=12,
                validation_limit_usd=100,
                monthly_limit_usd=250,
                scene_spend_usd=11.5,
            ),
            1,
        )
