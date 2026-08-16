from __future__ import annotations

from app.services.renderer_cost import CostInputs, monthly_projection


def test_monthly_projection_scales_linearly_from_accepted_output_cost() -> None:
    projection = monthly_projection(
        CostInputs(
            image_cost_usd=0.05,
            video_cost_usd=1.00,
            images_per_accepted_seed=2.0,
            videos_per_accepted_clip=1.0,
        )
    )
    assert projection[10] == 11.0
    assert projection[100] == 110.0
