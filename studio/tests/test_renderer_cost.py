from __future__ import annotations

from app.services.renderer_cost import CostInputs, accepted_clip_cost, monthly_projection


def test_cost_is_based_on_accepted_output_not_single_call() -> None:
    inputs = CostInputs(
        image_cost_usd=0.10,
        video_cost_usd=1.00,
        images_per_accepted_seed=3.0,
        videos_per_accepted_clip=1.5,
    )
    assert accepted_clip_cost(inputs) == 1.8
    assert monthly_projection(inputs) == {10: 18.0, 25: 45.0, 50: 90.0, 100: 180.0}
