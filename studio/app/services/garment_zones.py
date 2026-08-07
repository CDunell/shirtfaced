"""Finding the garment in a product shot, and the print's zone on it.

An earlier pass measured print placement inside a fixed box near the middle of
the image. That is only valid for one kind of photograph. The corpus actually
holds at least four: flat lays with the garment alone, worn close crops where
the torso fills the frame, worn full-body shots where the garment is a fraction
of the picture, and product-only shots of caps. A fixed box lands on the shirt
in the first, the midriff in the third, and nothing meaningful in the fourth --
so any placement statistic drawn from it is measuring the photographer's
framing as much as the designer's choice.

This locates the garment first, then reports the print's position and size
**relative to that garment**, which is the only frame in which "left breast"
and "full front" mean anything. Shots where the garment cannot be found are
reported as such rather than measured anyway.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
from PIL import Image

WORK_SIZE = 320

# Distance in 0-255 RGB. Below this a pixel matches its reference colour.
BACKGROUND_TOLERANCE = 42.0
GARMENT_TOLERANCE = 58.0
# Ink must clear the garment by more than fabric shading does.
PRINT_TOLERANCE = 66.0

Zone = Literal[
    "left breast",
    "right breast",
    "centre chest",
    "full front",
    "upper front",
    "lower front",
    "across front",
    "unplaced",
]


@dataclass(frozen=True)
class GarmentReading:
    """What was found, in garment-relative terms."""

    found: bool
    reason: str = ""
    # Garment box within the image, as fractions.
    garment_box: tuple[float, float, float, float] = (0, 0, 0, 0)
    garment_rgb: tuple[int, int, int] = (0, 0, 0)
    # Print box within the *garment*, as fractions.
    print_box: tuple[float, float, float, float] = (0, 0, 0, 0)
    # Print area as a share of garment area -- the honest version of "coverage".
    print_share: float = 0.0
    zone: Zone = "unplaced"
    size_class: str = ""
    shot_type: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "found": self.found,
            "reason": self.reason,
            "garment_box": [round(v, 3) for v in self.garment_box],
            "garment_rgb": list(self.garment_rgb),
            "print_box": [round(v, 3) for v in self.print_box],
            "print_share": round(self.print_share, 4),
            "zone": self.zone,
            "size_class": self.size_class,
            "shot_type": self.shot_type,
        }


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    rows = np.nonzero(mask.any(axis=1))[0]
    cols = np.nonzero(mask.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        return None
    return int(cols[0]), int(rows[0]), int(cols[-1]) + 1, int(rows[-1]) + 1


def _zone_of(cx: float, cy: float, width: float, height: float) -> Zone:
    """Name the print's position on the garment.

    Thresholds follow how the trade actually talks about placement: a breast
    hit is small and off-centre in the upper third; a full front is most of the
    garment's width and height.
    """
    if width >= 0.55 and height >= 0.45:
        return "full front"
    if width >= 0.55:
        return "across front"
    if width <= 0.30 and cy <= 0.42:
        # Viewer's left is the wearer's right, but placement is named as the
        # viewer sees it on a product shot, which is how briefs are written.
        if cx <= 0.42:
            return "left breast"
        if cx >= 0.58:
            return "right breast"
        return "centre chest"
    if cy <= 0.38:
        return "upper front"
    if cy >= 0.62:
        return "lower front"
    return "centre chest"


def _size_class(share: float) -> str:
    """Size bands, named the way a print brief names them."""
    if share < 0.02:
        return "small (pocket / breast scale)"
    if share < 0.08:
        return "medium (emblem scale)"
    if share < 0.25:
        return "large (hero scale)"
    return "oversized (jumbo / all-over)"


def read(image_path: Path) -> GarmentReading:
    """Locate the garment and place the print on it."""
    try:
        image = Image.open(image_path).convert("RGB").resize((WORK_SIZE, WORK_SIZE), Image.LANCZOS)
    except Exception as error:  # noqa: BLE001
        return GarmentReading(False, f"unreadable: {error}")

    pixels = np.asarray(image, dtype=np.float32)

    # Background from the corners. Product shots are shot on a sweep, a wall or
    # a plain floor, so the corners are background in every shot type here.
    patch = WORK_SIZE // 8
    corners = np.concatenate(
        [
            pixels[:patch, :patch].reshape(-1, 3),
            pixels[:patch, -patch:].reshape(-1, 3),
            pixels[-patch:, :patch].reshape(-1, 3),
            pixels[-patch:, -patch:].reshape(-1, 3),
        ]
    )
    background = np.median(corners, axis=0)
    foreground = np.sqrt(((pixels - background) ** 2).sum(axis=2)) > BACKGROUND_TOLERANCE

    if foreground.mean() < 0.05:
        return GarmentReading(False, "no subject stands clear of the background")
    if foreground.mean() > 0.97:
        return GarmentReading(False, "background is not separable — busy or full-bleed scene")

    box = _bbox(foreground)
    if box is None:
        return GarmentReading(False, "no foreground found")
    fx0, fy0, fx1, fy1 = box

    # The garment is the dominant colour across the subject's upper body. Taking
    # it from the upper-middle avoids trousers, which are often a different
    # colour and would otherwise win the vote in a full-body shot.
    subject_h = fy1 - fy0
    upper = pixels[fy0 + int(subject_h * 0.12) : fy0 + int(subject_h * 0.55), fx0:fx1]
    if upper.size == 0:
        return GarmentReading(False, "subject too small to sample")
    garment = np.median(upper.reshape(-1, 3), axis=0)

    garment_mask = np.zeros(foreground.shape, dtype=bool)
    region = np.sqrt(((pixels - garment) ** 2).sum(axis=2)) < GARMENT_TOLERANCE
    garment_mask[fy0:fy1, fx0:fx1] = region[fy0:fy1, fx0:fx1]
    garment_mask &= foreground

    if garment_mask.mean() < 0.02:
        return GarmentReading(False, "garment could not be separated from the subject")

    gbox = _bbox(garment_mask)
    if gbox is None:
        return GarmentReading(False, "garment has no extent")
    gx0, gy0, gx1, gy1 = gbox
    gw, gh = gx1 - gx0, gy1 - gy0
    if gw < 20 or gh < 20:
        return GarmentReading(False, "garment too small in frame to measure")

    # Shot type, for weighting later: a garment filling the frame is a flat lay
    # or close crop; a small one is a full-body shot where the print is only a
    # few pixels and any measurement of it is coarse.
    garment_share_of_frame = (gw * gh) / (WORK_SIZE * WORK_SIZE)
    if garment_share_of_frame > 0.35:
        shot_type = "flat or close crop"
    elif garment_share_of_frame > 0.12:
        shot_type = "worn, garment prominent"
    else:
        shot_type = "worn, garment small in frame"

    # The print: inside the garment box, far enough from the garment colour, and
    # still part of the garment silhouette rather than skin or background.
    inside = pixels[gy0:gy1, gx0:gx1]
    distance = np.sqrt(((inside - garment) ** 2).sum(axis=2))
    on_garment = garment_mask[gy0:gy1, gx0:gx1] | (distance < PRINT_TOLERANCE * 2.6)
    print_mask = (distance > PRINT_TOLERANCE) & on_garment

    share = float(print_mask.sum() / max(int(on_garment.sum()), 1))
    if share < 0.004:
        return GarmentReading(
            True,
            "no print detected on the garment",
            (gx0 / WORK_SIZE, gy0 / WORK_SIZE, gx1 / WORK_SIZE, gy1 / WORK_SIZE),
            tuple(int(v) for v in garment),  # type: ignore[arg-type]
            shot_type=shot_type,
        )

    pbox = _bbox(print_mask)
    if pbox is None:
        return GarmentReading(False, "print mask has no extent")
    px0, py0, px1, py1 = pbox

    rel = (px0 / gw, py0 / gh, px1 / gw, py1 / gh)
    cx = (rel[0] + rel[2]) / 2
    cy = (rel[1] + rel[3]) / 2

    return GarmentReading(
        found=True,
        garment_box=(gx0 / WORK_SIZE, gy0 / WORK_SIZE, gx1 / WORK_SIZE, gy1 / WORK_SIZE),
        garment_rgb=tuple(int(v) for v in garment),  # type: ignore[arg-type]
        print_box=rel,
        print_share=share,
        zone=_zone_of(cx, cy, rel[2] - rel[0], rel[3] - rel[1]),
        size_class=_size_class(share),
        shot_type=shot_type,
    )
