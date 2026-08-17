"""Coverage: the observations a scene is shot from, and how they are obtained.

Two routes, and the difference between them is the whole design.

**Nano extraction**, the active contract in
``NANO_BANANA_CONTACT_SHEET_PIPELINE.md``. An approved master plus approved
character references produce a 3x3 coverage contact sheet; a chosen panel is fed
back to the model and returns as a standalone still. That still is *generated*,
so it has its own bytes, its own hash, and no crop box. What identifies it is
the sheet it came from and the panel number on it — coordinates could neither
name it nor reproduce it.

**Deterministic crop**, superseded for the Nano route by §8 of that contract but
still the cheapest way to take an exact observation out of an image nobody needs
to regenerate. Same master and same box, same bytes, every time.

A frame is one or the other, and the database enforces that: a crop carries its
whole box, an extraction carries a sheet and a panel. Both end at the same gate,
because the thing that matters downstream is identical either way — Veo may
animate an approved observation of the scene's current master, and nothing else.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from io import BytesIO
from math import gcd
from typing import Any

from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore
from app.db.models import AuditEvent
from app.db.visual_models import (
    AssetLineage,
    CoverageFrame,
    SceneContactSheet,
    SceneMaster,
    VisualAsset,
)
from app.domain.enums import (
    AuditEventType,
    VisualAssetKind,
    VisualAssetSourceType,
    VisualAssetStatus,
)
from app.domain.errors import StudioError
from app.services import visual_library
from app.services.reference_resolution import ResolvedReference, resolve_scene_master

logger = logging.getLogger(__name__)

OWNER = "owner"
VERTICAL = (9, 16)


class CoverageRejected(StudioError):
    """The requested crop is not a usable observation of this master."""


@dataclass(frozen=True)
class CropBox:
    """A window on a master, in the master's own pixels."""

    x: int
    y: int
    width: int
    height: int

    @property
    def box(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)


def vertical_box(*, master_width: int, master_height: int, x: int, y: int, height: int) -> CropBox:
    """The largest exact 9:16 window of the requested height, at this offset.

    The height is reduced to a multiple of 16 so the width is a whole number of
    pixels. Never the other way around: enlarging would leave the frame's bottom
    edge outside the master, and scaling would stop the crop being original
    pixels.
    """
    requested = height or master_height
    usable = (requested // VERTICAL[1]) * VERTICAL[1]
    if usable < VERTICAL[1]:
        raise CoverageRejected(f"{requested}px is too short to make a 9:16 frame.")

    width = usable * VERTICAL[0] // VERTICAL[1]
    if x < 0 or y < 0:
        raise CoverageRejected(f"Crop origin ({x},{y}) is outside the master.")
    if x + width > master_width or y + usable > master_height:
        raise CoverageRejected(
            f"Crop ({x},{y}) {width}x{usable} falls outside a {master_width}x{master_height} "
            "master. Move it left, or ask for less height."
        )
    return CropBox(x=x, y=y, width=width, height=usable)


def crop_bytes(master_data: bytes, box: CropBox) -> bytes:
    """Original pixels, PNG, no resampling."""
    with Image.open(BytesIO(master_data)) as image:
        image.load()
        cropped = image.crop(box.box)
        buffer = BytesIO()
        cropped.save(buffer, format="PNG")
    return buffer.getvalue()


def derive_coverage_frame(
    session: Session,
    store: AssetStore,
    *,
    scene_key: str,
    name: str,
    x: int,
    y: int = 0,
    height: int = 0,
    notes: str | None = None,
    actor: str = OWNER,
) -> CoverageFrame:
    """Cut one named frame from the scene's approved master and record it.

    Re-cutting the same name from the same master replaces the row's geometry
    rather than adding a second frame with the same name: the shot is one shot,
    and two rows claiming it would put the choice back on a person.

    The new frame is never approved for Veo by this call. Cutting is not
    approving, and a frame nobody has looked at must not be animatable.
    """
    master_reference = resolve_scene_master(session, store, scene_key=scene_key)
    master = session.execute(
        select(SceneMaster).where(
            SceneMaster.scene_key == scene_key, SceneMaster.status == "approved"
        )
    ).scalar_one()

    box = vertical_box(
        master_width=master_reference.width,
        master_height=master_reference.height,
        x=x,
        y=y,
        height=height,
    )
    data = crop_bytes(master_reference.data, box)

    ingested = visual_library.ingest_asset(
        session,
        store,
        data=data,
        kind=VisualAssetKind.COVERAGE,
        source_type=VisualAssetSourceType.EDITED,
        role=name,
        description=f"{scene_key} coverage — {name}",
        # A crop carries its master's provenance, which is worth saying even
        # though the default is already verified: this frame is that master.
        rights_metadata={"inherited_from_master": str(master_reference.asset_id)},
        metadata={
            "scene": scene_key,
            "crop_box": list(box.box),
            "source_master_sha256": master_reference.sha256,
        },
    )
    # A crop is not a new picture of anything. Recording the edge is what lets a
    # finished clip be traced back to the master it observed.
    _record_lineage(session, parent=master_reference.asset_id, child=ingested.asset.id, box=box)

    frame = session.execute(
        select(CoverageFrame).where(
            CoverageFrame.scene_master_id == master.id, CoverageFrame.name == name
        )
    ).scalar_one_or_none()

    if frame is None:
        frame = CoverageFrame(scene_master_id=master.id, name=name)
        session.add(frame)

    frame.visual_asset_id = ingested.asset.id
    frame.x, frame.y = box.x, box.y
    frame.width, frame.height = box.width, box.height
    frame.aspect_ratio = "9:16"
    frame.source_master_sha256 = master_reference.sha256
    frame.frame_sha256 = ingested.asset.sha256
    frame.operation = "crop_only"
    # Geometry changed, so any previous approval was of a different picture.
    frame.approved_for_veo = False
    if notes is not None:
        frame.notes = notes
    session.flush()

    session.add(
        AuditEvent(
            event_type=AuditEventType.COVERAGE_FRAME_DERIVED,
            actor=actor,
            payload_json={
                "coverage_frame_id": str(frame.id),
                "scene": scene_key,
                "name": name,
                "crop_box": list(box.box),
                "master_sha256": master_reference.sha256,
                "frame_sha256": ingested.asset.sha256,
            },
        )
    )
    return frame


def measured_ratio(width: int, height: int) -> str:
    """``9:16`` from the pixels, reduced. What the image is, not what was asked.

    Falls back to the raw pair when the reduction is not a tidy one, because
    "1367:768" is a true statement about the file and "16:9" would not be.
    """
    if width <= 0 or height <= 0:  # pragma: no cover - measurements are positive
        return "unknown"
    divisor = gcd(width, height)
    left, right = width // divisor, height // divisor
    if left > 64 or right > 64:
        return f"{width}:{height}"
    return f"{left}:{right}"


def _record_lineage_edge(
    session: Session,
    *,
    parent: uuid.UUID,
    child: uuid.UUID,
    relationship: str,
    operation_metadata: dict[str, Any] | None = None,
) -> None:
    """One edge, recorded once. The input manifest §6 asks for is these."""
    existing = session.execute(
        select(AssetLineage).where(
            AssetLineage.parent_asset_id == parent,
            AssetLineage.child_asset_id == child,
            AssetLineage.relationship_kind == relationship,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return
    session.add(
        AssetLineage(
            parent_asset_id=parent,
            child_asset_id=child,
            relationship_kind=relationship,
            operation_metadata=operation_metadata or {},
        )
    )


def _record_lineage(session: Session, *, parent: uuid.UUID, child: uuid.UUID, box: CropBox) -> None:
    existing = session.execute(
        select(AssetLineage).where(
            AssetLineage.parent_asset_id == parent,
            AssetLineage.child_asset_id == child,
            AssetLineage.relationship_kind == "crop",
        )
    ).scalar_one_or_none()
    if existing is not None:
        return
    session.add(
        AssetLineage(
            parent_asset_id=parent,
            child_asset_id=child,
            relationship_kind="crop",
            operation_metadata={"crop_box": list(box.box)},
        )
    )


def approve_for_veo(
    session: Session, frame: CoverageFrame, *, actor: str = OWNER, note: str | None = None
) -> CoverageFrame:
    """Let this frame be animated. Refuses if its master is no longer current."""
    if frame.master.status != "approved":
        raise CoverageRejected(
            f"{frame.name}: its master is {frame.master.status}. Re-cut the frame from the "
            "scene's approved master before approving it."
        )
    if frame.source_master_sha256 != frame.master.asset.sha256:
        raise CoverageRejected(
            f"{frame.name}: taken from {frame.source_master_sha256[:12]}, but its master now "
            f"holds {frame.master.asset.sha256[:12]}. Redo it."
        )
    if (
        frame.is_extraction
        and frame.contact_sheet is not None
        and (frame.contact_sheet.status != "approved")
    ):
        raise CoverageRejected(
            f"{frame.name}: its contact sheet is {frame.contact_sheet.status}, so the panel "
            "it names is no longer the approved observation."
        )
    if frame.asset.status is not VisualAssetStatus.APPROVED:
        visual_library.approve_asset(session, frame.asset, note=note)

    frame.approved_for_veo = True
    session.add(
        AuditEvent(
            event_type=AuditEventType.COVERAGE_FRAME_APPROVED,
            actor=actor,
            payload_json={
                "coverage_frame_id": str(frame.id),
                "scene": frame.master.scene_key,
                "name": frame.name,
                "frame_sha256": frame.frame_sha256,
                "note": note,
            },
        )
    )
    return frame


def resolve_veo_seed(
    session: Session, store: AssetStore, *, scene_key: str, name: str
) -> ResolvedReference:
    """The bytes a Veo run may animate, or a refusal explaining which gate failed.

    §15 Phase E: a run cannot resolve a deprecated, replaced or lookalike asset
    by accident, because it does not name a file at all -- it names a shot in a
    scene, and everything else is checked here.
    """
    master = resolve_scene_master(session, store, scene_key=scene_key)

    frame = (
        session.execute(
            select(CoverageFrame)
            .join(SceneMaster, SceneMaster.id == CoverageFrame.scene_master_id)
            .where(SceneMaster.scene_key == scene_key, CoverageFrame.name == name)
            .order_by(CoverageFrame.created_at.desc())
        )
        .scalars()
        .first()
    )

    if frame is None:
        held = (
            session.execute(
                select(CoverageFrame.name)
                .join(SceneMaster, SceneMaster.id == CoverageFrame.scene_master_id)
                .where(SceneMaster.scene_key == scene_key)
            )
            .scalars()
            .all()
        )
        raise CoverageRejected(
            f"{scene_key}/{name}: no such coverage frame. "
            f"Held: {', '.join(sorted(held)) or 'nothing'}."
        )
    if not frame.approved_for_veo:
        raise CoverageRejected(
            f"{scene_key}/{name}: not approved for Veo. Cutting a frame is not approving it."
        )
    if frame.source_master_sha256 != master.sha256:
        origin = "extracted from a sheet of" if frame.is_extraction else "cut from"
        raise CoverageRejected(
            f"{scene_key}/{name}: {origin} master {frame.source_master_sha256[:12]}, but the "
            f"approved master is now {master.sha256[:12]}. Redo it against the current one."
        )
    if (
        frame.is_extraction
        and frame.contact_sheet is not None
        and (frame.contact_sheet.status != "approved")
    ):
        raise CoverageRejected(
            f"{scene_key}/{name}: its contact sheet is {frame.contact_sheet.status}. "
            "Extract the panel again from the approved sheet."
        )

    asset = session.get(VisualAsset, frame.visual_asset_id)
    if asset is None:  # pragma: no cover - foreign key prevents this
        raise CoverageRejected(f"{scene_key}/{name}: the frame's asset is missing.")

    from app.services.reference_resolution import resolve_asset

    return resolve_asset(session, store, asset.id, label=f"{scene_key}/{name}")


@dataclass(frozen=True)
class VeoTrigger:
    """The trigger file §17's workflow reads, and the name to save it under."""

    filename: str
    content: str


def veo_trigger(
    session: Session, store: AssetStore, *, frame: CoverageFrame, purpose: str, stamp: str
) -> VeoTrigger:
    """Build the trigger for one approved shot, or refuse with the reason why.

    The seed is resolved through ``resolve_veo_seed`` rather than read off the
    row, so building the trigger runs every gate the run itself would: approved
    for motion, cut from the master that is approved now, sheet still approved,
    and the file on disk still hashing to what the row says. A trigger that
    names a stale seed is worse than no trigger, because the workflow's own
    SHA check would pass -- it verifies the file matches the trigger, not that
    the trigger names the current shot.

    ``seed_relative_path`` is relative to the Studio checkout on the box, which
    is where the workflow resolves it from.
    """
    scene_key = frame.master.scene_key
    resolved = resolve_veo_seed(session, store, scene_key=scene_key, name=frame.name)

    asset = session.get(VisualAsset, resolved.asset_id)
    if asset is None:  # pragma: no cover - resolve_veo_seed already loaded it
        raise CoverageRejected(f"{frame.name}: the frame's asset is missing.")

    payload = {
        "scene": scene_key,
        "shot": frame.name,
        "seed_relative_path": f"assets/{asset.storage_key}",
        "seed_sha256": resolved.sha256,
        "source_master_sha256": frame.source_master_sha256,
        "purpose": purpose,
    }
    return VeoTrigger(
        filename=f"{stamp}-{frame.name}.json",
        content=json.dumps(payload, separators=(",", ":")),
    )


def register_contact_sheet(
    session: Session,
    store: AssetStore,
    *,
    scene_key: str,
    label: str,
    data: bytes,
    reference_asset_ids: Sequence[uuid.UUID] = (),
    rows: int = 3,
    columns: int = 3,
    prompt_template: str | None = None,
    resolved_prompt: str | None = None,
    panel_plan: Sequence[dict[str, Any]] = (),
    approve: bool = False,
    actor: str = OWNER,
) -> SceneContactSheet:
    """Record a Nano coverage sheet against the scene's approved master.

    ``reference_asset_ids`` is the exact set of character references fed to the
    model, recorded as lineage edges rather than a note: §6 asks for an input
    manifest, and edges are the version of that which can be queried from either
    end. The master is always one of the parents.

    Registering is not approving, and approving supersedes rather than replaces:
    a sheet that shots were already extracted from stays resolvable, because
    those shots cite it.
    """
    master_reference = resolve_scene_master(session, store, scene_key=scene_key)
    master = session.execute(
        select(SceneMaster).where(
            SceneMaster.scene_key == scene_key, SceneMaster.status == "approved"
        )
    ).scalar_one()

    ingested = visual_library.ingest_asset(
        session,
        store,
        data=data,
        kind=VisualAssetKind.COVERAGE,
        source_type=VisualAssetSourceType.GENERATED,
        role="contact_sheet",
        description=f"{scene_key} coverage contact sheet - {label}",
        metadata={
            "scene": scene_key,
            "grid": f"{rows}x{columns}",
            "prompt_template": prompt_template,
        },
    )

    sheet = session.execute(
        select(SceneContactSheet).where(SceneContactSheet.visual_asset_id == ingested.asset.id)
    ).scalar_one_or_none()
    if sheet is None:
        sheet = SceneContactSheet(
            scene_master_id=master.id, visual_asset_id=ingested.asset.id, label=label
        )
        session.add(sheet)

    sheet.rows, sheet.columns = rows, columns
    sheet.prompt_template = prompt_template
    sheet.resolved_prompt_sha256 = (
        hashlib.sha256(resolved_prompt.encode("utf-8")).hexdigest() if resolved_prompt else None
    )
    sheet.panel_plan = list(panel_plan)
    session.flush()

    # The master is spatial authority; each character reference is identity
    # authority. Both are parents of the sheet.
    _record_lineage_edge(
        session,
        parent=master_reference.asset_id,
        child=ingested.asset.id,
        relationship="generated_from_master",
    )
    for reference_id in reference_asset_ids:
        _record_lineage_edge(
            session,
            parent=reference_id,
            child=ingested.asset.id,
            relationship="generated_from_reference",
        )

    session.add(
        AuditEvent(
            event_type=AuditEventType.CONTACT_SHEET_REGISTERED,
            actor=actor,
            payload_json={
                "contact_sheet_id": str(sheet.id),
                "scene": scene_key,
                "label": label,
                "grid": f"{rows}x{columns}",
                "sha256": ingested.asset.sha256,
                "references": [str(one) for one in reference_asset_ids],
            },
        )
    )

    if approve:
        approve_contact_sheet(session, sheet, actor=actor)
    return sheet


def approve_contact_sheet(
    session: Session, sheet: SceneContactSheet, *, actor: str = OWNER, note: str | None = None
) -> SceneContactSheet:
    """Make this the sheet panels are chosen from. One per master."""
    if sheet.master.status != "approved":
        raise CoverageRejected(
            f"{sheet.label}: its master is {sheet.master.status}. A sheet of a superseded "
            "master cannot become the coverage authority."
        )
    if sheet.asset.status is not VisualAssetStatus.APPROVED:
        visual_library.approve_asset(session, sheet.asset, note=note)

    for other in session.execute(
        select(SceneContactSheet).where(
            SceneContactSheet.scene_master_id == sheet.scene_master_id,
            SceneContactSheet.status == "approved",
            SceneContactSheet.id != sheet.id,
        )
    ).scalars():
        other.status = "superseded"
    session.flush()

    sheet.status = "approved"
    sheet.approved_at = dt.datetime.now(dt.UTC)
    sheet.approved_by = actor
    session.add(
        AuditEvent(
            event_type=AuditEventType.CONTACT_SHEET_APPROVED,
            actor=actor,
            payload_json={
                "contact_sheet_id": str(sheet.id),
                "scene": sheet.master.scene_key,
                "label": sheet.label,
                "sha256": sheet.asset.sha256,
                "note": note,
            },
        )
    )
    return sheet


def approved_contact_sheet(session: Session, *, scene_key: str) -> SceneContactSheet:
    """The sheet panels are chosen from, or a refusal naming what is missing."""
    sheet = session.execute(
        select(SceneContactSheet)
        .join(SceneMaster, SceneMaster.id == SceneContactSheet.scene_master_id)
        .where(
            SceneMaster.scene_key == scene_key,
            SceneMaster.status == "approved",
            SceneContactSheet.status == "approved",
        )
    ).scalar_one_or_none()
    if sheet is None:
        raise CoverageRejected(
            f"{scene_key}: no approved coverage contact sheet for the current master. "
            "Register one and approve it before extracting panels."
        )
    return sheet


def record_panel_extraction(
    session: Session,
    store: AssetStore,
    *,
    scene_key: str,
    name: str,
    panel: int,
    data: bytes,
    aspect_ratio: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    provider_request_id: str | None = None,
    prompt_hash: str | None = None,
    notes: str | None = None,
    actor: str = OWNER,
) -> CoverageFrame:
    """Record the standalone still Nano returned for one panel.

    The bytes are the model's, not a crop of anything, so nothing here checks
    them against the sheet. What is checked is that the panel exists on the
    approved sheet; what is recorded is which sheet and which panel, the two
    facts that make the still traceable back to the master.

    Never approved for motion by this call. §5: a panel becomes a first frame
    only after it has been reviewed.
    """
    sheet = approved_contact_sheet(session, scene_key=scene_key)
    if panel < 1 or panel > sheet.panels:
        raise CoverageRejected(
            f"{scene_key}: panel {panel} is outside a {sheet.rows}x{sheet.columns} sheet "
            f"(1-{sheet.panels})."
        )

    ingested = visual_library.ingest_asset(
        session,
        store,
        data=data,
        kind=VisualAssetKind.COVERAGE,
        source_type=VisualAssetSourceType.GENERATED,
        role=name,
        description=f"{scene_key} panel {panel} - {name}",
        provider=provider,
        model=model,
        provider_request_id=provider_request_id,
        prompt_hash=prompt_hash,
        metadata={
            "scene": scene_key,
            "panel": panel,
            "contact_sheet": str(sheet.id),
            "aspect_ratio": aspect_ratio,
        },
    )
    _record_lineage_edge(
        session,
        parent=sheet.visual_asset_id,
        child=ingested.asset.id,
        relationship="extracted_from_panel",
        operation_metadata={"panel": panel},
    )

    frame = session.execute(
        select(CoverageFrame).where(
            CoverageFrame.contact_sheet_id == sheet.id, CoverageFrame.panel == panel
        )
    ).scalar_one_or_none()
    if frame is None:
        frame = CoverageFrame(
            scene_master_id=sheet.scene_master_id, contact_sheet_id=sheet.id, panel=panel
        )
        session.add(frame)

    frame.name = name
    frame.visual_asset_id = ingested.asset.id
    # Measured from what came back, not requested. §10's extraction is a crop:
    # the frame's shape is the panel's shape, and asking for a different one
    # turns a crop into a reframe. So this records the ratio rather than
    # imposing it.
    frame.aspect_ratio = aspect_ratio or measured_ratio(ingested.asset.width, ingested.asset.height)
    frame.width, frame.height = ingested.asset.width, ingested.asset.height
    frame.x = frame.y = None
    frame.frame_sha256 = ingested.asset.sha256
    frame.source_master_sha256 = sheet.master.asset.sha256
    frame.operation = "nano_extraction"
    frame.approved_for_veo = False
    if notes is not None:
        frame.notes = notes
    session.flush()

    session.add(
        AuditEvent(
            event_type=AuditEventType.COVERAGE_FRAME_DERIVED,
            actor=actor,
            payload_json={
                "coverage_frame_id": str(frame.id),
                "scene": scene_key,
                "name": name,
                "panel": panel,
                "operation": "nano_extraction",
                "contact_sheet_id": str(sheet.id),
                "frame_sha256": ingested.asset.sha256,
            },
        )
    )
    return frame
