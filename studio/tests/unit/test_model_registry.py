"""Every foreign key must resolve for a caller who imports only a session.

A mapped class registers itself with ``Base.metadata`` when its module is
imported. Import some and not others and the metadata is half a schema, so a
foreign key across the gap resolves to nothing -- and it fails at flush, in
production, on whichever path happens to touch that table.

``world_importer`` imported ``Shot`` alone; ``shots.campaign_id`` references
``campaigns`` in another module. It raised ``NoReferencedTableError`` on the
first deploy that actually delivered a changed SHOTLIST.md, having been latent
for as long as the importer existed.

**The check runs in a subprocess, and that is the whole point.** Inside pytest
the conftest has already imported most of the application, so every table is
registered by something and the assertion passes whether or not the fix is
present -- which is exactly what happened when this test was first written. A
CLI has a much narrower import graph than a test session, and the narrow graph
is where the bug lived. So the subprocess imports what a caller imports, and
nothing else.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.config import PROJECT_ROOT

# What app/cli.py's narrowest path does: open a session, use one mapped class.
CALLER = """
import sys
sys.path.insert(0, %r)
import app.db.session  # the one import a caller needs
from app.db.base import Base
from sqlalchemy.exc import NoReferencedTableError

broken = []
for table in Base.metadata.tables.values():
    for key in table.foreign_keys:
        try:
            key.column
        except NoReferencedTableError:
            broken.append(table.name + "." + key.parent.name)
print("TABLES=" + str(len(Base.metadata.tables)))
print("BROKEN=" + ",".join(sorted(broken)))
"""


def test_a_session_alone_gives_a_schema_whose_keys_all_resolve() -> None:
    result = subprocess.run(
        [sys.executable, "-c", CALLER % str(PROJECT_ROOT)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(PROJECT_ROOT),
        check=False,
    )

    assert result.returncode == 0, result.stderr[-2000:]

    # Counted before the keys are checked, because an empty schema has no keys
    # to break. Without the registry import a bare session registers zero
    # tables, and an earlier version of this test passed happily on that.
    tables = int(result.stdout.split("TABLES=")[1].split()[0])
    assert tables > 40, f"a session alone registered {tables} tables; the registry is not wired"

    broken = result.stdout.split("BROKEN=")[1].strip()
    assert not broken, "unresolved foreign keys for a caller importing only a session: " + broken


def test_the_registry_lists_every_model_module() -> None:
    """A new model file has to join the list, not wait to be missed."""
    from app.db import registry

    directory = Path(registry.__file__).parent
    on_disk = {
        path.stem
        for path in directory.glob("*.py")
        if path.stem.endswith("_models") or path.stem == "models"
    }

    assert on_disk == set(registry.MODEL_MODULES)
