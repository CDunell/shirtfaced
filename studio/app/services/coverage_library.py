"""Cutting coverage frames, and recording what they are observations of.

``VISUAL_ASSET_LIBRARY.md`` §8. A coverage frame is a named 9:16 window onto one
scene master: original pixels, never a resize, never a regeneration.

What this adds over the manifest-in-a-directory it replaces is that the frame
has an identity. It can be asked which master it came from, whether that master
is still the approved one, and whether anyone approved the frame itself for Veo.
None of those questions could be asked of a file.

The crop is deterministic: the same master and the same box produce the same
bytes, so a frame can be re-derived and checked rather than trusted.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from io import BytesIO

from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore
from app.db.models import AuditEvent
from app.db.visual_models import AssetLineage, CoverageFrame, SceneMaster, VisualAsset
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
            f"{frame.name}: cut from {frame.source_master_sha256[:12]}, but its master now "
            f"holds {frame.master.asset.sha256[:12]}. Re-cut it."
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
        raise CoverageRejected(
            f"{scene_key}/{name}: cut from master {frame.source_master_sha256[:12]}, but the "
            f"approved master is now {master.sha256[:12]}. Re-cut and re-approve it."
        )

    asset = session.get(VisualAsset, frame.visual_asset_id)
    if asset is None:  # pragma: no cover - foreign key prevents this
        raise CoverageRejected(f"{scene_key}/{name}: the frame's asset is missing.")

    from app.services.reference_resolution import resolve_asset

    return resolve_asset(session, store, asset.id, label=f"{scene_key}/{name}")
