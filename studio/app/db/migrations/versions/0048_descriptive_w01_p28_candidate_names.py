"""Use descriptive names for the remaining W01-P28 candidate masters.

Revision ID: 0048
Revises: 0047
"""

from alembic import op

revision = "0048"
down_revision = "0047"
branch_labels = None
depends_on = None

RENAMES = {
    "0": "trio-close-alt",
    "1": "damo-emma-alt",
    "c": "brock-pint",
    "e": "emma-laugh",
    "g": "damo-brock",
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


def _refresh_asset_metadata(names: tuple[str, ...]) -> None:
    values = ",".join(f"'{name}'" for name in names)
    op.execute(
        f"""
        UPDATE visual_assets AS asset
        SET role = shot.name,
            description = 'W01-P28 direct 9:16 shot master — ' || shot.name,
            metadata_json = jsonb_set(
                COALESCE(asset.metadata_json, '{{}}'::jsonb),
                '{{shot_master}}',
                to_jsonb(shot.name),
                true
            )
        FROM scene_shot_masters AS shot
        WHERE shot.scene_key = 'W01-P28'
          AND shot.visual_asset_id = asset.id
          AND shot.name IN ({values})
        """
    )


def upgrade() -> None:
    for old, new in RENAMES.items():
        _rename(old, new)
    _refresh_asset_metadata(tuple(RENAMES.values()))


def downgrade() -> None:
    for old, new in reversed(tuple(RENAMES.items())):
        _rename(new, old)
    _refresh_asset_metadata(tuple(RENAMES.keys()))
