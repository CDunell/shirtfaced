"""Producing prompts without generating anything.

The application's most useful job is assembling the canon correctly and writing the
prompt the canon implies. Generation happens elsewhere, so this plans and stops: no
image, no attempt row, no world lock, no decision.

Shared by the CLI and the API so the two cannot drift apart.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.adapters.factory import build_planning_client, planning_client_is_live
from app.adapters.markdown_store import WORLD_DOCUMENT, MarkdownStore
from app.config import Settings
from app.db.models import Shot, World
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

    shot: Shot
    selection_reason: str
    image_prompt: str
    # Image-to-video. The frame is uploaded separately, so this never names it.
    video_prompt: str
    # Whether a billable model wrote these, or the deterministic fake did.
    live: bool


def prompts_for_shot(
    session: Session,
    *,
    settings: Settings,
    store: MarkdownStore,
    world_slug: str,
    external_id: str | None = None,
) -> PromptSet:
    """Plan one shot. Names a shot explicitly, or takes the next eligible one."""
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

    return PromptSet(
        shot=shot,
        selection_reason=reason,
        image_prompt=plan.production_prompt,
        video_prompt=build_video_prompt(plan),
        live=planning_client_is_live(settings),
    )
