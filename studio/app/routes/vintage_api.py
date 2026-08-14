"""JSON for the vintage benches.

The vintage pages were server-rendered HTML built inside Python string
literals, which is why a navigation change meant editing a 2,000-character
line. Studio already has a React shell with a component library and tests, so
the pages move there and this serves them data.

Nothing here holds logic. ``vintage_research`` already owns retrieval,
execution and persistence; these are the thin wrappers that let a browser
reach them. The evidence listing keeps its existing endpoint in
``vintage_evidence``.

Sending an approved concept to the design pipeline is deliberately absent:
``vintage_design`` already does it, and does it properly -- it checks the
concept is approved, resolves the design concept, refuses an empty prompt
and creates the DesignAttempt. A wrapper here only recorded the intent and
created nothing, which made the button look like it worked.
"""

from __future__ import annotations

import io
import json
import zipfile
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.concept_models import DesignConcept
from app.db.session import get_db_session
from app.domain.errors import StudioError
from app.services.vintage_research import (
    VintageResearchError,
    _image_path,
    execute_research,
    import_run,
    list_runs,
    load_run,
    prepare_manual_run,
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


class ManualImport(BaseModel):
    """Concepts produced by hand, plus the selection they were produced from."""

    concepts: list[dict[str, Any]]
    prepared: dict[str, Any] = Field(default_factory=dict)


@router.post("/manual/prepare")
def manual_prepare(body: RunRequest) -> dict[str, Any]:
    """The prompt and the images, with no model call and no API spend.

    Selection is identical to POST /runs -- the same images in the same order.
    The difference is who runs the passes: this hands them to a person with a
    subscription instead of billing an API key for capability already paid for.
    """
    try:
        return prepare_manual_run(
            filters={
                "query": body.query,
                "brand": body.brand,
                "era": body.era,
                "tradition": body.tradition,
            },
            listing_ids=body.listing_ids or None,
            image_limit=body.image_limit,
        )
    except VintageResearchError as error:
        raise _handled(error) from error


@router.post("/manual/bundle")
def manual_bundle(body: RunRequest) -> StreamingResponse:
    """The same selection as /manual/prepare, as one zip.

    Saving sixteen images one right-click at a time is the tedious part of the
    manual path, and on a phone it is worse. The archive is a few megabytes per
    run, so this builds the zip in memory rather than staging files.

    Carries the prompts and a manifest beside the images: a folder of unlabelled
    jpegs a week later is not evidence of anything, and the manifest is what
    lets a design be traced back to the listings that informed it.
    """
    try:
        prepared = prepare_manual_run(
            filters={
                "query": body.query,
                "brand": body.brand,
                "era": body.era,
                "tradition": body.tradition,
            },
            listing_ids=body.listing_ids or None,
            image_limit=body.image_limit,
        )
    except VintageResearchError as error:
        raise _handled(error) from error

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("pass-1-prompt.txt", prepared["pass1_prompt"])
        archive.writestr("pass-2-prompt.txt", prepared["pass2_prompt"])
        archive.writestr(
            "manifest.json",
            json.dumps(
                {
                    "filters": prepared["evidence_filters"],
                    "listings": prepared["evidence_listings"],
                    "images": prepared["evidence_images"],
                },
                indent=2,
            ),
        )
        for index, image in enumerate(prepared["evidence_images"], start=1):
            try:
                _, path = _image_path(image["image_url"])
            except VintageResearchError:
                # A missing file is a gap in the zip, not a failed download.
                continue
            archive.writestr(f"images/{index:02d}-{path.name}", path.read_bytes())

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="vintage-research-run.zip"'},
    )


@router.post("/manual/import", status_code=201)
def manual_import(body: ManualImport) -> dict[str, Any]:
    """Store hand-run concepts as an ordinary run, held to the same validation."""
    try:
        return import_run({"concepts": body.concepts}, body.prepared)
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


@router.get("/design-concepts")
def design_concepts(session: SessionDep) -> list[dict[str, Any]]:
    """Targets for sending an approved concept into the design pipeline."""
    rows = session.query(DesignConcept).order_by(DesignConcept.external_number).all()
    return [{"id": str(r.id), "number": r.external_number, "title": r.title} for r in rows]
