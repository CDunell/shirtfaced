"""Command line entry points.

Importing a world is a deliberate operator action, not something that happens on
application startup, so it lives here rather than in a request handler.

    python -m app.cli list-worlds
    python -m app.cli validate-world world-01
    python -m app.cli import-world world-01
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from app.adapters.markdown_store import MarkdownStore
from app.config import get_settings
from app.db.session import get_session_factory
from app.domain.errors import StudioError, WorldValidationError
from app.services.world_importer import import_world
from app.services.world_loader import load_world

EXIT_OK = 0
EXIT_FAILED = 1


def _use_utf8_output() -> None:
    """Print status markers and em-dashes rather than escape sequences.

    The Windows console defaults to a legacy code page, which renders ⬜ ✅ ❌ as
    ``\\u2b1c`` and turns an em-dash into a replacement character. Those markers are
    exactly what a validation message needs to show.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")


def _store() -> MarkdownStore:
    return MarkdownStore(get_settings().worlds_root_resolved)


def _list_worlds() -> int:
    store = _store()
    slugs = store.available_slugs()
    if not slugs:
        print(f"No worlds found in {store.root}.")
        return EXIT_OK
    for slug in slugs:
        print(slug)
    return EXIT_OK


def _validate_world(slug: str) -> int:
    loaded = load_world(_store(), slug)
    print(f"{loaded.slug} — {loaded.name}")
    print(f"  shots: {len(loaded.shots)} ({len(loaded.planned_shots)} planned)")
    print(f"  WORLD.md      {loaded.world_document.sha256}")
    print(f"  CONTINUITY.md {loaded.continuity_document.sha256}")
    print(f"  SHOTLIST.md   {loaded.shotlist_document.sha256}")
    return EXIT_OK


def _import_world(slug: str) -> int:
    session_factory = get_session_factory()
    with session_factory() as session:
        report = import_world(session, _store(), slug)
        session.commit()

    print(report.summary())
    for conflict in report.status_conflicts:
        print(f"  conflict: {conflict}")
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    _use_utf8_output()

    parser = argparse.ArgumentParser(prog="app.cli", description="Shirtfaced Studio operations")
    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser("list-worlds", help="List world directories that can be loaded")

    validate = subcommands.add_parser("validate-world", help="Validate a world without importing")
    validate.add_argument("slug")

    importer = subcommands.add_parser("import-world", help="Import a world into PostgreSQL")
    importer.add_argument("slug")

    arguments = parser.parse_args(argv)

    try:
        if arguments.command == "list-worlds":
            return _list_worlds()
        if arguments.command == "validate-world":
            return _validate_world(arguments.slug)
        if arguments.command == "import-world":
            return _import_world(arguments.slug)
    except WorldValidationError as error:
        print(str(error), file=sys.stderr)
        return EXIT_FAILED
    except StudioError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_FAILED

    parser.error(f"Unknown command {arguments.command!r}")


if __name__ == "__main__":  # pragma: no cover - process entry point
    raise SystemExit(main())
