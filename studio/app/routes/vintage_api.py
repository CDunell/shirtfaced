"""JSON for the vintage benches.

The vintage pages were server-rendered HTML built inside Python string
literals, which is why a navigation change meant editing a 2,000-character
line. Studio already has a React shell with a component library and tests, so
the pages move there and this serves them data.

Nothing here holds logic. ``vintage_research`` already owns retrieval,
execution and persistence; these are the thin wrappers that let a browser
reach them. The evidence listing keeps its existing endpoint in
``vintage_evidence``.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.concept_models import DesignConcept
from app.db.session import get_db_session
from app.domain.errors import StudioError
from app.services.vintage_research import (
    VintageResearchError,
    execute_research,
    list_runs,
    load_run,
    mark_pipeline,
    update_concept,
)

router = APIRouter(prefix="/api/vintage-research", tags=["vintage-research"])
SessionDep = Annotated[Session, Depends(get_db_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


class RunRequest(BaseModel):
    query: str = ""
    brand: str = ""
    era: str = ""
    tradition: str = ""
    image_limit: int = Field(default=16, ge=1, le=24)
    listing_ids: list[str] = Field(default_factory=list)


class ConceptUpdate(BaseModel):
    """Both fields optional: a reviewer may set a status, an edit, or both."""

    status: str | None = None
    prompt: str | None = None
    review_note: str | None = None


class PipelineRequest(BaseModel):
    design_concept_id: str


def _handled(error: StudioError) -> HTTPException:
    """A research error is the caller's problem, not a server fault.

    Everything this service raises describes a bad id, an empty selection or a
    model response that failed validation. Left unhandled they surface as 500s
    with no message, which is how a reload of /vintage-research/run read as an
    Internal Server Error rather than "that is not a run id".
    """
    text = str(error)
    status = 404 if "not found" in text.lower() or "invalid" in text.lower() else 400
    return HTTPException(status_code=status, detail=text)


@router.get("/runs")
def runs_index() -> list[dict[str, Any]]:
    return list_runs()


@router.post("/runs", status_code=201)
def runs_create(body: RunRequest, settings: SettingsDep) -> dict[str, Any]:
    try:
        return execute_research(
            settings,
            filters={
                "query": body.query,
                "brand": body.brand,
                "era": body.era,
                "tradition": body.tradition,
            },
            listing_ids=body.listing_ids or None,
            image_urls=None,
            image_limit=body.image_limit,
        )
    except VintageResearchError as error:
        raise _handled(error) from error


@router.get("/runs/{run_id}")
def runs_show(run_id: str) -> dict[str, Any]:
    try:
        return load_run(run_id)
    except VintageResearchError as error:
        raise _handled(error) from error


@router.post("/runs/{run_id}/concepts/{number}")
def concept_update(run_id: str, number: int, body: ConceptUpdate) -> dict[str, Any]:
    try:
        return update_concept(
            run_id,
            number,
            status=body.status,
            edited_prompt=body.prompt,
            review_note=body.review_note,
        )
    except VintageResearchError as error:
        raise _handled(error) from error


@router.post("/runs/{run_id}/concepts/{number}/pipeline", status_code=202)
def concept_to_pipeline(run_id: str, number: int, body: PipelineRequest) -> dict[str, str]:
    try:
        mark_pipeline(run_id, number, {"design_concept_id": body.design_concept_id})
    except VintageResearchError as error:
        raise _handled(error) from error
    return {"status": "queued"}


@router.get("/design-concepts")
def design_concepts(session: SessionDep) -> list[dict[str, Any]]:
    """Targets for sending an approved concept into the design pipeline."""
    rows = session.query(DesignConcept).order_by(DesignConcept.external_number).all()
    return [{"id": str(r.id), "number": r.external_number, "title": r.title} for r in rows]
