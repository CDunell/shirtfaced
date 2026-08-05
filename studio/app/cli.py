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


def _list_attempts(slug: str) -> int:
    from sqlalchemy import select

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


def _write_prompt(slug: str, external_id: str | None, destination: str | None) -> int:
    """Produce one production prompt and stop.

    No image is generated, no attempt is recorded and the world is not locked. This
    is for taking a prompt somewhere else to run: the application's job here is to
    assemble the canon correctly and write the prompt the canon implies.
    """
    from app.adapters.factory import build_planning_client, planning_client_is_live
    from app.adapters.markdown_store import WORLD_DOCUMENT
    from app.services.prompt_planner import build_request, create_plan
    from app.services.rotation import RotationState, apply_continuity, rotation_from_shots
    from app.services.shot_selector import NoSelection, select_next_shot

    settings = get_settings()
    store = _store()

    with get_session_factory()() as session:
        world = session.execute(select(World).where(World.slug == slug)).scalar_one_or_none()
        if world is None:
            print(f"error: no world named {slug!r} has been imported.", file=sys.stderr)
            return EXIT_FAILED

        shots = sorted(world.shots, key=lambda item: item.sequence)
        rotation: RotationState
        if external_id:
            found = next((item for item in shots if item.external_id == external_id), None)
            if found is None:
                print(f"error: {slug} has no shot {external_id!r}.", file=sys.stderr)
                return EXIT_FAILED
            # Asked for by name, so the selector's eligibility rules do not apply. The
            # rotation state still comes from what has been approved.
            shot, reason, rotation = found, f"{external_id} requested.", rotation_from_shots(shots)
        else:
            outcome = select_next_shot(world, shots)
            if isinstance(outcome, NoSelection):
                print(f"Nothing to plan: {outcome.reason}")
                return EXIT_FAILED
            shot, reason, rotation = outcome.shot, outcome.reason, outcome.rotation

        documents = store.read_world_documents(slug)
        request = build_request(
            world_slug=slug,
            world_name=world.name,
            shot=shot,
            world_text=documents[WORLD_DOCUMENT].text,
            rotation=apply_continuity(rotation, documents["CONTINUITY.md"].text),
            selection_reason=reason,
        )
        plan = create_plan(build_planning_client(settings), request).plan

    if not planning_client_is_live(settings):
        print("(the deterministic fake wrote this: OPENAI_API_KEY and", file=sys.stderr)
        print(" OPENAI_TEXT_MODEL are not both set, so nothing was billed)", file=sys.stderr)

    print(f"# {shot.external_id} — {shot.title}", file=sys.stderr)
    print(f"# hero: {shot.hero_product}   camera: {shot.camera_position}", file=sys.stderr)
    print(file=sys.stderr)

    if destination:
        Path(destination).write_text(plan.production_prompt + "\n", encoding="utf-8")
        print(f"Written to {destination}", file=sys.stderr)
    else:
        print(plan.production_prompt)
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

    arguments = parser.parse_args(argv)

    try:
        if arguments.command == "list-worlds":
            return _list_worlds()
        if arguments.command == "validate-world":
            return _validate_world(arguments.slug)
        if arguments.command == "import-world":
            return _import_world(arguments.slug)
        if arguments.command == "prompt":
            return _write_prompt(arguments.slug, arguments.shot, arguments.out)
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
