"""Producing prompts without generating anything.

The application's most useful job is assembling the canon correctly and writing the
prompt the canon implies. Generation happens elsewhere, so this plans and stops: no
image, no attempt row, no world lock, no decision.

It does keep the prompt. Writing one used to record nothing, so asking again replaced
what came before -- and a variation you cannot put beside the one it varies from is
not much of a variation. Every prompt written for a shot is numbered and kept.

Shared by the CLI and the API so the two cannot drift apart.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.adapters.factory import build_planning_client, planning_client_is_live
from app.adapters.markdown_store import WORLD_DOCUMENT, MarkdownStore
from app.config import Settings
from app.db.models import PromptVariation, Shot, World
from app.domain.errors import StudioError
from app.services.prompt_planner import build_request, build_video_prompt, create_plan
from app.services.rotation import RotationState, apply_continuity, rotation_from_shots
from app.services.shot_selector import NoSelection, select_next_shot

CONTINUITY_DOCUMENT = "CONTINUITY.md"


class NothingToPlan(StudioError):
    """No shot is eligible, or the named shot does not exist."""


@dataclass(frozen=True)
class PromptSet:
    """Both prompts for one shot, and how they were made."""

    # The stored row. A photograph generated from this prompt is attributed to it.
    id: UUID
    shot: Shot
    selection_reason: str
    image_prompt: str
    # Image-to-video. The frame is uploaded separately, so this never names it.
    video_prompt: str
    # Whether a billable model wrote these, or the deterministic fake did.
    live: bool
    # 1 for the first prompt written for this shot, and up from there.
    variation: int
    written_at: dt.datetime


def _as_prompt_set(shot: Shot, row: PromptVariation) -> PromptSet:
    return PromptSet(
        id=row.id,
        shot=shot,
        selection_reason=row.selection_reason,
        image_prompt=row.image_prompt,
        video_prompt=row.video_prompt,
        live=row.live,
        variation=row.variation,
        written_at=row.created_at,
    )


def variations_for_shot(session: Session, *, world_slug: str, external_id: str) -> list[PromptSet]:
    """Every prompt already written for one shot, newest first.

    Empty for a shot nobody has planned yet, which is a fact about that shot and
    not an error.
    """
    shot = session.execute(
        select(Shot).join(World).where(World.slug == world_slug, Shot.external_id == external_id)
    ).scalar_one_or_none()
    if shot is None:
        raise NothingToPlan(f"{world_slug} has no shot {external_id!r}.")

    rows = session.execute(
        select(PromptVariation)
        .where(PromptVariation.shot_id == shot.id)
        .order_by(PromptVariation.variation.desc())
    ).scalars()
    return [_as_prompt_set(shot, row) for row in rows]


def prompts_for_shot(
    session: Session,
    *,
    settings: Settings,
    store: MarkdownStore,
    world_slug: str,
    external_id: str | None = None,
) -> PromptSet:
    """Plan one shot and keep the result.

    Names a shot explicitly, or takes the next eligible one. Each call adds a
    variation rather than replacing the last.
    """
    world = session.execute(
        select(World).where(World.slug == world_slug).options(selectinload(World.shots))
    ).scalar_one_or_none()
    if world is None:
        raise NothingToPlan(f"No world named {world_slug!r} has been imported.")

    shots = sorted(world.shots, key=lambda item: item.sequence)
    rotation: RotationState

    if external_id:
        found = next((item for item in shots if item.external_id == external_id), None)
        if found is None:
            raise NothingToPlan(f"{world_slug} has no shot {external_id!r}.")
        # Asked for by name, so the selector's eligibility rules do not apply — an
        # approved shot can be planned again for a variant. Rotation state still comes
        # from what has actually been approved.
        shot, reason, rotation = found, f"{external_id} requested.", rotation_from_shots(shots)
    else:
        outcome = select_next_shot(world, shots)
        if isinstance(outcome, NoSelection):
            raise NothingToPlan(outcome.reason)
        shot, reason, rotation = outcome.shot, outcome.reason, outcome.rotation

    documents = store.read_world_documents(world_slug)
    request = build_request(
        world_slug=world_slug,
        world_name=world.name,
        shot=shot,
        world_text=documents[WORLD_DOCUMENT].text,
        rotation=apply_continuity(rotation, documents[CONTINUITY_DOCUMENT].text),
        selection_reason=reason,
    )
    plan = create_plan(build_planning_client(settings), request).plan

    # Numbered from what this shot already has. The unique constraint on
    # (shot_id, variation) means two writers racing produce an error, not a
    # silently renumbered history.
    highest = session.execute(
        select(func.max(PromptVariation.variation)).where(PromptVariation.shot_id == shot.id)
    ).scalar()

    row = PromptVariation(
        shot_id=shot.id,
        variation=(highest or 0) + 1,
        image_prompt=plan.production_prompt,
        video_prompt=build_video_prompt(plan),
        selection_reason=reason,
        live=planning_client_is_live(settings),
    )
    session.add(row)
    # Committed here, not left to the caller. A flush alone is rolled back when the
    # request's session closes, which looks identical in a test that shares one
    # session and loses every prompt in production.
    session.commit()

    return _as_prompt_set(shot, row)
