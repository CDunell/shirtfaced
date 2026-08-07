"""An element's feature vector, derived from what it declares.

Every component below is computed from a field the element already carries, so
a similarity result can be explained by naming the field that caused it. That
is the whole reason this is not a learned embedding: an image model would give
better neighbours and no account of why, and it would move whenever the model
moved. This archive's premise is that any output can be regenerated from its
inputs, and a vector that drifts between runs breaks that at the root.

The vector is used for "what else is like this" and for keeping a composition
from stacking three intricate things on top of each other. It is not used to
decide whether an element may be used -- that is the licence gate, and it is a
hard yes or no rather than a distance.
"""

from __future__ import annotations

from app.db.archive_models import ELEMENT_FEATURE_DIMENSIONS

# Order is fixed and additions go on the end. Changing the meaning of an index
# silently invalidates every vector already stored, and nothing would fail
# loudly -- neighbours would just quietly get worse.
FAMILY_ORDER = (
    "frame",
    "type_layout",
    "wordmark",
    "badge",
    "texture",
    "print_effect",
    "patch_label",
    "placement",
    "composition_template",
    "colour_system",
    "illustration_part",
    "symbol",
    "ornament",
    "pattern",
)

SYMMETRY_ORDER = ("none", "vertical", "horizontal", "radial")

TREATMENT_ORDER = ("clean", "distressed", "embroidered", "vintage")

# Above this an element counts as "many slots" for normalisation. Chosen from
# the archive's own shape rather than from taste: a badge with a primary text,
# a secondary text and a symbol is three, and anything past six is a
# composition rather than an element.
SLOT_SATURATION = 6.0

# Inks are counted 1..6; a six-colour job is already past what most of the
# corpus does, where the median design uses five.
INK_SATURATION = 6.0


def _one_hot(value: str, order: tuple[str, ...]) -> list[float]:
    return [1.0 if value == candidate else 0.0 for candidate in order]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def element_feature(
    family: str,
    symmetry: str,
    complexity: float,
    ink_min: int,
    ink_max: int,
    slots: list[dict[str, object]],
    compatible_treatments: tuple[str, ...] | list[str],
    parameters: dict[str, float] | None = None,
) -> list[float]:
    """The vector for one element. Deterministic, and explainable per index."""
    parameters = parameters or {}
    accepts = {
        str(kind)
        for slot in slots
        for kind in (slot.get("accepts") or ("text",))
    }

    vector: list[float] = []
    vector += _one_hot(family, FAMILY_ORDER)            # 0..13
    vector += _one_hot(symmetry, SYMMETRY_ORDER)        # 14..17
    vector.append(_clamp(complexity))                   # 18
    vector.append(_clamp(ink_min / INK_SATURATION))     # 19
    vector.append(_clamp(ink_max / INK_SATURATION))     # 20
    vector.append(_clamp(len(slots) / SLOT_SATURATION))  # 21
    vector.append(1.0 if "text" in accepts else 0.0)    # 22
    vector.append(1.0 if "image" in accepts else 0.0)   # 23
    vector.append(1.0 if "symbol" in accepts else 0.0)  # 24
    vector += [                                         # 25..28
        1.0 if treatment in compatible_treatments else 0.0
        for treatment in TREATMENT_ORDER
    ]
    # Aspect is squashed rather than clamped: a 3:1 ticket and a 6:1 rule are
    # genuinely different, and clamping would make them identical.
    aspect = float(parameters.get("aspect", 1.0))
    vector.append(_clamp(aspect / (1.0 + aspect)))      # 29
    vector.append(_clamp(float(parameters.get("stroke", 0.0))))  # 30
    # Held open. Filling this later is additive; renumbering anything above it
    # is not, and would invalidate every stored vector without failing.
    vector.append(0.0)                                  # 31

    if len(vector) != ELEMENT_FEATURE_DIMENSIONS:
        raise ValueError(
            f"feature vector is {len(vector)} long, expected {ELEMENT_FEATURE_DIMENSIONS}"
        )
    return vector


def explain(index: int) -> str:
    """Which declared field drives one component, for reading a neighbour list."""
    if index < len(FAMILY_ORDER):
        return f"family={FAMILY_ORDER[index]}"
    index -= len(FAMILY_ORDER)
    if index < len(SYMMETRY_ORDER):
        return f"symmetry={SYMMETRY_ORDER[index]}"
    index -= len(SYMMETRY_ORDER)
    return (
        "complexity",
        "ink_min",
        "ink_max",
        "slot_count",
        "accepts_text",
        "accepts_image",
        "accepts_symbol",
        "treatment=clean",
        "treatment=distressed",
        "treatment=embroidered",
        "treatment=vintage",
        "aspect",
        "stroke",
        "reserved",
    )[index]
