"""Ingesting and resolving soundtrack audio.

The visual library's rules, unchanged, because they were never about images:
bytes are identity, measurements are immutable, approval is a decision rather
than a timestamp, and nothing is deleted.

What is genuinely different is reading the file. There is no Pillow for audio,
so the two formats that actually arrive are read directly: WAV through the
standard library, MP3 by parsing its own frame headers.

MP3 gets a real reader rather than a fallback because MP3 is what is delivered,
and because the production host has no ffmpeg â a probe that shells out would
measure nothing there and quietly store every duration as unknown. The parser
handles a Xing/Info header, which states the frame count outright, and constant
bitrate, where the length is arithmetic on the audio bytes.

``ffprobe`` is still tried for anything else, on a host that happens to have it.
Where nothing can read a file it is stored with an unknown duration rather than
a guessed one: absent is a fact about what could be measured, and a made-up
number is one an edit would trust.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import logging
import re
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.adapters.asset_store import AssetStore
from app.db.audio_models import AudioAsset, SoundtrackTrack, SoundtrackTrackAsset
from app.db.models import AuditEvent
from app.domain.enums import AudioAssetStatus, AudioSourceType, AuditEventType, LicenceStatus
from app.domain.errors import StudioError

logger = logging.getLogger(__name__)

OWNER = "owner"

# A 24-bit/48 kHz stereo master of a 2:48 song is about 48 MB, and the stem
# package is delivered a file at a time. 400 MB leaves room for a long
# uncompressed premaster without inviting somebody to post a whole session.
MAX_AUDIO_BYTES = 400 * 1024 * 1024

MIME_TYPES = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".flac": "audio/flac",
    ".aif": "audio/aiff",
    ".aiff": "audio/aiff",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
}
EXTENSIONS = {mime: suffix for suffix, mime in reversed(list(MIME_TYPES.items()))}

ROLE_PATTERN = re.compile(r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$")


class AudioRejected(StudioError):
    """The bytes are not audio this library will hold."""


class TrackNotFound(StudioError):
    """No such soundtrack track."""


@dataclass(frozen=True)
class AudioFacts:
    """What the file itself says. Nulls where nothing could read it."""

    sha256: str
    byte_size: int
    mime_type: str
    duration_ms: int | None
    sample_rate_hz: int | None
    channels: int | None
    bit_depth: int | None


def _probe_wav(data: bytes) -> AudioFacts | None:
    """Read a RIFF WAV with the standard library. No dependency, no subprocess."""
    try:
        with wave.open(BytesIO(data)) as handle:
            frames, rate = handle.getnframes(), handle.getframerate()
            return AudioFacts(
                sha256=hashlib.sha256(data).hexdigest(),
                byte_size=len(data),
                mime_type="audio/wav",
                duration_ms=round(frames / rate * 1000) if rate else None,
                sample_rate_hz=rate or None,
                channels=handle.getnchannels() or None,
                bit_depth=handle.getsampwidth() * 8 or None,
            )
    except (wave.Error, EOFError, ValueError):
        return None


# MPEG-1/2/2.5 Layer III header tables, indexed as the bits are laid out.
_MP3_BITRATES = {
    # version, layer 3
    (3, 1): (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0),
    (2, 1): (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0),
    (0, 1): (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0),
}
_MP3_RATES = {3: (44100, 48000, 32000), 2: (22050, 24000, 16000), 0: (11025, 12000, 8000)}
_MP3_SAMPLES = {3: 1152, 2: 576, 0: 576}
# The frame sync byte, as a constant rather than an escape: this file has
# already been mangled once by a literal 0xFF written into the source.
SYNC_WORD = bytes([0xFF])


def _id3_size(data: bytes) -> int:
    """Length of a leading ID3v2 tag, which is not audio and not a frame."""
    if len(data) < 10 or data[:3] != b"ID3":
        return 0
    # Syncsafe: seven bits per byte, high bit always clear.
    size = 0
    for byte in data[6:10]:
        size = (size << 7) | (byte & 0x7F)
    return size + 10 + (10 if data[5] & 0x10 else 0)


def _probe_mp3(data: bytes) -> AudioFacts | None:
    """Duration of an MP3 from its own frame headers. No decoder, no ffmpeg.

    The soundtrack is delivered as MP3 and the production host has no ffmpeg, so
    the fallback that reads it has to be arithmetic on the file itself. Handles
    the two cases that matter: a Xing/Info header, which states the frame count
    outright for a variable-rate file, and constant rate, where the length
    follows from the bitrate and the number of audio bytes.
    """
    start = _id3_size(data)
    frame = data.find(SYNC_WORD, start)
    while frame != -1 and frame + 4 <= len(data):
        header = data[frame : frame + 4]
        if header[1] & 0xE0 == 0xE0:
            version = (header[1] >> 3) & 0x03
            layer = (header[1] >> 1) & 0x03
            bitrate_index = (header[2] >> 4) & 0x0F
            rate_index = (header[2] >> 2) & 0x03
            if (
                version != 1
                and layer == 1
                and 0 < bitrate_index < 15
                and rate_index != 3
                and version in _MP3_RATES
            ):
                break
        frame = data.find(SYNC_WORD, frame + 1)
    else:
        return None
    if frame == -1:
        return None

    header = data[frame : frame + 4]
    version = (header[1] >> 3) & 0x03
    bitrate = _MP3_BITRATES[(version, 1)][(header[2] >> 4) & 0x0F] * 1000
    rate = _MP3_RATES[version][(header[2] >> 2) & 0x03]
    channels = 1 if (header[3] >> 6) & 0x03 == 3 else 2
    samples = _MP3_SAMPLES[version]

    # Xing (VBR) or Info (CBR) sits inside the first frame, after the side info.
    duration_ms: int | None = None
    window = data[frame : frame + 200]
    marker = max(window.find(b"Xing"), window.find(b"Info"))
    if marker != -1 and len(window) >= marker + 12:
        flags = int.from_bytes(window[marker + 4 : marker + 8], "big")
        if flags & 0x1:
            frames = int.from_bytes(window[marker + 8 : marker + 12], "big")
            if frames and rate:
                duration_ms = round(frames * samples / rate * 1000)
    if duration_ms is None and bitrate:
        duration_ms = round((len(data) - frame) * 8 / bitrate * 1000)

    return AudioFacts(
        sha256=hashlib.sha256(data).hexdigest(),
        byte_size=len(data),
        mime_type="audio/mpeg",
        duration_ms=duration_ms or None,
        sample_rate_hz=rate or None,
        channels=channels,
        # Lossy: there is no sample width to report, and inventing one would
        # imply a precision the file does not have.
        bit_depth=None,
    )


def _probe_ffprobe(data: bytes, suffix: str) -> dict[str, Any] | None:
    """Ask ffprobe, when the host has it. Absent on a machine without ffmpeg."""
    if shutil.which("ffprobe") is None:
        return None
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        path = Path(handle.name)
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=sample_rate,channels,bits_per_raw_sample:format=duration",
                "-select_streams",
                "a:0",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
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


def inspect(data: bytes, *, filename: str = "") -> AudioFacts:
    """Read what can be read, and refuse only what is genuinely unusable.

    The refusals are properties of the file: empty, oversized, or an extension
    this library has no MIME type for. Nothing about the content is judged â
    whether a mix is any good is a decision made later, by a person.
    """
    if not data:
        raise AudioRejected("The upload was empty.")
    if len(data) > MAX_AUDIO_BYTES:
        limit = MAX_AUDIO_BYTES // 1024 // 1024
        raise AudioRejected(f"{len(data) / 1024 / 1024:.0f} MB exceeds the {limit} MB limit.")

    suffix = Path(filename).suffix.lower()
    mime = MIME_TYPES.get(suffix)
    if mime is None:
        known = ", ".join(sorted(MIME_TYPES))
        raise AudioRejected(
            f"{suffix or 'a file with no extension'} is not an audio format this library "
            f"stores. Known: {known}."
        )

    facts = _probe_wav(data) if mime == "audio/wav" else None
    if facts is None and mime == "audio/mpeg":
        facts = _probe_mp3(data)
    if facts is not None:
        return facts

    probed = _probe_ffprobe(data, suffix) or {}
    stream = (probed.get("streams") or [{}])[0]
    duration = (probed.get("format") or {}).get("duration")

    def as_int(value: object) -> int | None:
        try:
            return int(float(str(value)))
        except (TypeError, ValueError):
            return None

    return AudioFacts(
        sha256=hashlib.sha256(data).hexdigest(),
        byte_size=len(data),
        mime_type=mime,
        duration_ms=None if duration is None else as_int(float(duration) * 1000),
        sample_rate_hz=as_int(stream.get("sample_rate")),
        channels=as_int(stream.get("channels")),
        bit_depth=as_int(stream.get("bits_per_raw_sample")),
    )


def storage_key_for(facts: AudioFacts) -> str:
    suffix = EXTENSIONS.get(facts.mime_type, ".bin")
    return f"audio/{facts.sha256[:2]}/{facts.sha256}{suffix}"


def find_by_sha(session: Session, sha256: str) -> AudioAsset | None:
    return session.execute(
        select(AudioAsset).where(AudioAsset.sha256 == sha256)
    ).scalar_one_or_none()


def _validated_role(role: str) -> str:
    cleaned = role.strip().lower()
    if not ROLE_PATTERN.match(cleaned):
        raise AudioRejected(f"{role!r} is not a usable role name.")
    return cleaned


@dataclass(frozen=True)
class Ingested:
    asset: AudioAsset
    created: bool


def ingest_audio(
    session: Session,
    store: AssetStore,
    *,
    data: bytes,
    filename: str,
    source_type: AudioSourceType = AudioSourceType.GENERATED,
    role: str | None = None,
    description: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    metadata: dict[str, Any] | None = None,
    rights_status: LicenceStatus = LicenceStatus.VERIFIED,
) -> Ingested:
    """Store the bytes and record the file, or return the one already held.

    Â§8 asks for SHA-256 checksums on the finals. They are not a field somebody
    fills in: the hash is how the file is addressed, so the checksum and the
    identity are the same fact.
    """
    facts = inspect(data, filename=filename)

    existing = find_by_sha(session, facts.sha256)
    if existing is not None:
        logger.info("audio asset %s already held as %s", facts.sha256[:12], existing.id)
        return Ingested(asset=existing, created=False)

    key = storage_key_for(facts)
    store.save(key, data, facts.mime_type)

    asset = AudioAsset(
        role=_validated_role(role) if role else None,
        storage_key=key,
        sha256=facts.sha256,
        mime_type=facts.mime_type,
        byte_size=facts.byte_size,
        duration_ms=facts.duration_ms,
        sample_rate_hz=facts.sample_rate_hz,
        channels=facts.channels,
        bit_depth=facts.bit_depth,
        source_type=source_type,
        provider=provider,
        model=model,
        status=AudioAssetStatus.PENDING,
        rights_status=rights_status,
        rights_metadata={"owner": "Shirtfaced", "origin": "owner-generated"},
        metadata_json=(metadata or {}) | {"original_filename": Path(filename).name},
        description=description,
    )
    session.add(asset)
    session.flush()

    session.add(
        AuditEvent(
            event_type=AuditEventType.AUDIO_ASSET_INGESTED,
            actor=OWNER,
            payload_json={
                "audio_asset_id": str(asset.id),
                "role": asset.role,
                "sha256": facts.sha256,
                "duration_ms": facts.duration_ms,
                "mime_type": facts.mime_type,
            },
        )
    )
    return Ingested(asset=asset, created=True)


def approve_audio(
    session: Session, asset: AudioAsset, *, actor: str = OWNER, note: str | None = None
) -> AudioAsset:
    """Mark a mix usable, and record who said so."""
    prior = asset.status
    asset.status = AudioAssetStatus.APPROVED
    asset.approved_at = dt.datetime.now(dt.UTC)
    asset.approved_by = actor
    session.add(
        AuditEvent(
            event_type=AuditEventType.AUDIO_ASSET_APPROVED,
            actor=actor,
            payload_json={
                "audio_asset_id": str(asset.id),
                "sha256": asset.sha256,
                "prior_state": prior.value,
                "note": note,
            },
        )
    )
    return asset


def deprecate_audio(
    session: Session, asset: AudioAsset, *, actor: str = OWNER, note: str | None = None
) -> AudioAsset:
    """Retire a mix without destroying it. An edit already cut against it."""
    prior = asset.status
    asset.status = AudioAssetStatus.DEPRECATED
    session.add(
        AuditEvent(
            event_type=AuditEventType.AUDIO_ASSET_DEPRECATED,
            actor=actor,
            payload_json={
                "audio_asset_id": str(asset.id),
                "sha256": asset.sha256,
                "prior_state": prior.value,
                "note": note,
            },
        )
    )
    return asset


def upsert_track(
    session: Session,
    *,
    slug: str,
    title: str,
    bpm: int | None = None,
    musical_key: str | None = None,
    time_signature: str | None = None,
) -> tuple[SoundtrackTrack, bool]:
    """Find or create a track. Facts given are filled in, never blanked."""
    track = (
        session.execute(select(SoundtrackTrack).where(SoundtrackTrack.slug == slug))
        .scalars()
        .first()
    )
    if track is None:
        track = SoundtrackTrack(slug=slug, title=title)
        session.add(track)
        created = True
    else:
        created = False

    track.title = title or track.title
    if bpm is not None:
        track.bpm = bpm
    if musical_key is not None:
        track.musical_key = musical_key
    if time_signature is not None:
        track.time_signature = time_signature
    session.flush()
    return track, created


def attach_to_track(
    session: Session,
    track: SoundtrackTrack,
    asset: AudioAsset,
    *,
    role: str,
    is_primary: bool = False,
    sort_order: int | None = None,
    notes: str | None = None,
    actor: str = OWNER,
) -> SoundtrackTrackAsset:
    """File a mix under a role. Passing ``is_primary`` demotes the incumbent."""
    role = _validated_role(role)

    link = session.execute(
        select(SoundtrackTrackAsset).where(
            SoundtrackTrackAsset.track_id == track.id,
            SoundtrackTrackAsset.audio_asset_id == asset.id,
        )
    ).scalar_one_or_none()

    if sort_order is None:
        highest = session.execute(
            select(func.max(SoundtrackTrackAsset.sort_order)).where(
                SoundtrackTrackAsset.track_id == track.id
            )
        ).scalar()
        sort_order = 0 if highest is None else highest + 1

    changed = link is None
    if link is None:
        link = SoundtrackTrackAsset(
            track_id=track.id, audio_asset_id=asset.id, role=role, sort_order=sort_order
        )
        session.add(link)
    else:
        changed = link.role != role
        link.role = role
    if notes is not None and notes != link.notes:
        link.notes = notes
        changed = True

    if is_primary and not link.is_primary:
        for other in session.execute(
            select(SoundtrackTrackAsset).where(
                SoundtrackTrackAsset.track_id == track.id,
                SoundtrackTrackAsset.role == role,
                SoundtrackTrackAsset.is_primary.is_(True),
                SoundtrackTrackAsset.audio_asset_id != asset.id,
            )
        ).scalars():
            other.is_primary = False
        session.flush()
        link.is_primary = True
        changed = True

    session.flush()
    if changed:
        session.add(
            AuditEvent(
                event_type=AuditEventType.SOUNDTRACK_ASSET_LINKED,
                actor=actor,
                payload_json={
                    "track": track.slug,
                    "audio_asset_id": str(asset.id),
                    "sha256": asset.sha256,
                    "role": role,
                    "is_primary": link.is_primary,
                },
            )
        )
    return link


@dataclass(frozen=True)
class ResolvedAudio:
    """Bytes, and the identity they came from."""

    asset_id: Any
    sha256: str
    data: bytes
    mime_type: str
    duration_ms: int | None
    role: str
    label: str

    def as_manifest(self) -> dict[str, object]:
        return {
            "label": self.label,
            "audio_asset_id": str(self.asset_id),
            "sha256": self.sha256,
            "role": self.role,
            "duration_ms": self.duration_ms,
            "mime_type": self.mime_type,
        }


def resolve_track_asset(
    session: Session, store: AssetStore, *, slug: str, role: str
) -> ResolvedAudio:
    """The approved primary mix for one role, or a refusal naming the gap.

    The same contract as a cast reference: an edit names the job it wants, not a
    filename, and gets back bytes with an identity attached.
    """
    label = f"{slug}/{role}"
    track = (
        session.execute(select(SoundtrackTrack).where(SoundtrackTrack.slug == slug))
        .scalars()
        .first()
    )
    if track is None:
        raise TrackNotFound(f"{label}: no track {slug!r}.")

    link = session.execute(
        select(SoundtrackTrackAsset).where(
            SoundtrackTrackAsset.track_id == track.id,
            SoundtrackTrackAsset.role == role,
            SoundtrackTrackAsset.is_primary.is_(True),
        )
    ).scalar_one_or_none()
    if link is None:
        held = (
            session.execute(
                select(SoundtrackTrackAsset.role).where(SoundtrackTrackAsset.track_id == track.id)
            )
            .scalars()
            .all()
        )
        raise AudioRejected(
            f"{label}: no primary {role!r} for {track.title}. "
            f"Held: {', '.join(sorted(set(held))) or 'nothing'}."
        )

    asset = session.get(AudioAsset, link.audio_asset_id)
    if asset is None:  # pragma: no cover - foreign key prevents this
        raise AudioRejected(f"{label}: the linked file is missing.")
    if asset.status is not AudioAssetStatus.APPROVED:
        raise AudioRejected(
            f"{label}: that mix is {asset.status.value}, not approved. "
            "Approve it before an edit is cut against it."
        )

    data = store.load(asset.storage_key)
    digest = hashlib.sha256(data).hexdigest()
    if digest != asset.sha256:
        raise AudioRejected(
            f"{label}: the stored file hashes to {digest[:12]} but the record says "
            f"{asset.sha256[:12]}. The store has been altered underneath the database."
        )

    return ResolvedAudio(
        asset_id=asset.id,
        sha256=digest,
        data=data,
        mime_type=asset.mime_type,
        duration_ms=asset.duration_ms,
        role=role,
        label=label,
    )
