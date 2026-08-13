"""Two-pass visual research over retained Vintage Evidence."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.services.vintage_research import (
    VintageResearchError,
    execute_research,
    list_runs,
    load_run,
    update_concept,
)

router = APIRouter(prefix="/api/vintage-design", tags=["vintage-design"])
SettingsDependency = Annotated[Settings, Depends(get_settings)]


class ResearchIn(BaseModel):
    filters: dict[str, Any] = Field(default_factory=dict)
    listing_ids: list[str] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
    image_limit: int = Field(default=16, ge=1, le=24)
    model: str = Field(default="", max_length=120)


class ConceptReviewIn(BaseModel):
    status: str | None = None
    edited_prompt: str | None = Field(default=None, max_length=20000)
    review_note: str | None = Field(default=None, max_length=4000)


def _fail(error: Exception, code: int = 422) -> HTTPException:
    return HTTPException(status_code=code, detail=str(error))


@router.get("/runs")
def runs() -> list[dict[str, Any]]:
    return list_runs()


@router.get("/runs/{run_id}")
def run_detail(run_id: str) -> dict[str, Any]:
    try:
        return load_run(run_id)
    except VintageResearchError as error:
        raise _fail(error, 404) from error


@router.post("/runs", status_code=status.HTTP_201_CREATED)
def create_run(body: ResearchIn, settings: SettingsDependency) -> dict[str, Any]:
    try:
        return execute_research(
            settings,
            filters=body.filters,
            listing_ids=body.listing_ids or None,
            image_urls=body.image_urls or None,
            image_limit=body.image_limit,
            model=body.model,
        )
    except VintageResearchError as error:
        raise _fail(error) from error


@router.patch("/runs/{run_id}/concepts/{concept_number}")
def review_concept(run_id: str, concept_number: int, body: ConceptReviewIn) -> dict[str, Any]:
    try:
        return update_concept(
            run_id,
            concept_number,
            status=body.status,
            edited_prompt=body.edited_prompt,
            review_note=body.review_note,
        )
    except VintageResearchError as error:
        raise _fail(error) from error
