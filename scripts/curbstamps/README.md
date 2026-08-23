# Curb Stamps centreline converter

Converts supplied transparent raster creature art into editable SVG centreline
paths. The output uses the locked `1200 500` viewBox, `4` unit stroke, round
caps and round joins. This equals a 0.8 mm line at 240 mm print width.

The converter does not generate character art. It only traces geometry already
present in the source alpha channel.

When a supplied legacy lockup contains the creature above old lettering, first
extract the complete creature run instead of masking the wordmark in place:

```bash
python scripts/curbstamps/extract_creature_sources.py \
  path/to/legacy-lockups curbstamps-site/public/creatures/masters/sources
```

```bash
python scripts/curbstamps/vectorize_creature.py \
  curbstamps-site/public/creatures/blip-icon.png \
  --slug blip --output curbstamps-site/public/creatures/masters
```

## Locked creature wordmarks

Run `python scripts/curbstamps/build_creature_lockups.py` after adding or
repairing a creature master. It creates the light and dark SVG print lockups
and refreshes the legacy PNG assets used by downstream integrations.

- Baloo 2 Bold (700) for both lines.
- Creature names use one fixed size; three-letter names receive restrained
  tracking, while four- and five-letter names use normal tracking.
- `CURB STAMPS` is a smaller fixed signature with fixed tracking.
- Names are never stretched or resized to match the brand-line width.
- All lettering is converted to vector outlines in the SVG output.
