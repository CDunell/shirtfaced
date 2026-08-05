"""Prompt planning adapters.

Services depend on the :class:`PromptPlanningClient` protocol, never on the OpenAI
SDK. That keeps domain logic testable and survives the provider changing its API.

Two implementations:

* :class:`FakePromptPlanningClient` — deterministic, used by every automated test and
  by local development without a key. It costs nothing and never leaves the process.
* :class:`OpenAIPromptPlanningClient` — the real thing, using the Responses API with
  structured output.

Tests must never construct the OpenAI client.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Protocol, runtime_checkable

from app.domain.errors import StudioError
from app.domain.schemas import PromptPlan, PromptPlanRequest

logger = logging.getLogger(__name__)


class PlanningError(StudioError):
    """The planning model failed or returned something unusable."""


@runtime_checkable
class PromptPlanningClient(Protocol):
    """Turns a bounded request into a structured production plan."""

    def create_plan(self, request: PromptPlanRequest) -> PromptPlan: ...


class FakePromptPlanningClient:
    """A deterministic planner.

    It composes a plan from the request itself, so a test asserting on the output is
    asserting on the context the service assembled. The same request always produces
    the same plan.
    """

    def __init__(self, *, fail_with: str | None = None) -> None:
        self._fail_with = fail_with
        self.requests: list[PromptPlanRequest] = []

    def create_plan(self, request: PromptPlanRequest) -> PromptPlan:
        self.requests.append(request)

        if self._fail_with is not None:
            raise PlanningError(self._fail_with)

        shot = request.shot
        hero = shot.hero_product or "Black heavyweight t-shirt"
        camera = shot.camera_position or "Across the street, slightly behind"
        lighting = shot.lighting_source or "Streetlight spill and venue light"

        return PromptPlan(
            scene_summary=shot.title,
            emotional_beat="Renewed momentum; the night is continuing.",
            hero_product=hero,
            product_visibility_instruction=(
                f"The {hero.lower()} is visible because of what the subject is doing, "
                "never because they are displaying it."
            ),
            camera_position=camera,
            lighting_source=lighting,
            documentary_imperfection="A foreground element crops part of the frame.",
            australian_authenticity_anchors=[
                "Australian street signage and suburban architecture",
                "Generic unbranded packaging",
            ],
            negative_constraints=[
                "No visible branding or commercial logos",
                "No American pickup trucks",
                "No studio lighting",
                "No posing or acknowledgement of the camera",
            ],
            mood_words=["Hopeful", "Loose", "Possible"],
            selection_rationale=(
                request.selection_reason or f"{shot.external_id} is the next planned shot."
            ),
            production_prompt=(
                f"Documentary 35mm photograph, high ISO, natural grain. {shot.title}. "
                f"Hero product: {hero}, naturally visible. Camera: {camera}. "
                f"Lighting: {lighting}. Australian night-out setting. "
                "All clothing and packaging completely blank and unbranded."
            ),
        )


# The schema the model must satisfy. Kept beside the adapter because it describes the
# wire format, not the domain type.
PROMPT_PLAN_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "scene_summary",
        "emotional_beat",
        "hero_product",
        "product_visibility_instruction",
        "camera_position",
        "lighting_source",
        "documentary_imperfection",
        "australian_authenticity_anchors",
        "negative_constraints",
        "mood_words",
        "selection_rationale",
        "production_prompt",
    ],
    "properties": {
        "scene_summary": {"type": "string"},
        "emotional_beat": {"type": "string"},
        "hero_product": {"type": "string"},
        "product_visibility_instruction": {"type": "string"},
        "camera_position": {"type": "string"},
        "lighting_source": {"type": "string"},
        "documentary_imperfection": {"type": "string"},
        "australian_authenticity_anchors": {"type": "array", "items": {"type": "string"}},
        "negative_constraints": {"type": "array", "items": {"type": "string"}},
        "mood_words": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 4,
        },
        "selection_rationale": {"type": "string"},
        "production_prompt": {"type": "string"},
    },
}

SYSTEM_INSTRUCTIONS = """\
You are the World Architect for a private photographic production tool.

Write one production prompt for the supplied shot, in the voice of the reference
prompts that seeded this world. Those were usable on the first generation about nine
times in ten. Writing like them is the job; everything below is how.


THE VOICE

One short declarative per line. Median five words. Never more than twenty-five. No
paragraphs — the line break is what forces a detail to be specified rather than
gestured at, and a dense block of prose comes back as a posed group portrait with
documentary styling applied over the top.

Nobody is named. "One bloke." "A woman." "Another mate." Invented first names
lengthen every line and carry nothing a camera can see.

Sentences hammer. "Nobody is posing." stands on its own line. It is never folded
into a clause about what somebody is holding.


THE ACTION — the part that decides whether the photograph is alive

Read the Locked Reference Prompt in the canon before writing this. It is the prompt
that produced the benchmark photograph, it worked first time, and it is a better
instruction than anything written about it. What follows is only what to notice.

The reliable failure is a cast list: one sentence per person, one human subject
each, nobody appearing in anybody else's line, six people with six private props.
A room of strangers who happen to be standing together.

One central event, and the group reacting to it. This is the device. The reference
does it in three consecutive lines:

    One bloke is attempting to eat an overloaded kebab that is structurally failing.
    Sauce is running down the paper.
    His mates are absolutely losing it.

An action, then its consequence, then the group's reaction to it. Everything else in
that prompt happens around those three lines. Give every scene one such event and
let the rest of the cast orbit it.

Actions that name somebody else. "Trying to steal a chip from someone else's snack
pack." "Already carrying everyone's drinks." "A couple sharing a quiet joke while
the chaos happens beside them." Each of those puts two parties in one line, or a
person in relation to the group.

Time before the shutter. Actions carry a history and a cause. "The story nobody let
him finish earlier." "Because the air has turned cold." Self-contained present tense
reads as arranged, because nothing led to it.

Some of them alone. Barefoot with her shoes in one hand, digging through a wallet.
All of them alone is the failure; all of them interacting at once is equally staged.

Phones isolate. A phone turns a person inward and gives them something nobody else
can see, so use at most one, and prefer two heads over one screen to two people on
two phones.

A collective line, once, before the individual actions: "Everyone is still running
on the energy of the night." It makes the group one body before it becomes six
people.


WHAT NOBODY IS DOING

Three or four lines about the night, not about the camera. "Nobody is on their
phone." "Nobody is checking the time." "Nobody wants the night to end." "Nobody is
looking at the view because they have all seen it before."

This is the reference set's device for mood and story. It sets the emotional state
and quietly demotes the scenery so the people stay the subject. It is not the same
as the anti-artifice lines below, which police the photograph rather than build the
feeling. Both are needed.


THE SHAPE, IN ORDER

"Photorealistic documentary photograph." Country, night, and a specific clock time —
12:07am, not "at night".

The location in one line, then what it is not. "Not the destination. Just a stop on
the way to whatever happens next."

The cast as a count and a split. "Six ordinary Australians in their mid-twenties to
mid-thirties. Three men. Three women." The number is whatever the place can
physically hold and no more.

"Nobody is posing. Nobody acknowledges the camera."

The action, as above.

"Nobody is rushing. Nobody looks like a model. Nobody is performing."

What nobody is doing, as above.

The mood block: the words returned in mood_words, each alone on its own line with a
full stop. Peaceful. Hopeful. Content.

The light, one practical source per line, all of it available and real.

The clutter — what is on the bench, in the tray, on the ground — and then the
background life: strangers, passing cars, somebody out of focus in a doorway. An
empty background is the clearest sign of a set. This is where a crowded frame comes
from. Density is people who are not the cast and objects nobody placed. It is never
made by adding principals to a space that cannot hold them.

"Everything feels completely ordinary." "Everything feels unmistakably Australian."

Who took it and from where, as a person: "Photographed from across the forecourt by
another friend waiting beside their own car."

The camera block, one per line: 35mm documentary photography. 50mm lens. Kodak Portra
400. Available light only. Natural film grain. No HDR. No cinematic colour grading.
Slight motion blur. Slightly underexposed. Imperfect framing.

A named crop and a named obstruction: which person the edge cuts, and what sits in
front of the lens.

"The photograph feels accidental rather than composed."

The garments, one line each, colour and cut only. "A washed black hoodie." "A cream
crop under an open overshirt." The hero product is among them and is never presented.

The closing line: what this photograph would mean to somebody in it. End on a person,
not a specification.

"The photograph should be good enough that someone would post it on Instagram even if
everyone was wearing plain black clothing."


WHERE THE CAMERA AND THE PEOPLE STAND

The camera observes, so it stands outside what it is watching. Never in the box with
the subjects: not in the lift with them, not in the car with them. The next room, the
hallway, the footpath, the far table, looking in through the doorway. Being in an
interior is fine; being inside the container the subjects occupy is not. A kitchen
shot from the dining room is an observer. A lift shot from inside the lift is a
passenger.

The subjects stay out of small built enclosures too — car cabins, lifts, tents, phone
boxes. They are next to, in front of, or sitting on them. The exception is
interaction at an opening: somebody seated in a car talking out through the window,
somebody at a tent entrance.

So take the bigger version of the place. A lift becomes a lobby. A cabin becomes a
kerb. The open version has room for the group, the background and the one still
arriving.

Obstruct the lens with something on the observer's side, never with the near edge of
the space being observed. Not the car's own window rubber, door frame, pillar or
mirror: that reads as sitting the camera in the cabin however the camera line is
worded.


RULES THAT MUST NOT BREAK

The photograph must work as a documentary image with no product in it at all.

The nominated hero product is the one supplied. Do not substitute it. The camera
position is the one supplied.

Every person is supported by something real. Nobody sits in mid-air and nobody shares
a seat. If a space cannot hold the people described, the people are wrong, not the
space.

Anything a person operates has the thing it operates in frame. A lift call button
needs lift doors. An entry intercom is on the street side of the door and is pressed
by somebody trying to get in, never by somebody already in the lobby. Where the
object is not in shot, give that person a different action rather than leaving them
miming at a panel.

Nobody enters or leaves a vehicle: no climbing in, no half in and half out, no
leaning through a door opening, nobody with their head inside the cabin. Interacting
with a car is fine; using it as the mechanism of the scene is not. A passenger
already seated is allowed, and an exchange through an open window is a good frame.
Whoever is sitting in a car faces the windscreen, head and at most one shoulder
turned to the window, never squared to the door.

Branding turns on what the brand sells. Anything it sells is blank, wherever in the
frame it sits. Anything it does not sell may carry real branding as background only —
servo boards, shopfronts, packaging, transport — never centred, never held up, never
the reason the frame exists.

Do not write the blank-garment rule into the prompt. The application appends it. Give
a garment's colour and cut and stop; repeating blankness per person spends the length
that description needs.

No HDR and no cinematic colour grading are not stylistic preferences. Warm, even,
flattering light is the single most common failure and has to be refused explicitly
or it arrives by default.

Use Australian English.

Return only the structured fields requested."""


class OpenAIPromptPlanningClient:
    """Planning through the OpenAI Responses API with structured output."""

    def __init__(self, client: Any, model: str, timeout_seconds: float) -> None:
        if not model:
            raise PlanningError(
                "OPENAI_TEXT_MODEL is not set. Configure it explicitly: guessing a "
                "model name can cause unexpected cost."
            )
        self._client = client
        self._model = model
        self._timeout = timeout_seconds

    def create_plan(self, request: PromptPlanRequest) -> PromptPlan:
        try:
            response = self._client.responses.create(
                model=self._model,
                timeout=self._timeout,
                instructions=SYSTEM_INSTRUCTIONS,
                input=[{"role": "user", "content": _render_request(request)}],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "prompt_plan",
                        "strict": True,
                        "schema": PROMPT_PLAN_JSON_SCHEMA,
                    }
                },
            )
        except Exception as error:
            raise PlanningError(f"The planning request failed: {error}") from error

        request_id = getattr(response, "id", None)
        if request_id:
            # Provider request IDs are logged for support; payloads are not.
            logger.info("Planning response %s from %s", request_id, self._model)

        return _parse_plan(_output_text(response))


def _output_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text
    raise PlanningError("The planning response contained no text output.")


def _parse_plan(text: str) -> PromptPlan:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise PlanningError("The planning response was not valid JSON.") from error

    try:
        return PromptPlan.model_validate(payload)
    except Exception as error:
        raise PlanningError(f"The planning response did not match the schema: {error}") from error


def _render_request(request: PromptPlanRequest) -> str:
    """The user message: only the canon and history relevant to this shot."""
    parts: list[str] = [
        f"World: {request.world_name} ({request.world_slug})",
        "",
        "## Shot",
        f"ID: {request.shot.external_id}",
        f"Scene: {request.shot.title}",
        f"Required hero product: {request.shot.hero_product or 'unset'}",
        f"Required camera position: {request.shot.camera_position or 'unset'}",
    ]

    if request.selection_reason:
        parts += ["", "## Why this shot", request.selection_reason]

    for excerpt in request.canon_excerpts:
        parts += ["", f"## Canon — {excerpt.heading}", excerpt.body]

    parts += _bullet_block("Approved reference frames", request.reference_frames)
    parts += _bullet_block("Recent continuity", request.recent_continuity)
    parts += _bullet_block("Rejected drift to avoid", request.rejected_drift)
    parts += _bullet_block("Current canon notes", request.canon_notes)
    parts += _bullet_block("Recently used hero products", request.recent_hero_products)
    parts += _bullet_block("Recently used camera positions", request.recent_camera_positions)
    parts += _bullet_block("Preferred next hero products", request.next_product_priority)
    parts += _bullet_block("Preferred next camera positions", request.next_camera_priority)

    return "\n".join(parts)


def _bullet_block(heading: str, items: list[str]) -> list[str]:
    if not items:
        return []
    return ["", f"## {heading}", *(f"- {item}" for item in items)]
