"""Direct 9:16 first frames for scene video coverage.

A scene may approve up to five independent shot masters. They are deliberately
separate from ``SceneMaster``: the older table is spatial truth for the legacy
master -> contact sheet -> panel workflow. A direct shot master is already the
camera observation Veo should animate, so making it pretend to be a crop or a
3x3 panel would add lineage that never happened.
"""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.visual_models import VisualAsset


class SceneShotMaster(Base, TimestampMixin):
    __tablename__ = "scene_shot_masters"
    __table_args__ = (
        UniqueConstraint("scene_key", "name", name="uq_scene_shot_masters_scene_name"),
        UniqueConstraint("visual_asset_id", name="uq_scene_shot_masters_visual_asset_id"),
        Index("ix_scene_shot_masters_scene_status", "scene_key", "status"),
        Index("ix_scene_shot_masters_scene_order", "scene_key", "sort_order"),
        CheckConstraint(
            "status IN ('candidate','approved','rejected','deprecated')",
            name="ck_scene_shot_masters_status_known",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    scene_key: Mapped[str] = mapped_column(String(96), nullable=False)
    name: Mapped[str] = mapped_column(String(96), nullable=False)
    visual_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visual_assets.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="candidate")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    notes: Mapped[str | None] = mapped_column(Text)
    motion_prompt: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[str | None] = mapped_column(String(64))

    asset: Mapped[VisualAsset] = relationship(lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SceneShotMaster {self.scene_key!r}/{self.name!r} {self.status!r}>"
