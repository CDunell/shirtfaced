"""One-off: put generation samples back to "pending" for real review.

Usage::

    python scripts/reset_generations_to_pending.py [--batch <label>]

Every row currently sitting at "kept" got there from the old
``eval_concept_batch.py``, which inserted every render as kept by default --
nobody ever actually decided on them. This is the one-time fix: move them
back to "pending" so Gallery's review queue (POST
/api/design/generations/{id}/decision) has something real to decide on,
instead of a queue that looks empty because everything was pre-approved by
a bug.

Only touches "kept" rows -- anything already "dropped" was a real decision
(via mark_generation_dropped.py, back when that existed) and stays dropped.
Pass --batch to scope it to one batch label instead of every kept row.
"""

from __future__ import annotations

import sys

from sqlalchemy import select

from app.db.generation_sample_models import DesignGenerationSample
from app.db.session import get_session_factory


def main() -> None:
    batch = None
    if len(sys.argv) == 3 and sys.argv[1] == "--batch":
        batch = sys.argv[2]
    elif len(sys.argv) != 1:
        print(__doc__)
        raise SystemExit(1)

    session = get_session_factory()()

    query = select(DesignGenerationSample).where(DesignGenerationSample.status == "kept")
    if batch:
        query = query.where(DesignGenerationSample.batch == batch)

    rows = session.execute(query).scalars().all()
    for row in rows:
        row.status = "pending"
    session.commit()

    scope = f"batch {batch!r}" if batch else "every batch"
    print(f"Moved {len(rows)} sample(s) from kept to pending, across {scope}.")


if __name__ == "__main__":
    main()
