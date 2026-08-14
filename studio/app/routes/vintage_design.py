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
from app.domain.enums import ConceptLibrary, DesignAttemptMethod
from app.services.design_pipeline import InvalidDesignAction, create_attempt, create_concept
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
    """Where the research concept lands.

    ``design_concept_id`` adds the attempt to an idea that already exists.
    Omitting it creates a new numbered concept from the research itself, which
    is the path that did not exist before Phase 1: the backlog was only
    reachable through ``concept_importer`` reading a Markdown file, so ten
    researched concepts could not become ten backlog concepts.
    """

    design_concept_id: uuid.UUID | None = None
    # Only read when creating. Empty falls back to the research concept's own
    # title, which is what the bench shows and what the owner just approved.
    title: str = Field(default="", max_length=200)


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


@router.post(
    "/runs/{run_id}/concepts/{concept_number}/pipeline",
    status_code=status.HTTP_201_CREATED,
)
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

    prompt = research.get("edited_prompt") or research.get("pass2_prompt")

    if body.design_concept_id is not None:
        target = session.get(DesignConcept, body.design_concept_id)
        if target is None:
            raise HTTPException(status_code=404, detail="Design concept not found.")
        created = False
    else:
        # The research becomes a numbered concept in its own library. Not the
        # tee library: concept_importer matches on (library, external_number)
        # and would overwrite this row's title and text the day
        # TSHIRT_CONCEPT_LIBRARY.md grew to the same number.
        title = body.title.strip() or str(research.get("title") or "").strip()
        if not title:
            title = f"Research concept {concept_number} from run {run_id}"
        try:
            target = create_concept(
                session,
                ConceptLibrary.VINTAGE_RESEARCH,
                title,
                str(research.get("concept") or research.get("summary") or prompt or ""),
                source_path=f"vintage-research/{run_id}#{concept_number}",
                parsed_json={
                    "vintage_research_run_id": run_id,
                    "research_concept_number": concept_number,
                },
            )
        except InvalidDesignAction as error:
            raise _fail(error) from error
        created = True
    # The attempt is opened only when the concept already has a brief carrying
    # a collection role and a graphic archetype. Phase 4 made that the
    # constitution's own order -- what a product is gets decided before artwork
    # exists -- and creating an attempt that cannot be worked is how this
    # endpoint produced dead rows for as long as it has existed.
    attempt = None
    if target.brief is not None and target.brief.ready_for_artwork:
        attempt = create_attempt(
            session,
            target,
            DesignAttemptMethod.IMAGE_GENERATION,
            production_prompt=str(prompt),
            model=settings.openai_image_model,
            model_settings={
                "size": settings.openai_image_size,
                "quality": settings.openai_image_quality,
            },
            reference_inputs={
                "vintage_research_run_id": run_id,
                "research_concept_number": concept_number,
                "evidence_listing_ids": run.get("evidence_listing_ids", []),
                "evidence_images": run.get("evidence_images", []),
            },
        )
    else:
        # The researched prompt is not lost -- it is the thing the brief is
        # written against, and the attempt picks it up when one is opened.
        target.preferred_execution = {
            **dict(target.preferred_execution),
            "vintage_research_run_id": run_id,
            "research_concept_number": concept_number,
            "production_prompt": str(prompt),
        }
    session.commit()
    payload = {
        "design_concept_id": str(target.id),
        "design_concept_number": target.external_number,
        "design_concept_title": target.title,
        "design_concept_library": target.library.value,
        "concept_created": created,
        "attempt_id": None if attempt is None else str(attempt.id),
        "attempt_number": None if attempt is None else attempt.attempt_number,
        "state": None if attempt is None else attempt.state.value,
        # What to do next, in words, rather than left for a screen to infer.
        "next_action": (
            "Open the attempt in Designs, copy the brief, make the artwork in a paid "
            "interface, and bring the file back to the drop zone."
            if attempt is not None
            else (
                "Open it in Work and write the brief: what the product is, its role in "
                "the range, and its graphic archetype. An attempt cannot open until "
                "those are chosen, and the researched prompt is kept against the "
                "concept until it does."
            )
        ),
    }
    mark_pipeline(run_id, concept_number, payload)
    return payload
