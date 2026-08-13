"""Mount the Vintage Evidence research UI and its pipeline hand-off."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.concept_models import DesignConcept
from app.db.session import get_db_session
from app.domain.enums import DesignAttemptMethod
from app.routes import vintage_research_page
from app.services.design_pipeline import create_attempt
from app.services.vintage_research import load_run, mark_pipeline

router = APIRouter()
router.include_router(vintage_research_page.router)
SessionDep = Annotated[Session, Depends(get_db_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/vintage-design")
def old_page() -> RedirectResponse:
    return RedirectResponse("/vintage-research", status_code=307)


@router.post("/vintage-research/{run_id}/{number}/pipeline")
def send_to_pipeline(
    run_id: str,
    number: int,
    session: SessionDep,
    settings: SettingsDep,
    design_concept_id: uuid.UUID = Form(...),
) -> RedirectResponse:
    run = load_run(run_id)
    research = next(
        (item for item in run.get("concepts", []) if item.get("concept_number") == number),
        None,
    )
    if research is None:
        raise HTTPException(status_code=404, detail="Research concept not found.")
    if research.get("status") != "approved":
        raise HTTPException(status_code=422, detail="Approve the research concept first.")
    target = session.get(DesignConcept, design_concept_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Design concept not found.")
    prompt = str(research.get("edited_prompt") or research.get("pass2_prompt") or "").strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Research prompt is empty.")

    attempt = create_attempt(
        session,
        target,
        DesignAttemptMethod.IMAGE_GENERATION,
        production_prompt=prompt,
        model=settings.openai_image_model,
        model_settings={
            "size": settings.openai_image_size,
            "quality": settings.openai_image_quality,
        },
        reference_inputs={
            "vintage_research_run_id": run_id,
            "research_concept_number": number,
            "evidence_listing_ids": run.get("evidence_listing_ids", []),
            "evidence_images": run.get("evidence_images", []),
        },
    )
    session.commit()
    mark_pipeline(
        run_id,
        number,
        {
            "design_concept_id": str(target.id),
            "attempt_id": str(attempt.id),
            "attempt_number": attempt.attempt_number,
            "state": attempt.state.value,
        },
    )
    return RedirectResponse(f"/vintage-research/{run_id}", status_code=303)
