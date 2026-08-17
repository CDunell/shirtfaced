"""Animating an approved shot, and keeping every take it costs to get one.

The last leg of the pipeline. §5 of the Nano contract: a standalone shot, once
approved, becomes the first frame of a Veo generation. Everything upstream of
that — which master, which sheet, which panel — is already settled by the time
this module runs, so it does not name a file. It names a scene and a shot, and
``resolve_veo_seed`` decides whether that is currently animatable.

The shape worth getting right is *takes*, plural. SHOTLIST.md's package asks for
roughly six seconds a shot and expects one and a half to four of them to
survive. So a shot accumulates attempts, most of them wrong, and a rejected one
is kept: it is the cheapest evidence there is about what a motion prompt does.
Rerunning is the next attempt number, never an overwrite.

Two things are deliberately not automated. Which take is the keeper, and which
seconds of it are worth cutting — neither is computable, and both are the only
part of this where a person's judgement is the product.

Reading the file is the one genuinely new problem, and it is the same one audio
had: the clip has to be measured without assuming ffprobe exists. MP4 states its
own duration, dimensions and track list in its header boxes, so those are parsed
directly and ffprobe is tried only for anything else.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import logging
import re
import shutil
import struct
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore
from app.adapters.google_media import GoogleMediaError, GoogleVideoClient, GoogleVideoRequest
from app.config import Settings
from app.db.models import AuditEvent
from app.db.visual_models import CoverageFrame, MotionTake, SceneMaster, VideoAsset
from app.domain.enums import AuditEventType, LicenceStatus, VideoAssetStatus
from app.domain.errors import StudioError
from app.services import coverage_library, markdown_sections
from app.services.generation_ledger import PROVIDER, record_call
from app.services.reference_resolution import ReferenceUnavailable

logger = logging.getLogger(__name__)

OWNER = "owner"

PENDING = "pending"
KEEPER = "keeper"
REJECTED = "rejected"

# A silent 8-second 1080p Veo clip is a few megabytes. 500 MB is far past
# anything the provider returns and still refuses a whole rushes folder posted
# by mistake.
MAX_VIDEO_BYTES = 500 * 1024 * 1024

MIME_TYPES = {".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm"}
EXTENSIONS = {"video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm"}

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$")


class MotionRejected(StudioError):
    """The bytes are not a clip this library will hold."""


class MotionUnavailable(StudioError):
    """The take cannot be generated, and the message says which input is missing."""


@dataclass(frozen=True)
class VideoFacts:
    """What the file itself says. Nulls where nothing could read it."""

    sha256: str
    byte_size: int
    mime_type: str
    duration_ms: int | None
    width: int | None
    height: int | None
    frame_rate: Decimal | None
    has_audio: bool | None


def _boxes(data: bytes, start: int, end: int) -> list[tuple[bytes, int, int]]:
    """The ISO base-media boxes directly inside ``data[start:end]``.

    Each is ``(type, payload start, payload end)``. Malformed input stops the
    walk rather than raising: an unreadable clip is stored with unknown
    measurements, the same way an unreadable audio file is.
    """
    found: list[tuple[bytes, int, int]] = []
    offset = start
    while offset + 8 <= end:
        size = int.from_bytes(data[offset : offset + 4], "big")
        kind = data[offset + 4 : offset + 8]
        body = offset + 8
        if size == 1:  # 64-bit extended size
            if body + 8 > end:
                break
            size = int.from_bytes(data[body : body + 8], "big")
            body += 8
        elif size == 0:  # runs to the end of the enclosing box
            size = end - offset
        if size < 8 or offset + size > end:
            break
        found.append((kind, body, offset + size))
        offset += size
    return found


def _find(data: bytes, path: tuple[bytes, ...], start: int, end: int) -> tuple[int, int] | None:
    """Walk a nested box path, e.g. ``(b"moov", b"mvhd")``."""
    for kind, body, stop in _boxes(data, start, end):
        if kind != path[0]:
            continue
        if len(path) == 1:
            return body, stop
        found = _find(data, path[1:], body, stop)
        if found is not None:
            return found
    return None


def _probe_mp4(data: bytes) -> VideoFacts | None:
    """Read an MP4/MOV header with no dependency and no subprocess.

    ``mvhd`` states the timescale and duration; each ``trak`` states its handler
    (so an audio track can be seen without decoding anything) and, for video,
    its display dimensions in ``tkhd`` as 16.16 fixed point. Frame rate is the
    video track's sample count over its own duration, which is exact for the
    constant-rate output a generator returns.
    """
    top = _boxes(data, 0, len(data))
    if not any(kind == b"ftyp" for kind, _, _ in top):
        return None
    moov = next(((body, stop) for kind, body, stop in top if kind == b"moov"), None)
    if moov is None:
        return None

    duration_ms: int | None = None
    mvhd = _find(data, (b"mvhd",), *moov)
    if mvhd is not None:
        body, _ = mvhd
        version = data[body]
        try:
            if version == 1:
                timescale, ticks = struct.unpack(">IQ", data[body + 20 : body + 32])
            else:
                timescale, ticks = struct.unpack(">II", data[body + 12 : body + 20])
            if timescale:
                duration_ms = round(ticks / timescale * 1000)
        except struct.error:
            duration_ms = None

    width = height = None
    frame_rate: Decimal | None = None
    has_audio = False

    for kind, body, stop in _boxes(data, *moov):
        if kind != b"trak":
            continue
        handler = _find(data, (b"mdia", b"hdlr"), body, stop)
        handler_type = b""
        if handler is not None:
            handler_type = data[handler[0] + 8 : handler[0] + 12]
        if handler_type == b"soun":
            has_audio = True
            continue
        if handler_type != b"vide":
            continue

        tkhd = _find(data, (b"tkhd",), body, stop)
        if tkhd is not None:
            head = tkhd[0]
            # Width and height are the last two fields of tkhd. Everything
            # before them is fixed-width, and version 1 widens the three time
            # fields by four bytes each: 76 becomes 88.
            offset = head + (88 if data[head] == 1 else 76)
            with contextlib.suppress(struct.error):
                raw_w, raw_h = struct.unpack(">II", data[offset : offset + 8])
                width, height = raw_w >> 16 or None, raw_h >> 16 or None

        mdhd = _find(data, (b"mdia", b"mdhd"), body, stop)
        stts = _find(data, (b"mdia", b"minf", b"stbl", b"stts"), body, stop)
        if mdhd is not None and stts is not None:
            with contextlib.suppress(struct.error, ZeroDivisionError):
                head = mdhd[0]
                if data[head] == 1:
                    timescale, ticks = struct.unpack(">IQ", data[head + 20 : head + 32])
                else:
                    timescale, ticks = struct.unpack(">II", data[head + 12 : head + 20])
                head = stts[0]
                (entries,) = struct.unpack(">I", data[head + 4 : head + 8])
                samples = sum(
                    struct.unpack(">I", data[head + 8 + index * 8 : head + 12 + index * 8])[0]
                    for index in range(min(entries, 4096))
                )
                if ticks and samples:
                    frame_rate = round(Decimal(samples) / (Decimal(ticks) / timescale), 3)

    return VideoFacts(
        sha256=hashlib.sha256(data).hexdigest(),
        byte_size=len(data),
        mime_type="video/mp4",
        duration_ms=duration_ms,
        width=width,
        height=height,
        frame_rate=frame_rate,
        has_audio=has_audio,
    )


def _probe_ffprobe(data: bytes, suffix: str) -> dict[str, Any] | None:
    """Ask ffprobe, on a host that has one. Absent is not an error."""
    if shutil.which("ffprobe") is None:
        return None
    with tempfile.NamedTemporaryFile(suffix=suffix or ".bin", delete=False) as handle:
        handle.write(data)
        path = Path(handle.name)
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=codec_type,width,height,avg_frame_rate:format=duration",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode != 0:
            return None
        parsed: dict[str, Any] = json.loads(result.stdout)
        return parsed
    except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
        return None
    finally:
        with contextlib.suppress(OSError):
            path.unlink()


def inspect(data: bytes, *, filename: str = "") -> VideoFacts:
    """Read what can be read, and refuse only what is a property of the file."""
    if not data:
        raise MotionRejected("The clip was empty.")
    if len(data) > MAX_VIDEO_BYTES:
        limit = MAX_VIDEO_BYTES // 1024 // 1024
        raise MotionRejected(f"{len(data) / 1024 / 1024:.0f} MB exceeds the {limit} MB limit.")

    suffix = Path(filename).suffix.lower()
    mime = MIME_TYPES.get(suffix, "video/mp4" if not suffix else None)
    if mime is None:
        raise MotionRejected(
            f"{suffix} is not a video format this library stores. "
            f"Known: {', '.join(sorted(MIME_TYPES))}."
        )

    if mime in {"video/mp4", "video/quicktime"}:
        facts = _probe_mp4(data)
        if facts is not None:
            return VideoFacts(**{**facts.__dict__, "mime_type": mime})

    probed = _probe_ffprobe(data, suffix) or {}
    streams = probed.get("streams") or []
    video: dict[str, Any] = next((one for one in streams if one.get("codec_type") == "video"), {})
    duration = (probed.get("format") or {}).get("duration")

    def as_int(value: object) -> int | None:
        try:
            return int(float(str(value)))
        except (TypeError, ValueError):
            return None

    rate: Decimal | None = None
    raw_rate = str(video.get("avg_frame_rate") or "")
    if "/" in raw_rate:
        top, _, bottom = raw_rate.partition("/")
        with contextlib.suppress(ArithmeticError, ValueError):
            if Decimal(bottom):
                rate = round(Decimal(top) / Decimal(bottom), 3)

    return VideoFacts(
        sha256=hashlib.sha256(data).hexdigest(),
        byte_size=len(data),
        mime_type=mime,
        duration_ms=None if duration is None else as_int(float(duration) * 1000),
        width=as_int(video.get("width")),
        height=as_int(video.get("height")),
        frame_rate=rate,
        has_audio=any(one.get("codec_type") == "audio" for one in streams) if streams else None,
    )


def storage_key_for(facts: VideoFacts) -> str:
    suffix = EXTENSIONS.get(facts.mime_type, ".mp4")
    return f"video/{facts.sha256[:2]}/{facts.sha256}{suffix}"


def find_by_sha(session: Session, sha256: str) -> VideoAsset | None:
    return session.execute(
        select(VideoAsset).where(VideoAsset.sha256 == sha256)
    ).scalar_one_or_none()


@dataclass(frozen=True)
class IngestedVideo:
    asset: VideoAsset
    created: bool


def ingest_video(
    session: Session,
    store: AssetStore,
    *,
    data: bytes,
    filename: str = "take.mp4",
    provider: str | None = None,
    model: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> IngestedVideo:
    """Store the bytes and record the clip, or return the one already held.

    Bytes are identity here as everywhere else: the same clip returned twice is
    one row, not two, and the SHA is the checksum an edit later cuts against.
    """
    facts = inspect(data, filename=filename)

    existing = find_by_sha(session, facts.sha256)
    if existing is not None:
        logger.info("video asset %s already held as %s", facts.sha256[:12], existing.id)
        return IngestedVideo(asset=existing, created=False)

    key = storage_key_for(facts)
    store.save(key, data, facts.mime_type)

    asset = VideoAsset(
        storage_key=key,
        sha256=facts.sha256,
        mime_type=facts.mime_type,
        byte_size=facts.byte_size,
        duration_ms=facts.duration_ms,
        width=facts.width,
        height=facts.height,
        frame_rate=facts.frame_rate,
        has_audio=facts.has_audio,
        provider=provider,
        model=model,
        status=VideoAssetStatus.PENDING,
        rights_status=LicenceStatus.VERIFIED,
        metadata_json=(metadata or {}) | {"original_filename": Path(filename).name},
    )
    session.add(asset)
    session.flush()
    return IngestedVideo(asset=asset, created=True)


def shot_spec_path(worlds_root: Path, scene_key: str) -> Path | None:
    """The scene's own shot specification, if a world holds one."""
    for shots in sorted(worlds_root.glob("*/shots")):
        candidate = shots / f"{scene_key}.md"
        if candidate.is_file():
            return candidate
    return None


def scene_motion_prompt(worlds_root: Path, scene_key: str) -> str | None:
    """The scene's motion direction, read from its own specification.

    ``W01-P28.md`` §6 is written as instructions to whatever animates the shot,
    and it is already the agreed answer -- Damo rocks rather than poses, the
    stool stays put, the crowd does not converge on him. Composing the default
    from it means the bench does not ask somebody to retype canon from memory,
    and the ledger records what was actually sent either way.

    Returned as a starting point, not a gate. The operator edits it per shot,
    because the shared direction is shared and the shot is not.
    """
    path = shot_spec_path(worlds_root, scene_key)
    if path is None:
        return None
    text = path.read_text(encoding="utf-8")
    section = next(
        (
            one
            for one in markdown_sections.split_sections(text)
            if "motion direction" in one.heading.casefold()
        ),
        None,
    )
    if section is None:
        return None
    lines = markdown_sections.bullets_of(section.body)
    return "\n".join(lines) if lines else section.body.strip() or None


def _frame_for(session: Session, *, scene_key: str, name: str) -> CoverageFrame:
    frame = (
        session.execute(
            select(CoverageFrame)
            .join(SceneMaster, SceneMaster.id == CoverageFrame.scene_master_id)
            .where(SceneMaster.scene_key == scene_key, CoverageFrame.name == name)
            .order_by(CoverageFrame.created_at.desc())
        )
        .scalars()
        .first()
    )
    if frame is None:
        raise MotionUnavailable(f"{scene_key}/{name}: no such coverage frame.")
    return frame


def next_attempt(session: Session, frame: CoverageFrame) -> int:
    """One past the highest attempt this shot holds. Numbers are never reused."""
    highest = session.execute(
        select(func.max(MotionTake.attempt)).where(MotionTake.coverage_frame_id == frame.id)
    ).scalar()
    return int(highest or 0) + 1


def takes_for_scene(session: Session, scene_key: str) -> list[MotionTake]:
    """Every take against every shot in this scene, newest attempt first."""
    return list(
        session.execute(
            select(MotionTake)
            .join(CoverageFrame, CoverageFrame.id == MotionTake.coverage_frame_id)
            .join(SceneMaster, SceneMaster.id == CoverageFrame.scene_master_id)
            .where(SceneMaster.scene_key == scene_key)
            .order_by(CoverageFrame.name, MotionTake.attempt.desc())
        )
        .scalars()
        .unique()
        .all()
    )


def _video_client(settings: Settings) -> GoogleVideoClient:
    if not settings.google_media_live or settings.gemini_api_key is None:
        raise MotionUnavailable(
            "Google media is not live on this host, so nothing was sent and nothing was "
            "charged. Set GOOGLE_MEDIA_ENABLED and GEMINI_API_KEY."
        )
    return GoogleVideoClient(
        api_key=settings.gemini_api_key.get_secret_value(),
        model=settings.google_video_model,
        poll_seconds=settings.google_video_poll_seconds,
        timeout_seconds=settings.google_video_timeout_seconds,
    )


def generate_take(
    session: Session,
    store: AssetStore,
    settings: Settings,
    *,
    scene_key: str,
    name: str,
    prompt: str,
    aspect_ratio: str = "9:16",
    actor: str = OWNER,
) -> MotionTake:
    """Animate the approved shot and keep whatever comes back, good or not.

    The seed is resolved rather than supplied: ``resolve_veo_seed`` re-checks
    that the shot is approved, that its master is still the approved one and
    that its sheet has not been superseded, so a run cannot animate a stale
    still by naming an old file.
    """
    try:
        seed = coverage_library.resolve_veo_seed(session, store, scene_key=scene_key, name=name)
    except (coverage_library.CoverageRejected, ReferenceUnavailable) as error:
        raise MotionUnavailable(str(error)) from error

    frame = _frame_for(session, scene_key=scene_key, name=name)
    client = _video_client(settings)
    started = time.monotonic()
    try:
        result = client.generate(
            GoogleVideoRequest(
                prompt=prompt,
                first_frame=seed.data,
                first_frame_mime=seed.mime_type,
                aspect_ratio=aspect_ratio,
                resolution=settings.google_video_resolution,
            )
        )
    except GoogleMediaError as error:
        record_call(
            session,
            operation="motion_take",
            model=settings.google_video_model,
            scene_key=scene_key,
            subject=name,
            prompt=prompt,
            inputs=[seed.asset_id],
            output_asset_id=None,
            succeeded=False,
            failure=str(error),
            duration_ms=round((time.monotonic() - started) * 1000),
            actor=actor,
        )
        session.commit()
        raise MotionUnavailable(f"Veo refused the generation: {error}") from error

    duration_ms = round((time.monotonic() - started) * 1000)
    ingested = ingest_video(
        session,
        store,
        data=result.data,
        filename=f"{scene_key}-{name}.mp4",
        provider=PROVIDER,
        model=result.model,
        metadata={
            "scene": scene_key,
            "shot": name,
            "operation_name": result.operation_name,
            "aspect_ratio": aspect_ratio,
            "resolution": settings.google_video_resolution,
        },
    )

    take = MotionTake(
        coverage_frame_id=frame.id,
        video_asset_id=ingested.asset.id,
        attempt=next_attempt(session, frame),
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        first_frame_sha256=seed.sha256,
        status=PENDING,
    )
    session.add(take)
    session.flush()

    record_call(
        session,
        operation="motion_take",
        model=result.model,
        scene_key=scene_key,
        subject=name,
        prompt=prompt,
        inputs=[seed.asset_id],
        output_asset_id=None,
        succeeded=True,
        failure=None,
        duration_ms=duration_ms,
        actor=actor,
    )
    session.add(
        AuditEvent(
            event_type=AuditEventType.MOTION_TAKE_GENERATED,
            actor=actor,
            payload_json={
                "motion_take_id": str(take.id),
                "scene": scene_key,
                "shot": name,
                "attempt": take.attempt,
                "video_sha256": ingested.asset.sha256,
                "first_frame_sha256": seed.sha256,
                "duration_ms": ingested.asset.duration_ms,
            },
        )
    )
    return take


def _existing_keeper(session: Session, frame_id: uuid.UUID) -> MotionTake | None:
    return session.execute(
        select(MotionTake).where(
            MotionTake.coverage_frame_id == frame_id, MotionTake.status == KEEPER
        )
    ).scalar_one_or_none()


def keep_take(
    session: Session,
    take: MotionTake,
    *,
    from_ms: int | None = None,
    to_ms: int | None = None,
    note: str | None = None,
    actor: str = OWNER,
) -> MotionTake:
    """Make this the take the edit cuts from, and record the range worth cutting.

    One keeper per shot, the same rule as one approved master per scene: the
    edit needs one answer. Naming a new keeper stands the previous one down
    rather than deleting it, so what was chosen and what was passed over both
    stay on the record.

    The range is optional, because a take can be right before anybody has
    scrubbed it. Where it is given it is checked against the clip's own
    duration — a keeper that runs past the end of the file is a typo, and the
    edit would find out later and more expensively.
    """
    if take.status == REJECTED:
        raise MotionRejected(
            f"Attempt {take.attempt} was rejected. Generate another take rather than "
            "reinstating one that was already judged."
        )

    duration = take.video.duration_ms
    if from_ms is not None and from_ms < 0:
        raise MotionRejected("A keeper cannot start before the clip does.")
    if from_ms is not None and to_ms is not None and to_ms <= from_ms:
        raise MotionRejected(f"{from_ms}-{to_ms}ms is not a range.")
    if duration is not None and to_ms is not None and to_ms > duration:
        raise MotionRejected(f"The clip runs {duration}ms and the keeper ends at {to_ms}ms.")

    superseded = _existing_keeper(session, take.coverage_frame_id)
    if superseded is not None and superseded.id != take.id:
        superseded.status = PENDING
        superseded.decided_at = dt.datetime.now(dt.UTC)
        superseded.decided_by = actor
        session.flush()

    take.status = KEEPER
    take.keeper_from_ms = from_ms
    take.keeper_to_ms = to_ms
    take.notes = note or take.notes
    take.decided_at = dt.datetime.now(dt.UTC)
    take.decided_by = actor

    video = take.video
    video.status = VideoAssetStatus.APPROVED
    video.approved_at = dt.datetime.now(dt.UTC)
    video.approved_by = actor

    session.add(
        AuditEvent(
            event_type=AuditEventType.MOTION_TAKE_APPROVED,
            actor=actor,
            payload_json={
                "motion_take_id": str(take.id),
                "shot": take.frame.name,
                "attempt": take.attempt,
                "keeper_from_ms": from_ms,
                "keeper_to_ms": to_ms,
                "superseded": None if superseded is None else str(superseded.id),
                "note": note,
            },
        )
    )
    return take


def reject_take(
    session: Session, take: MotionTake, *, note: str | None = None, actor: str = OWNER
) -> MotionTake:
    """Say no without deleting. The clip stays; the next attempt is a new row."""
    take.status = REJECTED
    take.keeper_from_ms = None
    take.keeper_to_ms = None
    take.notes = note or take.notes
    take.decided_at = dt.datetime.now(dt.UTC)
    take.decided_by = actor

    take.video.status = VideoAssetStatus.REJECTED

    session.add(
        AuditEvent(
            event_type=AuditEventType.MOTION_TAKE_REJECTED,
            actor=actor,
            payload_json={
                "motion_take_id": str(take.id),
                "shot": take.frame.name,
                "attempt": take.attempt,
                "note": note,
            },
        )
    )
    return take
