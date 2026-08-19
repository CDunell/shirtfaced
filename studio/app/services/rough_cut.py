"""AI-assisted rough cuts from existing Veo takes.

This is intentionally an editing layer, not another renderer. It samples the
silent Veo takes already on disk, asks the configured review model to identify
the strongest usable temporal window, records those decisions locally, then
uses ffmpeg to build one vertical rough cut. Generated Veo audio never enters
the edit.
"""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.config import PROJECT_ROOT, Settings
from app.db.scene_shot_models import SceneShotMaster
from app.domain.errors import StudioError
from app.services import motion_run


class RoughCutError(StudioError):
    """The rough-cut analyser or renderer could not complete."""


@dataclass
class ShotEdit:
    shot_id: str
    shot_name: str
    take_stamp: str
    decision: str
    in_seconds: float
    out_seconds: float
    identity_score: int
    deformation_score: int
    continuity_score: int
    world_score: int
    energy_score: int
    rationale: str


@dataclass
class RoughCutState:
    scene_key: str
    shots: list[ShotEdit]
    output_exists: bool = False


def _root(scene_key: str) -> Path:
    return PROJECT_ROOT / "var" / "renderer-validation" / scene_key


def _state_path(scene_key: str) -> Path:
    return _root(scene_key) / "rough-cut.json"


def output_path(scene_key: str) -> Path:
    return _root(scene_key) / "rough-cut.mp4"


def load(scene_key: str) -> RoughCutState:
    path = _state_path(scene_key)
    if not path.is_file():
        return RoughCutState(scene_key=scene_key, shots=[], output_exists=output_path(scene_key).is_file())
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        shots = [ShotEdit(**row) for row in payload.get("shots", [])]
    except (OSError, json.JSONDecodeError, TypeError) as error:
        raise RoughCutError(f"{scene_key}: rough-cut state is unreadable: {error}") from error
    return RoughCutState(scene_key=scene_key, shots=shots, output_exists=output_path(scene_key).is_file())


def _save(state: RoughCutState) -> RoughCutState:
    root = _root(state.scene_key)
    root.mkdir(parents=True, exist_ok=True)
    _state_path(state.scene_key).write_text(
        json.dumps({"scene_key": state.scene_key, "shots": [asdict(row) for row in state.shots]}, indent=2) + "\n",
        encoding="utf-8",
    )
    state.output_exists = output_path(state.scene_key).is_file()
    return state


def _take_for(shot: SceneShotMaster, stamp: str | None = None) -> motion_run.RecordedTake:
    takes = motion_run.takes_for(shot.scene_key, shot.name)
    if not takes:
        raise RoughCutError(f"{shot.scene_key}/{shot.name}: no Veo take exists.")
    if stamp is None:
        return takes[0]
    for take in takes:
        if take.stamp == stamp:
            return take
    raise RoughCutError(f"{shot.scene_key}/{shot.name}: take {stamp} does not exist.")


def _extract_samples(video: Path, duration: float, target: Path) -> list[tuple[float, Path]]:
    if not shutil.which("ffmpeg"):
        raise RoughCutError("ffmpeg is not installed on the Studio host.")
    # One frame per second is enough to locate a clean 1-3 second region without
    # turning review into a frame-by-frame billable operation.
    sample_times: list[float] = []
    t = 0.0
    while t < max(duration, 0.1):
        sample_times.append(round(t, 2))
        t += 1.0
    if duration > 0.25 and (not sample_times or sample_times[-1] < duration - 0.35):
        sample_times.append(round(max(0.0, duration - 0.2), 2))

    frames: list[tuple[float, Path]] = []
    for index, seconds in enumerate(sample_times):
        path = target / f"frame-{index:02d}.jpg"
        completed = subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y", "-ss", str(seconds), "-i", str(video),
                "-frames:v", "1", "-vf", "scale=512:-2", "-q:v", "3", str(path),
            ],
            capture_output=True,
            timeout=60,
            check=False,
        )
        if completed.returncode == 0 and path.is_file():
            frames.append((seconds, path))
    if len(frames) < 2:
        raise RoughCutError("Could not extract enough frames to analyse this take.")
    return frames


ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "decision", "in_seconds", "out_seconds", "identity_score", "deformation_score",
        "continuity_score", "world_score", "energy_score", "rationale",
    ],
    "properties": {
        "decision": {"type": "string", "enum": ["keep", "maybe", "reject"]},
        "in_seconds": {"type": "number", "minimum": 0},
        "out_seconds": {"type": "number", "minimum": 0},
        "identity_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "deformation_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "continuity_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "world_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "energy_score": {"type": "integer", "minimum": 1, "maximum": 5},
        "rationale": {"type": "string"},
    },
}

ANALYSIS_INSTRUCTIONS = """You are selecting a usable 1-3 second section from one generated video take for an editorial rough cut. The first supplied image is the authoritative production master. Remaining images are chronological samples from the generated take and are labelled with timestamps in the accompanying text.

Judge visible evidence only. Priorities, in order: preserve the same people and identity as the master; avoid face/body/hand deformation; preserve starting orientation and continuity; keep wardrobe and physical state stable; keep the crowd/world credible and independent; then prefer natural energy and an accidental documentary moment. Do not reward spectacle. Do not invent a need to face the stage or camera.

Choose the cleanest continuous window between 1.0 and 3.0 seconds long. Keep the requested range within the supplied video duration. If no clean window exists, return reject. Scores are 5=excellent, 1=unusable. deformation_score is 5 when there is no visible deformation and 1 when deformation is severe. Return concise rationale."""


def _analyse_one(settings: Settings, shot: SceneShotMaster, take: motion_run.RecordedTake) -> ShotEdit:
    if not settings.openai_api_key or not settings.openai_review_model:
        raise RoughCutError("OPENAI_API_KEY and OPENAI_REVIEW_MODEL are required for AI rough-cut analysis.")
    video = motion_run.ensure_silent(take.directory)
    if video is None:
        raise RoughCutError(f"{shot.scene_key}/{shot.name}: no silent Veo video is available.")
    duration = take.duration_seconds
    if duration is None or duration <= 0:
        raise RoughCutError(f"{shot.scene_key}/{shot.name}: video duration is unavailable.")

    with tempfile.TemporaryDirectory(prefix="shirtfaced-rough-cut-") as temp_name:
        frames = _extract_samples(video, duration, Path(temp_name))
        master_path = PROJECT_ROOT / "var" / "assets" / shot.asset.storage_key
        # FilesystemAssetStore may store beneath nested sha directories; if this
        # direct location is unavailable, use the asset's absolute storage key
        # when it already resolved there.
        if not master_path.is_file():
            candidate = Path(shot.asset.storage_key)
            if candidate.is_file():
                master_path = candidate
        if not master_path.is_file():
            raise RoughCutError(f"{shot.scene_key}/{shot.name}: master pixels are unavailable for comparison.")

        content: list[dict[str, Any]] = [
            {
                "type": "input_text",
                "text": (
                    f"Scene {shot.scene_key}; shot {shot.name}; take {take.stamp}; duration {duration:.3f}s. "
                    f"Chronological sample timestamps: {', '.join(f'{time:.2f}s' for time, _ in frames)}."
                ),
            },
            {
                "type": "input_image",
                "image_url": f"data:{shot.asset.mime_type};base64,{base64.b64encode(master_path.read_bytes()).decode()}",
            },
        ]
        for _, frame in frames:
            content.append(
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64.b64encode(frame.read_bytes()).decode()}",
                }
            )

        from openai import OpenAI

        client = OpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=settings.openai_timeout_seconds,
        )
        try:
            response = client.responses.create(
                model=settings.openai_review_model,
                timeout=settings.openai_timeout_seconds,
                instructions=ANALYSIS_INSTRUCTIONS,
                input=[{"role": "user", "content": content}],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "rough_cut_selection",
                        "strict": True,
                        "schema": ANALYSIS_SCHEMA,
                    }
                },
            )
            payload = json.loads(response.output_text)
        except Exception as error:
            raise RoughCutError(f"{shot.scene_key}/{shot.name}: AI analysis failed: {error}") from error

    start = max(0.0, min(float(payload["in_seconds"]), duration - 0.1))
    end = min(duration, float(payload["out_seconds"]))
    if end - start < 1.0:
        end = min(duration, start + 1.0)
    if end - start > 3.0:
        end = start + 3.0
    if end <= start:
        raise RoughCutError(f"{shot.scene_key}/{shot.name}: AI returned an invalid edit range.")

    return ShotEdit(
        shot_id=str(shot.id),
        shot_name=shot.name,
        take_stamp=take.stamp,
        decision=str(payload["decision"]),
        in_seconds=round(start, 3),
        out_seconds=round(end, 3),
        identity_score=int(payload["identity_score"]),
        deformation_score=int(payload["deformation_score"]),
        continuity_score=int(payload["continuity_score"]),
        world_score=int(payload["world_score"]),
        energy_score=int(payload["energy_score"]),
        rationale=str(payload["rationale"]),
    )


def analyse(settings: Settings, shots: list[SceneShotMaster]) -> RoughCutState:
    approved = [shot for shot in sorted(shots, key=lambda row: row.sort_order) if shot.status == "approved"]
    if not approved:
        raise RoughCutError("No approved shot masters are available for this scene.")
    rows = [_analyse_one(settings, shot, _take_for(shot)) for shot in approved]
    return _save(RoughCutState(scene_key=approved[0].scene_key, shots=rows))


def update_shot(
    scene_key: str,
    shot_id: str,
    *,
    decision: str | None = None,
    in_seconds: float | None = None,
    out_seconds: float | None = None,
    take_stamp: str | None = None,
) -> RoughCutState:
    state = load(scene_key)
    row = next((item for item in state.shots if item.shot_id == shot_id), None)
    if row is None:
        raise RoughCutError("That shot has not been analysed yet.")
    if decision is not None:
        if decision not in {"keep", "maybe", "reject"}:
            raise RoughCutError("Decision must be keep, maybe or reject.")
        row.decision = decision
    if in_seconds is not None:
        row.in_seconds = max(0.0, round(in_seconds, 3))
    if out_seconds is not None:
        row.out_seconds = max(0.0, round(out_seconds, 3))
    if row.out_seconds <= row.in_seconds:
        raise RoughCutError("Out time must be after in time.")
    if take_stamp is not None:
        row.take_stamp = take_stamp
    output_path(scene_key).unlink(missing_ok=True)
    return _save(state)


def render(scene_key: str, shots: list[SceneShotMaster]) -> RoughCutState:
    if not shutil.which("ffmpeg"):
        raise RoughCutError("ffmpeg is not installed on the Studio host.")
    state = load(scene_key)
    by_id = {str(shot.id): shot for shot in shots}
    selected = [row for row in state.shots if row.decision == "keep"]
    if not selected:
        raise RoughCutError("No analysed shots are marked keep.")

    root = _root(scene_key)
    root.mkdir(parents=True, exist_ok=True)
    output = output_path(scene_key)
    command: list[str] = ["ffmpeg", "-v", "error", "-y"]
    valid: list[ShotEdit] = []
    for row in selected:
        shot = by_id.get(row.shot_id)
        if shot is None:
            continue
        take = _take_for(shot, row.take_stamp)
        video = motion_run.ensure_silent(take.directory)
        if video is None:
            raise RoughCutError(f"{shot.name}: silent take is unavailable.")
        command += ["-ss", str(row.in_seconds), "-to", str(row.out_seconds), "-i", str(video)]
        valid.append(row)
    if not valid:
        raise RoughCutError("No kept shots could be resolved to videos.")

    filters: list[str] = []
    for index in range(len(valid)):
        filters.append(
            f"[{index}:v]setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[v{index}]"
        )
    concat_inputs = "".join(f"[v{index}]" for index in range(len(valid)))
    filters.append(f"{concat_inputs}concat=n={len(valid)}:v=1:a=0[outv]")
    command += [
        "-filter_complex", ";".join(filters), "-map", "[outv]",
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p", str(output),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=900, check=False)
    if completed.returncode != 0 or not output.is_file():
        detail = (completed.stderr or completed.stdout or "ffmpeg failed").strip().splitlines()
        raise RoughCutError(detail[-1] if detail else "ffmpeg failed to build the rough cut.")
    return _save(state)
