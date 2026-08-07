"""Turning a design image into measured parameters and rubric-ready evidence.

The gap this closes: ``design_scoring.py`` scores a filled-in
:class:`~app.domain.design_review.DesignReviewInput`, and nothing produced one.
A reviewer filled it by hand.

This measures what a machine can measure honestly -- print coverage, ink count,
placement, value polarity, and the scorecard's own T1/T2/T3 visual tests -- and
converts those into the specific gate results and category ratings the
measurements actually support. It deliberately stops short of the rest.

**What it will never decide.** Whether a design has one dominant proposition,
whether the joke lands, whether it belongs in the collection, whether the
composition is intentional rather than accidental -- those are the scorecard's
own words for judgement, and no measurement here substitutes for them. Those
gates come back ``NOT_TESTED``, which blocks release by design
(``DESIGN_REVIEW_SCORECARD.md`` §2: a design cannot be approved from one
floating artwork file). A partly-filled review that says so is worth more than
a fully-filled one that guessed.

Deterministic and offline: same image in, same review out. The corpus mined by
``scripts/mine_design_patterns.py`` supplies the thresholds, so "too many inks"
means more than real production work uses rather than a number someone liked.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter

from app.domain.design_review import (
    CategoryRating,
    DesignReviewInput,
    GateResult,
    GateStatus,
    HardGate,
    ScoreCategory,
)

# Corpus-derived thresholds, replaced by mine_design_patterns.py's real output
# when it is present. These fallbacks are the values that document is expected
# to land near, not invented preferences -- and they are only used when the
# corpus has not been mined.
DEFAULT_THRESHOLDS = {
    "ink_colours_p90": 6,
    "print_coverage_p10": 0.02,
    "print_coverage_p90": 0.35,
}


@dataclass(frozen=True)
class Measurements:
    """What was measured off the image, before any rubric judgement."""

    garment_rgb: tuple[int, int, int]
    has_print: bool
    print_coverage: float
    ink_colours: int
    centroid_x: float
    centroid_y: float
    light_on_dark: bool
    thumbnail_survives: bool
    blur_survives: bool
    greyscale_survives: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "garment_rgb": list(self.garment_rgb),
            "has_print": self.has_print,
            "print_coverage": round(self.print_coverage, 4),
            "ink_colours": self.ink_colours,
            "centroid": [round(self.centroid_x, 3), round(self.centroid_y, 3)],
            "light_on_dark": self.light_on_dark,
            "thumbnail_survives": self.thumbnail_survives,
            "blur_survives": self.blur_survives,
            "greyscale_survives": self.greyscale_survives,
        }


def load_thresholds(corpus_root: Path | None = None) -> dict[str, float]:
    """Corpus-derived thresholds, or the documented fallbacks."""
    if corpus_root is None:
        corpus_root = Path(__file__).resolve().parents[2] / "var" / "design_corpus"
    report = corpus_root / "design_patterns.json"
    if not report.is_file():
        return dict(DEFAULT_THRESHOLDS)
    try:
        overall = json.loads(report.read_text(encoding="utf-8"))["overall"]
        return {
            "ink_colours_p90": overall["ink_colours"]["p90"],
            "print_coverage_p10": overall["print_coverage"]["p10"],
            "print_coverage_p90": overall["print_coverage"]["p90"],
        }
    except (KeyError, ValueError, TypeError):
        return dict(DEFAULT_THRESHOLDS)


def _torso(pixels: np.ndarray) -> np.ndarray:
    return pixels[90:200, 80:176, :]


def _garment_colour(centre: np.ndarray) -> np.ndarray:
    """The garment colour, sampled where fabric shows even under a big print.

    Taking the median of the whole torso box fails on a jumbo print: once ink
    covers more than half the box, the median *is* the ink, the print reads as
    the garment, and coverage collapses toward zero. The vertical margins of
    the torso keep showing fabric at almost any print scale, so they are the
    honest sample.

    Known limit: a jumbo or all-over print that reaches the torso edges fills
    the flanks too, and is then read as the garment -- coverage collapses and
    the design looks unprinted. That is the constitution's S4 scale role and
    its ``G9`` all-over archetype, both of which it already calls exceptional
    and requiring their own production approval. Such a design needs the flat
    artwork, not a product photograph, and this module reports what it saw
    rather than pretending otherwise.
    """
    margin = max(4, centre.shape[1] // 6)
    flanks = np.concatenate(
        [centre[:, :margin, :].reshape(-1, 3), centre[:, -margin:, :].reshape(-1, 3)]
    )
    return np.median(flanks, axis=0)


def _print_mask(centre: np.ndarray, garment: np.ndarray) -> tuple[np.ndarray, float]:
    distance = np.sqrt(((centre - garment) ** 2).sum(axis=2))
    off_garment = distance > 180.0
    mask = (distance > 60.0) & ~off_garment
    coverage = float(mask.sum() / max(int((~off_garment).sum()), 1))
    return mask, coverage


def _survives_reduction(image: Image.Image, reducer) -> bool:  # type: ignore[no-untyped-def]
    """Whether a print's dominant mass is still detectable after a reduction.

    The scorecard's T1/T2/T3 all reduce information and ask whether the design
    still reads. Measured as: does a print region still stand out from the
    garment once the image is shrunk, blurred or desaturated?
    """
    reduced = reducer(image).convert("RGB").resize((256, 256), Image.LANCZOS)
    pixels = np.asarray(reduced, dtype=np.float32)
    centre = _torso(pixels)
    garment = _garment_colour(centre)
    _, coverage = _print_mask(centre, garment)
    return coverage >= 0.01


def measure(image_path: Path) -> Measurements:
    """Measure one design image. No judgement, only parameters."""
    original = Image.open(image_path).convert("RGB")
    image = original.resize((256, 256), Image.LANCZOS)
    pixels = np.asarray(image, dtype=np.float32)

    centre = _torso(pixels)
    garment = _garment_colour(centre)
    mask, coverage = _print_mask(centre, garment)

    if coverage < 0.004:
        return Measurements(
            garment_rgb=tuple(int(v) for v in garment),  # type: ignore[arg-type]
            has_print=False,
            print_coverage=coverage,
            ink_colours=0,
            centroid_x=0.5,
            centroid_y=0.5,
            light_on_dark=False,
            thumbnail_survives=False,
            blur_survives=False,
            greyscale_survives=False,
        )

    ink = centre[mask]
    step = 256 / 6
    quantised = (ink // step).astype(np.int16)
    keyed = quantised[:, 0] * 36 + quantised[:, 1] * 6 + quantised[:, 2]
    unique, counts = np.unique(keyed, return_counts=True)
    ink_colours = int((counts / counts.sum() >= 0.05).sum())

    rows, cols = np.nonzero(mask)
    weights = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

    return Measurements(
        garment_rgb=tuple(int(v) for v in garment),  # type: ignore[arg-type]
        has_print=True,
        print_coverage=coverage,
        ink_colours=ink_colours,
        centroid_x=float(cols.mean()) / mask.shape[1],
        centroid_y=float(rows.mean()) / mask.shape[0],
        light_on_dark=float(ink.mean(axis=0) @ weights) > float(garment @ weights),
        # T1 thumbnail: small enough that fine detail is gone.
        thumbnail_survives=_survives_reduction(
            original, lambda im: im.resize((max(im.width // 10, 8), max(im.height // 10, 8)), Image.LANCZOS)
        ),
        # T2 blur: enough to remove small text and detail.
        blur_survives=_survives_reduction(original, lambda im: im.filter(ImageFilter.GaussianBlur(radius=8))),
        # T3 greyscale: colour removed, hierarchy must survive on value alone.
        greyscale_survives=_survives_reduction(original, lambda im: im.convert("L")),
    )


def to_review(
    design_id: str,
    design_name: str,
    measurements: Measurements,
    thresholds: dict[str, float] | None = None,
) -> DesignReviewInput:
    """Convert measurements into the gates and ratings they actually support.

    Everything a measurement cannot speak to is left untested rather than
    assumed to pass. See this module's docstring.
    """
    limits = thresholds or load_thresholds()
    gates: list[GateResult] = []
    ratings: list[CategoryRating] = []

    def gate(name: HardGate, status: GateStatus, evidence: str) -> None:
        gates.append(GateResult(gate=name, status=status, evidence=evidence))

    # HF-05 Distance Failure. The scorecard's own T1/T2 are exactly this test,
    # and both are measurable.
    if measurements.thumbnail_survives and measurements.blur_survives:
        gate(
            HardGate.DISTANCE_FAILURE,
            GateStatus.PASS,
            f"print holds at thumbnail and under blur; coverage {measurements.print_coverage:.1%}",
        )
    elif not measurements.has_print:
        gate(
            HardGate.DISTANCE_FAILURE,
            GateStatus.FAIL,
            "no print detected in the torso region at analysis resolution",
        )
    else:
        failed = [
            label
            for label, survived in (
                ("thumbnail", measurements.thumbnail_survives),
                ("blur", measurements.blur_survives),
            )
            if not survived
        ]
        gate(
            HardGate.DISTANCE_FAILURE,
            GateStatus.FAIL,
            f"print does not survive the {' and '.join(failed)} test",
        )

    # HF-07 Production Failure, on ink count alone. A design inside the corpus's
    # own p90 is producible by the same means real work is; beyond it, the
    # method needs justifying rather than assuming.
    if not measurements.has_print:
        gate(HardGate.PRODUCTION_FAILURE, GateStatus.NOT_TESTED, "no print detected to assess")
    elif measurements.ink_colours <= limits["ink_colours_p90"]:
        gate(
            HardGate.PRODUCTION_FAILURE,
            GateStatus.NOT_TESTED,
            f"{measurements.ink_colours} significant ink colours, within the corpus p90 of "
            f"{limits['ink_colours_p90']:.0f} -- but line weight, gap integrity and "
            "registration cannot be judged from a product photograph",
        )
    else:
        gate(
            HardGate.PRODUCTION_FAILURE,
            GateStatus.FAIL,
            f"{measurements.ink_colours} significant ink colours exceeds the corpus p90 of "
            f"{limits['ink_colours_p90']:.0f}; colour count needs a documented reason",
        )

    # Everything else needs a human, a brief, or the range. Saying so is the point.
    for name, why in (
        (HardGate.NO_CLEAR_PRODUCT_DEFINITION, "blank, fit and production method are not in the image"),
        (HardGate.NO_COLLECTION_ROLE, "collection role is a brief decision, not a property of the artwork"),
        (HardGate.NO_DOMINANT_PROPOSITION, "requires reading the design's idea, not its parameters"),
        (HardGate.HIERARCHY_COLLAPSE, "requires judging which element is meant to lead"),
        (HardGate.GARMENT_CONFLICT, "seam and construction interaction needs the flat artwork and the blank"),
        (HardGate.IDENTITY_SUBSTITUTION, "requires knowing the permanent identity assets"),
        (HardGate.WEAK_WITHOUT_THE_LOGO, "requires isolating the logo from the artwork"),
        (HardGate.COLLECTION_REDUNDANCY, "requires the rest of the proposed range"),
        (HardGate.MOCK_UP_ONLY_SUCCESS, "requires comparing the flat artwork against the styled shot"),
        (HardGate.UNRESOLVED_RIGHTS_RISK, "provenance of artwork and references is not visible in the image"),
    ):
        gate(name, GateStatus.NOT_TESTED, why)

    # Distance and Silhouette is the one category the visual tests genuinely
    # measure: three tests, three of five points, plus one for surviving all.
    survived = sum(
        (measurements.thumbnail_survives, measurements.blur_survives, measurements.greyscale_survives)
    )
    rating = min(5, survived + (1 if survived == 3 else 0)) if measurements.has_print else 0
    ratings.append(
        CategoryRating(
            category=ScoreCategory.DISTANCE_AND_SILHOUETTE,
            rating=rating,
            evidence=(
                f"thumbnail {'pass' if measurements.thumbnail_survives else 'fail'}, "
                f"blur {'pass' if measurements.blur_survives else 'fail'}, "
                f"greyscale {'pass' if measurements.greyscale_survives else 'fail'}; "
                f"coverage {measurements.print_coverage:.1%}, "
                f"{'light on dark' if measurements.light_on_dark else 'dark on light'}"
            ),
        )
    )

    return DesignReviewInput(
        design_id=design_id,
        design_name=design_name,
        gate_results=gates,
        category_ratings=ratings,
    )


def extract(design_id: str, design_name: str, image_path: Path) -> DesignReviewInput:
    """Measure an image and return the review those measurements support."""
    return to_review(design_id, design_name, measure(image_path))
