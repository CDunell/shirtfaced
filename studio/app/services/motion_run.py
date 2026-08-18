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
