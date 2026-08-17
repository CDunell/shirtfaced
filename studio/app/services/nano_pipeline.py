"""Running the Nano coverage pipeline from Studio instead of by hand.

``NANO_BANANA_CONTACT_SHEET_PIPELINE.md`` describes three provider calls and a
review after each. Until now Studio could only record their results: somebody
generated a sheet elsewhere, downloaded it, and uploaded it back with the
reference IDs typed in from memory. That is the part worth removing — not the
reviews, which are the point.

So each call happens here, with the inputs resolved from the library rather than
supplied:

* the master comes from ``resolve_scene_master``;
* the character references come from the cast library, chosen by name;
* the scene prompt comes from the world's own persisted coverage prompt.

Every call is written to ``generation_calls`` whether it succeeds or fails,
which is §6's attempt record: prompt, model, exact inputs, output, lineage. A
refusal is worth keeping too — it is a fact about the prompt, and dropping it
means learning the same thing twice.

What is deliberately *not* automated: approving a sheet, approving a panel, and
approving a take. §5 of the contract makes those human, and they are the only
places where a person's judgement is the product.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest, GoogleMediaError
from app.adapters.reference_images import ReferenceImage
from app.config import Settings
from app.db.visual_models import (
    CastMember,
    CastMemberAsset,
    CoverageFrame,
    SceneContactSheet,
    VisualAsset,
)
from app.domain.errors import StudioError
from app.services import coverage_library, visual_library
from app.services.generation_ledger import record_call as _record_call
from app.services.nano_prompts import EXTRACTION_PROMPT, position_name
from app.services.reference_resolution import (
    ReferenceUnavailable,
    load_reference,
    resolve_scene_master,
)

logger = logging.getLogger(__name__)

OWNER = "owner"
PROVIDER = "google"


class PipelineUnavailable(StudioError):
    """The pipeline cannot run, and the message says which input is missing."""


@dataclass(frozen=True)
class SelectedReference:
    """One cast reference, chosen by name rather than by identifier."""

    slug: str
    role: str
    asset_id: uuid.UUID


def available_references(session: Session) -> list[SelectedReference]:
    """Every approved cast reference, for a picker that shows names.

    The bench used to ask for comma-separated UUIDs. Nobody remembers a UUID,
    and one typed wrong silently records the wrong provenance.
    """
    rows = session.execute(
        select(CastMember.slug, CastMemberAsset.role, VisualAsset.id)
        .join(CastMemberAsset, CastMemberAsset.cast_member_id == CastMember.id)
        .join(VisualAsset, VisualAsset.id == CastMemberAsset.visual_asset_id)
        .where(VisualAsset.status == "approved")
        .order_by(CastMember.slug, CastMemberAsset.sort_order)
    ).all()
    return [
        SelectedReference(slug=slug, role=role, asset_id=asset_id) for slug, role, asset_id in rows
    ]


def resolve_selected_references(
    session: Session, store: AssetStore, selections: list[str]
) -> list[tuple[SelectedReference, ReferenceImage]]:
    """Turn ``damo:contact_sheet`` style picks into bytes the model can take.

    Nano Banana Pro guarantees character consistency for five people, so a
    selection is refused past that rather than silently exceeding what the model
    promises. The contract already says to send only the characters a panel
    needs.
    """
    available = {f"{one.slug}:{one.role}": one for one in available_references(session)}
    chosen: list[tuple[SelectedReference, ReferenceImage]] = []
    people: set[str] = set()

    for selection in selections:
        reference = available.get(selection)
        if reference is None:
            raise PipelineUnavailable(
                f"{selection!r} is not an approved cast reference. "
                f"Available: {', '.join(sorted(available)) or 'none'}."
            )
        people.add(reference.slug)
        asset = session.get(VisualAsset, reference.asset_id)
        if asset is None:  # pragma: no cover - foreign key prevents this
            raise PipelineUnavailable(f"{selection}: the asset is missing.")
        loaded = load_reference(store, asset, selection)
        chosen.append(
            (
                reference,
                ReferenceImage(
                    name=selection, data=loaded.data, mime_type=loaded.mime_type, locked=True
                ),
            )
        )

    if len(people) > 5:
        raise PipelineUnavailable(
            f"{len(people)} characters selected. Nano Banana Pro guarantees identity for five, "
            "and the coverage contract says to send only the characters a panel needs."
        )
    return chosen


def coverage_prompts(worlds_root: Path) -> list[Path]:
    """Every resolved coverage prompt the worlds hold."""
    found: list[Path] = []
    for shots in sorted(worlds_root.glob("*/shots")):
        found.extend(sorted(shots.glob("*nano-banana-coverage.txt")))
    return found


def scene_prompt_path(worlds_root: Path, scene_key: str, name: str | None = None) -> Path | None:
    """The coverage prompt for this scene: named outright, or matched by key.

    Matching is exact on the normalised stem, and deliberately not fuzzy. It
    used to miss: the pub scene was keyed ``pub-1105`` while its prompt was
    filed under the shot id ``W01-P28``, and a fuzzy match would have had to
    decide those were the same thing — which is a naming decision, not a
    lookup. Migration 0039 made the decision instead, so the key and the prompt
    now agree. Where nothing matches, the caller is still offered the list and
    picks: one click, and a record of what was actually sent.
    """
    available = coverage_prompts(worlds_root)
    if name:
        return next((one for one in available if one.name == name), None)
    key = scene_key.lower().replace("-", "").replace("_", "")
    return next(
        (one for one in available if key in one.stem.lower().replace("-", "").replace("_", "")),
        None,
    )


# The coverage prompt numbers its nine observations, and that order is what the
# sheet comes back in. Panel 3 is not "whichever one looks like a three-quarter"
# — it is the third thing the prompt asked for. Parsing it means the bench can
# name the panels instead of asking somebody to count cells.
_PANEL_LINE = re.compile(r"^(\d{1,2})\.\s+\*\*(?P<title>[^*]+?):?\*\*:?\s*(?P<body>.*)$")


def panel_plan_from_prompt(prompt: str) -> list[dict[str, Any]]:
    """The numbered observations the prompt asks for, in its own order.

    Empty for a prompt that does not number them, which is honest: a plan that
    was guessed is worse than no plan, because the bench would then label a
    panel with something the model was never asked for.
    """
    plan: list[dict[str, Any]] = []
    for line in prompt.splitlines():
        match = _PANEL_LINE.match(line.strip())
        if match is None:
            continue
        panel = int(match.group(1))
        if panel != len(plan) + 1:  # Out of order, or a numbered list of something else.
            continue
        plan.append(
            {
                "panel": panel,
                "title": match.group("title").strip(),
                "summary": match.group("body").strip(),
            }
        )
    return plan


def slugify_title(title: str) -> str:
    """``Emma + Brock Crowd Observation`` -> ``emma-brock-crowd-observation``."""
    cleaned = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return cleaned[:96] or "panel"


def _image_client(settings: Settings) -> GoogleImageClient:
    if not settings.google_media_live or settings.gemini_api_key is None:
        raise PipelineUnavailable(
            "Google media is not live on this host, so nothing was sent and nothing was "
            "charged. Set GOOGLE_MEDIA_ENABLED and GEMINI_API_KEY."
        )
    return GoogleImageClient(
        api_key=settings.gemini_api_key.get_secret_value(), model=settings.google_image_model
    )


def generate_coverage_sheet(
    session: Session,
    store: AssetStore,
    settings: Settings,
    *,
    scene_key: str,
    label: str,
    selections: list[str],
    prompt: str,
    aspect_ratio: str | None = None,
    actor: str = OWNER,
) -> SceneContactSheet:
    """Send the master and the chosen references to Nano, keep what comes back.

    The sheet arrives as a candidate. Approving it is the human step, and the
    contract is explicit that a sheet is a planning artefact rather than a
    preview, so it is persisted either way.

    **No aspect ratio is requested.** The sheet comes back the shape the model
    decides, because the sheet is a layout of nine observations rather than a
    frame, and the frame shape is chosen later, per panel, at extraction.

    This was got wrong on 18 August 2026 on the theory that a 3x3 grid divides
    its canvas into nine cells of the canvas's ratio, so a 9:16 canvas would
    yield nine vertical panels. It does not work that way. The model composes a
    layout rather than dividing a canvas: asked for a 3x3 grid on a 9:16 canvas
    it returned 3072x5504 holding **twelve** cells in two columns of six, still
    landscape. The stated ratio did not reshape the panels, it reshaped the grid
    — and the sheet record still said nine, so three of them were unreachable.

    Stating a shape here is an invented constraint in the plainest sense: not a
    property of the model, and not a decision the owner made.
    """
    try:
        master = resolve_scene_master(session, store, scene_key=scene_key)
    except ReferenceUnavailable as error:
        raise PipelineUnavailable(str(error)) from error

    chosen = resolve_selected_references(session, store, selections)
    references = (
        ReferenceImage(
            name="scene-master", data=master.data, mime_type=master.mime_type, locked=True
        ),
        *(image for _, image in chosen),
    )
    inputs = [master.asset_id, *(one.asset_id for one, _ in chosen)]

    client = _image_client(settings)
    started = time.monotonic()
    try:
        result = client.generate(
            GoogleImageRequest(
                prompt=prompt,
                references=references,
                aspect_ratio=aspect_ratio,
                image_size=settings.google_sheet_image_size,
            )
        )
    except GoogleMediaError as error:
        _record_call(
            session,
            operation="coverage_sheet",
            model=settings.google_image_model,
            scene_key=scene_key,
            subject=label,
            prompt=prompt,
            inputs=inputs,
            output_asset_id=None,
            succeeded=False,
            failure=str(error),
            duration_ms=round((time.monotonic() - started) * 1000),
            actor=actor,
        )
        session.commit()
        raise PipelineUnavailable(f"Nano refused the coverage generation: {error}") from error

    duration_ms = round((time.monotonic() - started) * 1000)
    sheet = coverage_library.register_contact_sheet(
        session,
        store,
        scene_key=scene_key,
        label=label,
        data=result.data,
        reference_asset_ids=[one.asset_id for one, _ in chosen],
        prompt_template="NANO_BANANA_SCENE_COVERAGE_PROMPT.md",
        resolved_prompt=prompt,
        panel_plan=panel_plan_from_prompt(prompt),
    )
    _record_call(
        session,
        operation="coverage_sheet",
        model=result.model,
        scene_key=scene_key,
        subject=label,
        prompt=prompt,
        inputs=inputs,
        output_asset_id=sheet.visual_asset_id,
        succeeded=True,
        failure=None,
        duration_ms=duration_ms,
        actor=actor,
    )
    return sheet


def extract_panel(
    session: Session,
    store: AssetStore,
    settings: Settings,
    *,
    scene_key: str,
    panel: int,
    name: str,
    selections: list[str] | None = None,
    actor: str = OWNER,
) -> CoverageFrame:
    """Send the approved sheet back to Nano and keep the standalone still.

    Identity reinforcement is optional and per the contract: character
    references may be supplied again where a panel needs them.
    """
    try:
        sheet = coverage_library.approved_contact_sheet(session, scene_key=scene_key)
    except coverage_library.CoverageRejected as error:
        raise PipelineUnavailable(str(error)) from error

    if panel < 1 or panel > sheet.panels:
        raise PipelineUnavailable(
            f"Panel {panel} is outside a {sheet.rows}x{sheet.columns} sheet (1-{sheet.panels})."
        )

    sheet_image = load_reference(store, sheet.asset, f"{scene_key}:sheet")
    chosen = resolve_selected_references(session, store, selections or [])
    references = (
        ReferenceImage(
            name="contact-sheet",
            data=sheet_image.data,
            mime_type=sheet_image.mime_type,
            locked=True,
        ),
        *(image for _, image in chosen),
    )
    # §9: the panel is named by where it sits, not by an index Nano has to count.
    position = position_name(panel, sheet.rows, sheet.columns)
    prompt = EXTRACTION_PROMPT.format(
        position=position,
        rows=sheet.rows,
        columns=sheet.columns,
        siblings=sheet.panels - 1,
    )
    inputs = [sheet.visual_asset_id, *(one.asset_id for one, _ in chosen)]

    client = _image_client(settings)
    started = time.monotonic()
    try:
        result = client.generate(
            GoogleImageRequest(
                prompt=prompt,
                references=references,
                aspect_ratio=None,
                image_size=settings.google_image_size,
            )
        )
    except GoogleMediaError as error:
        _record_call(
            session,
            operation="panel_extraction",
            model=settings.google_image_model,
            scene_key=scene_key,
            subject=name,
            prompt=prompt,
            inputs=inputs,
            output_asset_id=None,
            succeeded=False,
            failure=str(error),
            duration_ms=round((time.monotonic() - started) * 1000),
            actor=actor,
        )
        session.commit()
        raise PipelineUnavailable(f"Nano refused the extraction: {error}") from error

    duration_ms = round((time.monotonic() - started) * 1000)
    frame = coverage_library.record_panel_extraction(
        session,
        store,
        scene_key=scene_key,
        name=name,
        panel=panel,
        data=result.data,
        aspect_ratio=None,
        provider=PROVIDER,
        model=result.model,
        prompt_hash=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
    )
    _record_call(
        session,
        operation="panel_extraction",
        model=result.model,
        scene_key=scene_key,
        subject=name,
        prompt=prompt,
        inputs=inputs,
        output_asset_id=frame.visual_asset_id,
        succeeded=True,
        failure=None,
        duration_ms=duration_ms,
        actor=actor,
    )
    return frame


def reject_asset(
    session: Session, asset: VisualAsset, *, note: str | None = None, actor: str = OWNER
) -> VisualAsset:
    """Say no to a generated image without deleting it.

    A rejected take is evidence about what the prompt does, which is worth more
    than the disk it costs. Rerunning is a new call, never an overwrite.
    """
    visual_library.deprecate_asset(session, asset, actor=actor, note=note or "Rejected")
    return asset
