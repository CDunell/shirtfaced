"""visual assets are owner-created, so rights default to verified

Revision ID: 0035
Revises: 0034
Create Date: 2026-08-17

0031 gave ``visual_assets.rights_status`` a default of ``unverified``, copied
from the element archive where that default is correct. It is not correct here.

Owner's ruling, 17 August 2026: everything in this library is invented here.
The worlds, the cast, the locations, the scene masters and the coverage are all
generated, there are no photographs of real people, and there is no third party
with a claim. Treating that as an open question made the location gate refuse
the owner's own plates and asked a question that has one answer.

So the default becomes ``verified`` and the existing rows are backfilled. The
column stays: a licence is a fact worth recording, ``refused`` still means
something if material ever does come in from outside, and §6.4's gate still
reads it — it simply passes for everything the owner makes, which is everything.

``app/archive/`` is untouched. That library holds found third-party design
elements whose terms genuinely are unknown until a person reads them, and its
default of ``unverified`` is the whole point of it. Same enum, different
question, and the two are not being merged.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0035"
down_revision: str | None = "0034"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("visual_assets", "rights_status", server_default="verified")

    # Everything held so far is owner-generated: the cast frames, the scene
    # master candidate and the coverage. Nothing came from outside, so nothing
    # is being asserted here that was not already true.
    op.execute(
        sa.text(
            "UPDATE visual_assets SET rights_status = 'verified' WHERE rights_status = 'unverified'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE visual_assets "
            "SET rights_metadata = rights_metadata || "
            '\'{"owner": "Shirtfaced", "origin": "owner-generated"}\'::jsonb '
            "WHERE rights_metadata = '{}'::jsonb"
        )
    )


def downgrade() -> None:
    # The rows keep their verified status: it is a true statement about where
    # the images came from, and a downgrade of the schema does not make the
    # owner stop having invented them.
    op.alter_column("visual_assets", "rights_status", server_default="unverified")
