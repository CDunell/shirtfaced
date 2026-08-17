"""Command line entry points.

Importing a world is a deliberate operator action, not something that happens on
application startup, so it lives here rather than in a request handler.

    python -m app.cli list-worlds
    python -m app.cli validate-world world-01
    python -m app.cli import-world world-01
    python -m app.cli import-design-concepts ../docs/design/TSHIRT_CONCEPT_LIBRARY.md
    python -m app.cli attempts world-01
    python -m app.cli discard-attempt <id>
    python -m app.cli prompt world-01 [--shot W01-015] [--out prompt.txt]
    python -m app.cli ingest-cast [--extra damo=expression_bridge=path.jpg] [--mirror]
    python -m app.cli resolve-reference damo head_shoulders_neutral
    python -m app.cli register-scene-master pub-1105 master.png [--approve]
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


def _import_design_concepts(path: str) -> int:
    """Seed or refresh the design backlog from a concept library document.

    Idempotent, like ``import-world``: numbers are matched, wording is updated,
    statuses the workflow owns are kept, and disagreements are reported rather
    than resolved. Nothing is ever deleted or renumbered.
    """
    from app.services.concept_importer import import_concepts
    from app.services.concept_loader import load_concept_library

    source = Path(path).resolve()
    # Recorded repo-relative so the same row reads the same on any host. A
    # document from outside the repository keeps its given path.
    repository_root = Path(__file__).resolve().parents[2]
    try:
        recorded = source.relative_to(repository_root).as_posix()
    except ValueError:
        recorded = Path(path).as_posix()
    loaded = load_concept_library(source, source_path=recorded)

    with get_session_factory()() as session:
        report = import_concepts(session, loaded)
        session.commit()

    print(report.summary())
    for conflict in report.status_conflicts:
        print(f"  conflict: {conflict}")
    for missing in report.missing_from_source:
        print(f"  missing: {missing}")
    return EXIT_OK


def _resolve_reference(slug: str, role: str) -> int:
    """Answer what production would resolve, and fail loudly if it would not.

    A precondition a paid pipeline can run before it spends anything. It used
    to be ``test -s var/cast/damo/b-head-shoulders.png``, which was true of a
    file nobody had approved, false of a file that had merely been renamed, and
    silent about which bytes the generator would actually receive.
    """
    from app.adapters.asset_store import FilesystemAssetStore
    from app.services.reference_resolution import ReferenceUnavailable, resolve_cast_reference

    store = FilesystemAssetStore(get_settings().assets_root_resolved)
    try:
        with get_session_factory()() as session:
            reference = resolve_cast_reference(session, store, slug=slug, role=role)
    except ReferenceUnavailable as error:
        print(str(error), file=sys.stderr)
        return EXIT_FAILED

    print(
        f"{slug}/{role} asset={reference.asset_id} sha256={reference.sha256} "
        f"{reference.width}x{reference.height} {reference.mime_type}"
    )
    return EXIT_OK


def _register_scene_master(scene_key: str, path: str, approve: bool, note: str | None) -> int:
    """Register an image as a scene's master. Registering is not approving.

    A candidate sits in the library with its hash and can be looked at. Only an
    approved master resolves, and approving one supersedes whatever held the
    scene before rather than overwriting it.
    """
    from app.adapters.asset_store import FilesystemAssetStore
    from app.domain.enums import LicenceStatus, VisualAssetKind, VisualAssetSourceType
    from app.services import visual_library

    source = Path(path).resolve()
    if not source.is_file():
        print(f"No such file: {source}", file=sys.stderr)
        return EXIT_FAILED

    store = FilesystemAssetStore(get_settings().assets_root_resolved)
    with get_session_factory()() as session:
        ingested = visual_library.ingest_asset(
            session,
            store,
            data=source.read_bytes(),
            kind=VisualAssetKind.SCENE_MASTER,
            source_type=VisualAssetSourceType.GENERATED,
            role=scene_key,
            description=f"Scene master candidate for {scene_key}",
            rights_status=LicenceStatus.VERIFIED,
            rights_metadata={"owner": "Shirtfaced", "origin": "owner-generated"},
            metadata={"registered_from": source.name},
        )
        master = visual_library.register_scene_master(
            session, scene_key=scene_key, asset=ingested.asset, notes=note
        )
        if approve:
            visual_library.approve_asset(session, ingested.asset, note=note)
            visual_library.approve_scene_master(session, master, note=note)
        session.commit()

        asset = ingested.asset
        print(
            f"{scene_key} master {master.status}: asset={asset.id} sha256={asset.sha256} "
            f"{asset.width}x{asset.height}"
        )
        if not approve:
            print("Candidate only. Nothing resolves it until it is approved.")
    return EXIT_OK


def _resolve_scene_master(scene_key: str) -> int:
    """What the coverage tool and every Veo run would resolve for this scene."""
    from app.adapters.asset_store import FilesystemAssetStore
    from app.services.reference_resolution import ReferenceUnavailable, resolve_scene_master

    store = FilesystemAssetStore(get_settings().assets_root_resolved)
    try:
        with get_session_factory()() as session:
            master = resolve_scene_master(session, store, scene_key=scene_key)
    except ReferenceUnavailable as error:
        print(str(error), file=sys.stderr)
        return EXIT_FAILED

    print(
        f"{scene_key} asset={master.asset_id} sha256={master.sha256} "
        f"{master.width}x{master.height} {master.mime_type}"
    )
    return EXIT_OK


def _export_cast_mirror(root: str | None) -> int:
    """Write the legacy ``<slug>/<file>.png`` view from the database.

    A generated compatibility artefact, never a source of truth. Useful for
    handing the approved references to something that can only take files --
    and for proving the database and the mirror agree.
    """
    from app.adapters.asset_store import FilesystemAssetStore
    from app.config import PROJECT_ROOT
    from app.services.visual_library import export_legacy_cast_mirror

    settings = get_settings()
    target = Path(root).resolve() if root else PROJECT_ROOT / "var" / "cast"
    store = FilesystemAssetStore(settings.assets_root_resolved)

    with get_session_factory()() as session:
        written = export_legacy_cast_mirror(session, store, target)

    if not written:
        print(f"No approved primary references to export into {target}.", file=sys.stderr)
        return EXIT_FAILED
    print(f"{len(written)} files written under {target}")
    return EXIT_OK


def _ingest_cast(
    root: str | None, extras: Sequence[str], assets: Sequence[str], mirror: bool
) -> int:
    """Phase 2 of VISUAL_ASSET_LIBRARY.md: ``var/cast`` becomes cast members.

    Idempotent. Assets are identified by the SHA of their bytes, so a second
    run re-links what is already there and ingests nothing twice.
    """
    from app.adapters.asset_store import FilesystemAssetStore
    from app.config import PROJECT_ROOT
    from app.domain.enums import VisualAssetKind, VisualAssetSourceType
    from app.services import visual_library
    from app.services.cast_ingest import (
        IngestReport,
        ingest_cast_directory,
        ingest_extra_reference,
    )

    settings = get_settings()
    cast_root = Path(root).resolve() if root else PROJECT_ROOT / "var" / "cast"
    if not cast_root.is_dir():
        print(f"No cast directory at {cast_root}", file=sys.stderr)
        return EXIT_FAILED

    store = FilesystemAssetStore(settings.assets_root_resolved)
    report = IngestReport()

    with get_session_factory()() as session:
        ingest_cast_directory(session, store, cast_root, report=report)

        for specification in extras:
            slug, role, path = _split_specification(specification, "--extra")
            ingest_extra_reference(
                session, store, slug=slug, role=role, path=Path(path).resolve(), report=report
            )

        for specification in assets:
            kind, role, path = _split_specification(specification, "--asset")
            source = Path(path).resolve()
            ingested = visual_library.ingest_asset(
                session,
                store,
                data=source.read_bytes(),
                kind=VisualAssetKind(kind),
                source_type=VisualAssetSourceType.GENERATED,
                role=role,
                description=f"Imported from {source.name}",
                metadata={"ingested_from": source.name},
            )
            bucket = report.assets_created if ingested.created else report.assets_already_held
            bucket.append(f"{kind}/{role}")

        session.commit()

        written: list[Path] = []
        if mirror:
            written = visual_library.export_legacy_cast_mirror(session, store, cast_root)

    print(report.summary())
    for line in report.skipped:
        print(f"  skipped: {line}")
    if mirror:
        print(f"  legacy mirror rewritten: {len(written)} files under {cast_root}")
    return EXIT_OK


def _split_specification(specification: str, flag: str) -> tuple[str, str, str]:
    """``a=b=path`` -- split on the first two separators so Windows paths survive."""
    parts = specification.split("=", 2)
    if len(parts) != 3:
        raise StudioError(f"{flag} expects three parts separated by '=', got {specification!r}")
    return parts[0], parts[1], parts[2]


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

    concepts = subcommands.add_parser(
        "import-design-concepts",
        help="Seed or refresh the design backlog from a concept library document",
    )
    concepts.add_argument("path", help="Path to the library document")

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

    cast = subcommands.add_parser(
        "ingest-cast",
        help="Import var/cast into the Visual Asset Library. Idempotent.",
    )
    cast.add_argument("--root", help="Cast directory. Defaults to var/cast.")
    cast.add_argument(
        "--extra",
        action="append",
        default=[],
        metavar="slug=role=path",
        help="One further reference for a member, such as damo=expression_bridge=shout.jpg",
    )
    cast.add_argument(
        "--asset",
        action="append",
        default=[],
        metavar="kind=role=path",
        help="An asset held without a cast link, such as coverage=shouting=frame.jpg",
    )
    cast.add_argument(
        "--mirror",
        action="store_true",
        help="Rewrite the legacy var/cast files from the database afterwards.",
    )

    register = subcommands.add_parser(
        "register-scene-master",
        help="Register an image as a scene's master. Candidate unless --approve.",
    )
    register.add_argument("scene_key")
    register.add_argument("path")
    register.add_argument("--approve", action="store_true", help="Approve it in the same step.")
    register.add_argument("--note")

    scene = subcommands.add_parser(
        "resolve-scene-master",
        help="Print the master a scene resolves to. Non-zero if production would refuse.",
    )
    scene.add_argument("scene_key")

    mirror = subcommands.add_parser(
        "export-cast-mirror",
        help="Write the legacy var/cast files from the database. A generated view.",
    )
    mirror.add_argument("--root", help="Where to write. Defaults to var/cast.")

    resolve = subcommands.add_parser(
        "resolve-reference",
        help="Print the asset a cast slug/role resolves to. Non-zero if it would refuse.",
    )
    resolve.add_argument("slug")
    resolve.add_argument("role")

    arguments = parser.parse_args(argv)

    try:
        if arguments.command == "list-worlds":
            return _list_worlds()
        if arguments.command == "validate-world":
            return _validate_world(arguments.slug)
        if arguments.command == "import-world":
            return _import_world(arguments.slug)
        if arguments.command == "import-design-concepts":
            return _import_design_concepts(arguments.path)
        if arguments.command == "sync-archive":
            return _sync_archive()
        if arguments.command == "register-scene-master":
            return _register_scene_master(
                arguments.scene_key, arguments.path, arguments.approve, arguments.note
            )
        if arguments.command == "resolve-scene-master":
            return _resolve_scene_master(arguments.scene_key)
        if arguments.command == "export-cast-mirror":
            return _export_cast_mirror(arguments.root)
        if arguments.command == "resolve-reference":
            return _resolve_reference(arguments.slug, arguments.role)
        if arguments.command == "ingest-cast":
            return _ingest_cast(arguments.root, arguments.extra, arguments.asset, arguments.mirror)
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
