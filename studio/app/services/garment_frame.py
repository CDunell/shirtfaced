"""Finding the garment in a photograph, and refusing when it cannot be found.

Everything the engine learns -- coverage, zone, band structure, and therefore
every cluster and every template -- is measured inside a region of a photograph
that is supposed to be garment. The first version assumed that region was
always in the same place: a fixed box of pixel coordinates applied to every
image in the corpus.

That assumption is wrong often enough to poison the corpus. The corpus holds
flat lays, close crops, worn full-body shots and product-only renders, and a
fixed box lands on the garment in the first two and on a model's face, hair or
the floor in the others. A small left-breast print measured as 93.8% "full
front" this way, which is not a small error but a measurement of the wrong
thing entirely.

So the box is derived per image, relative to the garment actually found, and
images where the garment cannot be located confidently are refused rather than
guessed at. This is the "restrict to measurable frames" path in
DESIGN_ENGINE_ADAPTATION.md section 7 -- honest now, with segmentation added
later per shot type once it has earned the promotion by agreeing with this.

Refusal fails closed: an exception while deciding whether the frame is
measurable resolves to "not measurable". A frame we could not assess is not a
frame we may measure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

# Working resolution. Large enough to keep a left-breast print several pixels
# across, small enough that mining the whole corpus stays cheap.
ANALYSIS_SIZE = 256

# --- Gate thresholds. Every one is a share or a ratio, never a pixel count, so
# the same numbers hold whatever resolution an image arrives at. ---

# Width of the border ring sampled to estimate the backdrop, as a share of the
# shorter side.
BORDER_RATIO = 0.06

# The backdrop must be near-uniform for foreground separation to mean anything.
# A busy ring is a lifestyle shot -- a street, a beach, a room -- where the
# subject cannot be separated by colour distance at all.
MAX_BACKGROUND_SPREAD = 34.0

# How far from the backdrop colour a pixel must sit to count as subject.
FOREGROUND_DISTANCE = 42.0

# A subject filling almost the whole frame has been cropped into, so its true
# extent is unknown and any proportion measured against it is a guess.
MAX_SUBJECT_AREA = 0.92
MIN_SUBJECT_AREA = 0.04

# Share of a frame edge the subject may occupy before it counts as running off
# that edge.
EDGE_CONTACT_RATIO = 0.55

# Visible skin inside the garment box means a person is wearing it, and the
# print sits on a curved, shadowed, partly turned surface.
MAX_SKIN_SHARE = 0.12

# A standing person is far taller than they are wide; a garment photographed
# flat is close to square, and a cap is wider than it is tall. Skin alone does
# not catch a model in long sleeves, dark clothing or profile -- several such
# shots passed as flat lays, and their torso fraction then landed on the
# model's legs. Shape catches what colour cannot.
MAX_SUBJECT_ASPECT = 1.65

# --- The torso, as a proportion of the garment found rather than of the image.
# A tee photographed flat is roughly shoulders at the top, hem at the bottom;
# the printable chest area sits inside those bounds by these fractions. ---
TORSO_TOP = 0.20
TORSO_BOTTOM = 0.78
TORSO_LEFT = 0.22
TORSO_RIGHT = 0.78


@dataclass(frozen=True)
class GarmentFrame:
    """Where the garment is, and whether we are willing to measure it."""

    measurable: bool
    # Reasons the frame was refused. Empty when measurable. Durable strings so
    # a corpus run can GROUP BY them and show which doubt is doing the work.
    reasons: tuple[str, ...] = ()
    # Garment bounding box in analysis-space, as (top, bottom, left, right).
    bounds: tuple[int, int, int, int] | None = None
    # The printable torso region inside those bounds, same convention.
    torso: tuple[int, int, int, int] | None = None
    # Share of the frame the garment occupies -- useful for ranking which of a
    # product's images is the best one to measure.
    subject_area: float = 0.0
    shot_type: str = "unknown"
    diagnostics: dict[str, float] = field(default_factory=dict)

    def torso_slices(self) -> tuple[slice, slice]:
        """The torso as numpy slices, for indexing an analysis-space array."""
        if self.torso is None:
            raise ValueError("frame is not measurable; no torso to slice")
        top, bottom, left, right = self.torso
        return slice(top, bottom), slice(left, right)


# Print inks that read as skin under the plain RGB rule -- gold, orange, tan --
# are far more saturated than skin ever is. Without this bound a black tee with
# an orange flame graphic is refused as a worn shot, which throws away exactly
# the graphic-rich flat lays the corpus is for.
MAX_SKIN_SATURATION = 0.58
MIN_SKIN_SATURATION = 0.10


def _skin_share(rgb: np.ndarray) -> float:
    """Share of pixels that look like human skin rather than warm ink.

    The usual RGB rule -- bright, red-dominant, red leading green -- catches
    skin but also catches gold and orange print. Skin is additionally
    *desaturated*: a face sits well below the saturation of any ink chosen to
    be seen from across a room. Bounding saturation separates the two.
    """
    pixels = rgb.astype(np.float32)
    red, green, blue = pixels[..., 0], pixels[..., 1], pixels[..., 2]

    high = pixels.max(axis=2)
    low = pixels.min(axis=2)
    saturation = np.divide(high - low, np.maximum(high, 1.0))

    skin = (
        (red > 95)
        & (green > 40)
        & (blue > 20)
        & (red > green)
        & (red > blue)
        & ((red - green) > 15)
        & (saturation >= MIN_SKIN_SATURATION)
        & (saturation <= MAX_SKIN_SATURATION)
    )
    return float(skin.mean())


def _background_ring(rgb: np.ndarray) -> np.ndarray:
    """Pixels around the frame edge, which is where the backdrop lives."""
    height, width = rgb.shape[:2]
    band = max(2, int(round(min(height, width) * BORDER_RATIO)))
    return np.concatenate(
        [
            rgb[:band, :, :].reshape(-1, 3),
            rgb[-band:, :, :].reshape(-1, 3),
            rgb[:, :band, :].reshape(-1, 3),
            rgb[:, -band:, :].reshape(-1, 3),
        ]
    )


def _largest_component(mask: np.ndarray) -> np.ndarray:
    """The biggest connected blob in a boolean mask.

    A product shot often carries a size tag, a shadow or a watermark alongside
    the garment. Taking the bounding box of every foreground pixel would stretch
    the box around those too, so only the largest blob is kept.

    Uses scipy when it is present and falls back to an iterative flood fill
    otherwise, because one optional dependency is not worth a hard requirement.
    """
    try:
        from scipy import ndimage
    except ImportError:
        return _largest_component_fallback(mask)

    labels, count = ndimage.label(mask)
    if count == 0:
        return mask
    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    return labels == (int(np.argmax(sizes)) + 1)


def _largest_component_fallback(mask: np.ndarray) -> np.ndarray:
    """Connected components without scipy, via an explicit stack."""
    height, width = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best_size = 0
    best: np.ndarray | None = None

    for start_y in range(height):
        for start_x in range(width):
            if not mask[start_y, start_x] or seen[start_y, start_x]:
                continue
            component = np.zeros_like(mask, dtype=bool)
            stack = [(start_y, start_x)]
            seen[start_y, start_x] = True
            size = 0
            while stack:
                y, x = stack.pop()
                component[y, x] = True
                size += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        if mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            if size > best_size:
                best_size, best = size, component

    return best if best is not None else mask


def _classify_shot(skin: float, area: float, touches_edge: bool, aspect: float) -> str:
    """A coarse shot label, recorded so promotion can be earned per shot type."""
    worn = skin >= MAX_SKIN_SHARE or aspect > MAX_SUBJECT_ASPECT
    if worn:
        return "worn_full_body" if aspect > 2.0 or touches_edge else "worn_crop"
    if area > 0.70:
        return "close_crop"
    return "flat_lay"


def locate_garment(source: Image.Image | Path | str) -> GarmentFrame:
    """Find the garment, or explain why we will not measure this image.

    Never raises. Any failure while assessing resolves to not-measurable, so a
    frame we could not assess is never treated as one we could.
    """
    try:
        return _locate(source)
    except Exception as error:  # noqa: BLE001 -- refusal must fail closed
        return GarmentFrame(measurable=False, reasons=(f"ASSESSMENT_FAILED:{type(error).__name__}",))


def _locate(source: Image.Image | Path | str) -> GarmentFrame:
    image = source if isinstance(source, Image.Image) else Image.open(source)
    image = image.convert("RGB").resize((ANALYSIS_SIZE, ANALYSIS_SIZE), Image.BILINEAR)
    rgb = np.asarray(image, dtype=np.uint8)

    reasons: list[str] = []

    ring = _background_ring(rgb).astype(np.float32)
    backdrop = np.median(ring, axis=0)
    # Spread of the ring around its own median. Mean absolute deviation rather
    # than standard deviation, so one dark corner does not dominate.
    spread = float(np.mean(np.abs(ring - backdrop)))
    if spread > MAX_BACKGROUND_SPREAD:
        reasons.append("BACKGROUND_NOT_UNIFORM")

    distance = np.linalg.norm(rgb.astype(np.float32) - backdrop, axis=2)
    foreground = distance > FOREGROUND_DISTANCE
    area = float(foreground.mean())

    if area < MIN_SUBJECT_AREA:
        reasons.append("NO_SUBJECT_FOUND")
    elif area > MAX_SUBJECT_AREA:
        reasons.append("SUBJECT_FILLS_FRAME")

    diagnostics = {"background_spread": spread, "foreground_area": area}

    if reasons:
        return GarmentFrame(
            measurable=False, reasons=tuple(reasons), subject_area=area, diagnostics=diagnostics
        )

    subject = _largest_component(foreground)
    rows = np.where(subject.any(axis=1))[0]
    columns = np.where(subject.any(axis=0))[0]
    if rows.size == 0 or columns.size == 0:
        return GarmentFrame(
            measurable=False, reasons=("NO_SUBJECT_FOUND",), diagnostics=diagnostics
        )

    top, bottom = int(rows[0]), int(rows[-1]) + 1
    left, right = int(columns[0]), int(columns[-1]) + 1
    subject_area = float(subject.mean())

    # A subject running off an edge has unknown true extent, so proportions
    # measured against its visible part are proportions of the wrong thing.
    edge = ANALYSIS_SIZE - 1
    touches = (
        subject[0, :].mean() > EDGE_CONTACT_RATIO
        or subject[edge, :].mean() > EDGE_CONTACT_RATIO
        or subject[:, 0].mean() > EDGE_CONTACT_RATIO
        or subject[:, edge].mean() > EDGE_CONTACT_RATIO
    )

    height = bottom - top
    width = right - left
    aspect = height / max(width, 1)
    diagnostics["aspect"] = aspect

    torso = (
        top + int(round(height * TORSO_TOP)),
        top + int(round(height * TORSO_BOTTOM)),
        left + int(round(width * TORSO_LEFT)),
        left + int(round(width * TORSO_RIGHT)),
    )

    # Across the whole subject, not just the torso. A worn shot is given away
    # by the face and arms, which sit outside the torso box entirely -- several
    # worn shots passed as flat lays when only the torso was checked, and their
    # torso fraction then landed on a sleeve instead of the chest.
    skin = _skin_share(rgb[top:bottom, left:right])
    diagnostics["skin_share"] = skin
    diagnostics["subject_area"] = subject_area

    shot_type = _classify_shot(skin, subject_area, touches, aspect)

    if aspect > MAX_SUBJECT_ASPECT:
        reasons.append("SUBJECT_NOT_GARMENT_SHAPED")
    if skin >= MAX_SKIN_SHARE:
        reasons.append("MODEL_IN_GARMENT_BOX")
    if touches:
        reasons.append("SUBJECT_RUNS_OFF_FRAME")

    if reasons:
        return GarmentFrame(
            measurable=False,
            reasons=tuple(reasons),
            bounds=(top, bottom, left, right),
            subject_area=subject_area,
            shot_type=shot_type,
            diagnostics=diagnostics,
        )

    return GarmentFrame(
        measurable=True,
        bounds=(top, bottom, left, right),
        torso=torso,
        subject_area=subject_area,
        shot_type=shot_type,
        diagnostics=diagnostics,
    )
