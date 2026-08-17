"""The trigger the bench hands over, against the workflow that consumes it.

§17 of ``NANO_BANANA_VEO_SCENE_PRODUCTION_PIPELINE.md``: motion runs from a JSON
file committed under ``studio/veo-coverage-triggers/``. Studio's part of the
pipeline ends at an approved shot, so building that file is the handover, and
building it by hand meant reading a storage key out of the database.

Two things are worth pinning. The file has to carry the fields the workflow
reads, which is checkable against the workflow itself rather than asserted. And
it must refuse to name a seed that is no longer current -- the workflow verifies
that the file on disk matches the checksum in the trigger, which is not the same
as the trigger naming the shot that is approved now.
"""

from __future__ import annotations

import json
import re
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy.orm import Session

from app.adapters.asset_store import FilesystemAssetStore
from app.db.visual_models import CoverageFrame, SceneMaster
from app.domain.enums import VisualAssetKind, VisualAssetSourceType
from app.services import coverage_library, visual_library
from app.services.coverage_library import CoverageRejected, veo_trigger

pytestmark = pytest.mark.integration

SCENE = "W01-P28"
WORKFLOW = (
    Path(__file__).resolve().parents[3] / ".github" / "workflows" / "renderer-veo-coverage.yml"
)


def png(width: int = 1080, height: int = 1920, shade: int = 40) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), (shade, shade, shade)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def store(tmp_path: Path) -> FilesystemAssetStore:
    return FilesystemAssetStore(tmp_path / "assets")


def approved_master(session: Session, store: FilesystemAssetStore, shade: int = 10) -> SceneMaster:
    ingested = visual_library.ingest_asset(
        session,
        store,
        data=png(1920, 1080, shade),
        kind=VisualAssetKind.SCENE_MASTER,
        source_type=VisualAssetSourceType.GENERATED,
        role=SCENE,
    )
    visual_library.approve_asset(session, ingested.asset)
    master = visual_library.register_scene_master(session, scene_key=SCENE, asset=ingested.asset)
    visual_library.approve_scene_master(session, master)
    session.flush()
    return master


def approved_shot(
    session: Session, store: FilesystemAssetStore, *, name: str = "damo-medium", shade: int = 50
) -> CoverageFrame:
    coverage_library.register_contact_sheet(
        session,
        store,
        scene_key=SCENE,
        label=f"{SCENE}-coverage",
        data=png(2048, 2048, shade - 5),
        approve=True,
    )
    frame = coverage_library.record_panel_extraction(
        session,
        store,
        scene_key=SCENE,
        name=name,
        panel=4,
        data=png(shade=shade),
        provider="google",
        model="gemini-3.1-flash-image",
        prompt_hash="0" * 64,
    )
    coverage_library.approve_for_veo(session, frame)
    session.flush()
    return frame


def test_the_trigger_carries_every_field_the_workflow_reads(
    session: Session, store: FilesystemAssetStore
) -> None:
    """Checked against the workflow's own json.load calls, not against a memory."""
    approved_master(session, store)
    frame = approved_shot(session, store)

    built = veo_trigger(
        session, store, frame=frame, purpose="animate approved shot", stamp="20260818T0100Z"
    )
    payload = json.loads(built.content)

    read_by_workflow = set(
        re.findall(
            r'json\.load\(open\(sys\.argv\[1\]\)\)\["(\w+)"\]', WORKFLOW.read_text(encoding="utf-8")
        )
    )
    assert read_by_workflow, "the workflow no longer reads the trigger the way this assumes"
    assert read_by_workflow <= set(payload)


def test_the_seed_path_is_where_the_workflow_looks(
    session: Session, store: FilesystemAssetStore
) -> None:
    """Relative to the Studio checkout on the box, under its asset root."""
    approved_master(session, store)
    frame = approved_shot(session, store)

    payload = json.loads(
        veo_trigger(session, store, frame=frame, purpose="p", stamp="20260818T0100Z").content
    )

    assert payload["seed_relative_path"].startswith("assets/visual/coverage/")
    assert payload["seed_sha256"] in payload["seed_relative_path"]
    assert payload["scene"] == SCENE
    assert payload["shot"] == "damo-medium"


def test_a_shot_not_approved_for_motion_has_no_trigger(
    session: Session, store: FilesystemAssetStore
) -> None:
    """Cutting a frame is not approving it, and §12 gates the paid call."""
    approved_master(session, store)
    frame = approved_shot(session, store)
    frame.approved_for_veo = False
    session.flush()

    with pytest.raises(CoverageRejected, match="not approved for Veo"):
        veo_trigger(session, store, frame=frame, purpose="p", stamp="20260818T0100Z")


def test_a_re_extracted_shot_will_not_hand_over_the_old_seed(
    session: Session, store: FilesystemAssetStore
) -> None:
    """The workflow checks the file matches the trigger, not that it is current.

    So the refusal has to happen here. Re-extracting a panel replaces the frame
    in place and clears its approval; a trigger built afterwards must not still
    name what was approved before.
    """
    approved_master(session, store)
    frame = approved_shot(session, store, shade=50)
    first = veo_trigger(session, store, frame=frame, purpose="p", stamp="20260818T0100Z")

    redone = coverage_library.record_panel_extraction(
        session,
        store,
        scene_key=SCENE,
        name="damo-medium",
        panel=4,
        data=png(shade=90),
        provider="google",
        model="gemini-3.1-flash-image",
        prompt_hash="1" * 64,
    )
    session.flush()

    assert redone.id == frame.id
    assert json.loads(first.content)["seed_sha256"] != redone.frame_sha256
    with pytest.raises(CoverageRejected, match="not approved for Veo"):
        veo_trigger(session, store, frame=redone, purpose="p", stamp="20260818T0200Z")


def test_the_filename_says_which_shot_it_animates(
    session: Session, store: FilesystemAssetStore
) -> None:
    approved_master(session, store)
    frame = approved_shot(session, store)

    built = veo_trigger(session, store, frame=frame, purpose="p", stamp="20260818T0100Z")

    assert built.filename == "20260818T0100Z-damo-medium.json"
