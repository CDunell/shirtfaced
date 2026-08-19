"""Direct scene shot masters: approved vertical first frames without a contact sheet."""

from __future__ import annotations

import datetime as dt
import re
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore
from app.config import get_settings
from app.db.scene_shot_models import SceneShotMaster
from app.domain.enums import VisualAssetKind, VisualAssetSourceType, VisualAssetStatus
from app.domain.errors import StudioError
from app.services import visual_library
from app.services.reference_resolution import ResolvedReference, resolve_asset

MAX_APPROVED_SHOT_MASTERS = 5
NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class DirectShotError(StudioError):
    pass


class DirectShotNotFound(DirectShotError):
    pass


class DirectShotUnavailable(DirectShotError):
    pass


def _clean_name(name: str) -> str:
    value = name.strip().lower()
    if not NAME.fullmatch(value):
        raise DirectShotError(f"{name!r} is not a usable shot-master name.")
    return value


def configured_motion_prompt(scene_key: str, name: str) -> str | None:
    """Shot-specific repo prompt, then scene-wide fallback."""
    name = _clean_name(name)
    worlds = get_settings().worlds_root_resolved
    for candidate in (f"{scene_key}.{name}.veo-motion.txt", f"{scene_key}.veo-motion.txt"):
        for shots in sorted(worlds.glob("*/shots")):
            path = shots / candidate
            if path.is_file():
                return path.read_text(encoding="utf-8").strip()
    return None


def effective_motion_prompt(shot: SceneShotMaster) -> tuple[str | None, str]:
    """Return the prompt used by Veo and where it came from."""
    if shot.motion_prompt and shot.motion_prompt.strip():
        return shot.motion_prompt.strip(), "override"
    configured = configured_motion_prompt(shot.scene_key, shot.name)
    if configured:
        return configured, "configured"
    return None, "missing"


def set_motion_prompt(shot: SceneShotMaster, prompt: str | None) -> SceneShotMaster:
    """Persist a per-master override. Blank resets to configured fallback."""
    value = (prompt or "").strip()
    shot.motion_prompt = value or None
    return shot


def list_scene(session: Session, scene_key: str) -> list[SceneShotMaster]:
    return (
        session.execute(
            select(SceneShotMaster)
            .where(SceneShotMaster.scene_key == scene_key)
            .order_by(SceneShotMaster.sort_order, SceneShotMaster.created_at)
        )
        .scalars()
        .all()
    )


def register(
    session: Session,
    store: AssetStore,
    *,
    scene_key: str,
    name: str,
    data: bytes,
    notes: str | None = None,
    source_type: VisualAssetSourceType = VisualAssetSourceType.GENERATED,
) -> SceneShotMaster:
    name = _clean_name(name)
    existing = session.execute(
        select(SceneShotMaster).where(
            SceneShotMaster.scene_key == scene_key, SceneShotMaster.name == name
        )
    ).scalar_one_or_none()

    ingested = visual_library.ingest_asset(
        session,
        store,
        data=data,
        kind=VisualAssetKind.SCENE_MASTER,
        source_type=source_type,
        role=name,
        description=f"{scene_key} direct 9:16 shot master — {name}",
        metadata={"scene": scene_key, "shot_master": name, "pipeline": "direct_vertical"},
    )

    if existing is not None:
        if existing.visual_asset_id != ingested.asset.id:
            if existing.status == "approved":
                raise DirectShotError(
                    f"{scene_key}/{name} is approved already. Reject or rename it before replacing bytes."
                )
            existing.visual_asset_id = ingested.asset.id
            existing.status = "candidate"
            existing.approved_at = None
            existing.approved_by = None
        if notes is not None:
            existing.notes = notes
        session.flush()
        return existing

    highest = session.execute(
        select(func.max(SceneShotMaster.sort_order)).where(SceneShotMaster.scene_key == scene_key)
    ).scalar()
    shot = SceneShotMaster(
        scene_key=scene_key,
        name=name,
        visual_asset_id=ingested.asset.id,
        sort_order=0 if highest is None else highest + 1,
        notes=notes,
    )
    session.add(shot)
    session.flush()
    return shot


def approve(
    session: Session, shot: SceneShotMaster, *, actor: str = "owner", note: str | None = None
) -> SceneShotMaster:
    if shot.status == "approved":
        return shot
    count = session.execute(
        select(func.count(SceneShotMaster.id)).where(
            SceneShotMaster.scene_key == shot.scene_key,
            SceneShotMaster.status == "approved",
            SceneShotMaster.id != shot.id,
        )
    ).scalar_one()
    if count >= MAX_APPROVED_SHOT_MASTERS:
        raise DirectShotError(
            f"{shot.scene_key} already has {MAX_APPROVED_SHOT_MASTERS} approved shot masters. "
            "Reject one before approving another."
        )
    if shot.asset.status is not VisualAssetStatus.APPROVED:
        visual_library.approve_asset(session, shot.asset, actor=actor, note=note)
    shot.status = "approved"
    shot.approved_at = dt.datetime.now(dt.UTC)
    shot.approved_by = actor
    if note is not None:
        shot.notes = note
    session.flush()
    return shot


def reject(
    session: Session, shot: SceneShotMaster, *, actor: str = "owner", note: str | None = None
) -> SceneShotMaster:
    shot.status = "rejected"
    shot.approved_at = None
    shot.approved_by = None
    if note is not None:
        shot.notes = note
    if shot.asset.status is VisualAssetStatus.APPROVED:
        visual_library.deprecate_asset(session, shot.asset, actor=actor, note=note)
    session.flush()
    return shot


def resolve(
    session: Session, store: AssetStore, *, scene_key: str, name: str
) -> ResolvedReference:
    name = _clean_name(name)
    shot = session.execute(
        select(SceneShotMaster).where(
            SceneShotMaster.scene_key == scene_key, SceneShotMaster.name == name
        )
    ).scalar_one_or_none()
    if shot is None:
        raise DirectShotNotFound(f"{scene_key}/{name}: no direct shot master.")
    if shot.status != "approved":
        raise DirectShotUnavailable(
            f"{scene_key}/{name}: direct shot master is {shot.status}, not approved for Veo."
        )
    return resolve_asset(session, store, shot.visual_asset_id, label=f"{scene_key}/{name}")


def by_scene_name(session: Session, scene_key: str, name: str) -> SceneShotMaster:
    name = _clean_name(name)
    shot = session.execute(
        select(SceneShotMaster).where(
            SceneShotMaster.scene_key == scene_key, SceneShotMaster.name == name
        )
    ).scalar_one_or_none()
    if shot is None:
        raise DirectShotNotFound(f"{scene_key}/{name}: no direct shot master.")
    return shot


def by_id(session: Session, shot_id: uuid.UUID) -> SceneShotMaster:
    shot = session.get(SceneShotMaster, shot_id)
    if shot is None:
        raise DirectShotNotFound(f"No direct shot master {shot_id}.")
    return shot
