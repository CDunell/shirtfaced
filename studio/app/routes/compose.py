"""Composing designs over HTTP.

The archive has 107 elements, 22 garments and 14 placements per fit, and until
this router existed none of it was reachable from the application. The engine
was a library you could drive from a Python prompt and nowhere else.

Three things, which is all it takes to make an engine into a product: compose a
brief and see what comes back, keep the ones worth keeping, and settle them.

A composed design is not a kept design and a kept design is not an approved one.
``POST /compose`` returns options and stores nothing. ``POST /designs`` keeps
one. ``POST /designs/{id}/decision`` is the only way out of
``awaiting_decision``, and it requires a name, because an approval nobody signed
is not an approval.
"""

from __future__ import annotations

import dataclasses
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.archive.palettes import SYSTEMS
from app.config import Settings, get_settings
from app.db.archive_models import ArchiveElement, ComposedDesign
from app.db.concept_models import DesignConcept
from app.db.session import get_db_session
from app.domain.enums import AttemptState, DesignAssetKind, DesignAttemptMethod
from app.services.design_composition import (
    CompositionRefused,
    Request,
    compose,
    decide,
    grammar_history,
    recompose,
    store,
)
from app.services.design_pipeline import (
    ElementUse,
    create_attempt,
    record_asset,
    submit_attempt,
)

router = APIRouter(prefix="/api/compose", tags=["compose"])

SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


class BriefIn(BaseModel):
    """What the owner supplies. The words are theirs and are never edited."""

    seed: int = Field(ge=0, description="Same seed, same brief, same bytes.")
    garment_key: str = Field(description="A file stem in assets/garments, without .svg")
    primary_text: str = ""
    secondary_text: str = ""
    placement: str = "centre_chest"
    fit: str = "adult"
    treatment: str = "clean"
    garment_colour: str = "#101010"
    inks: int = Field(default=2, ge=1, le=6)
    colour_system: str = Field(default="", description="Empty lets the seed choose")
    limit: int = Field(default=6, ge=1, le=12)

    def to_request(self) -> Request:
        return Request(
            seed=self.seed,
            garment_key=self.garment_key,
            primary_text=self.primary_text,
            secondary_text=self.secondary_text,
            placement=self.placement,
            fit=self.fit,
            treatment=self.treatment,
            garment_colour=self.garment_colour,
            inks=self.inks,
            colour_system=self.colour_system,
            limit=self.limit,
        )


class OptionView(BaseModel):
    grammar_key: str
    grammar_name: str
    reads_as: str
    rationale: str
    score: float
    confidence: float
    approvals: int
    decisions: int
    width_mm: float
    height_mm: float
    content_hash: str
    parts: dict[str, str]
    svg: str


class DesignView(BaseModel):
    id: str
    seed: int
    garment_key: str
    placement_key: str
    grammar_key: str
    state: str
    width_mm: float
    height_mm: float
    content_hash: str
    parts: dict[str, Any]
    decided_by: str
    decision_note: str
    svg: str

    @classmethod
    def of(cls, design: ComposedDesign) -> DesignView:
        return cls(
            id=str(design.id),
            seed=design.seed,
            garment_key=design.garment_key,
            placement_key=design.placement_key,
            grammar_key=design.grammar_key,
            state=design.state,
            width_mm=design.width_mm,
            height_mm=design.height_mm,
            content_hash=design.content_hash,
            parts=design.parts,
            decided_by=design.decided_by,
            decision_note=design.decision_note,
            svg=design.svg,
        )


class DecisionIn(BaseModel):
    approved: bool
    # No default. A decision has an author or it is not a decision.
    decided_by: str = Field(min_length=1, max_length=120)
    note: str = ""


def _refused(error: CompositionRefused) -> HTTPException:
    """A refusal is an answer, not a crash, and it keeps its reason code.

    422 rather than 500: the brief was understood and could not be met. The
    reason is durable and worth showing to whoever wrote the brief.
    """
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"reason": error.reason, "detail": error.detail},
    )


@router.get("/palettes", summary="The ink systems available")
def list_palettes() -> list[dict[str, Any]]:
    """What can be printed, and what each one is for."""
    return [
        {"key": s.key, "label": s.label, "inks": list(s.inks), "reads_as": s.reads_as}
        for s in SYSTEMS
    ]


@router.post("", response_model=list[OptionView], summary="Compose options for a brief")
def compose_brief(brief: BriefIn, session: SessionDependency) -> list[OptionView]:
    """Answer a brief. Stores nothing -- looking is free and reversible.

    The session is read-only here: it supplies the approve/reject history that
    weights each option's confidence, straight from ``composed_designs``.
    """
    try:
        _, options = compose(brief.to_request(), grammar_history(session))
    except CompositionRefused as error:
        raise _refused(error) from error

    return [
        OptionView(
            grammar_key=option.grammar_key,
            grammar_name=option.grammar_name,
            reads_as=option.reads_as,
            rationale=option.rationale,
            score=option.score,
            confidence=option.confidence,
            approvals=option.approvals,
            decisions=option.decisions,
            width_mm=option.design.width_mm,
            height_mm=option.design.height_mm,
            content_hash=option.design.content_hash,
            parts=dict(option.parts),
            svg=option.design.svg,
        )
        for option in options
    ]


@router.post(
    "/designs",
    response_model=DesignView,
    status_code=status.HTTP_201_CREATED,
    summary="Keep one composed option",
)
def keep_design(
    brief: BriefIn,
    session: SessionDependency,
    settings: SettingsDependency,
    grammar_key: Annotated[str, Query(description="Which option to keep")],
    concept_id: Annotated[
        uuid.UUID | None,
        Query(description="Keep this design as an attempt on a backlog concept"),
    ] = None,
) -> DesignView:
    """Recompose the brief and keep the named option.

    The brief is recomposed rather than the artwork being posted back, so what
    is stored is what this engine produces for these inputs. A client cannot
    hand us artwork and have it recorded as though the archive made it.

    With ``concept_id``, the kept design becomes a design attempt on that
    concept: the composer is a producer feeding the pipeline, and one call
    takes a concept to ``awaiting_decision``. The decision then belongs to
    ``/api/concepts``, not to this router.
    """
    request = brief.to_request()
    try:
        _, options = compose(request, grammar_history(session))
    except CompositionRefused as error:
        raise _refused(error) from error

    chosen = next((o for o in options if o.grammar_key == grammar_key), None)
    if chosen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "reason": "NO_SUCH_OPTION",
                "detail": f"{grammar_key} is not among {[o.grammar_key for o in options]}",
            },
        )

    if concept_id is None:
        design = store(session, request, chosen)
        # The dependency closes the session without committing; a kept design
        # that vanished with the request would make this endpoint a lie.
        session.commit()
        return DesignView.of(design)

    concept = session.get(DesignConcept, concept_id)
    if concept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such concept")

    # role -> element_key, resolved to archive rows so provenance is a join
    # rather than a JSON scan. A key that no longer resolves is skipped: the
    # parts blob on the composed row still holds the full record.
    keys = list(chosen.parts.values())
    elements_by_key = {
        element.element_key: element
        for element in session.execute(
            select(ArchiveElement).where(ArchiveElement.element_key.in_(keys))
        ).scalars()
    }
    uses = [
        ElementUse(element_id=elements_by_key[key].id, role=role)
        for role, key in chosen.parts.items()
        if key in elements_by_key
    ]

    attempt = create_attempt(
        session,
        concept,
        DesignAttemptMethod.DETERMINISTIC_COMPOSITION,
        brief_overrides={"compose_request": dataclasses.asdict(request)},
        elements=uses,
    )
    design = store(session, request, chosen, attempt=attempt)
    record_asset(
        session,
        FilesystemAssetStore(settings.assets_root_resolved),
        attempt,
        DesignAssetKind.ARTWORK,
        "design.svg",
        design.svg.encode("utf-8"),
        "image/svg+xml",
    )
    submit_attempt(session, attempt)
    session.commit()
    return DesignView.of(design)


@router.get("/designs", response_model=list[DesignView], summary="Designs, newest first")
def list_designs(
    session: SessionDependency,
    state: Annotated[str | None, Query(description="Filter by state")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[DesignView]:
    statement = select(ComposedDesign).order_by(ComposedDesign.created_at.desc()).limit(limit)
    if state:
        statement = statement.where(ComposedDesign.state == state)
    return [DesignView.of(row) for row in session.execute(statement).scalars()]


def _load(session: Session, design_id: str) -> ComposedDesign:
    design = session.get(ComposedDesign, design_id)
    if design is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no such design")
    return design


@router.get("/designs/{design_id}", response_model=DesignView, summary="One design")
def get_design(design_id: str, session: SessionDependency) -> DesignView:
    return DesignView.of(_load(session, design_id))


@router.get(
    "/designs/{design_id}.svg",
    response_class=Response,
    summary="One design's artwork",
)
def get_design_svg(design_id: str, session: SessionDependency) -> Response:
    """The artwork itself, so a browser or a print step can fetch it directly."""
    return Response(content=_load(session, design_id).svg, media_type="image/svg+xml")


@router.post(
    "/designs/{design_id}/decision",
    response_model=DesignView,
    summary="Approve or reject a design",
)
def decide_design(design_id: str, decision: DecisionIn, session: SessionDependency) -> DesignView:
    """The only way out of awaiting_decision, and it needs a person's name."""
    design = _load(session, design_id)
    if design.design_attempt_id is not None:
        # One decision surface per design. Deciding here as well would let the
        # compose bench and the designs bench disagree about the same artwork.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "reason": "DECIDED_ELSEWHERE",
                "detail": (
                    "this design belongs to a design attempt; decide it at "
                    f"/api/concepts/attempts/{design.design_attempt_id}/decision"
                ),
            },
        )
    try:
        settled = decide(session, design, decision.approved, decision.decided_by, decision.note)
    except CompositionRefused as error:
        raise _refused(error) from error
    session.commit()
    return DesignView.of(settled)


@router.post(
    "/designs/{design_id}/verify",
    summary="Rebuild the artwork from the stored brief",
)
def verify_design(design_id: str, session: SessionDependency) -> dict[str, Any]:
    """Prove the design can still be regenerated from its brief alone.

    Determinism inside one process is what the unit tests show. This is the
    claim that matters commercially: months later, on another machine, the row
    still rebuilds the artwork that was approved. A mismatch is a regression and
    should be found here rather than by a reprint that does not match.
    """
    design = _load(session, design_id)
    try:
        rebuilt = recompose(design)
    except CompositionRefused as error:
        return {
            "reproducible": False,
            "reason": error.reason,
            "detail": error.detail,
            "assembler_version": design.assembler_version,
        }
    return {
        "reproducible": rebuilt == design.svg,
        "content_hash": design.content_hash,
        "assembler_version": design.assembler_version,
        "state": design.state,
        "awaiting": design.state == AttemptState.AWAITING_DECISION.value,
    }
