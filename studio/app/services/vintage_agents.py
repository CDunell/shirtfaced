"""Control long-running vintage evidence collectors on the Studio host."""

from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
from pathlib import Path
from typing import Any

AGENT_COUNT = 4
STATE_ROOT = Path(
    os.environ.get(
        "VINTAGE_AGENT_ROOT",
        "/home/ubuntu/shirtfaced-research/vintage-agents",
    )
)
SCRIPT = Path(
    os.environ.get(
        "VINTAGE_AGENT_SCRIPT",
        "/home/ubuntu/shirtfaced-studio/worker_scripts/vintage-agent.mjs",
    )
)
EVIDENCE_ROOT = Path(
    os.environ.get(
        "VINTAGE_EVIDENCE_DOC_ROOT",
        "/home/ubuntu/shirtfaced-site/docs/research/vintage-market-evidence",
    )
)
IMAGE_ROOT = Path(
    os.environ.get(
        "VINTAGE_EVIDENCE_ROOT",
        "/home/ubuntu/shirtfaced-research/vintage-ebay-images",
    )
)
OUTBOX_ROOT = Path(
    os.environ.get(
        "VINTAGE_AGENT_OUTBOX",
        "/home/ubuntu/shirtfaced-research/vintage-agent-outbox",
    )
)


def _dir(agent_id: int) -> Path:
    if agent_id < 1 or agent_id > AGENT_COUNT:
        raise ValueError("invalid agent id")
    return STATE_ROOT / f"agent-{agent_id}"


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def status(agent_id: int) -> dict[str, Any]:
    d = _dir(agent_id)
    enabled = (d / "enabled").exists()
    state = _read(d / "state.json", {})
    pid_data = _read(d / "pid.json", {})
    pid = pid_data.get("pid") if isinstance(pid_data, dict) else None
    running = _pid_alive(pid)
    return {
        "id": agent_id,
        "enabled": enabled,
        "running": running,
        "pid": pid if running else None,
        "status": state.get("status", "idle" if not enabled else "starting"),
        "batch_progress": state.get("batch_progress", 0),
        "batch_target": state.get("batch_target", 15),
        "completed_batches": state.get("completed_batches", 0),
        "completed_records": state.get("completed_records", 0),
        "last_listing_id": state.get("last_listing_id"),
        "last_error": state.get("last_error"),
        "updated_at": state.get("updated_at"),
    }


def all_status() -> list[dict[str, Any]]:
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    return [status(i) for i in range(1, AGENT_COUNT + 1)]


def _start(agent_id: int) -> None:
    d = _dir(agent_id)
    d.mkdir(parents=True, exist_ok=True)
    OUTBOX_ROOT.mkdir(parents=True, exist_ok=True)
    IMAGE_ROOT.mkdir(parents=True, exist_ok=True)
    (d / "enabled").touch()
    current = status(agent_id)
    if current["running"]:
        return
    log = (d / "agent.log").open("ab", buffering=0)
    env = os.environ.copy()
    env.update(
        {
            "VINTAGE_AGENT_ID": str(agent_id),
            "VINTAGE_AGENT_COUNT": str(AGENT_COUNT),
            "VINTAGE_AGENT_STATE": str(d),
            "VINTAGE_AGENT_OUTBOX": str(OUTBOX_ROOT),
            "VINTAGE_IMAGE_ROOT": str(IMAGE_ROOT),
            "VINTAGE_EVIDENCE_DOC_ROOT": str(EVIDENCE_ROOT),
            "VINTAGE_TARGET": "15",
        }
    )
    proc = subprocess.Popen(
        ["node", str(SCRIPT)],
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=str(SCRIPT.parent),
        start_new_session=True,
    )
    (d / "pid.json").write_text(json.dumps({"pid": proc.pid}), encoding="utf-8")


def _stop(agent_id: int) -> None:
    d = _dir(agent_id)
    (d / "enabled").unlink(missing_ok=True)
    pid_data = _read(d / "pid.json", {})
    pid = pid_data.get("pid") if isinstance(pid_data, dict) else None
    # Narrowed to int deliberately: pid comes off an untyped json dict, and a
    # string or a null reaching killpg is a TypeError at the worst moment.
    if isinstance(pid, int) and _pid_alive(pid):
        with contextlib.suppress(OSError):
            os.killpg(pid, signal.SIGTERM)


def set_enabled(agent_id: int, enabled: bool) -> dict[str, Any]:
    _dir(agent_id)
    if enabled:
        _start(agent_id)
    else:
        _stop(agent_id)
    return status(agent_id)
