"""Metadata-level contract tests for the campaign production foundation.

These are intentionally database-free. Integration coverage still has to exercise
migration 0028 against PostgreSQL before merge, but these tests catch drift between
the ORM metadata and the hand-written migration while the schema is being built.
"""

from __future__ import annotations

from sqlalchemy import ForeignKeyConstraint, Index

from app.db import campaign_models  # noqa: F401 -- registers tables in Base.metadata
from app.db.base import Base
from app.db.campaign_models import CharacterAppearance, Scene, StoryVersion
from app.db.models import Shot


def _foreign_key_pairs(table_name: str) -> set[tuple[tuple[str, ...], tuple[str, ...]]]:
    table = Base.metadata.tables[table_name]
    pairs: set[tuple[tuple[str, ...], tuple[str, ...]]] = set()
    for constraint in table.constraints:
        if not isinstance(constraint, ForeignKeyConstraint):
            continue
        local = tuple(element.parent.name for element in constraint.elements)
        remote = tuple(element.target_fullname for element in constraint.elements)
        pairs.add((local, remote))
    return pairs


def test_campaign_domain_tables_are_registered() -> None:
    assert {
        "campaigns",
        "story_versions",
        "characters",
        "character_appearances",
        "locations",
        "scenes",
        "scene_characters",
        "shot_characters",
    } <= set(Base.metadata.tables)


def test_shot_is_one_dual_provenance_mapper() -> None:
    columns = Shot.__table__.c

    assert columns.source.server_default is not None
    assert str(columns.source.server_default.arg) == "markdown_import"
    assert columns.media_intent.server_default is not None
    assert str(columns.media_intent.server_default.arg) == "still"
    assert columns.campaign_id.nullable
    assert columns.scene_id.nullable
    assert "intended_duration_ms" in columns
    assert "camera_movement" in columns
    assert "locked_reference_manifest" in columns


def test_shot_scene_fk_proves_same_campaign() -> None:
    pairs = _foreign_key_pairs("shots")
    assert (
        ("scene_id", "campaign_id"),
        ("scenes.id", "scenes.campaign_id"),
    ) in pairs


def test_scene_story_and_location_fks_prove_same_campaign() -> None:
    pairs = _foreign_key_pairs("scenes")
    assert (
        ("story_version_id", "campaign_id"),
        ("story_versions.id", "story_versions.campaign_id"),
    ) in pairs
    assert (
        ("location_id", "campaign_id"),
        ("locations.id", "locations.campaign_id"),
    ) in pairs


def test_character_appearance_cannot_cross_campaign() -> None:
    pairs = _foreign_key_pairs("character_appearances")
    assert (
        ("character_id", "campaign_id"),
        ("characters.id", "characters.campaign_id"),
    ) in pairs
    assert CharacterAppearance.__table__.c.campaign_id.nullable is False


def test_scene_character_and_shot_character_preserve_character_identity() -> None:
    scene_pairs = _foreign_key_pairs("scene_characters")
    shot_pairs = _foreign_key_pairs("shot_characters")

    assert (
        ("appearance_id", "character_id"),
        ("character_appearances.id", "character_appearances.character_id"),
    ) in scene_pairs
    assert (
        ("appearance_id", "character_id"),
        ("character_appearances.id", "character_appearances.character_id"),
    ) in shot_pairs


def test_only_one_story_version_can_be_active_approved() -> None:
    indexes = {
        index.name: index
        for index in StoryVersion.__table__.indexes
        if isinstance(index, Index)
    }
    approved = indexes["uq_story_versions_one_approved_per_campaign"]

    assert approved.unique is True
    where = str(approved.dialect_options["postgresql"]["where"])
    assert "state = 'approved'" in where


def test_scene_sequence_is_campaign_scoped() -> None:
    names = {constraint.name for constraint in Scene.__table__.constraints}
    assert "uq_scenes_campaign_id_sequence" in names
