"""Recommending presentation for a phrase or graphic over HTTP.

The other direction from ``design.py``: that route measures a design that
already exists, this one recommends how to present content that doesn't yet.
See ``app/services/design_advisor.py`` for what it will and will not decide.

The evidence is ``design_measurements`` -- the corpus measured by code, in
the database where it cannot be absent from the box the way the mined JSON
file it replaced always was. An empty table keeps the same honest meaning:
every recommendation is a marked default until the corpus is measured.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.services.design_advisor import advise, measurement_rows, render_generation_prompt

router = APIRouter(prefix="/api/design", tags=["design"])

SessionDependency = Annotated[Session, Depends(get_db_session)]


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
    """``DesignDirection.to_dict()``'s own shape, plus a paste-ready prompt."""

    input: str
    intent: str
    tradition: str
    recommendations: list[RecommendationView]
    alternatives: list[str]
    not_decided: list[str]
    generation_prompt: str


@router.post("/advise", response_model=DirectionResponse, summary="Recommend presentation")
def advise_design(payload: AdviseRequest, session: SessionDependency) -> DirectionResponse:
    """Recommend how to present a supplied phrase and/or graphic.

    Prescribes presentation only -- archetype, scale, coverage, ink count,
    placement, polarity. Never the idea, the artwork or whether either is any
    good; see ``not_decided`` in the response for what this deliberately
    leaves to a human.
    """
    if not payload.phrase.strip() and not payload.has_graphic:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Supply a phrase, set has_graphic true, or both -- "
            "there is nothing to advise on otherwise.",
        )

    direction = advise(
        phrase=payload.phrase,
        has_graphic=payload.has_graphic,
        tradition=payload.tradition,
        rows=measurement_rows(session),
    )
    return DirectionResponse(
        **direction.to_dict(),
        generation_prompt=render_generation_prompt(direction, payload.phrase),
    )
