"""Two-pass visual research over retained Vintage Evidence."""
from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.concept_models import DesignConcept
from app.db.session import get_db_session
from app.domain.enums import DesignAttemptMethod
from app.services.design_pipeline import create_attempt
from app.services.vintage_research import (
    VintageResearchError,
    execute_research,
    list_runs,
    load_run,
    mark_pipeline,
    update_concept,
)

router = APIRouter(prefix="/api/vintage-design", tags=["vintage-design"])
SettingsDependency = Annotated[Settings, Depends(get_settings)]
SessionDependency = Annotated[Session, Depends(get_db_session)]


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


class PipelineIn(BaseModel):
    design_concept_id: uuid.UUID


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


@router.post("/runs/{run_id}/concepts/{concept_number}/pipeline", status_code=status.HTTP_201_CREATED)
def send_to_pipeline(
    run_id: str,
    concept_number: int,
    body: PipelineIn,
    session: SessionDependency,
    settings: SettingsDependency,
) -> dict[str, Any]:
    try:
        run = load_run(run_id)
    except VintageResearchError as error:
        raise _fail(error, 404) from error
    research = next(
        (item for item in run.get("concepts", []) if item.get("concept_number") == concept_number),
        None,
    )
    if research is None:
        raise HTTPException(status_code=404, detail="Research concept not found.")
    if research.get("status") != "approved":
        raise HTTPException(status_code=422, detail="Approve the research concept first.")
    target = session.get(DesignConcept, body.design_concept_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Design concept not found.")
    prompt = research.get("edited_prompt") or research.get("pass2_prompt")
    attempt = create_attempt(
        session,
        target,
        DesignAttemptMethod.IMAGE_GENERATION,
        production_prompt=str(prompt),
        model=settings.openai_image_model,
        model_settings={"size": settings.openai_image_size, "quality": settings.openai_image_quality},
        reference_inputs={
            "vintage_research_run_id": run_id,
            "research_concept_number": concept_number,
            "evidence_listing_ids": run.get("evidence_listing_ids", []),
            "evidence_images": run.get("evidence_images", []),
        },
    )
    session.commit()
    payload = {
        "design_concept_id": str(target.id),
        "attempt_id": str(attempt.id),
        "attempt_number": attempt.attempt_number,
        "state": attempt.state.value,
    }
    mark_pipeline(run_id, concept_number, payload)
    return payload
