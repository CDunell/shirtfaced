#!/usr/bin/env python3
"""Import staged direct scene shot masters into Studio's persistent asset library.

Staging is intentionally disposable. Deploy syncs files under
``transfer/scene-shot-masters/<SCENE>/`` to Oracle, this script ingests their
bytes into the content-addressed Visual Asset Library and records candidate
SceneShotMaster rows, and the staging files may then disappear from Git without
affecting the persistent asset or database row.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.adapters.asset_store import FilesystemAssetStore
from app.config import get_settings
from app.db.session import get_session_factory
from app.domain.enums import VisualAssetSourceType
from app.services import scene_shot_library

SUPPORTED = {".png", ".jpg", ".jpeg", ".webp"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "root",
        nargs="?",
        default=str(ROOT / "transfer" / "scene-shot-masters"),
        help="Directory containing one subdirectory per scene.",
    )
    args = parser.parse_args()

    staging = Path(args.root).resolve()
    if not staging.is_dir():
        print(f"No staged scene shot masters at {staging}; skipping.")
        return

    store = FilesystemAssetStore(get_settings().assets_root_resolved)
    factory = get_session_factory()
    imported = 0

    with factory() as session:
        for scene_dir in sorted(path for path in staging.iterdir() if path.is_dir()):
            scene_key = scene_dir.name.strip().upper()
            for path in sorted(scene_dir.iterdir()):
                if not path.is_file() or path.suffix.lower() not in SUPPORTED:
                    continue
                name = path.stem.lower()
                shot = scene_shot_library.register(
                    session,
                    store,
                    scene_key=scene_key,
                    name=name,
                    data=path.read_bytes(),
                    notes="Imported from staged approved production candidates.",
                    source_type=VisualAssetSourceType.GENERATED,
                )
                print(f"{scene_key}/{shot.name}: {shot.status} asset={shot.asset.sha256[:12]}")
                imported += 1
        session.commit()

    print(f"Imported {imported} direct scene shot master candidate(s).")


if __name__ == "__main__":
    main()
