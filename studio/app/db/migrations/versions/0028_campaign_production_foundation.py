"""campaign production foundation and dual-provenance shots

Revision ID: 0028
Revises: 0027
Create Date: 2026-08-14

ADR-016 keeps one world-production spine for still and video. ADR-017 keeps
Markdown-seeded photography and campaign-native production in the same ``shots``
table without teaching SHOTLIST.md about scenes.

This revision adds only the upstream campaign/story/cast/location/scene domain
and the directing fields required to make a campaign-native shot a persisted
production contract. It deliberately does not touch generation_attempts,
image_assets, automated_reviews or the social publishing tables. Those are
separate, coordinated revisions so the media rename and judge rewrite can be
audited independently.

Existing shots are backfilled as ``markdown_import`` + ``still`` and keep their
world_id, external_id and source_line unchanged.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONB = postgresql.JSONB(astext_type=sa.Text())
UUID = postgresql.UUID(as_uuid=True)


def _timestamps() -> tuple[sa.Column[object], sa.Column[object]]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("world_id", UUID, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=96), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("campaign_type", sa.String(length=64), nullable=False),
        sa.Column("premise", sa.Text(), server_default="", nullable=False),
        sa.Column("objective", sa.Text(), server_default="", nullable=False),
        sa.Column("cycle_number", sa.Integer(), nullable=True),
        sa.Column("cycle_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cycle_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target_platforms", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column(
            "target_primary_post_count", sa.Integer(), server_default=sa.text("10"), nullable=False
        ),
        sa.Column("channel_mix", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("presentation_mix", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("design_scope", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("creative_brief", sa.Text(), server_default="", nullable=False),
        sa.Column("origin_metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["world_id"],
            ["worlds.id"],
            name="fk_campaigns_world_id_worlds",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_campaigns"),
        sa.UniqueConstraint("slug", name="uq_campaigns_slug"),
        sa.CheckConstraint(
            "status IN ('draft','developing','preproduction','generating','editing',"
            "'review','scheduled','live','complete','abandoned')",
            name="campaign_status_valid",
        ),
        sa.CheckConstraint(
            "target_primary_post_count >= 0",
            name="campaign_target_primary_post_count_nonnegative",
        ),
        sa.CheckConstraint(
            "cycle_end_at IS NULL OR cycle_start_at IS NULL OR cycle_end_at >= cycle_start_at",
            name="campaign_cycle_dates_ordered",
        ),
    )
    op.create_index("ix_campaigns_world_id_status", "campaigns", ["world_id", "status"])

    op.create_table(
        "story_versions",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("campaign_id", UUID, nullable=False),
        sa.Column("parent_story_version_id", UUID, nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("logline", sa.Text(), server_default="", nullable=False),
        sa.Column("synopsis", sa.Text(), server_default="", nullable=False),
        sa.Column("setup", sa.Text(), server_default="", nullable=False),
        sa.Column("commitment", sa.Text(), server_default="", nullable=False),
        sa.Column("escalation", sa.Text(), server_default="", nullable=False),
        sa.Column("complication", sa.Text(), server_default="", nullable=False),
        sa.Column("peak", sa.Text(), server_default="", nullable=False),
        sa.Column("aftermath", sa.Text(), server_default="", nullable=False),
        sa.Column("mechanism", sa.Text(), server_default="", nullable=False),
        sa.Column("ending_callback", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "directing_language_plan",
            JSONB,
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("story_json", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column(
            "prompt_provenance", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("state", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
            name="fk_story_versions_campaign_id_campaigns",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_story_versions"),
        sa.UniqueConstraint("campaign_id", "version", name="uq_story_versions_campaign_id_version"),
        sa.UniqueConstraint("id", "campaign_id", name="uq_story_versions_id_campaign_id"),
        sa.CheckConstraint("version > 0", name="story_version_positive"),
        sa.CheckConstraint(
            "state IN ('draft','review','approved','rejected','superseded')",
            name="story_version_state_valid",
        ),
    )
    op.create_foreign_key(
        "fk_story_versions_parent_same_campaign",
        "story_versions",
        "story_versions",
        ["parent_story_version_id", "campaign_id"],
        ["id", "campaign_id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_story_versions_campaign_id_state", "story_versions", ["campaign_id", "state"]
    )
    op.create_index(
        "uq_story_versions_one_approved_per_campaign",
        "story_versions",
        ["campaign_id"],
        unique=True,
        postgresql_where=sa.text("state = 'approved'"),
    )

    op.create_table(
        "characters",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("campaign_id", UUID, nullable=False),
        sa.Column("handle", sa.String(length=96), nullable=False),
        sa.Column("story_role", sa.String(length=120), nullable=True),
        sa.Column("age_band", sa.String(length=64), nullable=True),
        sa.Column("build_height_intent", sa.Text(), nullable=True),
        sa.Column("appearance_spec", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("identity_lock", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("voice_dialogue_notes", sa.Text(), nullable=True),
        sa.Column(
            "reference_asset_ids", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False
        ),
        sa.Column("allowed_variation", sa.Text(), nullable=True),
        sa.Column("forbidden_drift", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
            name="fk_characters_campaign_id_campaigns",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_characters"),
        sa.UniqueConstraint("campaign_id", "handle", name="uq_characters_campaign_id_handle"),
        sa.UniqueConstraint("id", "campaign_id", name="uq_characters_id_campaign_id"),
    )

    op.create_table(
        "character_appearances",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("character_id", UUID, nullable=False),
        sa.Column("campaign_id", UUID, nullable=False),
        sa.Column("code", sa.String(length=96), nullable=False),
        sa.Column("first_scene_sequence", sa.Integer(), nullable=True),
        sa.Column("last_scene_sequence", sa.Integer(), nullable=True),
        sa.Column("garment_scope", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("colour", sa.String(length=80), nullable=True),
        sa.Column("fit_silhouette", sa.Text(), nullable=True),
        sa.Column("layer_state", sa.Text(), nullable=True),
        sa.Column("artwork_refs", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("accessories", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("mutable_state", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("allowed_changes", sa.Text(), nullable=True),
        sa.Column("forbidden_changes", sa.Text(), nullable=True),
        sa.Column(
            "reference_asset_ids", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False
        ),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
            name="fk_character_appearances_campaign_id_campaigns",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["character_id", "campaign_id"],
            ["characters.id", "characters.campaign_id"],
            name="fk_character_appearances_character_same_campaign",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_character_appearances"),
        sa.UniqueConstraint(
            "character_id", "code", name="uq_character_appearances_character_id_code"
        ),
        sa.UniqueConstraint("id", "character_id", name="uq_character_appearances_id_character_id"),
        sa.CheckConstraint(
            "last_scene_sequence IS NULL OR first_scene_sequence IS NULL OR "
            "last_scene_sequence >= first_scene_sequence",
            name="character_appearance_scene_range_ordered",
        ),
    )

    op.create_table(
        "locations",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("campaign_id", UUID, nullable=False),
        sa.Column("code", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("environment_intent", sa.Text(), nullable=True),
        sa.Column(
            "reference_asset_ids", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False
        ),
        sa.Column("spatial_json", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column(
            "lighting_defaults", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("fixed_props", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("allowed_variation", sa.Text(), nullable=True),
        sa.Column("forbidden_drift", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
            name="fk_locations_campaign_id_campaigns",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_locations"),
        sa.UniqueConstraint("campaign_id", "code", name="uq_locations_campaign_id_code"),
        sa.UniqueConstraint("id", "campaign_id", name="uq_locations_id_campaign_id"),
    )

    op.create_table(
        "scenes",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("campaign_id", UUID, nullable=False),
        sa.Column("story_version_id", UUID, nullable=False),
        sa.Column("location_id", UUID, nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("scene_code", sa.String(length=96), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("story_purpose", sa.Text(), server_default="", nullable=False),
        sa.Column("time_state", sa.String(length=120), nullable=True),
        sa.Column("lighting_state", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column(
            "environment_state", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("action_beats", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column(
            "dialogue_audio_intent",
            JSONB,
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("props", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("continuity_in", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("continuity_out", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column(
            "candidate_post_roles", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False
        ),
        sa.Column(
            "directing_language", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("state", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaigns.id"],
            name="fk_scenes_campaign_id_campaigns",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["story_version_id", "campaign_id"],
            ["story_versions.id", "story_versions.campaign_id"],
            name="fk_scenes_story_version_same_campaign",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["location_id", "campaign_id"],
            ["locations.id", "locations.campaign_id"],
            name="fk_scenes_location_same_campaign",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_scenes"),
        sa.UniqueConstraint("campaign_id", "scene_code", name="uq_scenes_campaign_id_scene_code"),
        sa.UniqueConstraint("campaign_id", "sequence", name="uq_scenes_campaign_id_sequence"),
        sa.UniqueConstraint("id", "campaign_id", name="uq_scenes_id_campaign_id"),
        sa.CheckConstraint("sequence > 0", name="scene_sequence_positive"),
        sa.CheckConstraint(
            "state IN ('draft','review','approved','rejected','superseded')",
            name="scene_state_valid",
        ),
    )
    op.create_index("ix_scenes_campaign_id_state", "scenes", ["campaign_id", "state"])

    op.create_table(
        "scene_characters",
        sa.Column("scene_id", UUID, nullable=False),
        sa.Column("campaign_id", UUID, nullable=False),
        sa.Column("character_id", UUID, nullable=False),
        sa.Column("appearance_id", UUID, nullable=True),
        sa.Column("role_in_scene", sa.String(length=120), nullable=True),
        sa.Column("entrance_state", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("exit_state", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("blocking_notes", sa.Text(), nullable=True),
        sa.Column("performance_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["scene_id", "campaign_id"],
            ["scenes.id", "scenes.campaign_id"],
            name="fk_scene_characters_scene_same_campaign",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["character_id", "campaign_id"],
            ["characters.id", "characters.campaign_id"],
            name="fk_scene_characters_character_same_campaign",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["appearance_id", "character_id"],
            ["character_appearances.id", "character_appearances.character_id"],
            name="fk_scene_characters_appearance_same_character",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("scene_id", "character_id", name="pk_scene_characters"),
    )

    op.add_column(
        "shots",
        sa.Column("source", sa.String(length=32), server_default="markdown_import", nullable=False),
    )
    op.add_column("shots", sa.Column("campaign_id", UUID, nullable=True))
    op.add_column("shots", sa.Column("scene_id", UUID, nullable=True))
    op.add_column(
        "shots",
        sa.Column("media_intent", sa.String(length=16), server_default="still", nullable=False),
    )
    op.add_column("shots", sa.Column("intended_duration_ms", sa.Integer(), nullable=True))
    op.add_column("shots", sa.Column("target_aspect", sa.String(length=32), nullable=True))
    op.add_column("shots", sa.Column("safe_crop", JSONB, nullable=True))
    op.add_column("shots", sa.Column("shot_size", sa.String(length=24), nullable=True))
    op.add_column("shots", sa.Column("camera_height", sa.String(length=80), nullable=True))
    op.add_column("shots", sa.Column("camera_angle", sa.String(length=80), nullable=True))
    op.add_column("shots", sa.Column("focal_length_intent", sa.String(length=120), nullable=True))
    op.add_column("shots", sa.Column("camera_movement", sa.String(length=120), nullable=True))
    op.add_column("shots", sa.Column("blocking_json", JSONB, nullable=True))
    op.add_column("shots", sa.Column("eyeline", sa.String(length=160), nullable=True))
    op.add_column("shots", sa.Column("foreground_action", sa.Text(), nullable=True))
    op.add_column("shots", sa.Column("midground_action", sa.Text(), nullable=True))
    op.add_column("shots", sa.Column("background_action", sa.Text(), nullable=True))
    op.add_column("shots", sa.Column("focus_depth_intent", sa.Text(), nullable=True))
    op.add_column("shots", sa.Column("lighting_spec", JSONB, nullable=True))
    op.add_column(
        "shots", sa.Column("garment_visibility_class", sa.String(length=32), nullable=True)
    )
    op.add_column("shots", sa.Column("garment_side_visible", sa.String(length=32), nullable=True))
    op.add_column("shots", sa.Column("garment_scale_in_frame", sa.String(length=64), nullable=True))
    op.add_column("shots", sa.Column("artwork_legibility_required", sa.Boolean(), nullable=True))
    op.add_column("shots", sa.Column("prop_continuity", JSONB, nullable=True))
    op.add_column("shots", sa.Column("first_frame_requirement", JSONB, nullable=True))
    op.add_column("shots", sa.Column("last_frame_requirement", JSONB, nullable=True))
    op.add_column("shots", sa.Column("intended_edit_in", sa.Text(), nullable=True))
    op.add_column("shots", sa.Column("intended_edit_out", sa.Text(), nullable=True))
    op.add_column("shots", sa.Column("still_extraction_potential", sa.Boolean(), nullable=True))
    op.add_column("shots", sa.Column("negative_constraints", sa.Text(), nullable=True))
    op.add_column("shots", sa.Column("locked_reference_manifest", JSONB, nullable=True))

    op.create_foreign_key(
        "fk_shots_campaign_id_campaigns",
        "shots",
        "campaigns",
        ["campaign_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_shots_scene_same_campaign",
        "shots",
        "scenes",
        ["scene_id", "campaign_id"],
        ["id", "campaign_id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint("uq_shots_id_campaign_id", "shots", ["id", "campaign_id"])
    op.create_check_constraint(
        "shot_source_valid",
        "shots",
        "source IN ('markdown_import','campaign_native')",
    )
    op.create_check_constraint(
        "shot_media_intent_valid",
        "shots",
        "media_intent IN ('still','video','either')",
    )
    op.create_check_constraint(
        "campaign_shot_requires_campaign",
        "shots",
        "source <> 'campaign_native' OR campaign_id IS NOT NULL",
    )
    op.create_check_constraint(
        "markdown_shot_has_no_campaign_scene",
        "shots",
        "source <> 'markdown_import' OR (campaign_id IS NULL AND scene_id IS NULL)",
    )
    op.create_check_constraint(
        "shot_scene_requires_campaign",
        "shots",
        "scene_id IS NULL OR campaign_id IS NOT NULL",
    )
    op.create_check_constraint(
        "shot_duration_nonnegative",
        "shots",
        "intended_duration_ms IS NULL OR intended_duration_ms >= 0",
    )
    op.create_index("ix_shots_campaign_id_sequence", "shots", ["campaign_id", "sequence"])
    op.create_index("ix_shots_scene_id_sequence", "shots", ["scene_id", "sequence"])

    op.create_table(
        "shot_characters",
        sa.Column("shot_id", UUID, nullable=False),
        sa.Column("campaign_id", UUID, nullable=False),
        sa.Column("character_id", UUID, nullable=False),
        sa.Column("appearance_id", UUID, nullable=True),
        sa.Column("prominence", sa.String(length=64), nullable=True),
        sa.Column("expected_position", JSONB, nullable=True),
        sa.Column("action", sa.Text(), nullable=True),
        sa.Column("eyeline", sa.String(length=160), nullable=True),
        sa.Column("continuity_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["shot_id", "campaign_id"],
            ["shots.id", "shots.campaign_id"],
            name="fk_shot_characters_shot_same_campaign",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["character_id", "campaign_id"],
            ["characters.id", "characters.campaign_id"],
            name="fk_shot_characters_character_same_campaign",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["appearance_id", "character_id"],
            ["character_appearances.id", "character_appearances.character_id"],
            name="fk_shot_characters_appearance_same_character",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("shot_id", "character_id", name="pk_shot_characters"),
    )


def downgrade() -> None:
    op.drop_table("shot_characters")

    op.drop_index("ix_shots_scene_id_sequence", table_name="shots")
    op.drop_index("ix_shots_campaign_id_sequence", table_name="shots")
    op.drop_constraint("shot_duration_nonnegative", "shots", type_="check")
    op.drop_constraint("shot_scene_requires_campaign", "shots", type_="check")
    op.drop_constraint("markdown_shot_has_no_campaign_scene", "shots", type_="check")
    op.drop_constraint("campaign_shot_requires_campaign", "shots", type_="check")
    op.drop_constraint("shot_media_intent_valid", "shots", type_="check")
    op.drop_constraint("shot_source_valid", "shots", type_="check")
    op.drop_constraint("uq_shots_id_campaign_id", "shots", type_="unique")
    op.drop_constraint("fk_shots_scene_same_campaign", "shots", type_="foreignkey")
    op.drop_constraint("fk_shots_campaign_id_campaigns", "shots", type_="foreignkey")

    for column in (
        "locked_reference_manifest",
        "negative_constraints",
        "still_extraction_potential",
        "intended_edit_out",
        "intended_edit_in",
        "last_frame_requirement",
        "first_frame_requirement",
        "prop_continuity",
        "artwork_legibility_required",
        "garment_scale_in_frame",
        "garment_side_visible",
        "garment_visibility_class",
        "lighting_spec",
        "focus_depth_intent",
        "background_action",
        "midground_action",
        "foreground_action",
        "eyeline",
        "blocking_json",
        "camera_movement",
        "focal_length_intent",
        "camera_angle",
        "camera_height",
        "shot_size",
        "safe_crop",
        "target_aspect",
        "intended_duration_ms",
        "media_intent",
        "scene_id",
        "campaign_id",
        "source",
    ):
        op.drop_column("shots", column)

    op.drop_table("scene_characters")
    op.drop_index("ix_scenes_campaign_id_state", table_name="scenes")
    op.drop_table("scenes")
    op.drop_table("locations")
    op.drop_table("character_appearances")
    op.drop_table("characters")
    op.drop_index("uq_story_versions_one_approved_per_campaign", table_name="story_versions")
    op.drop_index("ix_story_versions_campaign_id_state", table_name="story_versions")
    op.drop_constraint(
        "fk_story_versions_parent_same_campaign", "story_versions", type_="foreignkey"
    )
    op.drop_table("story_versions")
    op.drop_index("ix_campaigns_world_id_status", table_name="campaigns")
    op.drop_table("campaigns")
