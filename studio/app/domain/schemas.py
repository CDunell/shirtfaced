"""Structured representations of the canonical documents."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ShotStatus


class ParsedShot(BaseModel):
    """One row of ``SHOTLIST.md``."""

    model_config = ConfigDict(frozen=True)

    external_id: str = Field(min_length=1, max_length=64)
    sequence: int = Field(ge=1)
    priority: int = Field(default=100, ge=0)
    title: str = Field(min_length=1, max_length=200)
    hero_product: str | None = None
    camera_position: str | None = None
    lighting_source: str | None = None
    status: ShotStatus = ShotStatus.PLANNED
    source_line: int = Field(ge=1)


class DocumentSummary(BaseModel):
    """Identity of a loaded document."""

    model_config = ConfigDict(frozen=True)

    name: str
    sha256: str
    headings: list[str] = Field(default_factory=list)


class LoadedWorld(BaseModel):
    """A validated world, ready to import or display."""

    model_config = ConfigDict(frozen=True)

    slug: str
    name: str
    directory_path: str
    world_document: DocumentSummary
    continuity_document: DocumentSummary
    shotlist_document: DocumentSummary
    shots: list[ParsedShot] = Field(default_factory=list)

    @property
    def planned_shots(self) -> list[ParsedShot]:
        return [shot for shot in self.shots if shot.status is ShotStatus.PLANNED]
