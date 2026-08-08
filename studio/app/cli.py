"""Command line entry points.

Importing a world is a deliberate operator action, not something that happens on
application startup, so it lives here rather than in a request handler.

    python -m app.cli list-worlds
    python -m app.cli validate-world world-01
    python -m app.cli import-world world-01
    python -m app.cli attempts world-01
    python -m app.cli discard-attempt <id>
    python -m app.cli prompt world-01 [--shot W01-015] [--out prompt.txt]
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from sqlalchemy import select

from app.adapters.markdown_store import MarkdownStore
from app.config import get_settings
from app.db.models import GenerationAttempt, World
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


def _sync_archive() -> int:
    """Bring the stored archive in line with the authored elements.

    Idempotent, and it says what it changed. A sync that reports work it did not
    do makes the report worthless, which is the only reason anyone runs it.
    """
    from app.archive import authored
    from app.archive.repository import ElementRepository

    session_factory = get_session_factory()
    with session_factory() as session:
        repository = ElementRepository(session)
        result = repository.sync(authored.ALL)
        audit = repository.licence_audit()
        unverified = repository.unverified()
        session.commit()

    print(
        f"{result.total} authored element(s): "
        f"{len(result.added)} added, {len(result.updated)} updated, "
        f"{len(result.unchanged)} unchanged"
    )
    print(
        "  licences: "
        + ", ".join(f"{status} {count}" for status, count in sorted(audit.items()) if count)
    )
    # Named rather than counted. An element held but unusable is work already
    # done that nobody can reach, and it should be visible on every run rather
    # than waiting for someone to think of querying for it.
    standing_in = [element for element in authored.ALL if element.provisional]
    if standing_in:
        print(f"  {len(standing_in)} element(s) standing in for better artwork:")
        for element in standing_in:
            print(f"    {element.id}: {element.provisional.strip()}")
    for key, source, status in unverified:
        print(f"  {status}: {key} (from {source or 'no source recorded'})")
    return EXIT_OK


def _list_attempts(slug: str) -> int:

    with get_session_factory()() as session:
        world = session.execute(select(World).where(World.slug == slug)).scalar_one_or_none()
        if world is None:
            print(f"error: {slug!r} has not been imported.", file=sys.stderr)
            return EXIT_FAILED

        attempts = (
            session.execute(
                select(GenerationAttempt)
                .where(GenerationAttempt.world_id == world.id)
                .order_by(GenerationAttempt.created_at.desc())
            )
            .scalars()
            .all()
        )

        if not attempts:
            print("No attempts.")
            return EXIT_OK

        for attempt in attempts:
            active = " (active)" if attempt.is_active else ""
            print(f"{attempt.id}  {attempt.state.value:<18}{active}")
            print(f"    shot {attempt.shot.external_id} attempt {attempt.attempt_number}")
            if attempt.failure_message:
                print(f"    failure: {attempt.failure_code} — {attempt.failure_message[:120]}")
    return EXIT_OK


def _write_prompt(
    slug: str, external_id: str | None, destination: str | None, video: bool = False
) -> int:
    """Write one prompt and stop. No image, no attempt, no lock."""
    from app.services.prompt_service import NothingToPlan, prompts_for_shot

    settings = get_settings()
    try:
        with get_session_factory()() as session:
            prompts = prompts_for_shot(
                session,
                settings=settings,
                store=_store(),
                world_slug=slug,
                external_id=external_id,
            )
            shot_id, title = prompts.shot.external_id, prompts.shot.title
            hero, camera = prompts.shot.hero_product, prompts.shot.camera_position
            text = prompts.video_prompt if video else prompts.image_prompt
            live = prompts.live
    except NothingToPlan as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_FAILED

    if not live:
        print("(written by the deterministic fake: no key or text model set)", file=sys.stderr)
    print(f"# {shot_id} — {title}", file=sys.stderr)
    print(f"# hero: {hero}   camera: {camera}", file=sys.stderr)
    print(file=sys.stderr)

    if destination:
        Path(destination).write_text(text + "\n", encoding="utf-8")
        print(f"Written to {destination}", file=sys.stderr)
    else:
        print(text)
    return EXIT_OK


def _discard_attempt(attempt_id: str) -> int:
    """Release a world blocked by an attempt awaiting a decision.

    Operator tooling, not a creative decision. Approving and rejecting arrive with
    human decisions in a later phase; until then a generated attempt occupies its
    world indefinitely, and this is the way out.
    """
    import uuid as uuid_module

    from app.domain.enums import AttemptState

    try:
        parsed = uuid_module.UUID(attempt_id)
    except ValueError:
        print(f"error: {attempt_id!r} is not an attempt identifier.", file=sys.stderr)
        return EXIT_FAILED

    with get_session_factory()() as session:
        attempt = session.get(GenerationAttempt, parsed)
        if attempt is None:
            print(f"error: no attempt {attempt_id}.", file=sys.stderr)
            return EXIT_FAILED
        if not attempt.is_active:
            print(f"Attempt {attempt_id} is already {attempt.state.value}; nothing to do.")
            return EXIT_OK

        attempt.state = AttemptState.FAILED
        attempt.failure_code = None
        attempt.failure_message = "Discarded by the operator."
        session.commit()

    print(f"Discarded {attempt_id}. The world is free to generate again.")
    print("The image and its record are kept.")
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

    attempts = subcommands.add_parser("attempts", help="List generation attempts for a world")
    attempts.add_argument("slug")

    discard = subcommands.add_parser(
        "discard-attempt",
        help="Release a world blocked by an active attempt. Keeps the image and record.",
    )
    discard.add_argument("attempt_id")

    prompt = subcommands.add_parser(
        "prompt",
        help="Write one production prompt and stop. No image, no attempt, no lock.",
    )
    prompt.add_argument("slug")
    prompt.add_argument("--shot", help="Shot to plan, such as W01-015. Defaults to the next one.")
    prompt.add_argument("--out", help="Write to this file instead of standard output.")
    prompt.add_argument(
        "--video",
        action="store_true",
        help="Write the image-to-video prompt instead. Upload the frame separately.",
    )

    subcommands.add_parser(
        "sync-archive",
        help="Store the authored archive elements and their feature vectors",
    )

    arguments = parser.parse_args(argv)

    try:
        if arguments.command == "list-worlds":
            return _list_worlds()
        if arguments.command == "validate-world":
            return _validate_world(arguments.slug)
        if arguments.command == "import-world":
            return _import_world(arguments.slug)
        if arguments.command == "sync-archive":
            return _sync_archive()
        if arguments.command == "prompt":
            return _write_prompt(arguments.slug, arguments.shot, arguments.out, arguments.video)
        if arguments.command == "attempts":
            return _list_attempts(arguments.slug)
        if arguments.command == "discard-attempt":
            return _discard_attempt(arguments.attempt_id)
    except WorldValidationError as error:
        print(str(error), file=sys.stderr)
        return EXIT_FAILED
    except StudioError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_FAILED

    parser.error(f"Unknown command {arguments.command!r}")


if __name__ == "__main__":  # pragma: no cover - process entry point
    raise SystemExit(main())
