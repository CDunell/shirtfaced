"""Structured representations of the canonical documents."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import (
    RECOMMENDATION_VERDICTS,
    GateName,
    GateStatus,
    ReviewRecommendation,
    ReviewVerdict,
    ShotStatus,
)


class ParsedShot(BaseModel):
    """One row of ``SHOTLIST.md``."""

    model_config = ConfigDict(frozen=True)

    external_id: str = Field(min_length=1, max_length=64)
    sequence: int = Field(ge=1)
    priority: int = Field(default=100, ge=0)
    title: str = Field(min_length=1, max_length=200)
    hero_product: str | None = None
    camera_position: str | None = None
    lighting_source: str | None = None
    status: ShotStatus = ShotStatus.PLANNED
    source_line: int = Field(ge=1)


class DocumentSummary(BaseModel):
    """Identity of a loaded document."""

    model_config = ConfigDict(frozen=True)

    name: str
    sha256: str
    headings: list[str] = Field(default_factory=list)


class LoadedWorld(BaseModel):
    """A validated world, ready to import or display."""

    model_config = ConfigDict(frozen=True)

    slug: str
    name: str
    directory_path: str
    world_document: DocumentSummary
    continuity_document: DocumentSummary
    shotlist_document: DocumentSummary
    shots: list[ParsedShot] = Field(default_factory=list)

    @property
    def planned_shots(self) -> list[ParsedShot]:
        return [shot for shot in self.shots if shot.status is ShotStatus.PLANNED]


class CanonExcerpt(BaseModel):
    """One section of canon sent to a model.

    Excerpts are used rather than whole documents: the planning request carries the
    relevant rules, not every historic record.
    """

    model_config = ConfigDict(frozen=True)

    heading: str
    body: str


class ShotBrief(BaseModel):
    """The shot a plan is being built for."""

    model_config = ConfigDict(frozen=True)

    external_id: str
    title: str
    hero_product: str | None = None
    camera_position: str | None = None
    lighting_source: str | None = None


class PromptPlanRequest(BaseModel):
    """Bounded context for the planning model.

    Everything the model is allowed to see, and nothing else.
    """

    model_config = ConfigDict(frozen=True)

    world_slug: str
    world_name: str
    shot: ShotBrief
    canon_excerpts: list[CanonExcerpt] = Field(default_factory=list)
    recent_continuity: list[str] = Field(default_factory=list)
    rejected_drift: list[str] = Field(default_factory=list)
    canon_notes: list[str] = Field(default_factory=list)
    recent_hero_products: list[str] = Field(default_factory=list)
    recent_camera_positions: list[str] = Field(default_factory=list)
    next_product_priority: list[str] = Field(default_factory=list)
    next_camera_priority: list[str] = Field(default_factory=list)
    selection_reason: str = ""

    @property
    def required_hero_product(self) -> str | None:
        return self.shot.hero_product

    @property
    def required_camera_position(self) -> str | None:
        return self.shot.camera_position


def _non_empty(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value.strip()


class PromptPlan(BaseModel):
    """Structured planning output.

    The field list is fixed by the API contract. Model output is never parsed from
    informal Markdown; it either satisfies this schema or it is rejected.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    scene_summary: str = Field(min_length=1)
    emotional_beat: str = Field(min_length=1)
    hero_product: str = Field(min_length=1)
    product_visibility_instruction: str = Field(min_length=1)
    camera_position: str = Field(min_length=1)
    lighting_source: str = Field(min_length=1)
    documentary_imperfection: str = Field(min_length=1)
    australian_authenticity_anchors: list[str] = Field(min_length=1)
    negative_constraints: list[str] = Field(min_length=1)
    selection_rationale: str = Field(min_length=1)
    production_prompt: str = Field(min_length=1)

    @field_validator(
        "scene_summary",
        "emotional_beat",
        "hero_product",
        "product_visibility_instruction",
        "camera_position",
        "lighting_source",
        "documentary_imperfection",
        "selection_rationale",
        "production_prompt",
    )
    @classmethod
    def _reject_whitespace_only(cls, value: str) -> str:
        return _non_empty(value)

    @field_validator("australian_authenticity_anchors", "negative_constraints")
    @classmethod
    def _reject_blank_entries(cls, value: list[str]) -> list[str]:
        cleaned = [entry.strip() for entry in value if entry.strip()]
        if not cleaned:
            raise ValueError("must contain at least one non-blank entry")
        return cleaned


class GateResult(BaseModel):
    """One review gate.

    ``evidence`` describes what is visible. Confidence is evidentiary, not
    decorative: a low-confidence observation cannot on its own justify rejection.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: GateStatus
    evidence: str = Field(min_length=1)
    codes: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    # Whether this finding can change the recommendation.
    material: bool = False

    @field_validator("evidence")
    @classmethod
    def _reject_blank_evidence(cls, value: str) -> str:
        return _non_empty(value)

    @property
    def is_blocking(self) -> bool:
        """A material failure. Uncertainty is never blocking on its own."""
        return self.status is GateStatus.FAIL and self.material


class ImageReview(BaseModel):
    """Structured review of one generated image.

    Two vocabularies are carried deliberately. ``gates`` is the evidence-based
    contract; the five scores and two compliance booleans are what the data model and
    the dashboard require. The model supplies both, so neither is inferred from the
    other.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    recommendation: ReviewRecommendation
    gates: dict[GateName, GateResult]

    # Scores are 1 to 5, per the data model.
    mood_score: int = Field(ge=1, le=5)
    australian_authenticity_score: int = Field(ge=1, le=5)
    product_visibility_score: int = Field(ge=1, le=5)
    documentary_credibility_score: int = Field(ge=1, le=5)
    story_score: int = Field(ge=1, le=5)

    branding_compliant: bool
    vehicle_compliant: bool

    strongest_success: str = Field(min_length=1)
    material_drift: str | None = None
    # A repeatable rule not already covered by canon. Becomes a pending proposal; it
    # never changes WORLD.md.
    new_rule_proposal: str | None = None
    next_hero_product: str | None = None
    next_camera: str | None = None

    @field_validator("strongest_success")
    @classmethod
    def _reject_blank_success(cls, value: str) -> str:
        return _non_empty(value)

    @field_validator("gates")
    @classmethod
    def _require_every_gate(cls, value: dict[GateName, GateResult]) -> dict[GateName, GateResult]:
        missing = [gate.value for gate in GateName if gate not in value]
        if missing:
            raise ValueError(f"missing gates: {', '.join(missing)}")
        return value

    @property
    def verdict(self) -> ReviewVerdict:
        """The three-value verdict the product specification uses."""
        return RECOMMENDATION_VERDICTS[self.recommendation]

    @property
    def blocking_gates(self) -> list[GateName]:
        """Gates that materially failed, in the contract's declared order."""
        return [name for name in GateName if self.gates[name].is_blocking]

    @property
    def uncertain_gates(self) -> list[GateName]:
        return [name for name in GateName if self.gates[name].status is GateStatus.UNCERTAIN]

    @property
    def recommends_rejection(self) -> bool:
        return self.recommendation is ReviewRecommendation.REJECT
