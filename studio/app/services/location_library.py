"""Locations, their scouting plates, and the gate in front of a base master.

``VISUAL_ASSET_LIBRARY.md`` §6. The document's own framing is the useful one:
this is a virtual location department, not a folder of attractive photographs.
A useful plate is spatially legible and reusable, which is a different property
from being a good picture.

``promote_to_base_master`` is the only gated call in this module, and everything
it refuses, it refuses by naming the specific gate.

Rights are one of those gates and, as of the owner's ruling on 17 August 2026,
one that passes by construction: the locations are invented and generated here
like everything else, so assets default to verified. The check remains for the
case §6.4 was written for — something deliberately marked ``refused`` — and
costs nothing while that case does not exist.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore
from app.db.models import AuditEvent
from app.db.visual_models import LocationAsset, ScoutLocation, VisualAsset
from app.domain.enums import (
    BASE_MASTER_ROLES,
    AuditEventType,
    LicenceStatus,
    LocationAssetRole,
    VisualAssetStatus,
)
from app.domain.errors import StudioError
from app.services.reference_resolution import (
    ReferenceUnavailable,
    ResolvedReference,
    load_reference,
)

logger = logging.getLogger(__name__)

OWNER = "owner"

# A 9:16 window at full height is 0.5625 of the height wide. A plate narrower
# than that cannot yield one vertical frame at all -- that is arithmetic, and
# the only width rule here.
#
# §6.3 *prefers* 2.39:1, and the reason is lateral geography: room to move the
# window. Preference is not a gate. A 16:9 plate is what pub-1105 is actually
# built on, and refusing it because it is not ultrawide would be a rule nobody
# made -- the same mistake as the 25mm legibility test and the 20mm minimum
# print. The report says how much lateral room there is; the owner decides
# whether it is enough.
VERTICAL_RATIO = 9 / 16
PREFERRED_WIDE_RATIO = 2.39


class LocationRejected(StudioError):
    """This plate cannot do the job being asked of it."""


@dataclass(frozen=True)
class BaseMasterReadiness:
    """Why a plate can or cannot be the thing a scene is built into.

    Reported as a whole rather than one failure at a time: a scout who has to
    fix three things learns all three at once, §13's habit.
    """

    approved: bool
    rights_verified: bool
    role_is_a_stage: bool
    yields_a_vertical_frame: bool
    ratio: float
    # How far a full-height 9:16 window can travel across the plate, in pixels.
    # Zero means one fixed frame and no coverage; §6.3's preference is really a
    # preference for this number being large.
    lateral_room_px: int
    problems: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not self.problems

    @property
    def meets_the_wide_preference(self) -> bool:
        """§6.3's 2.39:1. Reported, never enforced."""
        return self.ratio >= PREFERRED_WIDE_RATIO


def register_location(
    session: Session,
    *,
    slug: str,
    display_name: str,
    parent: ScoutLocation | None = None,
    location_type: str | None = None,
    description: str | None = None,
    actor: str = OWNER,
    **notes: object,
) -> ScoutLocation:
    """Record a place. Idempotent on the slug: the same place is one row."""
    existing = session.execute(
        select(ScoutLocation).where(ScoutLocation.slug == slug)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    location = ScoutLocation(
        slug=slug,
        display_name=display_name,
        parent_location_id=parent.id if parent else None,
        location_type=location_type,
        description=description,
    )
    for field, value in notes.items():
        if hasattr(location, field):
            setattr(location, field, value)
    session.add(location)
    session.flush()

    session.add(
        AuditEvent(
            event_type=AuditEventType.LOCATION_REGISTERED,
            actor=actor,
            payload_json={
                "location_id": str(location.id),
                "slug": slug,
                "parent": parent.slug if parent else None,
            },
        )
    )
    return location


def attach_plate(
    session: Session,
    location: ScoutLocation,
    asset: VisualAsset,
    *,
    role: LocationAssetRole,
    camera_position: str | None = None,
    exposure_notes: str | None = None,
    notes: str | None = None,
    sort_order: int | None = None,
    actor: str = OWNER,
) -> LocationAsset:
    """File an image against a place. Never gated: everything gets ingested."""
    link = session.execute(
        select(LocationAsset).where(
            LocationAsset.location_id == location.id,
            LocationAsset.visual_asset_id == asset.id,
        )
    ).scalar_one_or_none()

    if sort_order is None:
        highest = session.execute(
            select(func.max(LocationAsset.sort_order)).where(
                LocationAsset.location_id == location.id
            )
        ).scalar()
        sort_order = 0 if highest is None else highest + 1

    if link is None:
        link = LocationAsset(
            location_id=location.id,
            visual_asset_id=asset.id,
            role=role,
            sort_order=sort_order,
        )
        session.add(link)
    else:
        link.role = role

    if camera_position is not None:
        link.camera_position = camera_position
    if exposure_notes is not None:
        link.exposure_notes = exposure_notes
    if notes is not None:
        link.notes = notes
    session.flush()

    session.add(
        AuditEvent(
            event_type=AuditEventType.LOCATION_ASSET_LINKED,
            actor=actor,
            payload_json={
                "location": location.slug,
                "asset_id": str(asset.id),
                "sha256": asset.sha256,
                "role": role.value,
            },
        )
    )
    return link


def assess_base_master(link: LocationAsset) -> BaseMasterReadiness:
    """§13's location gate, as a report rather than an exception."""
    asset = link.asset
    ratio = asset.width / asset.height
    problems: list[str] = []

    approved = asset.status is VisualAssetStatus.APPROVED
    if not approved:
        problems.append(f"the image is {asset.status.value}, not approved")

    # Assets default to verified because the owner invents them. This fires only
    # for something deliberately marked otherwise.
    rights_verified = asset.rights_status is LicenceStatus.VERIFIED
    if not rights_verified:
        problems.append(
            f"rights are {asset.rights_status.value}; a scene generated into this would be "
            "sold from it"
        )

    role_is_a_stage = link.role in BASE_MASTER_ROLES
    if not role_is_a_stage:
        problems.append(
            f"{link.role.value} is a reference, not a stage. A base master is an empty or "
            "participant-neutral plate"
        )

    window_width = round(asset.height * VERTICAL_RATIO)
    yields_a_vertical_frame = window_width <= asset.width
    if not yields_a_vertical_frame:
        problems.append(
            f"{asset.width}x{asset.height} cannot yield one full-height 9:16 frame, which "
            f"needs {window_width}px of width"
        )

    return BaseMasterReadiness(
        approved=approved,
        rights_verified=rights_verified,
        role_is_a_stage=role_is_a_stage,
        yields_a_vertical_frame=yields_a_vertical_frame,
        ratio=round(ratio, 3),
        lateral_room_px=max(0, asset.width - window_width),
        problems=tuple(problems),
    )


def promote_to_base_master(
    session: Session, link: LocationAsset, *, actor: str = OWNER, note: str | None = None
) -> LocationAsset:
    """Make this the plate scenes are built into. One per location.

    Promoting a second demotes the first rather than failing on the index: the
    caller is stating which plate the location is now, and there is one answer.
    """
    readiness = assess_base_master(link)
    if not readiness.ready:
        raise LocationRejected(
            f"{link.location.slug}: this plate cannot be the base master. "
            + "; ".join(readiness.problems)
            + "."
        )

    for other in session.execute(
        select(LocationAsset).where(
            LocationAsset.location_id == link.location_id,
            LocationAsset.is_base_master.is_(True),
            LocationAsset.id != link.id,
        )
    ).scalars():
        other.is_base_master = False
    session.flush()

    link.is_base_master = True
    session.add(
        AuditEvent(
            event_type=AuditEventType.LOCATION_MASTER_APPROVED,
            actor=actor,
            payload_json={
                "location": link.location.slug,
                "asset_id": str(link.visual_asset_id),
                "sha256": link.asset.sha256,
                "role": link.role.value,
                "ratio": readiness.ratio,
                "note": note,
            },
        )
    )
    return link


def resolve_base_master(session: Session, store: AssetStore, *, slug: str) -> ResolvedReference:
    """The plate a scene at this location is built into, or a refusal.

    Falls back to the parent location: a scene in the back room of a pub that
    has no plate of its own can still be built into the pub's, which is the
    point of letting locations nest.
    """
    location = session.execute(
        select(ScoutLocation).where(ScoutLocation.slug == slug)
    ).scalar_one_or_none()
    if location is None:
        raise ReferenceUnavailable(f"location:{slug}: no such location.")

    seen: list[str] = []
    current: ScoutLocation | None = location
    while current is not None:
        seen.append(current.slug)
        link = session.execute(
            select(LocationAsset).where(
                LocationAsset.location_id == current.id,
                LocationAsset.is_base_master.is_(True),
            )
        ).scalar_one_or_none()
        if link is not None:
            return load_reference(store, link.asset, f"location:{current.slug}")
        current = current.parent

    raise ReferenceUnavailable(
        f"location:{slug}: no approved base master here or above it (looked at "
        f"{', '.join(seen)}). Promote a plate before generating into this place."
    )
