"""Five-scene Google renderer validation harness.

This module prepares deterministic, auditable scene packages and exposes the manual
gates. Billable rendering is enabled only when a Gemini key is configured; no key
means planning/validation only.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BenchmarkScene:
    id: str
    title: str
    purpose: str
    hero: str
    exact_instant: str
    required_refs: tuple[str, ...]
    still_gate: tuple[str, ...]
    motion: str


def _load(world_root: Path) -> tuple[BenchmarkScene, ...]:
    """Every world's benchmark scenes, read rather than compiled in.

    These five used to be a tuple in this file, carrying the pub's prompt text
    -- Damo, the pool table, the cue, 11:05pm -- inside ``app/``. That makes the
    engine know one world. A scene is configuration, so it lives with its world:

        worlds/<world>/renderer-benchmarks.json

    Missing files are not an error. A world without benchmarks simply has none,
    and a deployment that has not synced them yet should serve an empty harness
    rather than fail to import.
    """
    found: list[BenchmarkScene] = []
    for path in sorted(world_root.glob("*/renderer-benchmarks.json")):
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("renderer benchmarks unreadable: %s", path)
            continue
        for scene in parsed.get("scenes", []):
            found.append(
                BenchmarkScene(
                    id=scene["id"],
                    title=scene["title"],
                    purpose=scene["purpose"],
                    hero=scene["hero"],
                    exact_instant=scene["exact_instant"],
                    required_refs=tuple(scene["required_refs"]),
                    still_gate=tuple(scene["still_gate"]),
                    motion=scene["motion"],
                )
            )
    return tuple(found)


@lru_cache(maxsize=1)
def scenes() -> tuple[BenchmarkScene, ...]:
    """Cached, because a harness request should not re-read five files."""
    return _load(get_settings().worlds_root_resolved)


def harness_manifest(
    *, google_enabled: bool, image_model: str, video_model: str
) -> dict[str, object]:
    return {
        "version": "1.0",
        "mode": "live" if google_enabled else "planning-only",
        "models": {"image": image_model, "video": video_model},
        "manual_gates": [
            "canon lock for new facts",
            "seed still approval",
            "final video/performance approval",
            "continuity promotion",
        ],
        "automated_stages": [
            "canon/reference resolution",
            "seed prompt package",
            "still QC checklist",
            "motion-only I2V prompt",
            "failure classification",
            "attempt lineage",
            "continuity output package",
        ],
        "scenes": [asdict(scene) for scene in scenes()],
    }


def scene_package(scene_id: str) -> dict[str, object]:
    scene = next((item for item in scenes() if item.id == scene_id), None)
    if scene is None:
        raise KeyError(scene_id)
    return {
        **asdict(scene),
        "authority_order": [
            "scene/world canon",
            "canonical character references",
            "scene appearance state",
            "generator interpretation",
        ],
        "seed_instruction": (
            "Use SHIRTFACED Seed Image Recipe. Preserve locked facts and referenced "
            "identities. Incidental environmental detail is allowed when it remains "
            "background texture."
        ),
        "manual_stop_after_seed": True,
        "video_mode": "first-frame-image-to-video",
        "video_prompt_rule": (
            "Describe only change through time; do not redescribe identity/location/"
            "style already carried by the approved seed."
        ),
    }
