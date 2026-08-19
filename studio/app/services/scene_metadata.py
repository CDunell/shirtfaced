"""Small display metadata for scene workspaces.

Scene production UI needs a stable human title and one-line description without
parsing historical production notes. A sibling ``<SCENE>.scene.json`` file owns
that display copy; persisted Shot metadata remains the fallback for older scenes.
"""

from __future__ import annotations

import json

from app.config import get_settings


def configured(scene_key: str) -> tuple[str | None, str | None]:
    worlds = get_settings().worlds_root_resolved
    filename = f"{scene_key}.scene.json"
    for shots in sorted(worlds.glob("*/shots")):
        path = shots / filename
        if not path.is_file():
            continue
        try:
            body = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None, None
        title = str(body.get("title") or "").strip() or None
        description = str(body.get("description") or "").strip() or None
        return title, description
    return None, None
