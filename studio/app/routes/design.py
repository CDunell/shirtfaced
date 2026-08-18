"""Measuring a design image over HTTP.

The design engine -- ``design_extraction`` measuring an image into
``domain.ts``-shaped gate results and score categories. This is the surface
for it: upload a design, get back the measurements and every gate/category the
image supports, with evidence.

No scoring, banding or status decision happens here. Those belong to
``admin/src/design-system/workflow.ts``'s ``evaluateReview`` /
``nextStatusForReview`` -- the tested contract this route's payload is shaped
to feed, not a second implementation of it
(``studio/docs/DESIGN_ENGINE_ADAPTATION.md`` Section 8).

The only database read is the thresholds: what the measured corpus
(``design_measurements``) says normal is, so a measurement can be read in
context. Measuring itself touches no world, no attempt and no canon.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.services.design_extraction import (
    CATEGORY_LIMITS,
    extract,
    load_thresholds,
    measure,
    points_floor,
)

router = APIRouter(prefix="/api/design", tags=["design"])

SessionDependency = Annotated[Session, Depends(get_db_session)]

# Product photographs from the corpus run to a few hundred kilobytes. Ten
# megabytes is generous for a design file and small enough to refuse abuse.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


class GateView(BaseModel):
    id: str
    label: str
    result: str
    evidence: str


class CategoryView(BaseModel):
    id: str
    label: str
    score: float
    maximum: int
    minimumRequired: int | None = None
    notes: str = ""


class ScoreResponse(BaseModel):
    """Everything a downstream review needs, in ``domain.ts``'s shape.

    ``hardGates`` and ``scoreCategories`` match ``hardGateSchema`` /
    ``scoreCategorySchema`` field-for-field so the caller can hand this
    straight to ``evaluateReview`` without translation. Gates this module
    could not test are still present, marked ``not_tested``; categories it
    could not rate are simply absent, not defaulted to zero.
    """

    designId: str
    designName: str
    measurements: dict[str, Any]
    hardGates: list[GateView]
    scoreCategories: list[CategoryView]
    thresholds: dict[str, Any]


@router.get("/thresholds", summary="Corpus-derived scoring thresholds")
def get_thresholds(session: SessionDependency) -> dict[str, Any]:
    """What the corpus says normal is, so a score can be read in context."""
    return {
        "thresholds": load_thresholds(session),
        "categories": {
            category_id: {
                "label": label,
                "maximum": maximum,
                "minimumRequired": points_floor(category_id),
            }
            for category_id, (label, maximum, _rating_floor) in CATEGORY_LIMITS.items()
        },
    }


@router.post("/score", response_model=ScoreResponse, summary="Measure a design image")
async def score_design_image(
    session: SessionDependency,
    image: UploadFile = File(..., description="The design, worn or flat"),
    design_name: str = Form(default=""),
) -> ScoreResponse:
    """Measure an uploaded design and report the gates/categories it supports.

    Every hard gate this module cannot test comes back ``not_tested``, and an
    untested gate blocks release exactly as a failed one does under
    ``workflow.ts``'s ``evaluateReview`` -- that is the scorecard's own rule,
    a design is not approved from one image. This is a starting point for a
    human review, never a verdict.
    """
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Expected one of {', '.join(sorted(ALLOWED_TYPES))}, got {image.content_type}.",
        )

    data = await image.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"Image is {len(data) / 1024 / 1024:.1f} MB; the limit is "
            f"{MAX_UPLOAD_BYTES / 1024 / 1024:.0f} MB.",
        )

    name = design_name.strip() or (image.filename or "Untitled design")

    # Written to a temporary file because the measurement path takes a path:
    # the same code serves the CLI, the corpus miner and this route.
    suffix = Path(image.filename or "upload.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        temp_path = Path(handle.name)

    try:
        measurements = measure(temp_path)
        review = extract(name, name, temp_path)
    except Exception as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"The image could not be measured: {error}",
        ) from error
    finally:
        temp_path.unlink(missing_ok=True)

    return ScoreResponse(
        designId=review["designId"],
        designName=review["designName"],
        measurements=measurements.to_dict(),
        hardGates=[GateView(**gate) for gate in review["hardGates"]],
        scoreCategories=[CategoryView(**category) for category in review["scoreCategories"]],
        thresholds=load_thresholds(session),
    )
