"""Building a planning request and validating what comes back.

Two responsibilities:

* assemble bounded context — the canon relevant to this shot, recent continuity and
  rotation state, not the whole archive;
* refuse a plan that does not obey the brief. A model that quietly substitutes the
  hero product would break product rotation, which is the whole point of the shotlist.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.adapters.planning import PlanningError, PromptPlanningClient
from app.db.models import Shot
from app.domain.schemas import CanonExcerpt, PromptPlan, PromptPlanRequest, ShotBrief
from app.services.markdown_sections import section_with_subsections
from app.services.rotation import RotationState

# Canon sections sent with every planning request, in the order they are sent.
#
# A section of WORLD.md that is not named here is never seen by the planning model.
# The omitted ones are operating instructions for the humans and roles — Operating
# System, Continuity Ledger and so on — not rules the photograph must obey.
#
# "Prompt Construction Protocol" is required by the end-to-end workflow: it is the
# checklist the planner must satisfy before writing a prompt.
PLANNING_CANON_HEADINGS = (
    "Purpose",
    "Emotional Tone",
    "Lighting",
    "Colour Palette",
    "Photography Language",
    "Locations",
    "People",
    "Wardrobe",
    "Composition",
    "Environmental Branding",
    "Reference Standard — The Photo We'd Post Anyway",
    "Global Production Rule — No Visible Branding",
    "Product Rotation & Vehicle Canon",
    "Prompt Construction Protocol",
    "Success Test",
)

RECENT_CONTINUITY_LIMIT = 3
RECENT_DRIFT_LIMIT = 3
# Long canon sections are truncated so the request stays bounded.
MAX_EXCERPT_CHARACTERS = 2000


@dataclass(frozen=True)
class PlanOutcome:
    """A validated plan and the request that produced it."""

    plan: PromptPlan
    request: PromptPlanRequest


def build_request(
    *,
    world_slug: str,
    world_name: str,
    shot: Shot,
    world_text: str,
    rotation: RotationState,
    selection_reason: str = "",
    recent_continuity: list[str] | None = None,
) -> PromptPlanRequest:
    """Assemble the bounded context for one shot."""
    # The whole subtree, so a section whose content sits in subsections is not lost.
    excerpts = [
        CanonExcerpt(heading=heading, body=truncate_excerpt(body))
        for heading in PLANNING_CANON_HEADINGS
        if (body := section_with_subsections(world_text, heading)) is not None and body.strip()
    ]

    drift = [
        f"{entry.title}: {truncate_excerpt(entry.body, 600)}"
        for entry in rotation.rejected_drift[:RECENT_DRIFT_LIMIT]
    ]

    return PromptPlanRequest(
        world_slug=world_slug,
        world_name=world_name,
        shot=ShotBrief(
            external_id=shot.external_id,
            title=shot.title,
            hero_product=shot.hero_product,
            camera_position=shot.camera_position,
            lighting_source=shot.lighting_source,
        ),
        canon_excerpts=excerpts,
        recent_continuity=(recent_continuity or [])[:RECENT_CONTINUITY_LIMIT],
        rejected_drift=drift,
        canon_notes=rotation.canon_notes,
        recent_hero_products=rotation.recent_hero_products,
        recent_camera_positions=rotation.recent_camera_positions,
        next_product_priority=rotation.next_product_priority,
        next_camera_priority=rotation.next_camera_priority,
        selection_reason=selection_reason,
    )


def create_plan(client: PromptPlanningClient, request: PromptPlanRequest) -> PlanOutcome:
    """Ask for a plan and validate it against the brief."""
    plan = client.create_plan(request)
    validate_plan(plan, request)
    return PlanOutcome(plan=plan, request=request)


def validate_plan(plan: PromptPlan, request: PromptPlanRequest) -> None:
    """Reject a plan that does not obey the shot brief.

    Schema conformance is enforced by :class:`PromptPlan` itself. What is checked here
    is agreement with what was asked for.
    """
    if not plan.production_prompt.strip():
        raise PlanningError("The plan contains no production prompt.")

    required_product = request.required_hero_product
    if required_product and not _matches(plan.hero_product, required_product):
        raise PlanningError(
            f"The plan nominates hero product {plan.hero_product!r}, but the shot "
            f"requires {required_product!r}. Product rotation depends on this."
        )

    required_camera = request.required_camera_position
    if required_camera and not _matches(plan.camera_position, required_camera):
        raise PlanningError(
            f"The plan nominates camera position {plan.camera_position!r}, but the "
            f"shot requires {required_camera!r}. Camera rotation depends on this."
        )


def _matches(produced: str, required: str) -> bool:
    """Agreement, not identity.

    The shotlist says "Tote bag"; a plan may reasonably say "Plain black tote bag".
    One containing the other is agreement; anything else is a substitution.
    """
    left = produced.strip().casefold()
    right = required.strip().casefold()
    return left == right or right in left or left in right


def truncate_excerpt(text: str, limit: int = MAX_EXCERPT_CHARACTERS) -> str:
    """Cap one canon excerpt so a request stays bounded.

    Shared with the reviewer so an image is judged against the same excerpt the
    planner used to build it.
    """
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[:limit].rsplit("\n", 1)[0].rstrip() + "\n…"
