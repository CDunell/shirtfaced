# Curb Stamps centreline converter

Converts supplied transparent raster creature art into editable SVG centreline
paths. The output uses the locked `1200 500` viewBox, `4` unit stroke, round
caps and round joins. This equals a 0.8 mm line at 240 mm print width.

The converter does not generate character art. It only traces geometry already
present in the source alpha channel.

```bash
python scripts/curbstamps/vectorize_creature.py \
  curbstamps-site/public/creatures/blip-icon.png \
  --slug blip --output curbstamps-site/public/creatures/masters
```
