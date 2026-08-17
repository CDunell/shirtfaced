"""the scene is W01-P28, which is what its own canon calls it

Revision ID: 0039
Revises: 0038
Create Date: 2026-08-18

The pub scene has been carrying two names. ``studio/worlds/world-01/shots/
W01-P28.md`` opens "SHOT SPECIFICATION — W01-P28" and states "Scene: W01-P28,
STORY_ARC.md scene 4"; SHOTLIST.md numbers every shot W01-NNN. Meanwhile the
library keyed it ``pub-1105``, which was never an identifier anybody chose — it
is the name of the directory the old scene references happened to sit in,
``var/scene-references/pub-1105``.

Two names cost something real: the coverage prompt is filed under the shot id
and the scene key matched nothing, so the interface had to ask which prompt to
use for a scene that already had exactly one.

So the world's own identifier wins, and this renames the data to match it. The
directory keeps its name -- it is a compatibility mirror, and renaming files on
the host is a separate operation from agreeing what the scene is called.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0039"
down_revision: str | None = "0038"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD = "pub-1105"
NEW = "W01-P28"


def _rename(old: str, new: str) -> None:
    op.execute(
        sa.text("UPDATE scene_masters SET scene_key = :new WHERE scene_key = :old").bindparams(
            new=new, old=old
        )
    )
    op.execute(
        sa.text("UPDATE generation_calls SET scene_key = :new WHERE scene_key = :old").bindparams(
            new=new, old=old
        )
    )
    # A master is ingested with the scene key as its role, so that moves too.
    op.execute(
        sa.text(
            "UPDATE visual_assets SET role = :new WHERE role = :old AND kind = 'scene_master'"
        ).bindparams(new=new, old=old)
    )
    # And the scene name recorded on coverage and sheet metadata.
    op.execute(
        sa.text(
            "UPDATE visual_assets SET metadata_json = jsonb_set(metadata_json, '{scene}', "
            "to_jsonb(cast(:new AS text))) WHERE metadata_json->>'scene' = :old"
        ).bindparams(new=new, old=old)
    )


def upgrade() -> None:
    _rename(OLD, NEW)


def downgrade() -> None:
    _rename(NEW, OLD)
