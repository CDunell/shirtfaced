"""Copy a batch's still-"kept" generation samples into the live concept pool.

Usage::

    python scripts/promote_kept_to_pool.py <batch-label>

``eval_concept_batch.py`` writes every render to ``design_generation_samples``
as ``status="kept"`` by default, before anyone has looked at a single image --
it has to, because nothing has been reviewed yet. Reviewing the renders and
calling ``mark_generation_dropped.py`` on the real failures happens next.
Only after that should the survivors reach ``design_concept_pool``, the table
``/api/design/random`` actually serves from -- this is that promotion step,
kept separate on purpose so nothing serves live before a human (or Claude)
has looked at the picture it produces.

Idempotent: samples already promoted (tracked via concept_pool_id) are
skipped, so this can be re-run safely after promoting some and dropping more.
"""

from __future__ import annotations

import sys
import uuid

from sqlalchemy import select

from app.db.concept_pool_models import DesignConceptPoolEntry
from app.db.generation_sample_models import DesignGenerationSample
from app.db.session import get_session_factory


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(1)

    batch_label = sys.argv[1]
    session = get_session_factory()()

    samples = session.execute(
        select(DesignGenerationSample).where(
            DesignGenerationSample.batch == batch_label,
            DesignGenerationSample.status == "kept",
            DesignGenerationSample.concept_pool_id.is_(None),
        )
    ).scalars().all()

    if not samples:
        print(f"Nothing to promote for {batch_label!r} -- already promoted, or nothing kept.")
        return

    for sample in samples:
        entry = DesignConceptPoolEntry(
            tradition=sample.tradition,
            concept_text=sample.concept_text,
            batch=batch_label,
        )
        session.add(entry)
        session.flush()  # assign entry.id before the sample references it
        sample.concept_pool_id = entry.id

    session.commit()
    print(f"Promoted {len(samples)} kept samples from {batch_label!r} into design_concept_pool.")


if __name__ == "__main__":
    main()
