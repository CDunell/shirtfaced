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
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore
from app.adapters.google_media import GoogleImageClient, GoogleImageRequest, GoogleMediaError
from app.adapters.reference_images import ReferenceImage
from app.config import Settings
from app.db.visual_models import (
    CastMember,
    CastMemberAsset,
    CoverageFrame,
    GenerationCall,
    SceneContactSheet,
    VisualAsset,
)
from app.domain.errors import StudioError
from app.services import coverage_library, visual_library
from app.services.reference_resolution import (
    ReferenceUnavailable,
    load_reference,
    resolve_scene_master,
)

logger = logging.getLogger(__name__)

OWNER = "owner"
PROVIDER = "google"

# The generic extraction prompt, quoted from
# NANO_BANANA_CONTACT_SHEET_EXTRACTION_PROMPT.md. Held here rather than read
# from docs/ because the contract calls it the generic master and a provider
# call should not depend on a documentation path staying put; the scene-specific
# coverage prompt is a different matter and is read from the world.
EXTRACTION_PROMPT = (
    "Using the supplied contact sheet as the visual authority, reproduce panel "
    "{panel} as one standalone full-resolution image at {aspect_ratio}. Keep the "
    "same people, faces, wardrobe, props, furniture scale, geography, lighting, "
    "crowd density and event state. Do not invent a new camera angle, restage "
    "the scene, move characters, alter props or create a different version of "
    "the world. Resolve missing fine detail conservatively from the same "
    "approved reference set."
)


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


def scene_prompt_path(worlds_root: Path, scene_key: str) -> Path | None:
    """The world's own resolved coverage prompt, if it has one.

    ``W01-P28.nano-banana-coverage.txt`` is where the pub scene keeps its
    nine-panel instruction. A scene without one has to be given a prompt
    explicitly rather than inheriting somebody else's.
    """
    for world in sorted(worlds_root.glob("*/shots")):
        for candidate in sorted(world.glob("*nano-banana-coverage.txt")):
            if scene_key.lower().replace("-", "") in candidate.stem.lower().replace("-", ""):
                return candidate
    return None


def _record_call(
    session: Session,
    *,
    operation: str,
    model: str,
    scene_key: str | None,
    subject: str | None,
    prompt: str,
    inputs: list[uuid.UUID],
    output_asset_id: uuid.UUID | None,
    succeeded: bool,
    failure: str | None,
    duration_ms: int,
    actor: str,
) -> None:
    session.add(
        GenerationCall(
            provider=PROVIDER,
            model=model,
            operation=operation,
            scene_key=scene_key,
            subject=subject,
            prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            input_asset_ids=[str(one) for one in inputs],
            output_asset_id=output_asset_id,
            succeeded=succeeded,
            failure=failure,
            duration_ms=duration_ms,
            actor=actor,
        )
    )


def calls_for_scene(session: Session, scene_key: str) -> int:
    """How many successful provider calls this scene has behind it."""
    return int(
        session.execute(
            select(func.count())
            .select_from(GenerationCall)
            .where(GenerationCall.scene_key == scene_key, GenerationCall.succeeded.is_(True))
        ).scalar()
        or 0
    )


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
    aspect_ratio: str = "16:9",
    actor: str = OWNER,
) -> SceneContactSheet:
    """Send the master and the chosen references to Nano, keep what comes back.

    The sheet arrives as a candidate. Approving it is the human step, and the
    contract is explicit that a sheet is a planning artefact rather than a
    preview, so it is persisted either way.
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
                image_size=settings.google_image_size,
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
        panel_plan=[],
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
    aspect_ratio: str = "9:16",
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
    prompt = EXTRACTION_PROMPT.format(panel=panel, aspect_ratio=aspect_ratio)
    inputs = [sheet.visual_asset_id, *(one.asset_id for one, _ in chosen)]

    client = _image_client(settings)
    started = time.monotonic()
    try:
        result = client.generate(
            GoogleImageRequest(
                prompt=prompt,
                references=references,
                aspect_ratio=aspect_ratio,
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
        aspect_ratio=aspect_ratio,
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
