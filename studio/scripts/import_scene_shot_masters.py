#!/usr/bin/env python3
"""Import staged direct scene shot masters into Studio's persistent asset library.

Staging is intentionally disposable. Deploy syncs files under
``transfer/scene-shot-masters/<SCENE>/`` to Oracle, this script ingests their
bytes into the content-addressed Visual Asset Library and records candidate
SceneShotMaster rows, and the staging files may then disappear from Git without
affecting the persistent asset or database row.

Binary uploads are not available through every control surface used to operate
Studio. For those cases the staging directory may contain chunked base64 text
named ``<shot>.<ext>.b64.001``, ``.002`` and so on. The chunks are concatenated
and decoded in memory; the encoded transport is never stored as the asset.
"""

from __future__ import annotations

import argparse
import base64
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.adapters.asset_store import FilesystemAssetStore
from app.config import get_settings
from app.db.session import get_session_factory
from app.domain.enums import VisualAssetSourceType
from app.services import scene_shot_library

SUPPORTED = {".png", ".jpg", ".jpeg", ".webp"}
CHUNK = re.compile(r"^(?P<name>[a-zA-Z0-9_-]+)(?P<ext>\.png|\.jpg|\.jpeg|\.webp)\.b64\.(?P<part>\d+)$")


def staged_payloads(scene_dir: Path):
    """Yield (shot name, bytes) from direct binaries or chunked base64 transport."""
    chunks: dict[tuple[str, str], list[tuple[int, Path]]] = defaultdict(list)
    for path in sorted(scene_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() in SUPPORTED:
            yield path.stem.lower(), path.read_bytes()
            continue
        match = CHUNK.fullmatch(path.name)
        if match:
            chunks[(match.group("name").lower(), match.group("ext").lower())].append(
                (int(match.group("part")), path)
            )

    for (name, _ext), parts in sorted(chunks.items()):
        ordered = [path for _, path in sorted(parts)]
        encoded = "".join(path.read_text(encoding="ascii").strip() for path in ordered)
        try:
            data = base64.b64decode(encoded, validate=True)
        except ValueError as error:
            raise SystemExit(f"Invalid base64 transfer for {scene_dir.name}/{name}: {error}") from error
        yield name, data


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
            for name, data in staged_payloads(scene_dir):
                shot = scene_shot_library.register(
                    session,
                    store,
                    scene_key=scene_key,
                    name=name,
                    data=data,
                    notes="Imported from staged production candidates.",
                    source_type=VisualAssetSourceType.GENERATED,
                )
                print(f"{scene_key}/{shot.name}: {shot.status} asset={shot.asset.sha256[:12]}")
                imported += 1
        session.commit()

    print(f"Imported {imported} direct scene shot master candidate(s).")


if __name__ == "__main__":
    main()
