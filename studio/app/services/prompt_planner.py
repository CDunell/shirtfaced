"""Building a planning request and validating what comes back.

Two responsibilities:

* assemble bounded context — the canon relevant to this shot, recent continuity and
  rotation state, not the whole archive;
* refuse a plan that does not obey the brief. A model that quietly substitutes the
  hero product would break product rotation, which is the whole point of the shotlist.
"""

from __future__ import annotations

import logging
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
    # The prompt that produced the benchmark photograph, in full. The canon described
    # it in nine abstract bullets for months -- "small moments between friends" -- and
    # never showed the planner the thing itself. Every rule written to describe its
    # behaviour is a worse instruction than the example.
    "Locked Reference Prompt",
    "Global Production Rule — Branding",
    # Split from one "Product Rotation & Vehicle Canon" heading, which reached 95% of
    # the excerpt cap and tripped it twice in a day. Two headings, two budgets: the
    # rules stop competing for room with each other.
    "Product Rotation",
    "Vehicle Canon",
    "Prompt Construction Protocol",
    "Success Test",
)

logger = logging.getLogger(__name__)

# Appended to every production prompt by the application, never requested from the
# model.
#
# It was requested from the model, and three consecutive previews dropped it: each
# time a newly required element was added to the protocol, this one fell out to make
# room, and the third prompt reached the point of having no branding instruction of
# any kind. Asking a model to reliably reproduce invariant text competes with the part
# of the prompt that actually varies, and loses.
#
# So the blank-garment rule is no longer part of what gets composed. It is a suffix.
BRANDING_CRITICAL_BLOCK = """CRITICAL.
Every garment in frame is blank.
No logos.
No graphics.
No printed text.
No embroidery.
No visible labels."""


def with_critical_block(prompt: str) -> str:
    """Guarantee the branding block, without duplicating one the model wrote."""
    if "CRITICAL" in prompt.upper():
        return prompt.rstrip()
    return f"{prompt.rstrip()}\n{BRANDING_CRITICAL_BLOCK}"


# The camera block opens with this line in every prompt the protocol produces. It is
# the anchor for inserting the mood block, because the seeds place mood after the
# action and before the technical specification.
CAMERA_BLOCK_MARKER = "35mm documentary photography."


def _has_mood_block(prompt: str) -> bool:
    """Three or more consecutive bare single-word lines, which is what the block is."""
    run = 0
    for line in prompt.splitlines():
        stripped = line.strip()
        bare = stripped.rstrip(".")
        if stripped.endswith(".") and bare and len(bare.split()) == 1 and bare[0].isupper():
            run += 1
            if run >= 3:
                return True
        else:
            run = 0
    return False


def with_mood_block(prompt: str, mood_words: list[str]) -> str:
    """Guarantee the mood block, placed before the camera specification.

    Requesting it in prose produced it in three prompts out of five, once failing
    while explicitly mandatory. ``mood_words`` is a schema field the model cannot
    skip, so the words always exist; this puts them in the prompt.
    """
    if not mood_words or _has_mood_block(prompt):
        return prompt

    block = "\n".join(f"{word.rstrip('.')}." for word in mood_words)
    lines = prompt.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith(CAMERA_BLOCK_MARKER):
            return "\n".join([*lines[:index], block, *lines[index:]])

    # No camera block to anchor to, so the mood still gets in rather than being lost.
    return f"{prompt.rstrip()}\n{block}"


RECENT_CONTINUITY_LIMIT = 3
RECENT_DRIFT_LIMIT = 3
# Long canon sections are truncated so the request stays bounded.
#
# Sized to fit every section of the real WORLD.md whole, with headroom. At 2000 this
# silently cut the last line off the branding rule -- "The blank-garment rule under
# One is not relaxed by anything here" -- which is the clause that stops the
# Shirtfaced exception being read as permission to brand a garment. Neither model
# ever saw it. The whole canon is around 11,000 characters, so the cap was never
# holding back anything that mattered; it was only deciding which rule to drop.
MAX_EXCERPT_CHARACTERS = 4000


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
    reference_frames: list[str] | None = None,
) -> PromptPlanRequest:
    """Assemble the bounded context for one shot."""
    # The whole subtree, so a section whose content sits in subsections is not lost.
    excerpts: list[CanonExcerpt] = []
    for heading in PLANNING_CANON_HEADINGS:
        body = section_with_subsections(world_text, heading)
        if body is None or not body.strip():
            continue

        excerpt = truncate_excerpt(body)
        # Truncation drops whatever sits at the end of a section, and what sits at the
        # end of a rule is usually the qualifier that closes the loophole. Losing it
        # quietly looks exactly like the rule working, so say so.
        if len(body.strip()) > len(excerpt):
            logger.warning(
                "Canon section %r is %d characters and was cut to %d before being sent. "
                "The end of it does not reach the model.",
                heading,
                len(body.strip()),
                len(excerpt),
            )
        excerpts.append(CanonExcerpt(heading=heading, body=excerpt))

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
        reference_frames=reference_frames or [],
        rejected_drift=drift,
        canon_notes=rotation.canon_notes,
        recent_hero_products=rotation.recent_hero_products,
        recent_camera_positions=rotation.recent_camera_positions,
        next_product_priority=rotation.next_product_priority,
        next_camera_priority=rotation.next_camera_priority,
        selection_reason=selection_reason,
    )


def create_plan(client: PromptPlanningClient, request: PromptPlanRequest) -> PlanOutcome:
    """Ask for a plan, validate it against the brief, and guarantee the branding block."""
    plan = client.create_plan(request)
    validate_plan(plan, request)
    # After validation, so the model is still judged on what it actually wrote.
    prompt = with_mood_block(plan.production_prompt, plan.mood_words)
    guaranteed = plan.model_copy(update={"production_prompt": with_critical_block(prompt)})
    return PlanOutcome(plan=guaranteed, request=request)


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


# Enough for a product name; nothing here contains a dash that matters.
_PUNCTUATION = ".,;:!?\"'()[]-"


def _matches(produced: str, required: str) -> bool:
    """Agreement, not identity.

    The shotlist says "Tote bag"; a plan may reasonably say "Plain black tote bag".
    Substring containment catches that, because the elaboration only adds words at
    the ends.

    It does not catch an elaboration that adds words in the middle. The shotlist
    column is narrow, so its values are clipped -- "Hoodie waist" -- and the natural
    expansion is "Hoodie tied around waist", which contains neither string. That
    failed a live plan as a substituted hero product, which it plainly is not.

    So every required word must appear in what was produced, in order. "Hoodie
    waist" agrees with "Hoodie tied around waist" and with "Plain black hoodie tied
    around the waist"; it disagrees with "Hoodie", which drops a required word, and
    with "Cap", which shares none.
    """
    left = produced.strip().casefold()
    right = required.strip().casefold()
    if left == right or right in left or left in right:
        return True

    # Punctuation is not part of a product name. A plan returning "hoodie tied around
    # the waist." failed against "Hoodie waist" purely on the full stop.
    produced_words = [word.strip(_PUNCTUATION) for word in left.split()]
    position = 0
    for required_word in (word.strip(_PUNCTUATION) for word in right.split()):
        try:
            position = produced_words.index(required_word, position) + 1
        except ValueError:
            return False
    return True


def truncate_excerpt(text: str, limit: int = MAX_EXCERPT_CHARACTERS) -> str:
    """Cap one canon excerpt so a request stays bounded.

    Shared with the reviewer so an image is judged against the same excerpt the
    planner used to build it.
    """
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[:limit].rsplit("\n", 1)[0].rstrip() + "\n…"
