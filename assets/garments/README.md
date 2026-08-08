# Garment files

Each file carries a garment outline and its print zones, in real millimetres.
Zone ids match the engine's placement keys, so `zone-centre_chest` is the
`centre_chest` placement. A zone split per side carries a `_left` / `_right`
suffix and resolves to the same placement.

Check one before it goes in:

    python studio/scripts/check_garment.py assets/garments/<file> --render out.png

The checker verifies the ids resolve, that the dimensions are sane against the
defaults in `placements.py`, and that a left-chest zone is on the wearer's left
rather than mirrored. It renders too, because a zone can measure correctly and
sit in the wrong place.

## Held

| File | State |
|---|---|
| `garment_tee_crew_front.svg` | good |
| `garment_tee_vneck_front.svg` | good |
| `garment_tee_vneck_back.svg` | good |
| `garment_tee_longsleeve_front.svg` | good |
| `garment_tee_longsleeve_back.svg` | good |
| `garment_tee_oversized_front.svg` | good |
| `garment_tee_oversized_back.svg` | good |
| `garment_crop_front.svg` | good |
| `garment_tank_muscle_front.svg` | good — redrawn with a proper deep armhole |
| `garment_tee_crew_back.svg` | good |

## Missing

The headwear set. Caps, bucket hat and beanie were drawn once and sent back:
the crowns came out as triangles rather than domes, they were drawn at roughly
1.7x life size, `zone-cap_side` held both sides in one path, and none carried
`zone-cap_back`.

## Zones larger than the defaults

Several files declare zones bigger than `placements.py` allows for a standard
adult tee. That is expected, and the checker reports it as a note rather than a
failure. An oversized cut genuinely has more printable area, and the composer
sizes a design to the garment's own zone rather than to the table. The table is
a default for a standard tee, not a ceiling for every garment.
