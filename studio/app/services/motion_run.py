"""Running the Veo leg from Studio, by invoking the runner that already exists.

The video stage used to require a git commit. A trigger file was pushed, a
GitHub Action woke up, SSHed into this box, ran ``run_pub_coverage_veo.py``
sitting right here, and copied the result back out. That made sense once: the
Action was the only place holding the Gemini key and the only place with ffmpeg.

Neither is true. The key is in this box's ``.env`` -- Studio makes paid Gemini
calls for every contact sheet and every panel extraction -- and ffmpeg was
installed on 18 August 2026. Video was the only stage detouring through a
commit, to a machine whose sole action was to call back to the machine it
started from.

So this invokes the runner directly. It does not reimplement it. That
distinction is the whole reason the last attempt at this was deleted: a second
implementation drifted from the proven one and quietly skipped the audio strip
§20 requires. The runner resolves the seed through ``resolve_veo_seed``, reads
the scene's motion direction from its world, generates, strips, probes and
checksums -- and it is the same code the workflow runs, so the two cannot
disagree.

The workflow stays. A commit is still a legitimate way to ask for a take, and it
uploads an artifact this does not.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.config import PROJECT_ROOT
from app.domain.errors import StudioError

logger = logging.getLogger(__name__)

RUNNER = PROJECT_ROOT / "scripts" / "run_pub_coverage_veo.py"

# Veo Lite takes a minute or two for six to eight seconds. Generous, because the
# alternative to waiting is a half-written result directory.
TIMEOUT_SECONDS = 900


class MotionRunFailed(StudioError):
    """The runner refused or failed, with its own message rather than a code."""


@dataclass(frozen=True)
class MotionResult:
    """Where the take landed, and what it is."""

    directory: Path
    manifest: dict[str, Any]

    @property
    def silent_video(self) -> Path:
        return self.directory / "video-1.mp4"

    @property
    def raw_video(self) -> Path:
        return self.directory / "video-generated.mp4"

    @property
    def playable(self) -> Path:
        """The stripped clip when there is one, otherwise the raw generation."""
        return self.silent_video if self.silent_video.is_file() else self.raw_video


def animate(scene_key: str, shot: str) -> MotionResult:
    """Generate one take for an approved shot, or raise with the reason.

    Every gate is the runner's: approved for motion, cut from the master
    approved now, from a sheet not superseded, and the file still hashing to
    what the row says. None of that is duplicated here, because duplicating it
    is how it drifts.
    """
    if not RUNNER.is_file():  # pragma: no cover - shipped with the repository
        raise MotionRunFailed(f"the runner is missing: {RUNNER}")

    completed = subprocess.run(
        [sys.executable, str(RUNNER), "--scene", scene_key, "--shot", shot],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        cwd=str(PROJECT_ROOT),
        check=False,
    )
    if completed.returncode != 0:
        # The runner's refusals are written for a person -- "not approved for
        # Veo. Cutting a frame is not approving it." -- so they are passed
        # through rather than replaced with a status code.
        detail = (completed.stderr or completed.stdout or "").strip().splitlines()
        raise MotionRunFailed(detail[-1] if detail else "the runner failed without a message")

    directory = next(
        (
            Path(line.removeprefix("RESULT_DIR=").strip())
            for line in reversed(completed.stdout.splitlines())
            if line.startswith("RESULT_DIR=")
        ),
        None,
    )
    if directory is None or not directory.is_dir():
        raise MotionRunFailed("the runner reported no result directory")

    manifest_path = directory / "manifest.json"
    manifest: dict[str, Any] = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    )
    logger.info("veo take for %s/%s landed in %s", scene_key, shot, directory)
    return MotionResult(directory=directory, manifest=manifest)


@dataclass(frozen=True)
class RecordedTake:
    """One take already on disk, whether this process made it or not."""

    stamp: str
    directory: Path
    silent: Path | None
    duration_seconds: float | None
    width: int | None
    height: int | None

    @property
    def has_silent(self) -> bool:
        return self.silent is not None


def _probe_json(directory: Path) -> dict[str, Any]:
    path = directory / "probe.json"
    if not path.is_file():
        return {}
    try:
        parsed: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return parsed
    except (OSError, json.JSONDecodeError):  # pragma: no cover - written by ffprobe
        return {}


def ensure_silent(directory: Path) -> Path | None:
    """The stripped clip, produced now if the take predates in-runner stripping.

    Takes generated through the workflow before 18 August 2026 were stripped on
    the runner rather than on this box, so the silent file lives only inside a
    GitHub artifact and the directory holds the raw generation alone. §20 is not
    a preference -- generated audio must not reach the edit -- so rather than
    serve the raw file, the strip happens here on demand and is kept.
    """
    silent = directory / "video-1.mp4"
    if silent.is_file():
        return silent
    raw = directory / "video-generated.mp4"
    if not raw.is_file() or not shutil.which("ffmpeg"):
        return None

    subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw), "-map", "0:v:0", "-c:v", "copy", "-an", str(silent)],
        check=True,
        capture_output=True,
        timeout=300,
    )
    if shutil.which("ffprobe") and not (directory / "probe.json").is_file():
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=width,height,r_frame_rate",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(silent),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        ).stdout
        (directory / "probe.json").write_text(probe, encoding="utf-8")
    return silent


def takes_for(scene_key: str, shot: str) -> list[RecordedTake]:
    """Every take on disk for this shot, newest first.

    Read from the filesystem rather than a table. A take is a directory the
    runner wrote, and both callers -- the bench and the workflow -- write to the
    same place, so the disk is the one view that sees all of them.
    """
    root = PROJECT_ROOT / "var" / "renderer-validation" / scene_key
    found: list[RecordedTake] = []
    for directory in sorted(root.glob(f"*-coverage-{shot}"), reverse=True):
        if not directory.is_dir():
            continue
        silent = directory / "video-1.mp4"
        probe = _probe_json(directory)
        stream = (probe.get("streams") or [{}])[0]
        duration = (probe.get("format") or {}).get("duration")
        found.append(
            RecordedTake(
                stamp=directory.name.split("-coverage-")[0],
                directory=directory,
                silent=silent if silent.is_file() else None,
                duration_seconds=None if duration is None else float(duration),
                width=stream.get("width"),
                height=stream.get("height"),
            )
        )
    return found
