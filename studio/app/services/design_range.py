"""One set of supplied assets, laid out across the whole garment range.

The owner hands over a bag: some images, some phrases, in whatever mix. Not a
design, not a brief -- raw material. Everything after that is the engine's to
decide, and it decides it for *every* garment, because a design is a range and
not one shirt.

Four decisions per garment, and each comes from a different place:

*Which surfaces.* A design is a treatment across a garment rather than one
print -- front alone, chest with back, front with sleeve. Which combinations are
legitimate comes from the product design constitution, section 13: a crop
recalculates rather than reusing tee placement, a cap front is embroidery-first
and compact.

*Which zone, and what form in it.* The zone is the garment file's own, in real
millimetres. The form -- full, half, band, vertical strip, small centred, pocket
-- is filtered to what physically fits: a 38x45mm cap side cannot take a band.

*What content lands where.* Scale role, from the constitution's section 7. A
small mark is an S1 chest identifier and a large detailed one is an S3 hero, so
supplying one of each places itself.

*How it is composed inside that area.* From ``composition_engine``, which
learned it from 1,166 corpus designs. That is the only thing the corpus is asked
for, because it is the only thing it knows: every mined template is centred on
its own bounding box, so it has an opinion about composition and none at all
about placement.

The range always covers every garment. A garment that cannot take the supplied
assets appears in it as a refusal with a reason, never as a gap -- a missing row
reads as "not applicable" when it usually means "not considered".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.archive.garment import Garment, GarmentError, Zone
from app.archive.garment import load as load_garment
from app.services.composition_engine import (
    Brief,
    Composition,
    CompositionEngine,
    Element,
    Option,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
GARMENT_DIR = REPO_ROOT / "assets" / "garments"

# The smallest a printed element can usefully be. Not a judgement about detail
# -- an eighth of a business card is simply not a place to put a design.
MIN_PRINT_MM = 20.0


@dataclass(frozen=True)
class Form:
    """A shape a print takes inside a zone, as shares of that zone."""

    key: str
    label: str
    width: float
    height: float
    # Off-centre forms exist because a pocket print is defined by not being
    # centred. Everything else sits on the vertical axis.
    centre_x: float = 0.5

    def fits(self, zone_width: float, zone_height: float) -> bool:
        return zone_width * self.width >= MIN_PRINT_MM and zone_height * self.height >= MIN_PRINT_MM

    def box(self, zone_width: float, zone_height: float) -> tuple[float, float, float, float]:
        """Left, top, width, height in millimetres inside the zone."""
        width = zone_width * self.width
        height = zone_height * self.height
        return (
            zone_width * self.centre_x - width / 2,
            (zone_height - height) / 2,
            width,
            height,
        )


FORMS: tuple[Form, ...] = (
    Form("full", "Full", 0.92, 0.88),
    Form("half", "Half", 0.90, 0.46),
    Form("band", "Band", 0.92, 0.18),
    Form("vertical_left", "Vertical strip, left", 0.30, 0.86, centre_x=0.24),
    Form("vertical_right", "Vertical strip, right", 0.30, 0.86, centre_x=0.76),
    Form("small_centred", "Small centred", 0.34, 0.26),
    Form("pocket", "Pocket", 0.24, 0.22, centre_x=0.28),
)

FORMS_BY_KEY = {form.key: form for form in FORMS}

# Scale roles, from the constitution's section 7. Assigned by zone rather than
# by size, because scale there is defined by function first and dimensions
# second: a chest identifier is one whatever the garment measures.
SCALE_ROLE = {
    "full_front": "S3",
    "full_back": "S3",
    "centre_chest": "S2",
    "centre_back": "S2",
    "left_chest": "S1",
    "upper_back_yoke": "S1",
    "outer_back_neck": "S0",
    "inner_neck_label": "S0",
    "short_sleeve": "S0",
    "long_sleeve": "S0",
    "pocket": "S0",
    "cap_front": "S1",
    "cap_side": "S0",
    "cap_back": "S0",
}

# Which zones a design may use together on one garment. Ordered, so the first
# combination that can be filled is the one offered.
SURFACE_SETS: tuple[tuple[str, ...], ...] = (
    ("full_front",),
    ("centre_chest",),
    ("left_chest", "full_back"),
    ("left_chest",),
    ("full_back",),
    ("cap_front",),
    ("cap_front", "cap_back"),
)


@dataclass(frozen=True)
class Placed:
    """One element, on one zone, in one form, composed."""

    # Which view of the garment carries it -- a chest print and a back print
    # belong to one design and are drawn on two different files.
    view: str
    zone_key: str
    scale_role: str
    form: Form
    zone_width_mm: float
    zone_height_mm: float
    composition: Composition


@dataclass
class GarmentRange:
    """What the engine proposes for one garment, or why it proposes nothing."""

    garment: str
    placed: tuple[Placed, ...] = ()
    refusal_reason: str = ""
    refusal_detail: str = ""

    @property
    def offered(self) -> bool:
        return bool(self.placed)


@dataclass
class Range:
    """The whole range for one set of supplied assets."""

    garments: tuple[GarmentRange, ...] = ()
    gaps: list[str] = field(default_factory=list)

    @property
    def offered(self) -> int:
        return sum(1 for g in self.garments if g.offered)


def _garments() -> dict[str, tuple[Path, ...]]:
    """Garment files grouped into garments.

    The twenty-two files are eleven garments seen from two sides. Treating each
    file as a garment makes every back view refuse -- it has no chest zone --
    and makes a chest-and-back treatment impossible to express, which is the
    single most common architecture there is.
    """
    grouped: dict[str, list[Path]] = {}
    for file in sorted(GARMENT_DIR.glob("garment_*.svg")):
        stem = file.stem.replace("garment_", "")
        for view in ("_front", "_back"):
            if stem.endswith(view):
                stem = stem[: -len(view)]
                break
        grouped.setdefault(stem, []).append(file)
    return {name: tuple(files) for name, files in sorted(grouped.items())}


def _forms_for(zone_width: float, zone_height: float, count: int) -> tuple[Form, ...]:
    """Forms that fit this zone and can hold this many elements.

    A band is one line of something. Asking it to hold four stacked elements
    gives each of them a quarter of an eighteenth of the zone, which is a
    smaller print than the minimum this module already refuses.
    """
    fits = tuple(f for f in FORMS if f.fits(zone_width, zone_height))
    if count <= 1:
        return fits
    return tuple(f for f in fits if f.height * zone_height / count >= MIN_PRINT_MM)


def _footprint(option: Option) -> tuple[float, float]:
    """The share of the print area the chosen arrangement actually occupies."""
    top = min(s.top for s in option.slots)
    bottom = max(s.top + s.height for s in option.slots)
    width = max(s.width for s in option.slots)
    return width, bottom - top


def _form_for(option: Option, candidates: tuple[Form, ...]) -> Form:
    """The container whose proportions match what the corpus arrangement needs.

    Taking the first that fits was a default dressed as a decision, and it meant
    a two-line lockup and a full-bleed hero were printed at identical size. The
    template already says how much room its arrangement wants -- a band of type
    occupies a fifth of the height, a lead-and-caption nearly half -- so the
    form is the container closest to that, which makes the size a consequence of
    the evidence rather than of list order.
    """
    want_width, want_height = _footprint(option)
    return min(
        candidates,
        key=lambda f: abs(f.width - want_width) + 2.0 * abs(f.height - want_height),
    )


def _surface_sets_for(zones: dict[str, tuple[str, Zone]]) -> tuple[tuple[str, ...], ...]:
    """The surface combinations this garment can carry, across both views."""
    available = set(zones)
    usable = []
    for combination in SURFACE_SETS:
        if all(any(z == key or z.startswith(key) for z in available) for key in combination):
            usable.append(combination)
    return tuple(usable)


def build(
    elements: tuple[Element, ...],
    engine: CompositionEngine,
    *,
    tradition: str | None = "streetwear",
) -> Range:
    """Lay one set of supplied assets across every garment we hold."""
    if not elements:
        return Range(gaps=["nothing was supplied"])

    garments: list[GarmentRange] = []
    for name, files in _garments().items():
        # Both views, so a zone can be found wherever it actually lives.
        views: dict[str, Garment] = {}
        zones: dict[str, tuple[str, Zone]] = {}
        failed = None
        for file in files:
            view = "back" if file.stem.endswith("_back") else "front"
            try:
                loaded = load_garment(file)
            except GarmentError as error:
                failed = error
                continue
            views[view] = loaded
            for key, zone in loaded.zones.items():
                zones.setdefault(key, (view, zone))

        if not views:
            garments.append(
                GarmentRange(
                    garment=name,
                    refusal_reason=failed.reason if failed else "UNREADABLE",
                    refusal_detail=failed.detail if failed else "no view could be read",
                )
            )
            continue

        sets = _surface_sets_for(zones)
        if not sets:
            garments.append(
                GarmentRange(
                    garment=name,
                    refusal_reason="NO_SURFACE_SET",
                    refusal_detail=(
                        f"none of the known surface combinations fit; this garment has "
                        f"{', '.join(sorted(zones))}"
                    ),
                )
            )
            continue

        placed: list[Placed] = []
        # Every combination the garment can carry, not the first one that
        # matched. `sets[0]` meant full_front always won and the chest-and-back
        # architecture -- the commonest two-surface treatment there is -- could
        # never be reached on any garment.
        for zone_key in [key for combination in sets for key in combination]:
            found = zones.get(zone_key) or next(
                (v for k, v in zones.items() if k.startswith(zone_key)), None
            )
            if found is None:
                continue
            view, zone = found

            forms = _forms_for(zone.width, zone.height, len(elements))
            if not forms:
                continue

            composition = engine.compose(
                Brief(
                    elements=elements,
                    garment=name,
                    surface=zone_key,
                    tradition=tradition,
                )
            )
            if any(p.zone_key == zone_key for p in placed):
                continue

            form = (
                _form_for(composition.options[0], forms)
                if composition.composable and composition.options
                else forms[0]
            )
            placed.append(
                Placed(
                    view=view,
                    zone_key=zone_key,
                    scale_role=SCALE_ROLE.get(zone.base_key, "S2"),
                    form=form,
                    zone_width_mm=zone.width,
                    zone_height_mm=zone.height,
                    composition=composition,
                )
            )

        if not placed:
            garments.append(
                GarmentRange(
                    garment=name,
                    refusal_reason="NO_FORM_FITS",
                    refusal_detail=(
                        f"no print form holds {len(elements)} element(s) above "
                        f"{MIN_PRINT_MM:.0f}mm on this garment's zones"
                    ),
                )
            )
            continue

        garments.append(GarmentRange(garment=name, placed=tuple(placed)))

    return Range(garments=tuple(garments))
