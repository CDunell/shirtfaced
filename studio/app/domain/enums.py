"""Enumerations shared by the domain and the database."""

from __future__ import annotations

from enum import StrEnum


class WorldStatus(StrEnum):
    """Lifecycle of a world.

    Version 1 runs a single active world. ``archived`` exists so a finished world can
    be retained for its history without appearing as a production target.
    """

    ACTIVE = "active"
    ARCHIVED = "archived"


class AttemptState(StrEnum):
    """Lifecycle of one generation attempt, per the architecture document.

    Phase 3 carries an attempt as far as ``GENERATED``. Review moves it through
    ``REVIEWING`` to ``AWAITING_DECISION``; the human decision settles it at
    ``APPROVED`` or ``REJECTED``.
    """

    PLANNED = "planned"
    PROMPT_READY = "prompt_ready"
    GENERATING = "generating"
    GENERATED = "generated"
    REVIEWING = "reviewing"
    AWAITING_DECISION = "awaiting_decision"
    APPROVED = "approved"
    REJECTED = "rejected"
    # Terminal, and deliberately not "rejected": the owner asked for another take,
    # which is not the same as saying the image was wrong. Recording it as a rejection
    # would pollute rejected-drift learning, which is the planner's strongest input.
    VARIATION_REQUESTED = "variation_requested"
    FAILED = "failed"


# An attempt in one of these states occupies the world: a partial unique index
# permits only one at a time, so a second Continue World is refused with 409 rather
# than quietly starting a parallel generation.
ACTIVE_ATTEMPT_STATES: frozenset[AttemptState] = frozenset(
    {
        AttemptState.PLANNED,
        AttemptState.PROMPT_READY,
        AttemptState.GENERATING,
        AttemptState.GENERATED,
        AttemptState.REVIEWING,
        AttemptState.AWAITING_DECISION,
    }
)


class HumanDecisionKind(StrEnum):
    """What the owner decided. Final, and never inferred from a review."""

    APPROVED = "approved"
    REJECTED = "rejected"
    VARIATION_REQUESTED = "variation_requested"


# The attempt state each decision moves the attempt to. All three are terminal and
# outside the active set, so the world is released either way.
DECISION_ATTEMPT_STATES: dict[HumanDecisionKind, AttemptState] = {
    HumanDecisionKind.APPROVED: AttemptState.APPROVED,
    HumanDecisionKind.REJECTED: AttemptState.REJECTED,
    HumanDecisionKind.VARIATION_REQUESTED: AttemptState.VARIATION_REQUESTED,
}


class SyncState(StrEnum):
    """Whether a downstream system caught up with the decision.

    The database, the filesystem and Git cannot share a transaction, so each is
    reported separately rather than collapsed into one success flag.
    """

    NOT_ATTEMPTED = "not_attempted"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class AuditEventType(StrEnum):
    """Append-only record of what happened."""

    DECISION_RECORDED = "decision_recorded"
    MARKDOWN_UPDATED = "markdown_updated"
    MARKDOWN_FAILED = "markdown_failed"
    WORLD_REIMPORTED = "world_reimported"
    IMPORT_FAILED = "import_failed"
    GIT_COMMITTED = "git_committed"
    GIT_FAILED = "git_failed"
    REFERENCE_PROMOTED = "reference_promoted"
    REFERENCE_FAILED = "reference_failed"
    REFERENCE_ARCHIVED = "reference_archived"
    REFERENCE_PINNED = "reference_pinned"
    RECONCILIATION_REQUIRED = "reconciliation_required"
    # Design pipeline events. Recorded here rather than in a new outbox table:
    # an outbox with no consumer is speculative, and the audit trail is already
    # the append-only record of what the application did.
    DESIGN_DECISION_RECORDED = "design_decision_recorded"
    DESIGN_APPROVED = "design_approved"
    # Visual Asset Library. Approval and deprecation are decisions about what
    # production may reach, so they are recorded here rather than inferred from
    # a status column's current value.
    VISUAL_ASSET_INGESTED = "visual_asset_ingested"
    VISUAL_ASSET_APPROVED = "visual_asset_approved"
    VISUAL_ASSET_DEPRECATED = "visual_asset_deprecated"
    VISUAL_ASSET_REJECTED = "visual_asset_rejected"
    CAST_ASSET_LINKED = "cast_asset_linked"
    SCENE_MASTER_REGISTERED = "scene_master_registered"
    SCENE_MASTER_APPROVED = "scene_master_approved"
    CONTACT_SHEET_REGISTERED = "contact_sheet_registered"
    CONTACT_SHEET_APPROVED = "contact_sheet_approved"
    CONTACT_SHEET_REJECTED = "contact_sheet_rejected"
    COVERAGE_FRAME_DERIVED = "coverage_frame_derived"
    COVERAGE_FRAME_APPROVED = "coverage_frame_approved"
    AUDIO_ASSET_INGESTED = "audio_asset_ingested"
    AUDIO_ASSET_APPROVED = "audio_asset_approved"
    AUDIO_ASSET_DEPRECATED = "audio_asset_deprecated"
    SOUNDTRACK_ASSET_LINKED = "soundtrack_asset_linked"
    LOCATION_REGISTERED = "location_registered"
    LOCATION_ASSET_LINKED = "location_asset_linked"
    LOCATION_MASTER_APPROVED = "location_master_approved"


class ReviewRecommendation(StrEnum):
    """What the review model advises.

    A recommendation, never a decision. The owner records the outcome separately in
    the human decision, using the canon's own vocabulary.
    """

    APPROVE = "APPROVE_RECOMMENDED"
    APPROVE_WITH_NOTE = "APPROVE_WITH_NOTE_RECOMMENDED"
    REJECT = "REJECT_RECOMMENDED"
    UNCERTAIN = "REVIEW_UNCERTAIN"


class ReviewVerdict(StrEnum):
    """The verdict vocabulary used by the product specification and data model.

    Derived from the recommendation, so both the gate-based review contract and the
    original three-value verdict are satisfied without inventing anything.
    """

    APPROVED = "approved"
    APPROVED_WITH_NOTE = "approved_with_note"
    REJECTED = "rejected"
    UNCERTAIN = "uncertain"


RECOMMENDATION_VERDICTS: dict[ReviewRecommendation, ReviewVerdict] = {
    ReviewRecommendation.APPROVE: ReviewVerdict.APPROVED,
    ReviewRecommendation.APPROVE_WITH_NOTE: ReviewVerdict.APPROVED_WITH_NOTE,
    ReviewRecommendation.REJECT: ReviewVerdict.REJECTED,
    ReviewRecommendation.UNCERTAIN: ReviewVerdict.UNCERTAIN,
}


class GateStatus(StrEnum):
    """The outcome of one review gate."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class GateName(StrEnum):
    """The ten gates, named after the Continuity Director's tests in WORLD.md.

    ``STRUCTURAL_PLAUSIBILITY`` is not one of the Continuity Director's creative
    tests. It was added because the other nine are all judgements of taste and
    intent, and none of them asks whether the thing photographed could exist. A car
    with no front seats scored documentary credibility 4/5; a van whose entire rear
    was missing scored 5/5. Both were right by every rubric that was being applied.
    """

    MOOD = "mood"
    AUSTRALIAN_AUTHENTICITY = "australian_authenticity"
    PRODUCT_VISIBILITY = "product_visibility"
    THIRD_PARTY_BRANDING = "third_party_branding"
    VEHICLE_CONTINUITY = "vehicle_continuity"
    WARDROBE_BALANCE = "wardrobe_balance"
    COMPOSITION = "composition"
    DOCUMENTARY_CREDIBILITY = "documentary_credibility"
    STORY = "story"
    STRUCTURAL_PLAUSIBILITY = "structural_plausibility"


class ProposalClassification(StrEnum):
    """How a proposed rule relates to canon that already exists.

    Advisory only. It orders the queue and explains the recommendation; the owner
    decides. The two live rulings on 5 August 2026 both went against what a naive
    reading would have said, which is why this never decides anything.
    """

    ALREADY_COVERED = "already_covered"
    GENUINE_ADDITION = "genuine_addition"
    REFINEMENT = "refinement"
    CONTRADICTION = "contradiction"
    TOO_SPECIFIC = "too_specific"


# Classifications that do not warrant a canon change on their own. Approval is still
# the owner's to give; these simply sort to the bottom of the queue.
NON_ADDITIVE_CLASSIFICATIONS: frozenset[ProposalClassification] = frozenset(
    {
        ProposalClassification.ALREADY_COVERED,
        ProposalClassification.TOO_SPECIFIC,
        ProposalClassification.CONTRADICTION,
    }
)


class CanonProposalStatus(StrEnum):
    """Lifecycle of a proposed permanent rule.

    A proposal never changes WORLD.md. Only an explicit human approval can, and that
    arrives with the canon proposal phase.
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    FAILED = "failed"


class ReferenceState(StrEnum):
    """Where a reference frame sits in the library.

    Only ``ACTIVE`` and ``PINNED`` reach the planner. The rest is history: nothing is
    deleted, because an approved frame is a record of a decision as well as an input.
    """

    ACTIVE = "active"
    ARCHIVED = "archived"
    # Exceptional frames. Never aged out automatically.
    PINNED = "pinned"


# The states the planner reads. Pinned frames are always among them.
PLANNING_REFERENCE_STATES: frozenset[ReferenceState] = frozenset(
    {ReferenceState.ACTIVE, ReferenceState.PINNED}
)


class AssetKind(StrEnum):
    """What a stored image is."""

    ORIGINAL = "original"
    THUMBNAIL = "thumbnail"
    REFERENCE = "reference"


class VisualAssetKind(StrEnum):
    """What part of production a Visual Asset Library image belongs to.

    ``VISUAL_ASSET_LIBRARY.md`` §18: one asset substrate, not one store per
    domain, so SHA, provenance, rights and lineage behave the same way whatever
    the image is of. The kind says which domain owns it; the link tables say
    which record.
    """

    CAST = "cast"
    LOCATION = "location"
    SCENE_MASTER = "scene_master"
    COVERAGE = "coverage"
    PROP = "prop"
    REFERENCE = "reference"
    OTHER = "other"


class VisualAssetSourceType(StrEnum):
    """How the bytes came to exist.

    §13 gates production on rights, and rights depend on origin. Stored as a
    property of the asset because it can never be recovered from the pixels.
    """

    UPLOAD = "upload"
    GENERATED = "generated"
    EDITED = "edited"
    IMPORTED = "imported"
    COMMISSIONED = "commissioned"
    LICENSED_STOCK = "licensed_stock"


class VisualAssetStatus(StrEnum):
    """Where an asset sits in the approval lifecycle, §12.

    ``pending -> approved -> deprecated``, or ``pending -> rejected``. Nothing
    becomes canonical by being newest, and deprecation is a state rather than a
    deletion: bytes an approved master or a finished clip depends on stay
    resolvable.
    """

    PENDING = "pending"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class AudioSourceType(StrEnum):
    """How an audio file came to exist.

    The same six origins as :class:`VisualAssetSourceType`, kept as its own type
    rather than borrowed: a column named after visual assets on an audio table
    would be a name that lies, and renaming the visual one to suit audio would
    churn tables that are already deployed.
    """

    UPLOAD = "upload"
    GENERATED = "generated"
    EDITED = "edited"
    IMPORTED = "imported"
    COMMISSIONED = "commissioned"
    LICENSED_STOCK = "licensed_stock"


class AudioAssetStatus(StrEnum):
    """Where an audio file sits in the approval lifecycle.

    Mirrors :class:`VisualAssetStatus` for the same reason and with the same
    rule: nothing becomes the mix that ships by being newest.
    """

    PENDING = "pending"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


# The deliverables SOUNDTRACK.md §8 and §6 name. A vocabulary the interface
# offers, not a constraint -- free text for the same reason cast roles are, so a
# mix nobody anticipated is still storable.
SOUNDTRACK_ASSET_ROLES: tuple[str, ...] = (
    # §8 required masters.
    "full_master",
    "instrumental",
    "tv_mix",
    "no_gang",
    "gang_only",
    "a_cappella",
    "clean",
    "premaster",
    # §6 cutdown map, named by the job the edit gives them. The length is in the
    # name because that is how both the spec and the edit refer to them.
    "hook_sting_6s",
    "hero_social_10s",
    "canonical_12s5",
    "paid_social_15s",
    "story_reel_30s",
    "bed_60s",
    "loop_8_bar",
    # §8 stem families.
    "stem_drums",
    "stem_bass",
    "stem_guitars",
    "stem_keys",
    "stem_vocals",
    "stem_fx",
    "stem_mix_groups",
    "other",
)


class LocationAssetRole(StrEnum):
    """What a location image is, §6.2.

    Closed, unlike the cast roles, and for the opposite reason: this decides
    whether an image may become the base master a scene is built into. A typo
    that silently created a new class would be a way to promote a photograph
    nobody assessed.
    """

    SCOUT_PHOTO = "scout_photo"
    SURVEY_WIDE = "survey_wide"
    SURVEY_DETAIL = "survey_detail"
    EMPTY_PLATE = "empty_plate"
    PARTICIPANT_NEUTRAL_BASE = "participant_neutral_base"
    GENERATED_LOCATION_PLATE = "generated_location_plate"
    APPROVED_BASE_MASTER = "approved_base_master"
    LIGHTING_REFERENCE = "lighting_reference"
    SCALE_REFERENCE = "scale_reference"


# The classes §6.3 will accept as the plate a scene is built into. A detail
# survey or a lighting reference is useful and is not a stage.
BASE_MASTER_ROLES: frozenset[LocationAssetRole] = frozenset(
    {
        LocationAssetRole.EMPTY_PLATE,
        LocationAssetRole.PARTICIPANT_NEUTRAL_BASE,
        LocationAssetRole.GENERATED_LOCATION_PLATE,
        LocationAssetRole.APPROVED_BASE_MASTER,
    }
)


# The cast reference roles §5.2 names. A vocabulary the interface offers, not a
# constraint the database enforces: the column is free text, because a closed
# list would mean a photograph nobody anticipated cannot be filed at all, and
# the standing rule is that everything gets ingested. Adding a role here makes
# it offerable; it was already storable.
CAST_ASSET_ROLES: tuple[str, ...] = (
    "full_body_neutral",
    "head_shoulders_neutral",
    "expression_bridge",
    "profile_left",
    "profile_right",
    "three_quarter",
    "shouting",
    "laughing",
    "sleeping",
    "severe_head_angle",
    "wardrobe_reference",
    "body_reference",
    "historical",
    # The Nano Banana 3x3 identity sheet, one per character. A first-class
    # reference asset, not a preview: panels are extracted from it by feeding it
    # back to the model, never by cropping it.
    "contact_sheet",
    "other",
)

# The two roles the renderer's fixed slots used to hold, and the only ones the
# legacy ``var/cast/<slug>/`` mirror can express.
PRIMARY_CAST_ROLES: tuple[str, ...] = ("full_body_neutral", "head_shoulders_neutral")


class FailureCode(StrEnum):
    """Why an attempt failed.

    Classified rather than free text so failures can be counted, and so retry can
    refuse the ones that will never succeed on their own.
    """

    PLANNING_FAILED = "planning_failed"
    REVIEW_FAILED = "review_failed"
    PROVIDER_ERROR = "provider_error"
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_REFUSED = "provider_refused"
    INVALID_IMAGE = "invalid_image"
    STORAGE_FAILED = "storage_failed"
    CONFIGURATION = "configuration"
    INTERNAL = "internal"


# Retrying these repeats the same failure: the cause is a key, a permission, a
# configuration value or a rule, none of which change by asking again.
PERMANENT_FAILURES: frozenset[FailureCode] = frozenset(
    {
        FailureCode.PROVIDER_REFUSED,
        FailureCode.CONFIGURATION,
    }
)


class ShotStatus(StrEnum):
    """Lifecycle of a planned shot, per the data model."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    ABANDONED = "abandoned"


# Status markers used in SHOTLIST.md. The emoji are the documented form; the text
# spellings keep the file usable in a plain terminal, as the Markdown contract
# requires.
SHOT_STATUS_MARKERS: dict[str, ShotStatus] = {
    "⬜": ShotStatus.PLANNED,
    "🟡": ShotStatus.IN_PROGRESS,
    "✅": ShotStatus.APPROVED,
    "❌": ShotStatus.REJECTED,
    "planned": ShotStatus.PLANNED,
    "in progress": ShotStatus.IN_PROGRESS,
    "in-progress": ShotStatus.IN_PROGRESS,
    "in_progress": ShotStatus.IN_PROGRESS,
    "approved": ShotStatus.APPROVED,
    "rejected": ShotStatus.REJECTED,
    "abandoned": ShotStatus.ABANDONED,
}


def parse_shot_status(value: str) -> ShotStatus | None:
    """Resolve a shotlist status cell, or ``None`` when it is not recognised."""
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned in SHOT_STATUS_MARKERS:
        return SHOT_STATUS_MARKERS[cleaned]
    return SHOT_STATUS_MARKERS.get(cleaned.casefold())


class LicenceStatus(StrEnum):
    """How well the right to use an archive element is established.

    Elements go on garments that are sold, so this is not advisory. The
    composer may only reach a verified element; everything else is stored so
    the find is not lost, and refused so it cannot be printed by accident.
    """

    # Checked against the source, terms recorded, commercial use permitted.
    VERIFIED = "verified"
    # Held but not yet checked. Never usable -- absence of a check is not a pass.
    UNVERIFIED = "unverified"
    # Checked and found to forbid the use we need. Kept so it is not re-found.
    REFUSED = "refused"


class ElementFamily(StrEnum):
    """The archive's families.

    Split by how an element comes into being rather than by what it looks
    like, because that is what determines whether it is authored as parametric
    geometry or ingested with a licence trail.
    """

    # Authored: parametric geometry and render recipes.
    FRAME = "frame"
    TYPE_LAYOUT = "type_layout"
    WORDMARK = "wordmark"
    BADGE = "badge"
    TEXTURE = "texture"
    PRINT_EFFECT = "print_effect"
    PATCH_LABEL = "patch_label"
    PLACEMENT = "placement"
    COMPOSITION_TEMPLATE = "composition_template"
    COLOUR_SYSTEM = "colour_system"
    # Ingested: artwork with a taxonomy and a licence.
    ILLUSTRATION_PART = "illustration_part"
    SYMBOL = "symbol"
    ORNAMENT = "ornament"
    PATTERN = "pattern"


class ConceptLibrary(StrEnum):
    """Which concept library a design concept was seeded from.

    Numbering is only unique within a library -- tee concept 5 and headwear H05
    are different ideas -- so the library is part of the concept's identity, not
    a display detail. Only the tee library is imported today; the other two are
    named now so their arrival is a data change, not a schema change.
    """

    TSHIRT = "tshirt"
    HEADWEAR = "headwear"
    BRAND_GARMENT = "brand_garment"
    # Concepts the research bench produced rather than a document seeded.
    #
    # Its own library rather than a high band of tee numbers, because the
    # importer matches on ``(library, external_number)`` and updates the
    # authored fields of whatever it matches. A research concept holding the
    # next free tee number would be silently overwritten -- title, text and all
    # -- the day the Markdown grew to that number. Nothing imports this
    # library, so nothing can collide with it.
    VINTAGE_RESEARCH = "vintage_research"
    # Concepts the quick-prompt screen produced -- a typed idea or a pool roll
    # turned straight into a concept, same reasoning as VINTAGE_RESEARCH: its
    # own library so nothing imported from a document can ever collide with
    # it.
    DESIGN_PROMPT = "design_prompt"


class ConceptStatus(StrEnum):
    """Where a concept sits in the backlog.

    The long-lived idea, not one execution of it -- attempts have their own
    state machine. ``held`` records a conditional retirement or a deliberate
    pause: a decision that has not been made yet, which is not the same thing
    as ``retired``, where it has.
    """

    BACKLOG = "backlog"
    READY = "ready"
    EXPLORING = "exploring"
    APPROVED = "approved"
    REJECTED = "rejected"
    HELD = "held"
    RETIRED = "retired"
    SUPERSEDED = "superseded"


# Statuses only the application can set. The importer derives backlog, held and
# retired from the Markdown and writes nothing else; once a concept carries one
# of these, re-import keeps it and reports any disagreement rather than silently
# resolving it -- the same rule the world importer follows for shots.
WORKFLOW_OWNED_CONCEPT_STATUSES: frozenset[ConceptStatus] = frozenset(
    {
        ConceptStatus.READY,
        ConceptStatus.EXPLORING,
        ConceptStatus.APPROVED,
        ConceptStatus.REJECTED,
        ConceptStatus.SUPERSEDED,
    }
)


class ConceptKind(StrEnum):
    """What kind of execution a concept calls for.

    The importer only ever derives ``garment_led`` (rounds 05-06 declare their
    garment in the entry itself); everything else defaults to ``other`` and is
    classified by the owner as concepts are worked, because reading a kind out
    of prose would be a guess presented as a fact.
    """

    IMAGE = "image"
    TYPOGRAPHY = "typography"
    MIXED = "mixed"
    GARMENT_LED = "garment_led"
    OTHER = "other"


class DesignAttemptMethod(StrEnum):
    """How a design attempt was produced."""

    IMAGE_GENERATION = "image_generation"
    DETERMINISTIC_COMPOSITION = "deterministic_composition"
    MANUAL_IMPORT = "manual_import"
    HYBRID = "hybrid"


class DesignAttemptState(StrEnum):
    """Lifecycle of one design attempt.

    Deliberately its own PostgreSQL type rather than a reuse of
    ``attempt_state``: migration 0017 taught ``composed_designs`` to share the
    photography enum, which means any value added for designs would silently
    widen the photography pipeline's vocabulary too. A design attempt also has
    no ``prompt_ready`` or ``reviewing`` -- borrowing the type would carry
    states that are meaningless here.
    """

    PLANNED = "planned"
    GENERATING = "generating"
    GENERATED = "generated"
    AWAITING_DECISION = "awaiting_decision"
    APPROVED = "approved"
    REJECTED = "rejected"
    VARIATION_REQUESTED = "variation_requested"
    FAILED = "failed"


class DesignDecisionKind(StrEnum):
    """What the owner decided about a design attempt.

    The same three values as ``HumanDecisionKind`` and a separate type for the
    same reason ``DesignAttemptState`` is: sharing the photography type couples
    two domains that must be able to evolve apart. There is no ``held`` here --
    holding is a concept-level status; an undecided attempt simply stays at
    ``awaiting_decision``.
    """

    APPROVED = "approved"
    REJECTED = "rejected"
    VARIATION_REQUESTED = "variation_requested"


# The attempt state each design decision moves the attempt to. All three are
# terminal: a decided attempt is history, and another take is a new attempt row
# with ``parent_attempt_id`` pointing back at this one.
DESIGN_DECISION_ATTEMPT_STATES: dict[DesignDecisionKind, DesignAttemptState] = {
    DesignDecisionKind.APPROVED: DesignAttemptState.APPROVED,
    DesignDecisionKind.REJECTED: DesignAttemptState.REJECTED,
    DesignDecisionKind.VARIATION_REQUESTED: DesignAttemptState.VARIATION_REQUESTED,
}


class DesignAssetKind(StrEnum):
    """The role a stored design file plays.

    Roles rather than formats -- ``mime_type`` already records what the bytes
    are; this records why they exist. Several kinds legitimately repeat per
    attempt (a separation per ink, a mockup per garment), so uniqueness lives
    on the path, not the kind.
    """

    ARTWORK = "artwork"
    PREVIEW = "preview"
    PRINT_MASTER = "print_master"
    SEPARATION = "separation"
    SOURCE = "source"
    MOCKUP = "mockup"


class CollectionRole(StrEnum):
    """A product's role in the range, ``SHIRTFACED_PRODUCT_DESIGN_CONSTITUTION``
    §4.

    The constitution's five, not ``domain.ts``'s six. That file carried
    ``staple`` and ``capsule`` and lacked ``anchor``; the constitution is the
    governing document and §4 names Anchor, Core, Expression, Hero and
    Collaboration. The discrepancy is recorded in ADR-018 rather than split the
    difference, because a role nobody can point to in the constitution is a
    role nobody can defend in a review.

    A collection must not consist entirely of hero or expression products
    (§4's closing rule). Nothing enforces that yet -- it is a property of a
    collection, and collections are not modelled.
    """

    ANCHOR = "anchor"
    CORE = "core"
    EXPRESSION = "expression"
    HERO = "hero"
    COLLABORATION = "collaboration"


class LayoutArchetype(StrEnum):
    """The approved layout library, constitution §6 — A1 through A8.

    "Every product must select one archetype before final artwork development.
    Departure from the library requires a written reason and additional
    review."
    """

    A1_SMALL_FRONT_LARGE_BACK = "a1_small_front_large_back"
    A2_FRONT_HERO_REAR_SIGNATURE = "a2_front_hero_rear_signature"
    A3_FRONT_HERO_CLEAN_BACK = "a3_front_hero_clean_back"
    A4_MICRO_FRONT_BACK_HERO = "a4_micro_front_back_hero"
    A5_UNEQUAL_FRONT_AND_BACK = "a5_unequal_front_and_back"
    A6_IMAGE_LANGUAGE_SPLIT = "a6_image_language_split"
    A7_MULTI_ZONE = "a7_multi_zone"
    A8_JUMBO_FIELD = "a8_jumbo_field"


class GraphicArchetype(StrEnum):
    """The dominant graphic family, constitution §8.

    "A design may contain supporting elements, but it must have one dominant
    archetype and one dominant proposition."
    """

    IMAGE_LED_HERO = "image_led_hero"
    TYPOGRAPHIC_HERO = "typographic_hero"
    EMBLEM_OR_BADGE = "emblem_or_badge"
    IMAGE_AND_TITLE_LOCKUP = "image_and_title_lockup"
    POSTER_OR_EDITORIAL = "poster_or_editorial"
    SYMBOLIC_ICON_SYSTEM = "symbolic_icon_system"
    COLLAGE_CONTROLLED_FRAME = "collage_controlled_frame"
    CHARACTER_OR_OBJECT_PORTRAIT = "character_or_object_portrait"
    ALL_OVER_OR_JUMBO_FIELD = "all_over_or_jumbo_field"


class ZoneState(StrEnum):
    """What a garment zone is for, constitution §5.

    "Each available zone must be assigned one state." Blank space is valid only
    when chosen deliberately, which is why ``NEGATIVE_SPACE`` is a state a
    person selects rather than the absence of a record.
    """

    ACTIVE_GRAPHIC = "active_graphic"
    PERMANENT_IDENTITY = "permanent_identity"
    NEGATIVE_SPACE = "negative_space"
