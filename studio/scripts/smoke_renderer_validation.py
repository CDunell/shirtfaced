#!/usr/bin/env python3
"""Smoke the deployed renderer validation contract without spending money."""

from __future__ import annotations

import argparse
import json
import urllib.request


def get_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=15) as response:
        return json.loads(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    args = parser.parse_args()
    base = args.base.rstrip("/")

    manifest = get_json(f"{base}/api/renderer/validation")
    scenes = manifest.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 5:
        raise SystemExit("renderer validation manifest must expose exactly five benchmark scenes")
    if manifest.get("billable_generation_exposed") is not False:
        raise SystemExit("validation deployment must not expose unguarded billable generation")

    pub = get_json(f"{base}/api/renderer/validation/W01-P28")
    instant = str(pub.get("exact_instant", "")).lower()
    if "stands on the pool table" not in instant or "cue horizontal overhead" not in instant:
        raise SystemExit("pub benchmark lost locked hero geometry")

    print("renderer validation smoke: ok")


if __name__ == "__main__":
    main()
