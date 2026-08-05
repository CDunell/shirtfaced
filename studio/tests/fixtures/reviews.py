"""Review fixtures.

These are the acceptance cases from the Phase 4 review contract, expressed as the
structured output a reviewer would return. They pin expected *material gate outcomes*,
not prose.
"""

from __future__ import annotations

from typing import Any

from app.domain.enums import GateName, GateStatus, ReviewRecommendation
from app.domain.schemas import ImageReview


def gate(
    evidence: str,
    status: GateStatus = GateStatus.PASS,
    *,
    codes: list[str] | None = None,
    confidence: float = 0.85,
    material: bool = False,
) -> dict[str, Any]:
    return {
        "status": status,
        "evidence": evidence,
        "codes": codes or [],
        "confidence": confidence,
        "material": material,
    }


def build_review(
    *,
    recommendation: ReviewRecommendation = ReviewRecommendation.APPROVE,
    overrides: dict[GateName, dict[str, Any]] | None = None,
    **fields: Any,
) -> ImageReview:
    """A passing review, with named gates overridden."""
    gates: dict[GateName, dict[str, Any]] = {
        name: gate(f"{name.value} reads as expected.") for name in GateName
    }
    gates.update(overrides or {})

    payload: dict[str, Any] = {
        "recommendation": recommendation,
        "gates": gates,
        "mood_score": 4,
        "australian_authenticity_score": 4,
        "product_visibility_score": 4,
        "documentary_credibility_score": 4,
        "story_score": 4,
        "branding_compliant": True,
        "vehicle_compliant": True,
        "structurally_sound": True,
        "strongest_success": "The moment reads as taken rather than arranged.",
        "material_drift": None,
        "new_rule_proposal": None,
        "next_hero_product": None,
        "next_camera": None,
    }
    payload.update(fields)
    return ImageReview.model_validate(payload)


# --- the acceptance set from the review contract -----------------------------------


def correct_car_interior() -> ImageReview:
    """1. W01-011 with natural tote visibility."""
    return build_review()


def branded_chip_packet() -> ImageReview:
    """2. The same scene with readable third-party packaging."""
    return build_review(
        recommendation=ReviewRecommendation.REJECT,
        overrides={
            GateName.THIRD_PARTY_BRANDING: gate(
                "A chip packet on the rear seat carries a readable commercial logo.",
                GateStatus.FAIL,
                codes=["BRAND_PACKAGING_MARK"],
                confidence=0.93,
                material=True,
            )
        },
        branding_compliant=False,
        material_drift="Readable third-party packaging is visible on the rear seat.",
    )


def american_pickup() -> ImageReview:
    """3. The same scene with a prohibited vehicle body."""
    return build_review(
        recommendation=ReviewRecommendation.REJECT,
        overrides={
            GateName.VEHICLE_CONTINUITY: gate(
                "The vehicle has an enclosed pickup tub rather than an open alloy tray.",
                GateStatus.FAIL,
                codes=["VEHICLE_AMERICAN_PICKUP", "VEHICLE_ENCLOSED_TUB"],
                confidence=0.9,
                material=True,
            )
        },
        vehicle_compliant=False,
        material_drift="The ute reads as an American pickup.",
        new_rule_proposal=(
            "Every ute prompt must state an open aluminium alloy tray and prohibit an enclosed tub."
        ),
    )


def correct_apartment_lift() -> ImageReview:
    """4. W01-012 with the hoodie tied at the waist."""
    return build_review(next_hero_product="Back graphic", next_camera="Inside lounge")


def posed_lift_lineup() -> ImageReview:
    """5. The lift scene as a fashion lineup."""
    return build_review(
        recommendation=ReviewRecommendation.REJECT,
        overrides={
            GateName.DOCUMENTARY_CREDIBILITY: gate(
                "Four people face the camera in a line, evenly spaced.",
                GateStatus.FAIL,
                codes=["DOCUMENTARY_FASHION"],
                confidence=0.88,
                material=True,
            ),
            GateName.COMPOSITION: gate(
                "The framing is centred and symmetrical.",
                GateStatus.FAIL,
                codes=["COMPOSITION_POSED"],
                confidence=0.86,
                material=True,
            ),
        },
        material_drift="The group is posing for the camera.",
    )


def blank_back_surface() -> ImageReview:
    """6. W01-013 showing a blank rear garment surface."""
    return build_review(
        overrides={
            GateName.PRODUCT_VISIBILITY: gate(
                "The rear of the t-shirt is visible and completely blank.",
                confidence=0.9,
            )
        }
    )


def invented_back_graphic() -> ImageReview:
    """7. W01-013 with artwork invented on the garment."""
    return build_review(
        recommendation=ReviewRecommendation.REJECT,
        overrides={
            GateName.PRODUCT_VISIBILITY: gate(
                "A printed graphic appears across the rear of the t-shirt.",
                GateStatus.FAIL,
                codes=["PRODUCT_INVENTED_GRAPHIC"],
                confidence=0.95,
                material=True,
            )
        },
        product_visibility_score=1,
        material_drift="Artwork was invented on a garment that must stay blank.",
    )


def quiet_optimistic_sunrise() -> ImageReview:
    """8. A quiet scene that still carries momentum."""
    return build_review(
        recommendation=ReviewRecommendation.APPROVE_WITH_NOTE,
        overrides={
            GateName.MOOD: gate(
                "The group is still and watching the sunrise, but talking.", confidence=0.7
            )
        },
        material_drift=None,
        new_rule_proposal=(
            "A quiet scene needs a visible conversation or shared action to keep momentum readable."
        ),
    )


def miserable_hangover() -> ImageReview:
    """9. The same scene read as resignation."""
    return build_review(
        recommendation=ReviewRecommendation.REJECT,
        overrides={
            GateName.MOOD: gate(
                "Everyone is slumped and looking away from one another.",
                GateStatus.FAIL,
                codes=["MOOD_RESIGNATION"],
                confidence=0.87,
                material=True,
            )
        },
        mood_score=1,
        material_drift="The scene reads as the end of the night rather than its continuation.",
    )


def ambiguous_environmental_mark() -> ImageReview:
    """10. A mark too small to judge, which must be uncertain rather than guessed."""
    return build_review(
        recommendation=ReviewRecommendation.UNCERTAIN,
        overrides={
            GateName.THIRD_PARTY_BRANDING: gate(
                "A small sticker on the door frame is below readable resolution.",
                GateStatus.UNCERTAIN,
                confidence=0.3,
                material=False,
            )
        },
    )


def car_with_no_seats() -> ImageReview:
    """11. The failure the first nine gates could not see.

    Scored documentary credibility 4/5 by a live reviewer, correctly: the frame was
    convincingly photographic. It showed a car with no front seats.
    """
    return build_review(
        recommendation=ReviewRecommendation.REJECT,
        overrides={
            GateName.STRUCTURAL_PLAUSIBILITY: gate(
                "The front row has no seats and a passenger is sitting on empty air.",
                GateStatus.FAIL,
                codes=["STRUCTURE_MISSING_ELEMENT", "STRUCTURE_UNSUPPORTED_BODY"],
                confidence=0.94,
                material=True,
            )
        },
        structurally_sound=False,
        material_drift="The car has no front seats.",
    )


def van_with_no_rear_end() -> ImageReview:
    """12. Structurally impossible while every creative gate passes.

    The live review of this frame returned documentary credibility 5/5 and
    vehicle_compliant true. Both were defensible. Nothing asked whether the van had a
    back.
    """
    return build_review(
        recommendation=ReviewRecommendation.REJECT,
        overrides={
            GateName.STRUCTURAL_PLAUSIBILITY: gate(
                "The road is visible through the opening where the van's rear body should be.",
                GateStatus.FAIL,
                codes=["STRUCTURE_MISSING_ELEMENT"],
                confidence=0.91,
                material=True,
            )
        },
        structurally_sound=False,
        material_drift="The van has no rear end.",
    )


def camera_inside_the_cabin() -> ImageReview:
    """13. Vehicle continuity is about where the camera is, not only the body shape.

    A live review passed this as vehicle_compliant true. The photograph was taken from
    the passenger seat, which the oldest rule in the vehicle canon forbids.
    """
    return build_review(
        recommendation=ReviewRecommendation.REJECT,
        overrides={
            GateName.VEHICLE_CONTINUITY: gate(
                "The frame looks out over a door sill with an occupant inside the glass.",
                GateStatus.FAIL,
                codes=["VEHICLE_CAMERA_INSIDE"],
                confidence=0.9,
                material=True,
            )
        },
        vehicle_compliant=False,
        material_drift="The photograph is taken from inside the vehicle.",
    )


def unbranded_can_is_not_branding() -> ImageReview:
    """14. An unmarked object is not a branding failure.

    A live review failed a frame for "unbranded drink can in the foreground", which is
    the gate firing on the presence of an object rather than on a readable mark.
    """
    return build_review(
        overrides={
            GateName.THIRD_PARTY_BRANDING: gate(
                "A plain drink can sits on the kerb with no legible mark.",
                GateStatus.PASS,
                confidence=0.86,
            )
        },
    )


ACCEPTANCE_SET: dict[str, ImageReview] = {
    "correct_car_interior": correct_car_interior(),
    "branded_chip_packet": branded_chip_packet(),
    "american_pickup": american_pickup(),
    "correct_apartment_lift": correct_apartment_lift(),
    "posed_lift_lineup": posed_lift_lineup(),
    "blank_back_surface": blank_back_surface(),
    "invented_back_graphic": invented_back_graphic(),
    "quiet_optimistic_sunrise": quiet_optimistic_sunrise(),
    "miserable_hangover": miserable_hangover(),
    "ambiguous_environmental_mark": ambiguous_environmental_mark(),
    # Added after four live frames slipped through the original nine.
    "car_with_no_seats": car_with_no_seats(),
    "van_with_no_rear_end": van_with_no_rear_end(),
    "camera_inside_the_cabin": camera_inside_the_cabin(),
    "unbranded_can_is_not_branding": unbranded_can_is_not_branding(),
}
