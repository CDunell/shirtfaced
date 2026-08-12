"""Recommending presentation for a phrase or graphic over HTTP.

The other direction from ``design.py``: that route measures a design that
already exists, this one recommends how to present content that doesn't yet.
See ``app/services/design_advisor.py`` for what it will and will not decide.

No database. Advising touches no world, no attempt and no canon, so this
router depends on nothing but the request body and the mined corpus file.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.design_advisor import advise

router = APIRouter(prefix="/api/design", tags=["design"])


class AdviseRequest(BaseModel):
    phrase: str = ""
    has_graphic: bool = False
    tradition: str = "novelty"


class RecommendationView(BaseModel):
    field: str
    value: str
    evidence: str
    confidence: str


class DirectionResponse(BaseModel):
    """``DesignDirection.to_dict()``'s own shape, verbatim."""

    input: str
    intent: str
    tradition: str
    recommendations: list[RecommendationView]
    alternatives: list[str]
    not_decided: list[str]


@router.post("/advise", response_model=DirectionResponse, summary="Recommend presentation")
def advise_design(payload: AdviseRequest) -> DirectionResponse:
    """Recommend how to present a supplied phrase and/or graphic.

    Prescribes presentation only -- archetype, scale, coverage, ink count,
    placement, polarity. Never the idea, the artwork or whether either is any
    good; see ``not_decided`` in the response for what this deliberately
    leaves to a human.
    """
    if not payload.phrase.strip() and not payload.has_graphic:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Supply a phrase, set has_graphic true, or both -- there is nothing to advise on otherwise.",
        )

    direction = advise(
        phrase=payload.phrase,
        has_graphic=payload.has_graphic,
        tradition=payload.tradition,
    )
    return DirectionResponse(**direction.to_dict())
