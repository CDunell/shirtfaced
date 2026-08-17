"""The motion leg: reading a clip, and the takes a shot accumulates.

§5 of ``NANO_BANANA_CONTACT_SHEET_PIPELINE.md`` ends with an approved standalone
shot becoming a Veo first frame. What is covered here is everything that happens
around the provider call, because that is the part that has to be right whether
or not a call is ever made: the clip is measured without ffmpeg, a take is kept
rather than overwritten, one keeper answers for a shot, and a shot re-extracted
after a take was animated shows that take as stale.

The MP4s are built byte by byte rather than fetched. A generated clip is not
available in a test, and a fixture file would only prove the parser can read
that one file — composing the boxes means the header the parser reads is the
header the test wrote.
"""

from __future__ import annotations

import struct
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.db.visual_models import CoverageFrame, MotionTake, SceneContactSheet, SceneMaster
from app.domain.enums import VideoAssetStatus, VisualAssetKind, VisualAssetSourceType
from app.services import coverage_library, motion_library, visual_library
from app.services.motion_library import (
    MotionRejected,
    ingest_video,
    inspect,
    keep_take,
    next_attempt,
    reject_take,
    takes_for_scene,
)

pytestmark = pytest.mark.integration

SCENE = "W01-P28"


def _box(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload) + 8) + kind + payload


def mp4(
    *,
    seconds: float = 6.0,
    width: int = 1080,
    height: int = 1920,
    fps: int = 24,
    audio: bool = False,
    tag: int = 0,
) -> bytes:
    """A structurally valid MP4 header stating what the test wants read back.

    No media data: the parser reads the header boxes, and a real payload would
    make the fixture large without making it more true. ``tag`` varies the bytes
    so two otherwise identical clips are two identities.
    """
    timescale = 1000
    ticks = int(seconds * timescale)
    frames = int(seconds * fps)

    mvhd = _box(
        b"mvhd",
        struct.pack(">IIIII", 0, 0, 0, timescale, ticks)
        + struct.pack(">Ihh", 0x00010000, 0x0100, 0)
        + b"\x00" * 8
        + b"\x00" * 36
        + b"\x00" * 24
        + struct.pack(">I", 3),
    )

    def trak(handler: bytes, track_id: int) -> bytes:
        tkhd = _box(
            b"tkhd",
            struct.pack(">IIIIII", 7, 0, 0, track_id, 0, ticks)
            + b"\x00" * 8
            + struct.pack(">hhhh", 0, 0, 0, 0)
            + b"\x00" * 36
            + struct.pack(">II", width << 16, height << 16),
        )
        mdhd = _box(b"mdhd", struct.pack(">IIIIIhh", 0, 0, 0, timescale, ticks, 0x55C4, 0))
        hdlr = _box(b"hdlr", struct.pack(">II", 0, 0) + handler + b"\x00" * 12 + b"\x00")
        stts = _box(
            b"stts", struct.pack(">III", 0, 1, frames) + struct.pack(">I", timescale // fps)
        )
        stbl = _box(b"stbl", stts)
        minf = _box(b"minf", stbl)
        mdia = _box(b"mdia", mdhd + hdlr + minf)
        return _box(b"trak", tkhd + mdia)

    tracks = trak(b"vide", 1) + (trak(b"soun", 2) if audio else b"")
    ftyp = _box(b"ftyp", b"isom" + struct.pack(">I", 512) + b"isomiso2avc1mp41")
    free = _box(b"free", bytes([tag % 256]) * (1 + tag))
    return ftyp + free + _box(b"moov", mvhd + tracks)


def png(width: int = 1080, height: int = 1920, shade: int = 40) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), (shade, shade, shade)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def store(tmp_path: Path) -> FilesystemAssetStore:
    return FilesystemAssetStore(tmp_path / "assets")


def approved_master(
    session: Session, store: FilesystemAssetStore, *, shade: int = 10
) -> SceneMaster:
    ingested = visual_library.ingest_asset(
        session,
        store,
        data=png(width=1920, height=1080, shade=shade),
        kind=VisualAssetKind.SCENE_MASTER,
        source_type=VisualAssetSourceType.GENERATED,
        role=SCENE,
    )
    visual_library.approve_asset(session, ingested.asset)
    master = visual_library.register_scene_master(session, scene_key=SCENE, asset=ingested.asset)
    visual_library.approve_scene_master(session, master)
    session.flush()
    return master


def approved_sheet(
    session: Session, store: FilesystemAssetStore, *, shade: int = 45
) -> SceneContactSheet:
    return coverage_library.register_contact_sheet(
        session,
        store,
        scene_key=SCENE,
        label=f"{SCENE}-coverage",
        data=png(width=2048, height=2048, shade=shade),
        approve=True,
    )


def extract(
    session: Session,
    store: FilesystemAssetStore,
    *,
    name: str = "damo-wide",
    panel: int = 1,
    shade: int = 50,
    approve: bool = True,
) -> CoverageFrame:
    """A standalone extraction from the approved sheet. Stage three's output."""
    frame = coverage_library.record_panel_extraction(
        session,
        store,
        scene_key=SCENE,
        name=name,
        panel=panel,
        data=png(shade=shade),
        aspect_ratio="9:16",
        provider="google",
        model="gemini-3.1-flash-image",
        prompt_hash="0" * 64,
    )
    if approve:
        coverage_library.approve_for_veo(session, frame)
    session.flush()
    return frame


def approved_shot(session: Session, store: FilesystemAssetStore, **kwargs: object) -> CoverageFrame:
    approved_sheet(session, store)
    return extract(session, store, **kwargs)  # type: ignore[arg-type]


def take_for(
    session: Session,
    store: FilesystemAssetStore,
    frame: CoverageFrame,
    *,
    tag: int = 0,
    seconds: float = 6.0,
) -> MotionTake:
    """A take recorded without a provider call, which is all the model needs."""
    ingested = ingest_video(
        session, store, data=mp4(tag=tag, seconds=seconds), provider="google", model="veo-3.1"
    )
    take = MotionTake(
        coverage_frame_id=frame.id,
        video_asset_id=ingested.asset.id,
        attempt=next_attempt(session, frame),
        prompt_sha256="1" * 64,
        first_frame_sha256=frame.frame_sha256,
        status=motion_library.PENDING,
    )
    session.add(take)
    session.flush()
    return take


def test_a_clip_is_measured_without_ffmpeg(tmp_path: Path) -> None:
    """The production host had no ffmpeg for months and stored nothing wrong.

    Duration, dimensions and frame rate are stated in the file's own header, so
    they are read there rather than shelled out for.
    """
    facts = inspect(mp4(seconds=6.5, width=1080, height=1920, fps=24), filename="take.mp4")

    assert facts.duration_ms == 6500
    assert (facts.width, facts.height) == (1080, 1920)
    assert facts.frame_rate is not None and round(float(facts.frame_rate)) == 24
    assert facts.has_audio is False


def test_generated_sound_is_visible_in_the_file_rather_than_the_filename() -> None:
    """SHOTLIST.md discards Veo's audio. Whether a file still has it is a fact."""
    assert inspect(mp4(audio=True), filename="take.mp4").has_audio is True
    assert inspect(mp4(audio=False), filename="take.mp4").has_audio is False


def test_an_unreadable_clip_is_stored_with_unknown_measurements_not_guessed_ones() -> None:
    facts = inspect(b"not an mp4, but bytes all the same" * 40, filename="take.mp4")

    assert facts.duration_ms is None
    assert facts.width is None
    assert facts.byte_size > 0


def test_an_empty_upload_is_refused() -> None:
    with pytest.raises(MotionRejected, match="empty"):
        inspect(b"", filename="take.mp4")


def test_the_same_clip_twice_is_one_identity(session: Session, store: FilesystemAssetStore) -> None:
    first = ingest_video(session, store, data=mp4(tag=1))
    second = ingest_video(session, store, data=mp4(tag=1))

    assert second.created is False
    assert second.asset.id == first.asset.id


def test_rerunning_a_shot_is_the_next_attempt_not_an_overwrite(
    session: Session, store: FilesystemAssetStore
) -> None:
    """Most takes are wrong, and a wrong one is evidence about the prompt."""
    approved_master(session, store)
    frame = approved_shot(session, store)

    first = take_for(session, store, frame, tag=1)
    reject_take(session, first, note="Damo goes rigid at 3s")
    second = take_for(session, store, frame, tag=2)
    session.flush()

    assert (first.attempt, second.attempt) == (1, 2)
    assert first.status == motion_library.REJECTED
    assert first.video.status is VideoAssetStatus.REJECTED
    assert len(takes_for_scene(session, SCENE)) == 2


def test_one_keeper_per_shot_and_naming_a_new_one_stands_the_old_one_down(
    session: Session, store: FilesystemAssetStore
) -> None:
    """The edit needs one answer, the same rule as one approved master."""
    approved_master(session, store)
    frame = approved_shot(session, store)
    first = take_for(session, store, frame, tag=1)
    second = take_for(session, store, frame, tag=2)

    keep_take(session, first, from_ms=1200, to_ms=3600)
    session.flush()
    keep_take(session, second, from_ms=800, to_ms=3000)
    session.flush()

    assert first.status == motion_library.PENDING
    # The range it was given stays. Somebody watched that clip and decided which
    # seconds were the good ones; losing that because a later take won is
    # throwing away the judgement, not the decision.
    assert first.keeper_length_ms == 2400
    assert second.status == motion_library.KEEPER
    assert second.keeper_length_ms == 2200
    assert second.video.status is VideoAssetStatus.APPROVED


def test_a_keeper_range_cannot_run_past_the_end_of_the_clip(
    session: Session, store: FilesystemAssetStore
) -> None:
    """A typo the edit would otherwise find later and more expensively."""
    approved_master(session, store)
    frame = approved_shot(session, store)
    take = take_for(session, store, frame, seconds=6.0)

    with pytest.raises(MotionRejected, match="6000ms"):
        keep_take(session, take, from_ms=1000, to_ms=9000)


def test_a_rejected_take_is_not_reinstated_as_a_keeper(
    session: Session, store: FilesystemAssetStore
) -> None:
    approved_master(session, store)
    frame = approved_shot(session, store)
    take = take_for(session, store, frame)
    reject_take(session, take)
    session.flush()

    with pytest.raises(MotionRejected, match="rejected"):
        keep_take(session, take)


def test_a_take_records_the_still_it_actually_animated(
    session: Session, store: FilesystemAssetStore
) -> None:
    """Re-extracting a panel does not retrospectively change what was animated."""
    approved_master(session, store)
    approved_sheet(session, store)
    frame = extract(session, store, shade=50)
    take = take_for(session, store, frame)
    animated = take.first_frame_sha256

    redone = extract(session, store, shade=60, approve=False)
    session.flush()

    assert redone.name == frame.name
    assert take.first_frame_sha256 == animated
    assert take.first_frame_sha256 != redone.frame_sha256


def test_the_motion_prompt_comes_from_the_scene_s_own_specification() -> None:
    """Nobody retypes canon from memory into a generation prompt."""
    worlds = Path(__file__).resolve().parents[2] / "worlds"
    prompt = motion_library.scene_motion_prompt(worlds, SCENE)

    assert prompt is not None
    assert "rocking out" in prompt
    assert motion_library.scene_motion_prompt(worlds, "no-such-scene") is None
