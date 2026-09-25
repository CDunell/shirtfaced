"""Get an evidence-informed generation prompt for one concept.

Usage::

    python scripts/render_prompt_for.py <tradition> <concept text...>

Thin wrapper around ``advise()`` + ``render_generation_prompt()`` -- the
same path Prompt, Designs' brief step and every batch run already use.
Exists so a batch run reaches for one command instead of a hand-typed
python -c snippet each time.
"""

from __future__ import annotations

import sys

from app.db.session import get_session_factory
from app.services.design_advisor import advise, measurement_rows, render_generation_prompt


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(1)

    tradition = sys.argv[1]
    concept_text = " ".join(sys.argv[2:])

    session = get_session_factory()()
    rows = measurement_rows(session)
    direction = advise(phrase="", has_graphic=True, tradition=tradition, rows=rows)
    print(render_generation_prompt(direction, concept_text))


if __name__ == "__main__":
    main()
