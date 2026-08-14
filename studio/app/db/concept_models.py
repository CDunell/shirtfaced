"""ORM models for the design concept pipeline.

Kept apart from ``archive_models.py`` for the same reason that file is kept
apart from ``models.py``: these tables describe a different thing. The archive
holds the parts a design is assembled from; ``composed_designs`` holds one
deterministic output. Neither answers the question the owner actually asks,
which is "what is next, and what happened to the ones we already did?".

The concept library in ``docs/design/TSHIRT_CONCEPT_LIBRARY.md`` is the seed:
excellent human-readable creative documentation, and a hopeless operational
queue. Markdown cannot remember that #4 has three attempts and a rejection, and
every edit risks renumbering the backlog. So the Markdown stays the authored
source and these tables become the record of what was done with it -- the same
split the world pipeline already made between ``SHOTLIST.md`` and ``shots``.

Four ideas carry the design:

* ``DesignConcept`` is the long-lived idea. ``external_number`` is permanent:
  #1 stays #1 forever, retired entries remain rows rather than gaps, and
  nothing is ever renumbered.
* ``DesignAttempt`` is one execution of an idea. A concept can have seventeen.
* ``DesignAsset`` is one set of bytes an attempt produced.
* ``ApprovedDesign`` is the frozen production milestone. Only approved versions
  may reach anything downstream, which is what stops "we made an image" being
  quietly read as "that design is finished".
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import archive_models  # noqa: F401  # registers archive_elements/element_renders
from app.db.base import Base, TimestampMixin
from app.db.models import SHA256_HEX_LENGTH, _enum
from app.domain.enums import (
    CollectionRole,
    ConceptKind,
    ConceptLibrary,
    ConceptStatus,
    DesignAssetKind,
    DesignAttemptMethod,
    DesignAttemptState,
    DesignDecisionKind,
    FailureCode,
    GraphicArchetype,
    LayoutArchetype,
    SyncState,
)

__all__ = [
    "ApprovedDesign",
    "DesignAsset",
    "DesignAttempt",
    "DesignAttemptElement",
    "DesignBrief",
    "DesignConcept",
    "DesignDecision",
    "DesignReviewRecord",
    "ProductLink",
]

EMPTY_VARCHAR_ARRAY = text("'{}'::varchar[]")
EMPTY_TEXT_ARRAY = text("'{}'::text[]")


class DesignConcept(Base, TimestampMixin):
    """One entry from a concept library, with its number kept forever.

    Two kinds of field live here and the importer respects the boundary. The
    authored fields -- title, text, garments, round, retirement -- come from
    the Markdown and are updated when the Markdown changes. The workflow fields
    -- status once the application has moved it, priority, tags, treatment
    lanes, execution notes -- belong to the owner, and a re-import never
    touches them. Where the two disagree about status, the database wins and
    the conflict is reported, exactly as the world importer treats shots.
    """

    __tablename__ = "design_concepts"
    __table_args__ = (
        UniqueConstraint(
            "library", "external_number", name="uq_design_concepts_library_external_number"
        ),
        # Titles repeat in the source ("shirtfaced" appears three times), so the
        # slug carries the number and stays unique on its own.
        UniqueConstraint("slug", name="uq_design_concepts_slug"),
        CheckConstraint("external_number >= 1", name="external_number_positive"),
        # The parser's classification of how retirement was written in the
        # source. A fact about the Markdown, not a workflow state.
        CheckConstraint(
            "retirement IN ('', 'hard', 'unconditional', 'conditional')",
            name="retirement_known",
        ),
        Index("ix_design_concepts_status", "status"),
        # Partial: "what is next" only ever reads the undone end of the queue,
        # and that set shrinks while the decided set grows without bound.
        Index(
            "ix_design_concepts_queue",
            "library",
            "priority",
            "external_number",
            postgresql_where=text("status IN ('backlog', 'ready')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    library: Mapped[ConceptLibrary] = mapped_column(
        _enum(ConceptLibrary, "concept_library"), nullable=False
    )
    # The number in the source document. Permanent identity: #1 stays #1, a
    # retired entry keeps its number, and nothing ever moves up one.
    external_number: Mapped[int] = mapped_column(Integer, nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)

    # --- Authored fields. The importer owns these. ---------------------------
    # Cleaned title: a hard retirement's "RETIRED — " prefix is stripped, with
    # the raw form preserved in parsed_json. The lane parenthetical stays.
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # The owner's words, verbatim from the em-dash to the end of the line.
    # Never edited: the pipeline decides what happens to a concept, not what
    # it says.
    concept_text: Mapped[str] = mapped_column(Text, nullable=False)
    retirement: Mapped[str] = mapped_column(String(16), nullable=False, server_default="")
    # Declared garments, parsed from the round 05-06 entry prefix ("Tee.",
    # "Crop/tee."). Earlier rounds have none.
    garments: Mapped[list[str]] = mapped_column(
        ARRAY(String(16)), nullable=False, server_default=EMPTY_VARCHAR_ARRAY
    )
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    round_label: Mapped[str] = mapped_column(String(64), nullable=False, server_default="")
    source_path: Mapped[str] = mapped_column(String(512), nullable=False)
    source_line: Mapped[int | None] = mapped_column(Integer)
    # SHA-256 of the library document that last touched this row, so a wording
    # change is attributable to the edit that made it.
    source_document_hash: Mapped[str] = mapped_column(String(SHA256_HEX_LENGTH), nullable=False)
    # What the parser saw but the columns do not hold: the raw title of a hard
    # retirement, the raw garment prefix, the salvage clause of a conditional.
    parsed_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # --- Workflow fields. The owner owns these; import never touches them. ---
    status: Mapped[ConceptStatus] = mapped_column(
        _enum(ConceptStatus, "concept_status"),
        nullable=False,
        default=ConceptStatus.BACKLOG,
        server_default=ConceptStatus.BACKLOG.value,
    )
    concept_kind: Mapped[ConceptKind] = mapped_column(
        _enum(ConceptKind, "concept_kind"),
        nullable=False,
        default=ConceptKind.OTHER,
        server_default=ConceptKind.OTHER.value,
    )
    # Queue knob. Lower sorts first, matching "ORDER BY priority, number".
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text()), nullable=False, server_default=EMPTY_TEXT_ARRAY
    )
    # Same vocabulary as design_observations.treatment_lanes, so a concept can
    # retrieve precedent from the corpus rather than styling from scratch.
    treatment_lanes: Mapped[list[str]] = mapped_column(
        ARRAY(Text()), nullable=False, server_default=EMPTY_TEXT_ARRAY
    )
    # Owner-authored execution guidance, filled as concepts are worked. Not
    # parseable from the prose, and a guess presented as a fact would be worse
    # than an empty field.
    preferred_execution: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    integral_text: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    constraints: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    notes: Mapped[str] = mapped_column(Text, nullable=False, server_default="")

    attempts: Mapped[list[DesignAttempt]] = relationship(
        back_populates="concept",
        cascade="all, delete-orphan",
        order_by="DesignAttempt.attempt_number",
    )
    approved_versions: Mapped[list[ApprovedDesign]] = relationship(
        back_populates="concept",
        cascade="all, delete-orphan",
        order_by="ApprovedDesign.version",
    )
    # At most one. What the product is, decided before artwork exists.
    brief: Mapped[DesignBrief | None] = relationship(
        back_populates="concept", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<DesignConcept #{self.external_number} {self.slug!r} {self.status.value!r}>"


class DesignBrief(Base, TimestampMixin):
    """What the product is, decided before any artwork exists.

    Constitution steps 1-4 and 6, which had no representation in software at
    all: define the product, define its role in the range, select the garment
    architecture, select the graphic architecture, integrate typography. The
    14 August audit's finding was that the research bench produced a graphic
    idea and jumped straight to artwork, "which is why output arrives as
    competent generic work with no collection role and no declared archetype".

    One brief per concept. A concept is the long-lived product idea, and §3's
    required fields -- blank, fit, weight, colour, wash, method -- describe that
    idea rather than one execution of it. ``create_attempt`` snapshots this into
    ``brief_snapshot`` so an attempt stays explicable after the brief changes.

    Two of the scorecard's thirteen hard gates finally have a source of truth
    here: ``product_blank_defined`` and ``collection_role_defined`` were being
    answered by a person with nothing in the software to answer them from.
    """

    __tablename__ = "design_briefs"
    __table_args__ = (UniqueConstraint("concept_id", name="uq_design_briefs_concept_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_concepts.id", ondelete="CASCADE"), nullable=False
    )

    # --- Step 1: define the product. Constitution §3's required fields. ------
    garment_category: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    canonical_blank: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    fit_block: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    fabric_weight: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    garment_colour: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    wash: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    production_method: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    intended_use: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    commercial_tier: Mapped[str] = mapped_column(String(60), nullable=False, server_default="")
    target_release: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")

    # --- Steps 2 and 4: the two the exit test gates an attempt on. ----------
    # Nullable because a brief is filled in over time; the gate is that an
    # attempt cannot open until both are set, not that a draft cannot exist.
    collection_role: Mapped[CollectionRole | None] = mapped_column(
        _enum(CollectionRole, "collection_role")
    )
    graphic_archetype: Mapped[GraphicArchetype | None] = mapped_column(
        _enum(GraphicArchetype, "graphic_archetype")
    )
    layout_archetype: Mapped[LayoutArchetype | None] = mapped_column(
        _enum(LayoutArchetype, "layout_archetype")
    )
    # A departure from the approved library needs a written reason (§6).
    archetype_departure_reason: Mapped[str] = mapped_column(Text, nullable=False, server_default="")

    # --- Step 3: garment architecture. zone key -> ZoneState (§5). ----------
    # JSONB because the zones available depend on the garment: a cap has three
    # panels and a hoodie has a pocket, and a column per zone would be a table
    # that grows every time a blank is added.
    zones: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # --- Step 6: typography, by function (§10). identity/display/information.
    typography: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # What the advisor recommended when these were chosen, and on what evidence.
    # Kept so a decision can be read back against the advice it was given --
    # including where the owner went the other way, which is the interesting case.
    advisor_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    notes: Mapped[str] = mapped_column(Text, nullable=False, server_default="")

    concept: Mapped[DesignConcept] = relationship(back_populates="brief")

    @property
    def ready_for_artwork(self) -> bool:
        """The plan's exit test, as one property.

        Deliberately narrower than the constitution: §3 requires eleven fields
        before artwork, and this gates on two. Widening it is a decision about
        how much ceremony precedes a first sketch, and that is the owner's.
        """
        return self.collection_role is not None and self.graphic_archetype is not None


class DesignAttempt(Base, TimestampMixin):
    """One execution of a concept.

    The design-side equivalent of ``GenerationAttempt``: everything needed to
    explain the result is recorded before the result exists. ``brief_snapshot``
    keeps the concept as it stood when the attempt started, because the library
    can be re-imported afterwards and the attempt must still be explicable.
    """

    __tablename__ = "design_attempts"
    __table_args__ = (
        # The race arbiter: two concurrent attempts computing max+1 collide
        # here instead of both succeeding.
        UniqueConstraint(
            "concept_id", "attempt_number", name="uq_design_attempts_concept_id_attempt_number"
        ),
        CheckConstraint("attempt_number >= 1", name="attempt_number_positive"),
        Index("ix_design_attempts_concept_id", "concept_id"),
        # Partial: the review queue only ever asks for the undecided ones.
        Index(
            "ix_design_attempts_awaiting",
            "created_at",
            postgresql_where=text("state = 'awaiting_decision'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_concepts.id", ondelete="CASCADE"), nullable=False
    )
    # Set when this attempt varies an earlier one, so the chain is intact.
    parent_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_attempts.id", ondelete="SET NULL")
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[DesignAttemptMethod] = mapped_column(
        _enum(DesignAttemptMethod, "design_attempt_method"), nullable=False
    )
    state: Mapped[DesignAttemptState] = mapped_column(
        _enum(DesignAttemptState, "design_attempt_state"),
        nullable=False,
        default=DesignAttemptState.PLANNED,
        server_default=DesignAttemptState.PLANNED.value,
    )

    # The concept as it stood when this attempt started.
    brief_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    source_concept_hash: Mapped[str] = mapped_column(
        String(SHA256_HEX_LENGTH), nullable=False, server_default=""
    )

    # How the artwork was asked for, when a model was involved. Empty for
    # deterministic composition and manual imports.
    production_prompt: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    model: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    model_settings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    reference_inputs: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    execution_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    failure_code: Mapped[FailureCode | None] = mapped_column(_enum(FailureCode, "failure_code"))
    failure_message: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str] = mapped_column(Text, nullable=False, server_default="")

    concept: Mapped[DesignConcept] = relationship(back_populates="attempts")
    parent: Mapped[DesignAttempt | None] = relationship(remote_side=[id])
    assets: Mapped[list[DesignAsset]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="DesignAsset.created_at",
    )
    # At most one. The uniqueness is enforced by the database, not this mapping.
    decision: Mapped[DesignDecision | None] = relationship(
        back_populates="attempt", cascade="all, delete-orphan", uselist=False
    )
    # Also at most one, for the same reason: a review is a working document
    # until the decision freezes it, not a log of sittings.
    review: Mapped[DesignReviewRecord | None] = relationship(
        back_populates="attempt", cascade="all, delete-orphan", uselist=False
    )
    approved_design: Mapped[ApprovedDesign | None] = relationship(
        back_populates="attempt", uselist=False
    )
    elements: Mapped[list[DesignAttemptElement]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
        order_by="DesignAttemptElement.role",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<DesignAttempt #{self.attempt_number} {self.state.value!r}>"


class DesignAsset(Base):
    """One stored design file. Immutable: replacing bytes is a new row.

    Mirrors ``ImageAsset``: the database stores a key relative to
    ``ASSETS_ROOT`` so the same row works on any host, and the sha256 recorded
    at write time is the standing assertion the bytes have not drifted.
    Uniqueness is on the path rather than the kind, because separations and
    mockups legitimately repeat per attempt.
    """

    __tablename__ = "design_assets"
    __table_args__ = (
        UniqueConstraint(
            "design_attempt_id",
            "relative_path",
            name="uq_design_assets_design_attempt_id_relative_path",
        ),
        Index("ix_design_assets_design_attempt_id", "design_attempt_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    design_attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_attempts.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[DesignAssetKind] = mapped_column(
        _enum(DesignAssetKind, "design_asset_kind"), nullable=False
    )
    # Relative to ASSETS_ROOT, so the same row works on any host.
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(SHA256_HEX_LENGTH), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    attempt: Mapped[DesignAttempt] = relationship(back_populates="assets")


class DesignDecision(Base):
    """The owner's judgment on one attempt. Immutable, and exactly one.

    The design-side ``HumanDecision``: that table's foreign key is bound to
    photography's ``generation_attempts``, so it cannot serve here, but its
    shape is proven and is mirrored deliberately -- a decision row is written
    once, names its author, and is never edited or deleted.
    """

    __tablename__ = "design_decisions"
    __table_args__ = (
        UniqueConstraint("design_attempt_id", name="uq_design_decisions_design_attempt_id"),
        # A decision nobody signed is an assertion, not a decision.
        CheckConstraint("actor <> ''", name="decision_has_an_author"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    design_attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_attempts.id", ondelete="CASCADE"), nullable=False
    )
    decision: Mapped[DesignDecisionKind] = mapped_column(
        _enum(DesignDecisionKind, "design_decision_kind"), nullable=False
    )
    # The owner's words, verbatim. reason explains a rejection, note annotates
    # an approval, instruction directs a variation.
    reason: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    instruction: Mapped[str | None] = mapped_column(Text)
    actor: Mapped[str] = mapped_column(String(64), nullable=False, server_default=text("'owner'"))
    # Lets a retried request recognise itself instead of conflicting.
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    attempt: Mapped[DesignAttempt] = relationship(back_populates="decision")


class DesignReviewRecord(Base, TimestampMixin):
    """One attempt's review against the scorecard: the answers and the verdict.

    The row that closes the gap the 14 August audit called blocking. Nothing
    could answer the scorecard's human questions, so ``score_design`` could
    never receive a complete input and no design could pass -- not one, ever,
    by construction. This is where those answers live.

    One row per attempt, not one per sitting. A review is a working document
    while the attempt is undecided: answering three more gates updates it, and
    a pile of half-finished reviews would answer nothing. The moment a
    ``design_decisions`` row exists the review is frozen by
    ``design_scoring.score_design``, because what justified a decision has to
    stay readable exactly as it was when the decision was made.

    ``evaluation`` stores the computed verdict beside the raw answers on
    purpose. The arithmetic is deterministic and could be recomputed, but the
    thresholds are explicitly calibratable (``DESIGN_REVIEW_SCORECARD.md``
    §12) -- so a recomputation next year would silently re-judge last year's
    decisions against numbers nobody applied at the time.
    """

    __tablename__ = "design_reviews"
    __table_args__ = (
        UniqueConstraint("design_attempt_id", name="uq_design_reviews_design_attempt_id"),
        CheckConstraint("reviewer <> ''", name="review_has_a_reviewer"),
        CheckConstraint("percentage >= 0 AND percentage <= 100", name="percentage_is_a_percentage"),
        # Partial: the attempt screen asks for the ones still open, and that
        # set stays small while the decided set grows without bound.
        Index(
            "ix_design_reviews_eligible",
            "updated_at",
            postgresql_where=text("eligible_for_design_approval"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    design_attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_attempts.id", ondelete="CASCADE"), nullable=False
    )
    reviewer: Mapped[str] = mapped_column(String(64), nullable=False)

    # What the machine measured off the artwork: coverage, ink count, the
    # T1/T2/T3 reductions. Kept beside the human answers rather than in its own
    # table because it is evidence for this review and meaningless without it.
    measurements: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    # The thirteen gates and the nine categories, in domain.ts's shape.
    hard_gates: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    score_categories: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    # What the reviewer asked for, before the scorecard was consulted.
    requested_decision: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="design_approved"
    )

    # The verdict, and the parts of it worth querying without opening the blob.
    evaluation: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    total_score: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0"))
    percentage: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0"))
    band: Mapped[str] = mapped_column(String(32), nullable=False, server_default="")
    eligible_for_design_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    scored_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    attempt: Mapped[DesignAttempt] = relationship(back_populates="review")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<DesignReviewRecord {self.percentage:.0f}/100 {self.band!r}>"


class ApprovedDesign(Base):
    """The frozen production milestone: one approved version of a concept.

    A concept can have seventeen attempts; only rows here may reach anything
    downstream. Versions are immutable -- a later edit is a new attempt and a
    new version, and ``superseded_at`` is the old row's one mutable field: a
    tombstone recording when a newer version took over, never a change to what
    was approved.
    """

    __tablename__ = "approved_designs"
    __table_args__ = (
        UniqueConstraint("design_attempt_id", name="uq_approved_designs_design_attempt_id"),
        UniqueConstraint("concept_id", "version", name="uq_approved_designs_concept_id_version"),
        CheckConstraint("version >= 1", name="version_positive"),
        CheckConstraint("approved_by <> ''", name="approval_has_an_author"),
        Index("ix_approved_designs_concept_id", "concept_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_concepts.id", ondelete="CASCADE"), nullable=False
    )
    design_attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_attempts.id", ondelete="CASCADE"), nullable=False
    )
    # RESTRICT: an approved design must keep its master. Deleting the bytes a
    # production milestone points at should be loud, not a cascade.
    master_asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_assets.id", ondelete="RESTRICT"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_by: Mapped[str] = mapped_column(String(64), nullable=False)
    approved_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    superseded_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    # Print method, colours, sizing -- whatever production needs frozen with
    # the approval rather than recalled later.
    production_spec: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    concept: Mapped[DesignConcept] = relationship(back_populates="approved_versions")
    attempt: Mapped[DesignAttempt] = relationship(back_populates="approved_design")
    master_asset: Mapped[DesignAsset] = relationship()


class DesignAttemptElement(Base):
    """Which archive elements an attempt was assembled from, by role.

    Normalises what ``composed_designs.parts`` keeps as a JSON blob of element
    key strings, so an element can be traced to every attempt it appears in
    with a join instead of a JSON scan. RESTRICT on the element: provenance
    rows must not vanish because the archive was tidied.
    """

    __tablename__ = "design_attempt_elements"
    __table_args__ = (
        # Parts are role -> element: one element per role per attempt.
        UniqueConstraint(
            "design_attempt_id", "role", name="uq_design_attempt_elements_design_attempt_id_role"
        ),
        Index("ix_design_attempt_elements_element_id", "element_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    design_attempt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_attempts.id", ondelete="CASCADE"), nullable=False
    )
    element_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("archive_elements.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    render_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("element_renders.id", ondelete="SET NULL")
    )
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    attempt: Mapped[DesignAttempt] = relationship(back_populates="elements")


class ProductLink(Base, TimestampMixin):
    """A soft reference from an approved design to a shop product.

    Studio and the shop are separate databases by decision, so this is an
    identifier and a sync state, never a foreign key. If the commerce stack is
    replaced, the creative provenance on this side survives untouched.
    """

    __tablename__ = "product_links"
    __table_args__ = (
        UniqueConstraint(
            "approved_design_id",
            "external_system",
            name="uq_product_links_approved_design_id_external_system",
        ),
        # A link that claims to be synced must say what it synced to.
        CheckConstraint(
            "sync_state <> 'succeeded' OR external_product_id <> ''",
            name="synced_links_name_a_product",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    approved_design_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("approved_designs.id", ondelete="CASCADE"), nullable=False
    )
    external_system: Mapped[str] = mapped_column(
        String(40), nullable=False, server_default=text("'shirtfaced_shop'")
    )
    external_product_id: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    external_slug: Mapped[str] = mapped_column(String(200), nullable=False, server_default="")
    sync_state: Mapped[SyncState] = mapped_column(
        _enum(SyncState, "sync_state"),
        nullable=False,
        default=SyncState.NOT_ATTEMPTED,
        server_default=SyncState.NOT_ATTEMPTED.value,
    )
    last_synced_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    approved_design: Mapped[ApprovedDesign] = relationship()
