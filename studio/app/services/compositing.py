"""Printing a design onto a photograph.

The photographs are made with blank garments, on purpose. This puts a design on one
afterwards, locally: no image model, no per-image cost, and re-running with a
different design or ink is free.

Three things have to be true or it reads as a sticker:

- it follows the fabric. Folds displace the print, so the design is pushed around by
  the gradient of the garment's own shading.
- it takes the light. A crease that darkens the shirt darkens the ink on it, so the
  photograph's luminance is multiplied back over the design.
- it stops at the garment. Anything inside the placement that is not the garment --
  an arm, a bag, hair -- is cut out by colour distance from the fabric itself.

Where the design goes is not decided here. A quadrilateral is supplied, because
finding a garment in a dark photograph without a model is the fragile part, and a
person does it in seconds.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageFilter

# Corners in the order a person would drag them.
Point = tuple[float, float]


@dataclass(frozen=True)
class Placement:
    """Where the design sits, as four corners in photograph pixels.

    A quadrilateral rather than a box: a chest is rarely square to the camera, and
    the perspective is most of what makes a print look like it is on someone.
    """

    top_left: Point
    top_right: Point
    bottom_right: Point
    bottom_left: Point

    def corners(self) -> list[Point]:
        return [self.top_left, self.top_right, self.bottom_right, self.bottom_left]

    def bounds(self) -> tuple[int, int, int, int]:
        """Integer box enclosing the quad, clipped by the caller to the photo."""
        xs = [point[0] for point in self.corners()]
        ys = [point[1] for point in self.corners()]
        return (int(min(xs)), int(min(ys)), int(max(xs)) + 1, int(max(ys)) + 1)


@dataclass(frozen=True)
class PrintSettings:
    """How hard the print is pressed into the photograph.

    The defaults are deliberately restrained. Overdoing any of them is more obvious
    than leaving it flat: a print that ripples more than the shirt does looks wrong
    in a way a slightly flat one does not.
    """

    # How far a fold may push the print, in pixels at the photograph's scale.
    displacement: float = 6.0
    # 0 keeps the design's own flat colour; 1 takes all of the garment's shading.
    shading: float = 0.85
    # Screen print is not glass. A little transparency lets the weave through.
    opacity: float = 0.92
    # How far a pixel's colour may sit from the fabric before it is treated as
    # something in front of the garment. 0 disables the cut-out entirely.
    garment_tolerance: float = 0.22


def _luminance(image: Image.Image) -> np.ndarray:
    """Perceptual luminance in 0..1."""
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    return rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def _perspective_coefficients(source: list[Point], target: list[Point]) -> tuple[float, ...]:
    """Coefficients mapping the target box back to the source quad.

    Pillow's PERSPECTIVE transform is defined backwards -- it asks where each output
    pixel comes from -- so the pairs are given in that direction.
    """
    matrix = []
    for (sx, sy), (tx, ty) in zip(source, target, strict=True):
        matrix.append([tx, ty, 1, 0, 0, 0, -sx * tx, -sx * ty])
        matrix.append([0, 0, 0, tx, ty, 1, -sy * tx, -sy * ty])

    a = np.array(matrix, dtype=np.float64)
    b = np.array(source, dtype=np.float64).reshape(8)
    solved = np.linalg.solve(a, b)
    return tuple(float(value) for value in solved)


def _warp_into(design: Image.Image, placement: Placement, size: tuple[int, int]) -> Image.Image:
    """Put the design onto a transparent canvas the size of the photograph."""
    width, height = design.size
    source = [(0.0, 0.0), (float(width), 0.0), (float(width), float(height)), (0.0, float(height))]
    coefficients = _perspective_coefficients(source, placement.corners())
    return design.convert("RGBA").transform(
        size, Image.Transform.PERSPECTIVE, coefficients, Image.Resampling.BICUBIC
    )


def _sample(source: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Bilinear sample of an (h, w, c) array at floating coordinates.

    Nearest-neighbour is visibly steppy on the thin strokes these designs are mostly
    made of, which is exactly where a displaced print gives itself away.
    """
    height, width = source.shape[:2]
    x = np.clip(x, 0, width - 1)
    y = np.clip(y, 0, height - 1)

    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    x1 = np.clip(x0 + 1, 0, width - 1)
    y1 = np.clip(y0 + 1, 0, height - 1)

    fx = (x - x0)[..., None]
    fy = (y - y0)[..., None]

    top = source[y0, x0] * (1 - fx) + source[y0, x1] * fx
    bottom = source[y1, x0] * (1 - fx) + source[y1, x1] * fx
    return top * (1 - fy) + bottom * fy


def _displaced(warped: np.ndarray, luminance: np.ndarray, strength: float) -> np.ndarray:
    """Push the print around by the slope of the garment's shading.

    The gradient of a blurred luminance points across a fold, which is the direction
    fabric actually carries a print. Blurring first matters: run on the raw image and
    the print chases film grain rather than folds.
    """
    if strength <= 0:
        return warped

    height, width = luminance.shape
    smooth = np.asarray(
        Image.fromarray((luminance * 255).astype(np.uint8)).filter(
            # Wide enough to be a fold rather than a thread, at any photo size.
            ImageFilter.GaussianBlur(radius=max(2.0, min(width, height) * 0.006))
        ),
        dtype=np.float32,
    ) / 255.0

    dy, dx = np.gradient(smooth)
    # Gradients here are small; scaling by the strength alone would barely move it.
    scale = strength * 40.0
    grid_x, grid_y = np.meshgrid(
        np.arange(width, dtype=np.float32), np.arange(height, dtype=np.float32)
    )
    return _sample(warped, grid_x + dx * scale, grid_y + dy * scale)


def _garment_mask(photo: np.ndarray, alpha: np.ndarray, tolerance: float) -> np.ndarray:
    """Keep the print off whatever is in front of the garment.

    The fabric colour is taken from the photograph under the design itself, so it
    works on a black tee at night and a white one at sunrise without being told
    which. Anything far enough from that colour -- an arm, a bag, hair, a strap --
    loses the print.
    """
    if tolerance <= 0:
        return np.ones_like(alpha)

    covered = alpha > 0.5
    if not covered.any():
        return np.ones_like(alpha)

    fabric = np.median(photo[covered], axis=0)
    distance = np.sqrt(((photo - fabric) ** 2).sum(axis=2))
    # Soft edge: a hard cut leaves a cartoon outline around an arm.
    return np.clip(1.0 - (distance - tolerance) / max(tolerance, 1e-3), 0.0, 1.0)


def print_design(
    photo: Image.Image,
    design: Image.Image,
    placement: Placement,
    settings: PrintSettings | None = None,
) -> Image.Image:
    """The photograph with the design printed on the garment."""
    settings = settings or PrintSettings()

    photo_rgb = photo.convert("RGB")
    warped = _warp_into(design, placement, photo_rgb.size)

    base = np.asarray(photo_rgb, dtype=np.float32) / 255.0
    layer = np.asarray(warped, dtype=np.float32) / 255.0
    luminance = _luminance(photo_rgb)

    layer = _displaced(layer, luminance, settings.displacement)
    ink, alpha = layer[..., :3], layer[..., 3]

    # Shading, normalised against the fabric the design covers rather than the whole
    # frame: a bright doorway elsewhere must not wash out a print on a dark shirt.
    covered = alpha > 0.5
    reference = float(np.median(luminance[covered])) if covered.any() else 0.5
    relative = np.clip(luminance / max(reference, 1e-3), 0.25, 2.0)[..., None]
    ink = np.clip(ink * (1.0 - settings.shading + settings.shading * relative), 0.0, 1.0)

    alpha = alpha * settings.opacity * _garment_mask(base, alpha, settings.garment_tolerance)

    result = base * (1.0 - alpha[..., None]) + ink * alpha[..., None]
    return Image.fromarray((np.clip(result, 0.0, 1.0) * 255).astype(np.uint8))
