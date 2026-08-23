#!/usr/bin/env python3
"""Build the locked CURB STAMPS creature + wordmark SVG assets."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont


ROOT = Path(__file__).resolve().parents[2]
MASTERS = ROOT / "curbstamps-site/public/creatures/masters"
OUTPUT = ROOT / "curbstamps-site/public/creatures/lockups"
FONT = Path(__file__).resolve().parent / "fonts/Baloo2[wght].ttf"

CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 550
NAME_SIZE = 104
NAME_BASELINE = 460
SHORT_NAME_TRACKING = 13
BRAND_SIZE = 29
BRAND_BASELINE = 515
BRAND_TRACKING = 11
CREATURE_STROKE_WIDTH = 5


def outlined_text(font: TTFont, text: str, size: float, baseline: float, tracking: float) -> str:
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upm = font["head"].unitsPerEm
    scale = size / upm
    names = [cmap[ord(char)] for char in text]
    advances = [hmtx[glyph][0] * scale for glyph in names]
    total = sum(advances) + tracking * max(0, len(text) - 1)
    cursor = (CANVAS_WIDTH - total) / 2
    paths: list[str] = []
    for glyph_name, advance in zip(names, advances):
        pen = SVGPathPen(glyphs)
        transformed = TransformPen(pen, (scale, 0, 0, -scale, cursor, baseline))
        glyphs[glyph_name].draw(transformed)
        commands = pen.getCommands()
        if commands:
            paths.append(f'    <path d="{commands}"/>')
        cursor += advance + tracking
    return "\n".join(paths)


def creature_group(master: Path, colour: str) -> str:
    svg = master.read_text()
    match = re.search(r"(<g\b.*?</g>)", svg, flags=re.DOTALL)
    if not match:
        raise ValueError(f"No creature group in {master}")
    group = match.group(1).replace('stroke="currentColor"', f'stroke="{colour}"')
    return re.sub(r'stroke-width="[^"]+"', f'stroke-width="{CREATURE_STROKE_WIDTH}"', group)


def build_one(font: TTFont, master: Path, colour: str, suffix: str) -> Path:
    slug = master.stem
    name = slug.upper()
    name_tracking = SHORT_NAME_TRACKING if len(name) == 3 else 0
    name_paths = outlined_text(font, name, NAME_SIZE, NAME_BASELINE, name_tracking)
    brand_paths = outlined_text(font, "CURB STAMPS", BRAND_SIZE, BRAND_BASELINE, BRAND_TRACKING)
    group = creature_group(master, colour)
    output = OUTPUT / f"{slug}-{suffix}.svg"
    output.write_text(
        f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}">
  <g fill="none">
{group}
  </g>
  <g fill="{colour}">
{name_paths}
{brand_paths}
  </g>
</svg>
'''
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-png", action="store_true", help="Only build SVG lockups")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    font = instantiateVariableFont(TTFont(FONT), {"wght": 700}, inplace=True)
    masters = sorted(p for p in MASTERS.glob("*.svg") if not p.name.endswith("-qa-vector.svg"))
    for master in masters:
        build_one(font, master, "#fffaf0", "light")
        build_one(font, master, "#1c1a17", "dark")
    if not args.skip_png:
        subprocess.run(
            ["node", str(Path(__file__).with_name("render_creature_assets.mjs"))],
            cwd=ROOT,
            check=True,
        )
    print(f"Built {len(masters)} creature lockups in {OUTPUT}")


if __name__ == "__main__":
    main()
