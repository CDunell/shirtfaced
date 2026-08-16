"""Renderer cost projection helpers.

Provider price inputs are runtime/config data; this module never claims a permanent
price. It answers the production question: given measured acceptance/retry behaviour,
what does an accepted clip cost at scale?
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostInputs:
    image_cost_usd: float
    video_cost_usd: float
    images_per_accepted_seed: float
    videos_per_accepted_clip: float


def accepted_clip_cost(inputs: CostInputs) -> float:
    return (
        inputs.image_cost_usd * inputs.images_per_accepted_seed
        + inputs.video_cost_usd * inputs.videos_per_accepted_clip
    )


def monthly_projection(
    inputs: CostInputs,
    clip_counts: tuple[int, ...] = (10, 25, 50, 100),
) -> dict[int, float]:
    unit = accepted_clip_cost(inputs)
    return {count: round(unit * count, 2) for count in clip_counts}
