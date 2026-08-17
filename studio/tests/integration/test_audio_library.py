"""The soundtrack library, held to the same rules as the pictures.

``SOUNDTRACK.md`` §8 asks for many files of one song and SHA-256 checksums on
the finals. These cover what that needs: the hash is the identity, a role says
what a file is for, one file answers to each role, and an edit resolves a job
rather than a filename.

What actually arrives is MP3 — the first delivered mix is one — and the
production host has no ffmpeg, so the MP3 reader is arithmetic on the file's own
frame headers and is tested as such. WAV is read with the standard library. A
file nothing can read keeps an unknown duration rather than a guessed one, and
there is a test for that too: an absent measurement has to stay absent, or an
edit will trust a number nobody measured.
"""

from __future__ import annotations

import hashlib
import struct
import wave
from io import BytesIO
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.db.audio_models import AudioAsset, SoundtrackTrackAsset
from app.db.models import AuditEvent
from app.domain.enums import AudioAssetStatus, AuditEventType, LicenceStatus
from app.services.audio_library import (
    AudioRejected,
    TrackNotFound,
    approve_audio,
    attach_to_track,
    deprecate_audio,
    ingest_audio,
    inspect,
    resolve_track_asset,
    upsert_track,
)

pytestmark = pytest.mark.integration


def wav(seconds: float = 1.0, rate: int = 48000, channels: int = 2, width: int = 3) -> bytes:
    """A silent WAV at the spec's 24-bit / 48 kHz unless asked otherwise."""
    buffer = BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(width)
        handle.setframerate(rate)
        handle.writeframes(b"\x00" * int(rate * seconds) * channels * width)
    return buffer.getvalue()


def wav_with_tone(seconds: float = 1.0, level: int = 1000) -> bytes:
    """Distinct bytes, so two files are genuinely two assets."""
    rate, frames = 48000, int(48000 * seconds)
    buffer = BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(
            b"".join(struct.pack("<h", (level if i % 100 < 50 else -level)) for i in range(frames))
        )
    return buffer.getvalue()


@pytest.fixture
def store(tmp_path: Path) -> FilesystemAssetStore:
    return FilesystemAssetStore(tmp_path / "assets")


@pytest.fixture
def track(session: Session):
    created, _ = upsert_track(
        session,
        slug="all-in-tonight",
        title="All In Tonight",
        bpm=132,
        musical_key="D major",
        time_signature="4/4",
    )
    return created


def test_a_wav_is_measured_by_the_standard_library(
    session: Session, store: FilesystemAssetStore
) -> None:
    """§8's authoritative format, read without a dependency or a subprocess."""
    facts = inspect(wav(seconds=2.5), filename="SF_W01_AllInTonight_full_master_v01.wav")

    assert facts.mime_type == "audio/wav"
    assert facts.duration_ms == 2500
    assert facts.sample_rate_hz == 48000
    assert facts.channels == 2
    assert facts.bit_depth == 24


def test_the_hash_is_the_checksum(session: Session, store: FilesystemAssetStore) -> None:
    data = wav_with_tone()
    asset = ingest_audio(session, store, data=data, filename="master.wav").asset

    assert asset.sha256 == hashlib.sha256(data).hexdigest()
    assert store.load(asset.storage_key) == data


def test_the_same_mix_twice_is_one_asset(session: Session, store: FilesystemAssetStore) -> None:
    data = wav_with_tone()
    first = ingest_audio(session, store, data=data, filename="master.wav")
    second = ingest_audio(session, store, data=data, filename="renamed-master.wav")

    assert first.created is True
    assert second.created is False
    assert first.asset.id == second.asset.id
    assert len(session.execute(select(AudioAsset)).scalars().all()) == 1


def test_an_unreadable_extension_is_refused(session: Session, store: FilesystemAssetStore) -> None:
    with pytest.raises(AudioRejected, match="not an audio format"):
        ingest_audio(session, store, data=wav(), filename="mix.txt")


def test_an_empty_upload_is_refused(session: Session, store: FilesystemAssetStore) -> None:
    with pytest.raises(AudioRejected, match="empty"):
        ingest_audio(session, store, data=b"", filename="mix.wav")


def test_a_format_nothing_can_read_keeps_an_unknown_duration(
    session: Session, store: FilesystemAssetStore
) -> None:
    """Absent, not guessed. An edit would trust a number nobody measured."""
    asset = ingest_audio(
        session, store, data=b"ID3\x04\x00" + b"\x00" * 4096, filename="reference.mp3"
    ).asset

    assert asset.mime_type == "audio/mpeg"
    assert asset.duration_ms is None
    assert asset.duration_seconds is None


def test_measurements_cannot_be_edited(session: Session, store: FilesystemAssetStore) -> None:
    from app.db.visual_models import AssetIsImmutable

    asset = ingest_audio(session, store, data=wav_with_tone(), filename="master.wav").asset
    with pytest.raises(AssetIsImmutable):
        asset.sha256 = "0" * 64
    with pytest.raises(AssetIsImmutable):
        asset.duration_ms = 999


def test_rights_are_verified_by_default(session: Session, store: FilesystemAssetStore) -> None:
    asset = ingest_audio(session, store, data=wav_with_tone(), filename="master.wav").asset

    assert asset.rights_status is LicenceStatus.VERIFIED
    assert asset.rights_metadata == {"owner": "Shirtfaced", "origin": "owner-generated"}


def test_the_track_carries_the_facts_every_mix_shares(session: Session, track) -> None:
    assert (track.bpm, track.musical_key, track.time_signature) == (132, "D major", "4/4")

    again, created = upsert_track(session, slug="all-in-tonight", title="All In Tonight")
    assert created is False
    assert again.id == track.id
    assert again.bpm == 132, "an upsert that omits a fact must not blank it"


def test_one_file_answers_to_each_role(
    session: Session, store: FilesystemAssetStore, track
) -> None:
    first = ingest_audio(session, store, data=wav_with_tone(level=800), filename="a.wav").asset
    second = ingest_audio(session, store, data=wav_with_tone(level=900), filename="b.wav").asset

    attach_to_track(session, track, first, role="canonical_12s5", is_primary=True)
    attach_to_track(session, track, second, role="canonical_12s5", is_primary=True)
    session.flush()

    primaries = (
        session.execute(
            select(SoundtrackTrackAsset).where(
                SoundtrackTrackAsset.track_id == track.id,
                SoundtrackTrackAsset.is_primary.is_(True),
            )
        )
        .scalars()
        .all()
    )
    assert len(primaries) == 1
    assert primaries[0].audio_asset_id == second.id


def test_an_edit_resolves_a_job_not_a_filename(
    session: Session, store: FilesystemAssetStore, track
) -> None:
    data = wav_with_tone(seconds=12.5)
    asset = ingest_audio(session, store, data=data, filename="canonical.wav").asset
    approve_audio(session, asset)
    attach_to_track(session, track, asset, role="canonical_12s5", is_primary=True)
    session.flush()

    resolved = resolve_track_asset(session, store, slug="all-in-tonight", role="canonical_12s5")
    assert resolved.sha256 == asset.sha256
    assert resolved.duration_ms == 12500
    assert resolved.as_manifest()["audio_asset_id"] == str(asset.id)


def test_an_unapproved_mix_does_not_resolve(
    session: Session, store: FilesystemAssetStore, track
) -> None:
    asset = ingest_audio(session, store, data=wav_with_tone(), filename="rough.wav").asset
    attach_to_track(session, track, asset, role="full_master", is_primary=True)
    session.flush()

    with pytest.raises(AudioRejected, match="pending, not approved"):
        resolve_track_asset(session, store, slug="all-in-tonight", role="full_master")


def test_a_deprecated_mix_stops_resolving_but_survives(
    session: Session, store: FilesystemAssetStore, track
) -> None:
    asset = ingest_audio(session, store, data=wav_with_tone(), filename="v1.wav").asset
    approve_audio(session, asset)
    attach_to_track(session, track, asset, role="full_master", is_primary=True)
    session.flush()
    deprecate_audio(session, asset, note="Superseded by v2")
    session.flush()

    with pytest.raises(AudioRejected, match="deprecated"):
        resolve_track_asset(session, store, slug="all-in-tonight", role="full_master")
    assert session.get(AudioAsset, asset.id) is not None
    assert store.exists(asset.storage_key)


def test_a_role_with_nothing_filed_says_what_is_held(
    session: Session, store: FilesystemAssetStore, track
) -> None:
    asset = ingest_audio(session, store, data=wav_with_tone(), filename="stem.wav").asset
    approve_audio(session, asset)
    attach_to_track(session, track, asset, role="stem_drums", is_primary=True)
    session.flush()

    with pytest.raises(AudioRejected, match="stem_drums"):
        resolve_track_asset(session, store, slug="all-in-tonight", role="loop_8_bar")


def test_an_unknown_track_is_refused(session: Session, store: FilesystemAssetStore) -> None:
    with pytest.raises(TrackNotFound, match="no track"):
        resolve_track_asset(session, store, slug="nothing", role="full_master")


def test_bytes_replaced_underneath_the_row_are_refused(
    session: Session, store: FilesystemAssetStore, track
) -> None:
    asset = ingest_audio(session, store, data=wav_with_tone(level=700), filename="m.wav").asset
    approve_audio(session, asset)
    attach_to_track(session, track, asset, role="full_master", is_primary=True)
    session.flush()

    store.save(asset.storage_key, wav_with_tone(level=1200), asset.mime_type)
    with pytest.raises(AudioRejected, match="altered underneath"):
        resolve_track_asset(session, store, slug="all-in-tonight", role="full_master")


def test_a_role_outside_the_offered_list_is_still_stored(
    session: Session, store: FilesystemAssetStore, track
) -> None:
    """Everything gets ingested. The vocabulary guides; it does not gate."""
    asset = ingest_audio(
        session, store, data=wav_with_tone(), filename="oddity.wav", role="crowd_bed_alt"
    ).asset
    assert asset.role == "crowd_bed_alt"


def test_ingest_and_approval_are_audited(
    session: Session, store: FilesystemAssetStore, track
) -> None:
    asset = ingest_audio(session, store, data=wav_with_tone(), filename="m.wav").asset
    approve_audio(session, asset, note="Signed off")
    attach_to_track(session, track, asset, role="full_master")
    session.flush()

    recorded = {
        event.event_type
        for event in session.execute(select(AuditEvent)).scalars()
        if str(event.payload_json.get("audio_asset_id")) == str(asset.id)
        or event.payload_json.get("track") == "all-in-tonight"
    }
    assert AuditEventType.AUDIO_ASSET_INGESTED in recorded
    assert AuditEventType.AUDIO_ASSET_APPROVED in recorded
    assert AuditEventType.SOUNDTRACK_ASSET_LINKED in recorded


def test_the_deliverable_vocabulary_matches_the_specification() -> None:
    """The roles the interface offers are the ones §8 and §6 name."""
    from app.domain.enums import SOUNDTRACK_ASSET_ROLES

    for required in ("full_master", "instrumental", "a_cappella", "premaster"):
        assert required in SOUNDTRACK_ASSET_ROLES
    for cutdown in ("hook_sting_6s", "canonical_12s5", "story_reel_30s", "loop_8_bar"):
        assert cutdown in SOUNDTRACK_ASSET_ROLES
    for stem in ("stem_drums", "stem_bass", "stem_vocals", "stem_mix_groups"):
        assert stem in SOUNDTRACK_ASSET_ROLES


def test_approval_is_not_implied_by_arrival(session: Session, store: FilesystemAssetStore) -> None:
    asset = ingest_audio(session, store, data=wav_with_tone(), filename="m.wav").asset
    assert asset.status is AudioAssetStatus.PENDING
    assert asset.approved_at is None


def mp3(seconds: float = 2.0, bitrate_kbps: int = 128) -> bytes:
    """A synthetic constant-rate MPEG-1 Layer III file.

    Built by hand rather than encoded, so the test runs on any host including
    one with no ffmpeg: an ID3v2 tag to be skipped, then frames whose headers
    say 128 kbps at 44.1 kHz.
    """
    tag = b"ID3\x03\x00\x00" + bytes([0, 0, 0, 0x0A]) + b"\x00" * 10
    # FF FB: MPEG-1 Layer III, no CRC. 90: 128 kbps at 44.1 kHz. C0: mono.
    header = bytes([0xFF, 0xFB, 0x90, 0xC0])
    frame_bytes = int(144 * bitrate_kbps * 1000 / 44100)
    frames = round(seconds * 44100 / 1152)
    return tag + (header + b"\x00" * (frame_bytes - 4)) * frames


def test_an_mp3_is_measured_from_its_own_frame_headers() -> None:
    """MP3 is what actually arrives, and the box has no ffmpeg to fall back on."""
    facts = inspect(mp3(seconds=2.0), filename="Our_Life_short_mix.mp3")

    assert facts.mime_type == "audio/mpeg"
    assert facts.sample_rate_hz == 44100
    assert facts.duration_ms is not None
    # Arithmetic over whole frames, so a few milliseconds either way.
    assert abs(facts.duration_ms - 2000) < 60
    # Lossy: reporting a sample width would imply precision the file lacks.
    assert facts.bit_depth is None


def test_an_id3_tag_is_not_mistaken_for_audio() -> None:
    """The tag is skipped before the first frame is looked for."""
    tagged = mp3(seconds=1.0)
    untagged = tagged[20:]  # drop the ID3v2 header this helper writes

    assert inspect(tagged, filename="a.mp3").duration_ms is not None
    assert inspect(untagged, filename="b.mp3").duration_ms is not None
    # Same audio either way, so the measured length agrees within a frame.
    difference = abs(
        (inspect(tagged, filename="a.mp3").duration_ms or 0)
        - (inspect(untagged, filename="b.mp3").duration_ms or 0)
    )
    assert difference < 60
