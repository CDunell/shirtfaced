"""Use descriptive stable names for the approved W01-P28 shot masters.

Revision ID: 0047
Revises: 0046
"""

from alembic import op

revision = "0047"
down_revision = "0046"
branch_labels = None
depends_on = None

RENAMES = {
    "a": "trio-wide",
    "b": "damo-emma",
    "d": "trio-together",
    "f": "band-room",
    "h": "trio-chorus",
}


def _rename(old: str, new: str) -> None:
    op.execute(
        f"""
        UPDATE scene_shot_masters
        SET name = '{new}'
        WHERE scene_key = 'W01-P28'
          AND name = '{old}'
          AND NOT EXISTS (
              SELECT 1 FROM scene_shot_masters
              WHERE scene_key = 'W01-P28' AND name = '{new}'
          )
        """
    )


def _refresh_asset_metadata() -> None:
    op.execute(
        """
        UPDATE visual_assets AS asset
        SET role = shot.name,
            description = 'W01-P28 direct 9:16 shot master — ' || shot.name,
            metadata_json = jsonb_set(
                COALESCE(asset.metadata_json, '{}'::jsonb),
                '{shot_master}',
                to_jsonb(shot.name),
                true
            )
        FROM scene_shot_masters AS shot
        WHERE shot.scene_key = 'W01-P28'
          AND shot.visual_asset_id = asset.id
          AND shot.name IN ('trio-wide','damo-emma','trio-together','band-room','trio-chorus')
        """
    )


def upgrade() -> None:
    for old, new in RENAMES.items():
        _rename(old, new)
    _refresh_asset_metadata()


def downgrade() -> None:
    for old, new in reversed(tuple(RENAMES.items())):
        _rename(new, old)
    op.execute(
        """
        UPDATE visual_assets AS asset
        SET role = shot.name,
            description = 'W01-P28 direct 9:16 shot master — ' || shot.name,
            metadata_json = jsonb_set(
                COALESCE(asset.metadata_json, '{}'::jsonb),
                '{shot_master}',
                to_jsonb(shot.name),
                true
            )
        FROM scene_shot_masters AS shot
        WHERE shot.scene_key = 'W01-P28'
          AND shot.visual_asset_id = asset.id
          AND shot.name IN ('a','b','d','f','h')
        """
    )
