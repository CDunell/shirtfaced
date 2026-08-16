"""Renderer budget guardrails.

Budget values are workflow policy. They prevent an API integration from turning a
creative retry loop into an unbounded spend loop.
"""
from __future__ import annotations

from dataclasses import dataclass


class RendererBudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class BudgetSnapshot:
    scene_limit_usd: float
    validation_limit_usd: float
    monthly_limit_usd: float
    scene_spend_usd: float = 0.0
    validation_spend_usd: float = 0.0
    monthly_spend_usd: float = 0.0


def assert_can_spend(snapshot: BudgetSnapshot, estimated_call_usd: float) -> None:
    if estimated_call_usd < 0:
        raise ValueError("estimated_call_usd must be non-negative")
    checks = (
        ("scene", snapshot.scene_spend_usd, snapshot.scene_limit_usd),
        ("validation", snapshot.validation_spend_usd, snapshot.validation_limit_usd),
        ("monthly", snapshot.monthly_spend_usd, snapshot.monthly_limit_usd),
    )
    for label, spent, limit in checks:
        if spent + estimated_call_usd > limit:
            raise RendererBudgetExceeded(
                f"{label} renderer budget would be exceeded: "
                f"{spent:.2f} + {estimated_call_usd:.2f} > {limit:.2f} USD"
            )
