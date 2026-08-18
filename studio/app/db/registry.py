"""Every model module, imported for the side effect of registering its tables.

A mapped class attaches itself to ``Base.metadata`` when its module is imported
and not before. Import half of them and the metadata is half a schema: SQLAlchemy
resolves a foreign key by looking the target table up in that metadata, so a
cross-module key points at nothing.

That is not theoretical. ``world_importer`` imported ``Shot`` from ``models`` and
nothing else, and ``shots.campaign_id`` references ``campaigns`` in
``campaign_models``. Flushing an imported world raised

    NoReferencedTableError: Foreign key associated with column
    'shots.campaign_id' could not find table 'campaigns'

and it had been latent for as long as the importer existed, because the deploy's
worlds rsync ran ``--ignore-existing`` and never delivered a changed SHOTLIST.md,
so the shot-import path had nothing to do and never ran. Two bugs holding each
other up: fixing the rsync is what made this one visible.

Alembic already kept a list like this in ``migrations/env.py``. Application code
had no equivalent, which is why the gap existed at all. ``session`` imports this
module, so anything holding a session has the whole schema.
"""

from __future__ import annotations

from app.db import (  # noqa: F401
    archive_models,
    audio_models,
    campaign_models,
    concept_models,
    email_models,
    models,
    observation_models,
    social_models,
    visual_models,
)

__all__ = ["MODEL_MODULES"]

# Named so a test can assert the list is complete rather than trusting that
# somebody remembered to add the next one.
MODEL_MODULES = (
    "archive_models",
    "audio_models",
    "campaign_models",
    "concept_models",
    "email_models",
    "models",
    "observation_models",
    "social_models",
    "visual_models",
)
