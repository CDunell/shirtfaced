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
    CheckConstraint,
    DateTime,
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
    ConceptKind,
    ConceptLibrary,
    ConceptStatus,
    DesignAssetKind,
    DesignAttemptMethod,
    DesignAttemptState,
    DesignDecisionKind,
    FailureCode,
    SyncState,
)

__all__ = [
    "ApprovedDesign",
    "DesignAsset",
    "DesignAttempt",
    "DesignAttemptElement",
    "DesignConcept",
    "DesignDecision",
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

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<DesignConcept #{self.external_number} {self.slug!r} {self.status.value!r}>"


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
