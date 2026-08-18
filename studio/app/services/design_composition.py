"""Composing a design and keeping it.

The archive could already assemble a design. It had nowhere to put one: no route
touched ``app.archive``, so the engine was a library you could only drive from a
Python prompt. Nothing was stored, so nothing reached ``awaiting_decision``, so
nothing could be approved, and ADR-010's whole point -- that human approval is
visible in the data -- had nothing to be visible about.

This is the join. It composes, stores the brief that produced the artwork, and
leaves the result undecided.

Two things it deliberately does not do. It does not invent or edit the owner's
words; the engine decides how supplied text is set, never what it says. And it
does not approve anything: a stored design is not an approved design, and the
only way out of ``awaiting_decision`` is a person.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.archive.design_composer import Brief, DesignComposer, DesignOption
from app.archive.garment import Garment, GarmentError
from app.archive.garment import load as load_garment
from app.config import GARMENTS_DIR, PROJECT_ROOT
from app.db.archive_models import ComposedDesign
from app.domain.enums import AttemptState
from app.services.composition_engine import ApprovalStore

if TYPE_CHECKING:
    from app.db.concept_models import DesignAttempt

# Both resolved from the application's own root rather than by walking up past
# it: the deploy syncs studio/'s contents to the box, so a repo-root walk lands
# outside the deployment and finds nothing. See config._garments_dir.
GARMENT_DIR = GARMENTS_DIR

# Where approvals are remembered for the composer's own confidence weighting.
# Separate from the database on purpose: it is the composer's learning, not the
# record of what was decided, and that record is the table.
APPROVALS_PATH = PROJECT_ROOT / "var" / "approvals.json"


class CompositionRefused(Exception):
    """The brief could not be answered, with a durable reason code."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Request:
    """One brief, plus where it is going and how it should be settled."""

    seed: int
    garment_key: str
    primary_text: str = ""
    secondary_text: str = ""
    placement: str = "centre_chest"
    fit: str = "adult"
    treatment: str = "clean"
    garment_colour: str = "#101010"
    inks: int = 2
    style_tags: tuple[str, ...] = ()
    # Empty lets the seed choose one that reads on this garment.
    colour_system: str = ""
    limit: int = 6


def garment_for(key: str) -> Garment:
    """Load a garment by file stem. Refuses rather than substituting a default.

    A missing garment is a typo or a file that never landed. Falling back to a
    tee would place the design in the wrong zones and produce something that
    looks plausible, which is worse than an error.
    """
    if "/" in key or "\\" in key or key.startswith("."):
        raise CompositionRefused("BAD_GARMENT_KEY", key)
    file = GARMENT_DIR / f"{key}.svg"
    if not file.is_file():
        raise CompositionRefused("UNKNOWN_GARMENT", key)
    try:
        return load_garment(file)
    except GarmentError as error:
        raise CompositionRefused(error.reason, error.detail) from error


def compose(request: Request) -> tuple[Garment, list[DesignOption]]:
    """Answer a brief. Raises only when nothing can be composed at all."""
    garment = garment_for(request.garment_key)
    composer = DesignComposer(APPROVALS_PATH)
    result = composer.compose(
        Brief(
            primary_text=request.primary_text,
            secondary_text=request.secondary_text,
            placement=request.placement,
            fit=request.fit,
            style_tags=request.style_tags,
            inks=request.inks,
            treatment=request.treatment,
            garment=request.garment_colour,
            colour_system=request.colour_system,
        ),
        seed=request.seed,
        limit=request.limit,
        garment=garment,
    )
    if not result.composable:
        raise CompositionRefused(result.refusal_reason, result.refusal_detail)
    return garment, list(result.options)


def store(
    session: Session,
    request: Request,
    option: DesignOption,
    *,
    attempt: DesignAttempt | None = None,
) -> ComposedDesign:
    """Keep one composed design, or return the one already kept.

    The same brief composed twice is the same design, so a repeat finds the
    existing row rather than filling the review queue with duplicates a person
    then has to tell apart. That also makes this safe to call again after a
    failure part-way through a batch.

    ``attempt`` records which design attempt this composition was made for. An
    existing unlinked row gains the link -- the same design is the same design,
    and the lineage is worth having. A row already linked to a *different*
    attempt is returned untouched: rewriting history is not this function's
    call to make.
    """
    existing = session.execute(
        select(ComposedDesign).where(ComposedDesign.content_hash == option.design.content_hash)
    ).scalar_one_or_none()
    if existing is not None:
        if attempt is not None and existing.design_attempt_id is None:
            existing.design_attempt_id = attempt.id
            session.flush()
        return existing

    design = ComposedDesign(
        seed=request.seed,
        garment_key=request.garment_key,
        placement_key=request.placement,
        fit=request.fit,
        content={
            "primary_text": request.primary_text,
            "secondary_text": request.secondary_text,
        },
        palette={
            "garment": request.garment_colour,
            "inks": request.inks,
            "system": request.colour_system,
        },
        treatment=request.treatment,
        grammar_key=option.grammar_key,
        parts=dict(option.parts),
        width_mm=option.design.width_mm,
        height_mm=option.design.height_mm,
        content_hash=option.design.content_hash,
        svg=option.design.svg,
        assembler_version=option.design.assembler_version,
        state=AttemptState.AWAITING_DECISION.value,
        design_attempt_id=None if attempt is None else attempt.id,
    )
    session.add(design)
    session.flush()
    return design


def decide(
    session: Session,
    design: ComposedDesign,
    approved: bool,
    decided_by: str,
    note: str = "",
) -> ComposedDesign:
    """Settle a design. Only a person gets to call this.

    Refuses to settle one twice. A second decision is either a mistake or a
    disagreement, and silently overwriting the first loses which it was.
    """
    if design.state in (AttemptState.APPROVED.value, AttemptState.REJECTED.value):
        raise CompositionRefused("ALREADY_DECIDED", design.state)
    if not decided_by.strip():
        raise CompositionRefused("NO_DECIDER", "an approval nobody signed is not an approval")

    design.state = AttemptState.APPROVED.value if approved else AttemptState.REJECTED.value
    design.decided_by = decided_by.strip()
    design.decided_at = dt.datetime.now(dt.UTC)
    design.decision_note = note
    session.flush()
    record_learning(design.grammar_key, approved)
    return design


def record_learning(grammar_key: str, approved: bool) -> None:
    """Feed one settled decision to the composer's approval store.

    The approve control is the training signal -- the engine ranks its options
    by ``approvals / decisions`` per grammar, and until this existed no
    decision path ever wrote to the store, so every option carried
    ``decisions: 0`` forever and the confidence weighting was decorative.

    Approve and reject both count. A variation request does not: it is a
    verdict on the content, not on the construction that set it.
    """
    ApprovalStore(APPROVALS_PATH).record(grammar_key, approved)


def rebuild_approvals(session: Session) -> dict[str, dict[str, int]]:
    """Derive the approval store from the decisions actually recorded.

    The table is the record; the store is the composer's reading of it. A file
    written incrementally can drift from the rows -- decisions made before the
    learning wire existed, a store lost with a box, a corrupt write. Rebuilding
    from ``composed_designs`` makes the store a regenerable view, so drift
    self-heals instead of accumulating.
    """
    data: dict[str, dict[str, int]] = {}
    rows = session.execute(
        select(ComposedDesign.grammar_key, ComposedDesign.state).where(
            ComposedDesign.state.in_(
                (AttemptState.APPROVED.value, AttemptState.REJECTED.value)
            )
        )
    ).all()
    for grammar_key, state in rows:
        entry = data.setdefault(grammar_key, {"approved": 0, "decisions": 0})
        entry["decisions"] += 1
        if state == AttemptState.APPROVED.value:
            entry["approved"] += 1

    APPROVALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    APPROVALS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def recompose(design: ComposedDesign) -> str:
    """Rebuild a stored design's artwork from its brief alone.

    This is the determinism claim made checkable across a restart rather than
    only inside one process: the row keeps the brief, and the same brief must
    produce the same bytes months later on another machine.
    """
    request = Request(
        seed=design.seed,
        garment_key=design.garment_key,
        primary_text=str(design.content.get("primary_text", "")),
        secondary_text=str(design.content.get("secondary_text", "")),
        placement=design.placement_key,
        fit=design.fit,
        treatment=design.treatment,
        garment_colour=str(design.palette.get("garment", "#101010")),
        inks=int(design.palette.get("inks", 2)),
        colour_system=str(design.palette.get("system", "")),
    )
    _, options = compose(request)
    for option in options:
        if option.design.content_hash == design.content_hash:
            return option.design.svg
    raise CompositionRefused(
        "NOT_REPRODUCIBLE",
        f"no option for this brief now hashes to {design.content_hash[:12]}",
    )
