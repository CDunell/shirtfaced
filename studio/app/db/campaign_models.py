"""Campaign/story/cast/location models for AI-native world production.

ADR-016 keeps the existing ``Shot`` / ``GenerationAttempt`` production spine.
This module therefore owns only the genuinely new campaign-domain tables added
by migration 0029. ``Shot`` remains mapped in ``app.db.models`` and is extended
there rather than remapped here.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"
    __table_args__ = (
        Index("ix_campaigns_world_id_status", "world_id", "status"),
        CheckConstraint(
            "status IN ('draft','developing','preproduction','generating','editing',"
            "'review','scheduled','live','complete','abandoned')",
            name="campaign_status_valid",
        ),
        CheckConstraint(
            "target_primary_post_count >= 0",
            name="campaign_target_primary_post_count_nonnegative",
        ),
        CheckConstraint(
            "cycle_end_at IS NULL OR cycle_start_at IS NULL OR cycle_end_at >= cycle_start_at",
            name="campaign_cycle_dates_ordered",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worlds.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(96), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="draft")
    campaign_type: Mapped[str] = mapped_column(String(64), nullable=False)
    premise: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    objective: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    cycle_number: Mapped[int | None] = mapped_column(Integer)
    cycle_start_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    cycle_end_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    target_platforms: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    target_primary_post_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("10")
    )
    channel_mix: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    presentation_mix: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    design_scope: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    creative_brief: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    origin_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )


class StoryVersion(Base, TimestampMixin):
    __tablename__ = "story_versions"
    __table_args__ = (
        UniqueConstraint("campaign_id", "version", name="uq_story_versions_campaign_id_version"),
        UniqueConstraint("id", "campaign_id", name="uq_story_versions_id_campaign_id"),
        ForeignKeyConstraint(
            ["parent_story_version_id", "campaign_id"],
            ["story_versions.id", "story_versions.campaign_id"],
            name="fk_story_versions_parent_same_campaign",
            ondelete="RESTRICT",
        ),
        Index("ix_story_versions_campaign_id_state", "campaign_id", "state"),
        Index(
            "uq_story_versions_one_approved_per_campaign",
            "campaign_id",
            unique=True,
            postgresql_where=text("state = 'approved'"),
        ),
        CheckConstraint("version > 0", name="story_version_positive"),
        CheckConstraint(
            "state IN ('draft','review','approved','rejected','superseded')",
            name="story_version_state_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    parent_story_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    logline: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    synopsis: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    setup: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    commitment: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    escalation: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    complication: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    peak: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    aftermath: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    mechanism: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    ending_callback: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    directing_language_plan: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    story_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    prompt_provenance: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    state: Mapped[str] = mapped_column(String(32), nullable=False, server_default="draft")
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class Character(Base, TimestampMixin):
    __tablename__ = "characters"
    __table_args__ = (
        UniqueConstraint("campaign_id", "handle", name="uq_characters_campaign_id_handle"),
        UniqueConstraint("id", "campaign_id", name="uq_characters_id_campaign_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    handle: Mapped[str] = mapped_column(String(96), nullable=False)
    story_role: Mapped[str | None] = mapped_column(String(120))
    age_band: Mapped[str | None] = mapped_column(String(64))
    build_height_intent: Mapped[str | None] = mapped_column(Text)
    appearance_spec: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    identity_lock: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    voice_dialogue_notes: Mapped[str | None] = mapped_column(Text)
    reference_asset_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    allowed_variation: Mapped[str | None] = mapped_column(Text)
    forbidden_drift: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class CharacterAppearance(Base, TimestampMixin):
    __tablename__ = "character_appearances"
    __table_args__ = (
        ForeignKeyConstraint(
            ["character_id", "campaign_id"],
            ["characters.id", "characters.campaign_id"],
            name="fk_character_appearances_character_same_campaign",
            ondelete="CASCADE",
        ),
        UniqueConstraint("character_id", "code", name="uq_character_appearances_character_id_code"),
        UniqueConstraint("id", "character_id", name="uq_character_appearances_id_character_id"),
        CheckConstraint(
            "last_scene_sequence IS NULL OR first_scene_sequence IS NULL OR "
            "last_scene_sequence >= first_scene_sequence",
            name="appearance_scene_range_ordered",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    character_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(96), nullable=False)
    first_scene_sequence: Mapped[int | None] = mapped_column(Integer)
    last_scene_sequence: Mapped[int | None] = mapped_column(Integer)
    garment_scope: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    colour: Mapped[str | None] = mapped_column(String(80))
    fit_silhouette: Mapped[str | None] = mapped_column(Text)
    layer_state: Mapped[str | None] = mapped_column(Text)
    artwork_refs: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    accessories: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    mutable_state: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    allowed_changes: Mapped[str | None] = mapped_column(Text)
    forbidden_changes: Mapped[str | None] = mapped_column(Text)
    reference_asset_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )


class Location(Base, TimestampMixin):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("campaign_id", "code", name="uq_locations_campaign_id_code"),
        UniqueConstraint("id", "campaign_id", name="uq_locations_id_campaign_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(96), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    environment_intent: Mapped[str | None] = mapped_column(Text)
    reference_asset_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    spatial_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    lighting_defaults: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    fixed_props: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    allowed_variation: Mapped[str | None] = mapped_column(Text)
    forbidden_drift: Mapped[str | None] = mapped_column(Text)


class Scene(Base, TimestampMixin):
    __tablename__ = "scenes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["story_version_id", "campaign_id"],
            ["story_versions.id", "story_versions.campaign_id"],
            name="fk_scenes_story_version_same_campaign",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["location_id", "campaign_id"],
            ["locations.id", "locations.campaign_id"],
            name="fk_scenes_location_same_campaign",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("campaign_id", "scene_code", name="uq_scenes_campaign_id_scene_code"),
        UniqueConstraint("campaign_id", "sequence", name="uq_scenes_campaign_id_sequence"),
        UniqueConstraint("id", "campaign_id", name="uq_scenes_id_campaign_id"),
        Index("ix_scenes_campaign_id_state", "campaign_id", "state"),
        CheckConstraint("sequence > 0", name="scene_sequence_positive"),
        CheckConstraint(
            "state IN ('draft','review','approved','rejected','superseded')",
            name="scene_state_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    story_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    location_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    scene_code: Mapped[str] = mapped_column(String(96), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    story_purpose: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    time_state: Mapped[str | None] = mapped_column(String(120))
    lighting_state: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    environment_state: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    action_beats: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    dialogue_audio_intent: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    props: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    continuity_in: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    continuity_out: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    candidate_post_roles: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    directing_language: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    state: Mapped[str] = mapped_column(String(32), nullable=False, server_default="draft")
    review_reason: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))


class SceneCharacter(Base):
    __tablename__ = "scene_characters"
    __table_args__ = (
        ForeignKeyConstraint(
            ["scene_id", "campaign_id"],
            ["scenes.id", "scenes.campaign_id"],
            name="fk_scene_characters_scene_same_campaign",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["character_id", "campaign_id"],
            ["characters.id", "characters.campaign_id"],
            name="fk_scene_characters_character_same_campaign",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["appearance_id", "character_id"],
            ["character_appearances.id", "character_appearances.character_id"],
            name="fk_scene_characters_appearance_same_character",
            ondelete="RESTRICT",
        ),
    )

    scene_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    character_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    appearance_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    role_in_scene: Mapped[str | None] = mapped_column(String(120))
    entrance_state: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    exit_state: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    blocking_notes: Mapped[str | None] = mapped_column(Text)
    performance_notes: Mapped[str | None] = mapped_column(Text)


class ShotCharacter(Base):
    __tablename__ = "shot_characters"
    __table_args__ = (
        ForeignKeyConstraint(
            ["character_id", "campaign_id"],
            ["characters.id", "characters.campaign_id"],
            name="fk_shot_characters_character_same_campaign",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["appearance_id", "character_id"],
            ["character_appearances.id", "character_appearances.character_id"],
            name="fk_shot_characters_appearance_same_character",
            ondelete="RESTRICT",
        ),
    )

    shot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shots.id", name="fk_shot_characters_shot_id_shots", ondelete="CASCADE"),
        primary_key=True,
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    character_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    appearance_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    prominence: Mapped[str | None] = mapped_column(String(64))
    expected_position: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    action: Mapped[str | None] = mapped_column(Text)
    eyeline: Mapped[str | None] = mapped_column(String(160))
    continuity_notes: Mapped[str | None] = mapped_column(Text)
