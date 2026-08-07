"""Scoring a design image over HTTP.

The design engine -- ``design_extraction`` measuring an image, ``design_scoring``
applying ``DESIGN_REVIEW_SCORECARD.md`` -- had no surface. This is it: upload a
design, get back the measurements, every gate with its evidence, the weighted
categories and the band.

No database. Scoring a design touches no world, no attempt and no canon, so this
router depends on nothing but the uploaded bytes.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.domain.design_review import CATEGORY_LIMITS
from app.services.design_extraction import extract, load_thresholds, measure
from app.services.design_scoring import score_design

router = APIRouter(prefix="/api/design", tags=["design"])

# Product photographs from the corpus run to a few hundred kilobytes. Ten
# megabytes is generous for a design file and small enough to refuse abuse.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


class GateView(BaseModel):
    gate: str
    status: str
    evidence: str


class CategoryView(BaseModel):
    category: str
    rating: int
    points: float
    max_points: int
    floor: int
    below_floor: bool


class ScoreResponse(BaseModel):
    """Everything the reviewer needs to see, in one payload."""

    design_id: str
    design_name: str
    measurements: dict[str, Any]
    blocked: bool
    total_score: float
    max_total_score: int
    band: str
    failed_gates: list[str]
    untested_gates: list[str]
    floor_failures: list[str]
    gates: list[GateView]
    categories: list[CategoryView]
    thresholds: dict[str, Any]


@router.get("/thresholds", summary="Corpus-derived scoring thresholds")
def get_thresholds() -> dict[str, Any]:
    """What the corpus says normal is, so a score can be read in context."""
    return {
        "thresholds": load_thresholds(),
        "categories": {
            category.value: {"max_points": maximum, "floor": floor}
            for category, (maximum, floor) in CATEGORY_LIMITS.items()
        },
    }


@router.post("/score", response_model=ScoreResponse, summary="Score a design image")
async def score_design_image(
    image: UploadFile = File(..., description="The design, worn or flat"),  # noqa: B008 -- FastAPI declares dependencies this way
    design_name: str = Form(default=""),
) -> ScoreResponse:
    """Measure an uploaded design and score it against the scorecard.

    The result always blocks: extraction fills the gates a measurement can
    honestly answer and leaves the rest untested, and an untested gate blocks
    release exactly as a failed one does. That is the scorecard's own rule --
    a design is not approved from one image -- so this is a starting point for
    a human review, never a verdict.
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

    outcome = score_design(review)
    evidence = {result.gate: result.evidence for result in review.gate_results}
    statuses = {result.gate: result.status for result in review.gate_results}

    return ScoreResponse(
        design_id=outcome.design_id,
        design_name=outcome.design_name,
        measurements=measurements.to_dict(),
        blocked=outcome.blocked,
        total_score=outcome.total_score,
        max_total_score=outcome.max_total_score,
        band=outcome.band.value,
        failed_gates=[gate.value for gate in outcome.failed_gates],
        untested_gates=[gate.value for gate in outcome.untested_gates],
        floor_failures=[category.value for category in outcome.floor_failures],
        gates=[
            GateView(gate=gate.value, status=statuses[gate].value, evidence=evidence[gate])
            for gate in statuses
        ],
        categories=[
            CategoryView(
                category=score.category.value,
                rating=score.rating,
                points=score.points,
                max_points=score.max_points,
                floor=score.floor,
                below_floor=score.below_floor,
            )
            for score in outcome.category_scores
        ],
        thresholds=load_thresholds(),
    )
