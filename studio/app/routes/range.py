"""The design range over HTTP, and the decision that trains it.

This is the second half of DESIGN_ENGINE_ADAPTATION.md section 9's thread. The
first half -- compose, approve, watch the confidence move -- is proven at the
engine level and tested. None of it was reachable: `CompositionEngine` sat on no
route, so the approve control that is supposed to be the training signal did not
exist for anyone to press.

Three endpoints, and the shape matters.

``POST /api/range`` takes whatever the owner supplied -- images and phrases in
any mix -- and lays it across every garment. It stores nothing, because looking
should be free and a range is cheap to rebuild from a seed.

``POST /api/range/decision`` records an approval or a rejection against a
template. That is the feedback edge and the reason the control exists: section 9
is explicit that if approving does not move the number, the loop is decorative.
It answers with the confidence before and after, so the person pressing it can
see that it did.

``GET /api/range/templates`` shows what the engine has learned so far, which is
the only way to check the kill gate in section 10 without reading a JSON file
off the disk.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.composition_engine import CompositionEngine, Element
from app.services.design_range import Range, build

router = APIRouter(prefix="/api/range", tags=["range"])

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = REPO_ROOT / "studio" / "var" / "design_corpus" / "design_templates.json"
APPROVALS = REPO_ROOT / "studio" / "var" / "approvals.json"


def get_engine() -> CompositionEngine:
    """One engine per request.

    Constructed rather than cached because the approval store is read at
    construction: a cached engine would keep serving the confidence it saw at
    startup, and the whole point is that the number moves while you watch.
    """
    return CompositionEngine(TEMPLATES, APPROVALS)


EngineDependency = Annotated[CompositionEngine, Depends(get_engine)]


class SuppliedElement(BaseModel):
    """One thing the owner handed over. Never invented, never edited."""

    kind: Literal["text", "image", "logo"]
    content: str = ""
    # Width over height. Only meaningful for images, and the reason a tall
    # photograph and a wide one are not the same brief.
    aspect: float = Field(default=1.0, gt=0)


class RangeRequest(BaseModel):
    elements: list[SuppliedElement] = Field(min_length=1, max_length=4)
    tradition: str | None = "streetwear"


class DecisionRequest(BaseModel):
    element_count: int = Field(ge=1, le=4)
    template_id: str
    approved: bool
    # No default. A decision has an author or it is not a decision.
    decided_by: str = Field(min_length=1, max_length=120)


def _elements(request: RangeRequest) -> tuple[Element, ...]:
    return tuple(Element(kind=e.kind, content=e.content, aspect=e.aspect) for e in request.elements)


def _placement_view(placed: Any) -> dict[str, Any]:
    composition = placed.composition
    leading = composition.options[0] if composition.options else None
    return {
        "view": placed.view,
        "zone": placed.zone_key,
        "scale_role": placed.scale_role,
        "form": placed.form.key,
        "form_label": placed.form.label,
        "zone_mm": [placed.zone_width_mm, placed.zone_height_mm],
        "composable": composition.composable,
        "refusal_reason": composition.refusal_reason,
        "refusal_detail": composition.refusal_detail,
        "gaps": list(composition.gaps),
        "options": [
            {
                "template_id": option.template_id,
                "template_name": option.template_name,
                "fit": option.fit,
                "confidence": option.confidence,
                "corpus_designs": option.corpus_designs,
                "approvals": option.approvals,
                "decisions": option.decisions,
                "rationale": option.rationale,
                "slots": [
                    {
                        "slot": s.slot,
                        "kind": s.element_kind,
                        "content": s.content,
                        "top": s.top,
                        "height": s.height,
                        "width": s.width,
                        "centre_x": s.centre_x,
                    }
                    for s in option.slots
                ],
            }
            for option in composition.options
        ],
        "leading_template": leading.template_id if leading else "",
    }


def _range_view(built: Range) -> dict[str, Any]:
    return {
        "garments": [
            {
                "garment": g.garment,
                "offered": g.offered,
                "refusal_reason": g.refusal_reason,
                "refusal_detail": g.refusal_detail,
                "placements": [_placement_view(p) for p in g.placed],
            }
            for g in built.garments
        ],
        "offered": built.offered,
        "total": len(built.garments),
        "gaps": list(built.gaps),
    }


@router.post("", summary="Lay supplied assets across every garment")
def build_range(request: RangeRequest, engine: EngineDependency) -> dict[str, Any]:
    """Answer with the whole range. Stores nothing."""
    if not engine.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "reason": "NO_TEMPLATES",
                "detail": "the corpus has not been mined here; run learn_design_templates.py",
            },
        )
    return _range_view(build(_elements(request), engine, tradition=request.tradition))


@router.post("/decision", summary="Approve or reject a template, and train the engine")
def record_decision(request: DecisionRequest, engine: EngineDependency) -> dict[str, Any]:
    """Record one decision and answer with what it changed.

    Before and after are both returned because the claim being made is that the
    decision moved something. Reporting only the new number asks to be trusted;
    reporting both can be checked.
    """
    key = engine.template_key(request.element_count, request.template_id)
    approved_before, decisions_before = engine.approvals.history(key)

    engine.record_decision(request.element_count, request.template_id, request.approved)

    # Re-read the store this request is actually using rather than constructing
    # a default one, or a test with an overridden store would report against the
    # real file.
    reloaded = CompositionEngine(engine.templates_path, engine.approvals.path)
    approved_after, decisions_after = reloaded.approvals.history(key)
    if decisions_after == decisions_before:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"reason": "DECISION_NOT_RECORDED", "detail": key},
        )

    return {
        "template": key,
        "decided_by": request.decided_by,
        "approved": request.approved,
        "before": {"approvals": approved_before, "decisions": decisions_before},
        "after": {"approvals": approved_after, "decisions": decisions_after},
    }


@router.get("/templates", summary="What the engine has learned")
def learned(engine: EngineDependency) -> list[dict[str, Any]]:
    """Every template with a decision against it, most decided first.

    The kill gate in section 10 is whether these numbers move within the first
    twenty decisions. Without a surface it can only be checked by reading a file
    off the disk, which means in practice it is not checked.
    """
    # pylint: disable=protected-access
    store = engine.approvals._data
    rows = [
        {
            "template": key,
            "approvals": int(entry.get("approved", 0)),
            "decisions": int(entry.get("decisions", 0)),
            "approval_rate": (
                round(entry.get("approved", 0) / entry["decisions"], 4)
                if entry.get("decisions")
                else None
            ),
        }
        for key, entry in store.items()
    ]
    return sorted(rows, key=lambda r: -r["decisions"])
