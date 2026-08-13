"""Two-part design queries backed by the retained vintage evidence corpus."""
from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.concept_models import DesignConcept
from app.db.session import get_db_session
from app.domain.enums import DesignAttemptMethod
from app.services.design_pipeline import InvalidDesignAction, create_attempt
from app.services.vintage_patterns import concept_pattern_query, retrieve_pattern, two_part_bundle

router = APIRouter(prefix="/api/vintage-design", tags=["vintage-design"])
SessionDependency = Annotated[Session, Depends(get_db_session)]


class TwoPartQueryIn(BaseModel):
    structure_query: str = Field(min_length=2, max_length=1000)
    creative_query: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=12, ge=1, le=30)


class TwoPartAttemptIn(BaseModel):
    creative_query: str | None = Field(default=None, max_length=4000)
    structure_query: str | None = Field(default=None, max_length=1000)
    evidence_limit: int = Field(default=12, ge=1, le=30)
    method: DesignAttemptMethod = DesignAttemptMethod.GENERATED
    production_prompt: str = ""
    model: str = ""
    model_settings: dict[str, Any] = Field(default_factory=dict)
    execution_rules: dict[str, Any] = Field(default_factory=dict)
    brief_overrides: dict[str, Any] = Field(default_factory=dict)


def _concept(session: Session, concept_id: uuid.UUID) -> DesignConcept:
    concept = session.get(DesignConcept, concept_id)
    if concept is None:
        raise HTTPException(status_code=404, detail="no such concept")
    return concept


@router.get("/patterns", summary="Preview the structural evidence half")
def pattern_preview(
    query: Annotated[str, Query(min_length=2, max_length=1000)],
    limit: Annotated[int, Query(ge=1, le=30)] = 12,
) -> dict[str, Any]:
    return retrieve_pattern(query, limit=limit)


@router.post("/two-part", summary="Preview structure evidence + original Shirtfaced content")
def two_part_preview(body: TwoPartQueryIn) -> dict[str, Any]:
    return two_part_bundle(body.structure_query, body.creative_query, limit=body.limit)


@router.post(
    "/concepts/{concept_id}/attempts",
    status_code=status.HTTP_201_CREATED,
    summary="Create a design attempt with vintage structure evidence frozen into provenance",
)
def create_two_part_attempt(
    concept_id: uuid.UUID,
    body: TwoPartAttemptIn,
    session: SessionDependency,
) -> dict[str, Any]:
    concept = _concept(session, concept_id)
    structure_query = (body.structure_query or concept_pattern_query(concept)).strip()
    creative_query = (body.creative_query or concept.concept_text or concept.title).strip()
    bundle = two_part_bundle(structure_query, creative_query, limit=body.evidence_limit)

    references = {
        "vintage_evidence": bundle["part_1_structure"],
        "original_content": creative_query,
        "separation_rule": bundle["combined_instruction"],
    }
    brief = dict(body.brief_overrides)
    brief["vintage_structure"] = bundle["part_1_structure"]["structure"]
    brief["original_content"] = creative_query

    rules = dict(body.execution_rules)
    rules.setdefault("vintage_evidence_role", "structure_only")
    rules.setdefault("copy_source_assets", False)
    rules.setdefault("synthesise_across_multiple_references", True)

    prompt = body.production_prompt.strip()
    if not prompt:
        prompt = (
            f"ORIGINAL SHIRTFACED CONTENT:\n{creative_query}\n\n"
            "Use the attached vintage evidence only for visual grammar: composition, scale, placement, "
            "type/illustration balance, print economy and period character. Synthesize across the evidence. "
            "Do not copy source logos, slogans, characters, brand identifiers or an exact source composition."
        )

    try:
        attempt = create_attempt(
            session,
            concept,
            body.method,
            brief_overrides=brief,
            production_prompt=prompt,
            model=body.model,
            model_settings=body.model_settings,
            reference_inputs=references,
            execution_rules=rules,
        )
    except InvalidDesignAction as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    session.commit()
    return {
        "attempt_id": str(attempt.id),
        "concept_id": str(concept.id),
        "attempt_number": attempt.attempt_number,
        "state": attempt.state.value,
        "structure_query": structure_query,
        "creative_query": creative_query,
        "vintage_match_count": bundle["part_1_structure"]["match_count"],
        "vintage_evidence": bundle["part_1_structure"],
        "production_prompt": attempt.production_prompt,
    }
