"""Flip a tested render to dropped, with the reason it failed review.

Usage::

    python scripts/mark_generation_dropped.py <sample-id> "<reason>"

The counterpart to ``eval_concept_batch.py``, which always inserts rows as
``status="kept"``. Reviewing a batch's renders and deciding which ones failed
is a judgment call the eval script does not make -- this is the tool that
records the call once it's made.
"""

from __future__ import annotations

import sys
import uuid

from app.db.generation_sample_models import DesignGenerationSample
from app.db.session import get_session_factory


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(1)

    sample_id = uuid.UUID(sys.argv[1])
    reason = sys.argv[2]

    session = get_session_factory()()
    row = session.get(DesignGenerationSample, sample_id)
    if row is None:
        print(f"No sample with id {sample_id}")
        raise SystemExit(1)

    row.status = "dropped"
    row.drop_reason = reason
    session.commit()
    print(f"Marked {sample_id} ({row.tradition}) dropped: {reason}")


if __name__ == "__main__":
    main()
