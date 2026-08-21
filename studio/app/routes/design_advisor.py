"""Recommending presentation for a phrase or graphic over HTTP.

The other direction from ``design.py``: that route measures a design that
already exists, this one recommends how to present content that doesn't yet.
See ``app/services/design_advisor.py`` for what it will and will not decide.

The evidence is ``design_measurements`` -- the corpus measured by code, in
the database where it cannot be absent from the box the way the mined JSON
file it replaced always was. An empty table keeps the same honest meaning:
every recommendation is a marked default until the corpus is measured.
"""

from __future__ import annotations

import re
import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStoreError, FilesystemAssetStore
from app.config import Settings, get_settings
from app.db.concept_models import DesignBrief
from app.db.concept_pool_models import DesignConceptPoolEntry
from app.db.generation_sample_models import DesignGenerationSample
from app.db.session import get_db_session
from app.domain.enums import CollectionRole, ConceptLibrary, DesignAttemptMethod, GraphicArchetype
from app.services.design_advisor import advise, measurement_rows, render_generation_prompt
from app.services.design_pipeline import InvalidDesignAction, create_attempt, create_concept

router = APIRouter(prefix="/api/design", tags=["design"])

SessionDependency = Annotated[Session, Depends(get_db_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


class AdviseRequest(BaseModel):
    phrase: str = ""
    has_graphic: bool = False
    tradition: str = "novelty"


class RecommendationView(BaseModel):
    field: str
    value: str
    evidence: str
    confidence: str


class DirectionResponse(BaseModel):
    """``DesignDirection.to_dict()``'s own shape, plus a paste-ready prompt."""

    input: str
    intent: str
    tradition: str
    recommendations: list[RecommendationView]
    alternatives: list[str]
    not_decided: list[str]
    generation_prompt: str
    concept_id: str | None = None


class RandomRequest(BaseModel):
    tradition: str = "novelty"


@router.post("/advise", response_model=DirectionResponse, summary="Recommend presentation")
def advise_design(payload: AdviseRequest, session: SessionDependency) -> DirectionResponse:
    """Recommend how to present a supplied phrase and/or graphic.

    Prescribes presentation only -- archetype, scale, coverage, ink count,
    placement, polarity. Never the idea, the artwork or whether either is any
    good; see ``not_decided`` in the response for what this deliberately
    leaves to a human.
    """
    if not payload.phrase.strip() and not payload.has_graphic:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Supply a phrase, set has_graphic true, or both -- "
            "there is nothing to advise on otherwise.",
        )

    direction = advise(
        phrase=payload.phrase,
        has_graphic=payload.has_graphic,
        tradition=payload.tradition,
        rows=measurement_rows(session),
    )
    return DirectionResponse(
        **direction.to_dict(),
        generation_prompt=render_generation_prompt(direction, payload.phrase),
    )


@router.post(
    "/random", response_model=DirectionResponse, summary="A batch-written concept, not typed"
)
def random_design(payload: RandomRequest, session: SessionDependency) -> DirectionResponse:
    """Pick one batch-generated concept for this tradition and advise on it.

    The concept text was written once, in a session, ahead of time -- see
    ``app/db/concept_pool_models.py`` -- never a live model call. This picks a
    row at random and runs it through the same ``advise()`` +
    ``render_generation_prompt()`` path as a typed idea, so the output is
    exactly as evidence-backed either way. Hit and miss by nature: nobody
    curated any one row, only the batch as a whole.
    """
    entry = session.execute(
        select(DesignConceptPoolEntry)
        .where(
            DesignConceptPoolEntry.tradition == payload.tradition,
            DesignConceptPoolEntry.active.is_(True),
        )
        .order_by(func.random())
        .limit(1)
    ).scalar_one_or_none()
    if entry is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"No batch-generated concepts for tradition '{payload.tradition}' yet.",
        )

    # entry.concept_text is an English description of a scene/graphic --
    # "A vintage skate-shop price tag, string and all, blown up to graphic
    # scale..." -- not on-shirt copy. advise() buckets ink/coverage/scale by
    # word count because that's a real proxy for print size when the phrase
    # IS what gets printed (a typed idea in /advise might be). Passing a
    # 25-to-35-word description as that phrase put every single pool concept
    # in the same "7+ words" bucket regardless of tradition, so within one
    # tradition every random pick returned the same fixed ink/coverage/scale
    # numbers -- only the concept text ever changed. Advise on the graphic
    # alone (no phrase) so the numbers reflect an actual graphic-led design
    # in this tradition, not a description miscounted as a slogan.
    direction = advise(
        phrase="",
        has_graphic=True,
        tradition=payload.tradition,
        rows=measurement_rows(session),
    )
    return DirectionResponse(
        **direction.to_dict(),
        generation_prompt=render_generation_prompt(direction, entry.concept_text),
        concept_id=str(entry.id),
    )


class RetireResponse(BaseModel):
    concept_id: str
    active: bool


@router.post(
    "/concept-pool/{concept_id}/retire",
    response_model=RetireResponse,
    summary="Take a bad batch-written concept out of rotation",
)
def retire_concept(concept_id: str, session: SessionDependency) -> RetireResponse:
    """Set one pool entry to inactive so ``/random`` stops serving it.

    The only pruning tool available for this pool that doesn't require
    database access -- see ``app/db/concept_pool_models.py``'s ``active``
    column, which was worthless without a button in front of it.
    """
    try:
        parsed_id = uuid.UUID(concept_id)
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not a valid concept id.") from error

    entry = session.get(DesignConceptPoolEntry, parsed_id)
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No concept with that id.")

    entry.active = False
    session.commit()
    return RetireResponse(concept_id=concept_id, active=False)


# --- Quick attempt: idea straight to an upload-ready attempt ---------------
#
# `create_attempt` (design_pipeline.py) refuses without a brief carrying a
# collection role and a graphic archetype -- constitution steps 2 and 4,
# enforced where artwork begins, not a screen's choice to make or skip. This
# answers both here instead of sending the owner to Work to fill in a form:
# graphic archetype from the advisor's own corpus recommendation (the same
# one /advise and /random already compute), collection role from the one
# thing nothing in Studio can infer -- so it is a single required field, not
# a form.


class QuickAttemptIn(BaseModel):
    source: Literal["typed", "pool"]
    phrase: str = Field(default="", max_length=4000)
    pool_concept_id: str | None = None
    has_graphic: bool = True
    tradition: str = "novelty"
    collection_role: CollectionRole


class QuickAttemptOut(BaseModel):
    concept_id: str
    concept_number: int
    concept_title: str
    attempt_id: str
    generation_prompt: str
    graphic_archetype: str
    collection_role: str


def _archetype_from_label(label: str) -> GraphicArchetype:
    key = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    try:
        return GraphicArchetype(key)
    except ValueError:
        return GraphicArchetype.IMAGE_AND_TITLE_LOCKUP


@router.post(
    "/quick-attempt",
    response_model=QuickAttemptOut,
    status_code=status.HTTP_201_CREATED,
    summary="A typed idea or a pool roll, straight to an upload-ready attempt",
)
def quick_attempt(payload: QuickAttemptIn, session: SessionDependency) -> QuickAttemptOut:
    if payload.source == "pool":
        if payload.pool_concept_id is None:
            # No id supplied -- roll the die here rather than making the
            # caller fetch one from /random first and send it straight back.
            # Same query /random runs, so a card asking for N designs is N of
            # these calls, not a preview step in front of each one.
            entry = session.execute(
                select(DesignConceptPoolEntry)
                .where(
                    DesignConceptPoolEntry.tradition == payload.tradition,
                    DesignConceptPoolEntry.active.is_(True),
                )
                .order_by(func.random())
                .limit(1)
            ).scalar_one_or_none()
            if entry is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND,
                    f"No batch-written concepts for tradition '{payload.tradition}' yet.",
                )
        else:
            try:
                pool_id = uuid.UUID(payload.pool_concept_id)
            except ValueError as error:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, "Not a valid pool concept id."
                ) from error
            entry = session.get(DesignConceptPoolEntry, pool_id)
            if entry is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "No pool concept with that id.")
        concept_text = entry.concept_text
        # advise() on the graphic alone, same reasoning as /random: a 25-35
        # word scene description miscounted as on-shirt copy puts every pool
        # concept in the same word bucket regardless of tradition.
        direction = advise(
            phrase="", has_graphic=True, tradition=payload.tradition, rows=measurement_rows(session)
        )
        prompt_text = render_generation_prompt(direction, concept_text)
        source_path = f"design-prompt/pool/{entry.id}"
    else:
        phrase = payload.phrase.strip()
        if not phrase:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Type an idea, or roll the dice instead."
            )
        direction = advise(
            phrase=phrase,
            has_graphic=payload.has_graphic,
            tradition=payload.tradition,
            rows=measurement_rows(session),
        )
        prompt_text = render_generation_prompt(direction, phrase)
        concept_text = phrase
        source_path = f"design-prompt/typed/{uuid.uuid4()}"

    title = concept_text.strip()[:80] or "Untitled"
    archetype_label = next(
        (r.value for r in direction.recommendations if r.field_name == "Graphic archetype"),
        "image-and-title lockup",
    )
    graphic_archetype = _archetype_from_label(archetype_label)

    concept = create_concept(
        session,
        ConceptLibrary.DESIGN_PROMPT,
        title,
        concept_text,
        source_path=source_path,
    )
    brief = DesignBrief(
        concept_id=concept.id,
        collection_role=payload.collection_role,
        graphic_archetype=graphic_archetype,
    )
    session.add(brief)
    concept.brief = brief
    session.flush()

    try:
        attempt = create_attempt(
            session,
            concept,
            DesignAttemptMethod.IMAGE_GENERATION,
            production_prompt=prompt_text,
        )
    except InvalidDesignAction as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error

    session.commit()
    return QuickAttemptOut(
        concept_id=str(concept.id),
        concept_number=concept.external_number,
        concept_title=concept.title,
        attempt_id=str(attempt.id),
        generation_prompt=prompt_text,
        graphic_archetype=graphic_archetype.value,
        collection_role=payload.collection_role.value,
    )


# --- Gallery: every concept that was actually rendered and looked at -------
#
# The concept pool holds ideas; ``design_generation_samples`` holds proof one
# was tested -- the image and the exact prompt that produced it. Written by
# the batch-eval harness (``scripts/eval_concept_batch.py``), read here.


class GenerationSampleView(BaseModel):
    id: str
    tradition: str
    concept_text: str
    prompt: str
    status: str
    drop_reason: str | None
    batch: str
    created_at: str


class GenerationSamplePage(BaseModel):
    items: list[GenerationSampleView]
    total: int
    page: int
    page_size: int


def _sample_view(row: DesignGenerationSample) -> GenerationSampleView:
    return GenerationSampleView(
        id=str(row.id),
        tradition=row.tradition,
        concept_text=row.concept_text,
        prompt=row.prompt,
        status=row.status,
        drop_reason=row.drop_reason,
        batch=row.batch,
        created_at=row.created_at.isoformat(),
    )


@router.get(
    "/generations",
    response_model=GenerationSamplePage,
    summary="Every tested concept render, newest first",
)
def list_generations(
    session: SessionDependency,
    page: int = 1,
    page_size: int = 16,
    tradition: str | None = None,
    status_filter: str | None = None,
) -> GenerationSamplePage:
    """Paginated gallery feed. ``page_size`` is capped at 64 -- this is a
    review page for a person, not a bulk export."""
    page = max(page, 1)
    page_size = max(1, min(page_size, 64))

    query = select(DesignGenerationSample)
    if tradition:
        query = query.where(DesignGenerationSample.tradition == tradition)
    if status_filter:
        query = query.where(DesignGenerationSample.status == status_filter)

    total = session.execute(
        select(func.count()).select_from(query.subquery())
    ).scalar_one()

    rows = session.execute(
        query.order_by(DesignGenerationSample.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    return GenerationSamplePage(
        items=[_sample_view(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/generations/{sample_id}/image", summary="Fetch a tested render")
def get_generation_image(
    sample_id: str,
    session: SessionDependency,
    settings: SettingsDependency,
    variant: Literal["thumb", "full"] = "thumb",
) -> Response:
    try:
        parsed_id = uuid.UUID(sample_id)
    except ValueError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not a valid sample id.") from error

    row = session.get(DesignGenerationSample, parsed_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No sample with that id.")

    key = row.thumb_relative_path if variant == "thumb" else row.image_relative_path
    mime_type = "image/jpeg" if variant == "thumb" else "image/png"

    store = FilesystemAssetStore(settings.assets_root_resolved)
    try:
        data = store.load(key)
    except AssetStoreError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"The image is recorded but its file could not be read. {error}",
        ) from error

    return Response(
        content=data,
        media_type=mime_type,
        headers={"Cache-Control": "private, max-age=31536000, immutable"},
    )
