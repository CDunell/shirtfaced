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
    python -m app.cli register-scene-master W01-P28 master.png [--approve]
    python -m app.cli ingest-soundtrack all-in-tonight canonical_12s5 mix.wav --approve --primary
    python -m app.cli sync-archive
    python -m app.cli design-data [--refresh]
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


def _ingest_soundtrack(
    slug: str,
    role: str,
    path: str,
    title: str | None,
    approve: bool,
    primary: bool,
    bpm: int | None,
    key: str | None,
) -> int:
    """File one delivered mix against a track.

    Idempotent on the bytes: the same WAV twice is one asset, which is also what
    makes SOUNDTRACK.md §8's checksum requirement free -- the hash is the
    identity, not a field somebody fills in.
    """
    from app.adapters.asset_store import FilesystemAssetStore
    from app.domain.enums import AudioAssetStatus
    from app.services import audio_library

    source = Path(path).resolve()
    if not source.is_file():
        print(f"No such file: {source}", file=sys.stderr)
        return EXIT_FAILED

    store = FilesystemAssetStore(get_settings().assets_root_resolved)
    with get_session_factory()() as session:
        try:
            ingested = audio_library.ingest_audio(
                session,
                store,
                data=source.read_bytes(),
                filename=source.name,
                role=role,
                description=f"{slug} - {role.replace('_', ' ')}",
            )
        except audio_library.AudioRejected as error:
            print(str(error), file=sys.stderr)
            return EXIT_FAILED

        track, created = audio_library.upsert_track(
            session,
            slug=slug,
            title=title or slug.replace("-", " ").title(),
            bpm=bpm,
            musical_key=key,
        )
        if approve:
            audio_library.approve_audio(session, ingested.asset, note="Approved at ingest")
        audio_library.attach_to_track(session, track, ingested.asset, role=role, is_primary=primary)
        session.commit()

        asset = ingested.asset
        duration = "unknown length" if asset.duration_ms is None else f"{asset.duration_ms}ms"
        print(
            f"{'new track, ' if created else ''}"
            f"{'ingested' if ingested.created else 'already held'}: {slug}/{role} "
            f"asset={asset.id} sha256={asset.sha256} {duration} {asset.mime_type}"
        )
        if asset.status is not AudioAssetStatus.APPROVED:
            print("Pending. Nothing resolves it until it is approved.")
    return EXIT_OK


def _soundtrack(slug: str) -> int:
    """What a track holds, and which file answers to each role."""
    from app.db.audio_models import SoundtrackTrack, SoundtrackTrackAsset

    with get_session_factory()() as session:
        track = (
            session.execute(select(SoundtrackTrack).where(SoundtrackTrack.slug == slug))
            .scalars()
            .first()
        )
        if track is None:
            print(f"No track {slug!r}.", file=sys.stderr)
            return EXIT_FAILED

        facts = " ".join(
            part
            for part in (
                f"{track.bpm} BPM" if track.bpm else "",
                track.musical_key or "",
                track.time_signature or "",
            )
            if part
        )
        print(f"{track.title} ({track.slug}){' - ' + facts if facts else ''}")

        links = (
            session.execute(
                select(SoundtrackTrackAsset)
                .where(SoundtrackTrackAsset.track_id == track.id)
                .order_by(SoundtrackTrackAsset.role)
            )
            .scalars()
            .all()
        )
        if not links:
            print("  nothing filed yet")
            return EXIT_OK
        for link in links:
            asset = link.asset
            length = "?" if asset.duration_ms is None else f"{asset.duration_ms / 1000:.1f}s"
            print(
                f"  {link.role:18} {asset.status.value:9} {length:>7} "
                f"{asset.sha256[:12]}{'  primary' if link.is_primary else ''}"
            )
    return EXIT_OK


def _add_cast_members(specifications: Sequence[str]) -> int:
    """Create cast members who have no photographs yet.

    A person exists before any picture of them does, and the library should not
    require one to record that. Seeds a host whose ``var/cast`` holds only some
    of the cast, so the references can be uploaded through the Cast bench
    instead of provisioned as files.

    Idempotent: an existing slug is left alone, including its canon.
    """
    from app.db.visual_models import CastMember
    from app.services.cast_ingest import display_name_for

    created: list[str] = []
    existing: list[str] = []
    with get_session_factory()() as session:
        for specification in specifications:
            slug, _, display_name = specification.partition("=")
            slug = slug.strip().lower()
            if not slug:
                continue
            found = (
                session.execute(select(CastMember).where(CastMember.slug == slug)).scalars().first()
            )
            if found is not None:
                existing.append(slug)
                continue
            session.add(
                CastMember(slug=slug, display_name=display_name.strip() or display_name_for(slug))
            )
            created.append(slug)
        session.commit()

    print(f"{len(created)} created, {len(existing)} already present")
    for slug in created:
        print(f"  added: {slug}")
    for slug in existing:
        print(f"  kept:  {slug}")
    return EXIT_OK


def _coverage(scene_key: str, approve: str | None, show: bool) -> int:
    """List a scene's coverage frames, or approve one for Veo."""
    from sqlalchemy import select

    from app.db.visual_models import CoverageFrame, SceneMaster
    from app.services.coverage_library import CoverageRejected, approve_for_veo

    with get_session_factory()() as session:
        frames = (
            session.execute(
                select(CoverageFrame)
                .join(SceneMaster, SceneMaster.id == CoverageFrame.scene_master_id)
                .where(SceneMaster.scene_key == scene_key)
                .order_by(CoverageFrame.name)
            )
            .scalars()
            .all()
        )

        if approve:
            match = next((frame for frame in frames if frame.name == approve), None)
            if match is None:
                print(f"No coverage frame {approve!r} for {scene_key}.", file=sys.stderr)
                return EXIT_FAILED
            try:
                approve_for_veo(session, match, note="Approved from the command line")
            except CoverageRejected as error:
                print(str(error), file=sys.stderr)
                return EXIT_FAILED
            session.commit()
            print(f"{scene_key}/{approve} approved for Veo.")
            return EXIT_OK

        if not frames:
            print(f"No coverage frames for {scene_key}.")
            return EXIT_OK
        for frame in frames:
            stale = frame.source_master_sha256 != frame.master.asset.sha256
            state = "approved" if frame.approved_for_veo else "pending"
            print(
                f"{frame.name:16} {state:8} {frame.width}x{frame.height} "
                f"at ({frame.x},{frame.y}) frame={frame.frame_sha256[:12]} "
                f"master={frame.source_master_sha256[:12]}{'  STALE' if stale else ''}"
            )
        if show:
            print("STALE means the frame was cut from a master that is no longer approved.")
    return EXIT_OK


def _register_scene_master(scene_key: str, path: str, approve: bool, note: str | None) -> int:
    """Register an image as a scene's master. Registering is not approving.

    A candidate sits in the library with its hash and can be looked at. Only an
    approved master resolves, and approving one supersedes whatever held the
    scene before rather than overwriting it.
    """
    from app.adapters.asset_store import FilesystemAssetStore
    from app.domain.enums import VisualAssetKind, VisualAssetSourceType
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


def _design_data(refresh: bool) -> int:
    """Report -- or produce -- the measured corpus the design pipeline reads.

    The consumers (the advisor, the scoring thresholds, the composer's
    confidence) read PostgreSQL: ``design_measurements`` for the corpus,
    ``composed_designs`` for the decisions. This command reports both, and
    with ``--refresh`` it measures the corpus into the table -- one row per
    primary product shot, refusals recorded with their reason -- and merges
    the design archive into the vintage evidence root.

    The measurements used to be JSON files under ``var/design_corpus/`` that
    existed only on whichever machine last ran a mining script, which for the
    advisor's whole life was no machine at all. A table cannot be absent from
    the box, and this report is how an empty one stays loud.
    """
    import subprocess

    from sqlalchemy import func as sa_func
    from sqlalchemy import select as sa_select

    from app.config import PROJECT_ROOT
    from app.db.archive_models import ComposedDesign
    from app.db.measurement_models import DesignMeasurement
    from app.domain.enums import AttemptState
    from app.services.vintage_research import root as evidence_root

    corpus_root = PROJECT_ROOT / "var" / "design_corpus"
    archive_root = PROJECT_ROOT / "var" / "design_archive"
    scripts_root = PROJECT_ROOT / "scripts"

    if refresh:
        # The archive merge is genuinely file-domain: it hard-links reference
        # images into the root the Research bench reads. Everything measured
        # goes to the database below.
        if archive_root.is_dir():
            command = [
                sys.executable,
                str(scripts_root / "adapt_archive_to_evidence.py"),
                "--out",
                str(evidence_root()),
            ]
            print("-> merge design archive into evidence")
            if subprocess.run(command, cwd=PROJECT_ROOT).returncode != 0:
                print(f"FAILED. Re-run alone:\n  {' '.join(command)}")
                return EXIT_FAILED
        else:
            print(f"skip: no design archive at {archive_root}, nothing to merge")

        if corpus_root.is_dir():
            result = _measure_corpus(corpus_root, scripts_root)
            if result is None:
                return EXIT_FAILED
        else:
            print(f"skip: no design corpus at {corpus_root}, nothing to measure")

    try:
        with get_session_factory()() as session:
            measured = session.execute(
                sa_select(
                    DesignMeasurement.tradition,
                    sa_func.count(DesignMeasurement.id),
                )
                .where(DesignMeasurement.refusal_reason.is_(None))
                .group_by(DesignMeasurement.tradition)
                .order_by(sa_func.count(DesignMeasurement.id).desc())
            ).all()
            refused = session.execute(
                sa_select(sa_func.count(DesignMeasurement.id)).where(
                    DesignMeasurement.refusal_reason.is_not(None)
                )
            ).scalar_one()
            decisions = session.execute(
                sa_select(
                    ComposedDesign.grammar_key,
                    ComposedDesign.state,
                    sa_func.count(ComposedDesign.id),
                )
                .where(
                    ComposedDesign.state.in_(
                        (AttemptState.APPROVED.value, AttemptState.REJECTED.value)
                    )
                )
                .group_by(ComposedDesign.grammar_key, ComposedDesign.state)
            ).all()
    except Exception as error:
        print(f"database unreachable: {error}")
        return EXIT_FAILED

    total = sum(count for _, count in measured)
    print(f"\nmeasured corpus (design_measurements): {total} frames, {refused} refused")
    for tradition, count in measured:
        print(f"  {tradition or '(no tradition)':<24} {count}")
    if not total:
        print(
            "  The corpus has not been measured; the advisor and thresholds run\n"
            "  on documented defaults. Run: python -m app.cli design-data --refresh"
        )

    if decisions:
        print("\ncomposer learning (composed_designs decisions):")
        by_grammar: dict[str, list[int]] = {}
        for grammar_key, state, count in decisions:
            entry = by_grammar.setdefault(grammar_key, [0, 0])
            entry[1] += count
            if state == AttemptState.APPROVED.value:
                entry[0] += count
        for grammar_key, (approved, decided) in sorted(by_grammar.items()):
            print(f"  {grammar_key:<24} {approved}/{decided} approved")
    else:
        print("\ncomposer learning: no decisions yet -- confidence is baseline until some exist")

    evidence = evidence_root()
    listings = (
        sum(1 for child in evidence.iterdir() if child.is_dir() and child.name.isdigit())
        if evidence.is_dir()
        else 0
    )
    print(f"\nevidence root {evidence}: {listings} listing(s)")
    return EXIT_OK


def _measure_corpus(corpus_root: Path, scripts_root: Path) -> int | None:
    """Measure every brand's primary product shots into design_measurements.

    Reuses the analyser and the walk order of the mining scripts unchanged --
    first image per product, later ones are alternate angles of the same
    design and would double-count it. A refusal is a row with its reason; a
    frame with no detected print is skipped, matching the joiner this
    replaces. Idempotent: re-measuring a frame replaces its row.
    """
    import json as json_module

    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from app.db.measurement_models import DesignMeasurement
    from app.services.design_advisor import phrase_words

    sys.path.insert(0, str(scripts_root))
    try:
        from corpus_tiers import is_excluded  # type: ignore[import-not-found]
        from mine_design_patterns import (  # type: ignore[import-not-found]
            _analyse,
            _placement_band,
        )
    finally:
        sys.path.remove(str(scripts_root))

    import hashlib

    analyser_version = hashlib.sha256(
        (scripts_root / "mine_design_patterns.py").read_bytes()
    ).hexdigest()[:12]

    session_factory = get_session_factory()
    measured = refused = skipped = 0
    with session_factory() as session:
        for brand_dir in sorted(corpus_root.iterdir()):
            if not brand_dir.is_dir() or is_excluded(brand_dir.name):
                continue
            brand_file = brand_dir / "brand.json"
            if not brand_file.is_file():
                continue
            brand = json_module.loads(brand_file.read_text(encoding="utf-8-sig"))
            tradition = brand.get("design_tradition", "unknown")
            products_dir = brand_dir / "products"
            if not products_dir.is_dir():
                continue
            for product_dir in sorted(products_dir.iterdir()):
                product_file = product_dir / "product.json"
                if not product_file.is_file():
                    continue
                product = json_module.loads(product_file.read_text(encoding="utf-8-sig"))
                images = product.get("images") or []
                if not images:
                    continue
                result = _analyse(product_dir / images[0])
                if result is None:
                    skipped += 1
                    continue

                values: dict[str, object] = {
                    "corpus": "design_corpus",
                    "brand_slug": brand_dir.name,
                    "product_slug": product_dir.name[:128],
                    "image_path": images[0],
                    "product_name": product.get("name", ""),
                    "tradition": tradition,
                    "phrase_words": len(phrase_words(product.get("name", ""))),
                    "analyser_version": analyser_version,
                }
                if "refused" in result:
                    values["refusal_reason"] = str(result["refused"])[:64]
                    refused += 1
                elif not result.get("has_print"):
                    skipped += 1
                    continue
                else:
                    values.update(
                        refusal_reason=None,
                        print_coverage=result["print_coverage"],
                        ink_colours=result["ink_colours"],
                        placement_band=_placement_band(result["centroid_y"]),
                        light_on_dark=result["light_on_dark"],
                    )
                    measured += 1

                statement = pg_insert(DesignMeasurement).values(**values)
                session.execute(
                    statement.on_conflict_do_update(
                        constraint="uq_design_measurements_frame",
                        set_={
                            key: getattr(statement.excluded, key)
                            for key in values
                            if key not in ("corpus", "brand_slug", "product_slug", "image_path")
                        },
                    )
                )
                if (measured + refused) % 250 == 0:
                    print(f"  {measured} measured, {refused} refused...", flush=True)
                    session.commit()
        session.commit()

    print(f"-> corpus measured: {measured} frames, {refused} refused, {skipped} skipped")
    return measured


def _split_specification(specification: str, flag: str) -> tuple[str, str, str]:
    """``a=b=path`` -- split on the first two separators so Windows paths survive."""
    parts = specification.split("=", 2)
    if len(parts) != 3:
        raise StudioError(f"{flag} expects three parts separated by '=', got {specification!r}")
    return parts[0], parts[1], parts[2]


def _sync_archive() -> int:
    """Bring the stored archive in line with the elements the composer uses.

    Idempotent, and it says what it changed. A sync that reports work it did not
    do makes the report worthless, which is the only reason anyone runs it.

    The set synced is ``registry.all_elements()`` -- authored and drawn both --
    because that is the set the composer draws from. Syncing only the authored
    elements left every drawn part unresolvable at provenance time: the compose
    route joins chosen parts against ``archive_elements`` and silently skips a
    key it cannot find, so most of a composed design's parts produced no
    ``ElementUse`` row.
    """
    from app.archive import registry
    from app.archive.repository import ElementRepository

    elements = registry.all_elements()
    session_factory = get_session_factory()
    with session_factory() as session:
        repository = ElementRepository(session)
        result = repository.sync(elements)
        audit = repository.licence_audit()
        unverified = repository.unverified()
        session.commit()

    print(
        f"{result.total} element(s) in the composer's set: "
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
    standing_in = [element for element in elements if element.provisional]
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
        help="Store the composer's element set (authored and drawn) and its feature vectors",
    )

    design_data = subcommands.add_parser(
        "design-data",
        help="Report the mined-corpus artefacts and what each consumer runs on",
    )
    design_data.add_argument(
        "--refresh",
        action="store_true",
        help="Run the producers in order: merge archive into evidence, mine, join, rebuild",
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

    soundtrack_in = subcommands.add_parser(
        "ingest-soundtrack",
        help="File one delivered mix against a track. Idempotent on the bytes.",
    )
    soundtrack_in.add_argument("slug", help="Track slug, e.g. all-in-tonight")
    soundtrack_in.add_argument("role", help="What the file is, e.g. canonical_12s5")
    soundtrack_in.add_argument("path")
    soundtrack_in.add_argument("--title")
    soundtrack_in.add_argument("--bpm", type=int)
    soundtrack_in.add_argument("--key", help="Musical key, e.g. 'D major'")
    soundtrack_in.add_argument("--approve", action="store_true")
    soundtrack_in.add_argument(
        "--primary", action="store_true", help="Make it the file this role resolves to."
    )

    soundtrack_out = subcommands.add_parser(
        "soundtrack", help="What a track holds, and which file answers to each role."
    )
    soundtrack_out.add_argument("slug")

    add_members = subcommands.add_parser(
        "add-cast-members",
        help="Create cast members with no references yet, so photos can be uploaded.",
    )
    add_members.add_argument(
        "members", nargs="+", metavar="slug[=Display Name]", help="One or more members."
    )

    coverage = subcommands.add_parser(
        "coverage",
        help="List a scene's coverage frames, or approve one for Veo.",
    )
    coverage.add_argument("scene_key")
    coverage.add_argument("--approve", metavar="SHOT", help="Approve this frame for Veo.")
    coverage.add_argument("--explain", action="store_true", help="Explain the STALE marker.")

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
        if arguments.command == "design-data":
            return _design_data(refresh=arguments.refresh)
        if arguments.command == "ingest-soundtrack":
            return _ingest_soundtrack(
                arguments.slug,
                arguments.role,
                arguments.path,
                arguments.title,
                arguments.approve,
                arguments.primary,
                arguments.bpm,
                arguments.key,
            )
        if arguments.command == "soundtrack":
            return _soundtrack(arguments.slug)
        if arguments.command == "add-cast-members":
            return _add_cast_members(arguments.members)
        if arguments.command == "coverage":
            return _coverage(arguments.scene_key, arguments.approve, arguments.explain)
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
