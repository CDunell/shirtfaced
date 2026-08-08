# SHIRTFACED — END-TO-END PUBLISHING PIPELINE

**Status:** Target Architecture / Product Vision  
**Date:** 2026-08-08  
**Target:** ~90% automated production with explicit human approval at critical creative and commercial gates.

---

## 1. The end state

SHIRTFACED Studio becomes the operating system for the brand.

A concept should be able to move through one traceable pipeline:

```text
IDEATION
  ↓
DESIGN SYSTEM / DESIGN GENERATION
  ↓ [HUMAN GATE — design approval]
PRODUCT / GARMENT DEFINITION
  ↓
GARMENT PLACEMENT
  ↓ [HUMAN GATE — product accuracy]
WORLD + SCENE PLANNING
  ↓
PHOTOGRAPHY GENERATION
  ↓ [HUMAN GATE — hero/source asset approval]
VIDEO GENERATION / EDIT
  ↓ [HUMAN GATE — motion realism when used]
SITE / DROP ASSEMBLY
  ↓ [HUMAN GATE — commercial release]
SOCIAL DERIVATIVES
  ↓ [HUMAN GATE — post approval]
PUBLISHING QUEUE
  ↓
LIVE SITE + INSTAGRAM + TIKTOK + LATER CHANNELS
  ↓
TRAFFIC + SALES + CONTENT PERFORMANCE
  ↓
MARKETING ENGINE
  ↓
NEXT ACTION / CADENCE / PROMOTION / RETARGETING / CREATIVE BRIEF
  └──────────────────────────────────────────────→ back into pipeline
```

The system automates production and orchestration. Humans approve taste, truth and commercial release.

---

## 2. Architectural principle: one source, many renderers

The pipeline must not be a chain of prompts copying prompts.

Creative truth lives in structured source objects. Renderers consume those objects.

The existing Scene Specification principle remains correct: WORLD and SCENE are creative sources; photography, video, Instagram, TikTok, website, paid media and product placement are downstream renderers.

Add two upstream sources that Scene does not own:

- **Design Specification** — the canonical artwork/design intent.
- **Product Specification** — garment/SKU/colour/placement/print truth.

Add one downstream orchestration source:

- **Campaign / Drop Specification** — commercial objective, launch state, timing, channels, cadence policy, inventory and promotion constraints.

No renderer silently changes these sources.

---

## 3. Core domain graph

```text
Idea
 └─ DesignSpec
     ├─ DesignAttempt(s)
     └─ ApprovedDesign
          └─ ProductSpec
              ├─ GarmentVariant / SKU
              ├─ PlacementSpec
              └─ ApprovedProductProof
                   ├─ World
                   │   └─ Scene
                   │       ├─ Shot
                   │       │   ├─ PhotoAttempt
                   │       │   └─ ApprovedPhoto
                   │       └─ MotionIntent
                   │           ├─ VideoAttempt
                   │           └─ ApprovedVideo
                   └─ Campaign / Drop
                       ├─ SiteRelease
                       ├─ SocialPost
                       │   ├─ SocialDerivative(s)
                       │   ├─ Approval
                       │   └─ PublicationJob
                       ├─ PromotionPlan
                       └─ PerformanceSnapshot(s)
```

Every object has a stable ID. Every derivative records its parents. Nothing important should exist only as a filename.

---

## 4. Stage 0 — ideation and opportunity

### Inputs
- human idea
- phrase/concept bank
- design-element archive
- world/story opportunity
- product gap
- campaign requirement
- performance signal from Marketing Engine

### Automation
- normalise idea into an `IdeaBrief`
- classify likely design families
- retrieve compatible design elements/references
- flag similarity/repetition against existing catalogue
- generate production candidates/briefs

### Human gate
Not every idea needs approval before exploration. Approval becomes mandatory before a design is promoted to product candidate.

### Required fields
```text
idea_id
origin: human | world | marketing_engine | performance | backlog
concept
why_now
world_affinity[]
product_affinity[]
campaign_id?
status
```

---

## 5. Stage 1 — deterministic design engine

The design engine should use the curated garment-design element archive rather than asking a model to invent the entire visual language from scratch every time.

### Responsibilities
- assemble design direction
- select layout/type/illustration/mark treatments
- generate deterministic variants where possible
- invoke image generation only for genuinely generative elements
- enforce print constraints
- create production-ready master candidates
- record provenance of every element

### Automated checks
- dimensions/resolution
- transparency
- colour count where screen-print constrained
- minimum line weight
- printable bounds
- forbidden background/mockup contamination
- duplicate/similarity check
- spelling/text extraction where relevant

### GATE 1 — DESIGN APPROVAL
Human chooses:
- approve
- reject + reason
- variation
- hold

**Approval output:** immutable approved design version. Later edits create a new version.

---

## 6. Stage 2 — product and garment truth

An approved design becomes one or more products.

### Product Specification
```text
product_id
approved_design_id
garment_type
blank/style
colourway
sizes
print_method
placement
physical_dimensions
inventory_mode
price
cost
margin
sku_map
release_state
```

This is commercial truth. Photography is not allowed to invent a different garment, colour, placement or print scale.

### Automation
- generate placement coordinates
- create front/back/alternate placement proofs
- create SKU/variant records
- calculate basic margin
- prepare ecommerce metadata shell

### GATE 2 — PRODUCT ACCURACY
Human approves the visual product proof and commercial configuration.

This is distinct from liking the design.

---

## 7. Stage 3 — World Builder and Scene Specification

World Builder turns the brand universe into production-ready scenes.

### Creative source
Human-authored:
- narrative
- mood
- cast
- location
- lighting
- emotional state
- continuity
- canon rules
- motion intent
- product role/prominence

### Generated downstream
- shot list
- photography prompts
- video prompts
- placement instructions
- crop requirements
- social metadata
- filenames

### Continuity
Scene records previous/next scene, continuing people/props, time, weather and emotional trajectory.

Product appearance references `product_id` and `placement_spec_id`; it does not duplicate product truth in prose.

---

## 8. Stage 4 — photography studio

### Inputs
- Scene Specification
- Shot Specification
- approved Product Specification where product is present
- continuity state

### Automation
1. choose next deterministic shot
2. assemble photography prompt
3. generate one or more attempts
4. run technical checks
5. store attempts + model/settings/cost/provenance
6. present review set

### Automated checks
- output dimensions
- obvious generation failure
- product presence when required
- expected garment region/placement where machine-checkable
- logos/text contamination
- crop viability for intended channels
- duplicate similarity

### GATE 3 — SOURCE PHOTO APPROVAL
Human decides whether the photograph belongs in SHIRTFACED.

Approval creates an `ApprovedPhoto`; rejected attempts remain useful training/decision evidence and are never silently deleted from provenance.

Approved photography can branch simultaneously to website, social, video reference and paid media.

---

## 9. Stage 5 — video studio

Video consumes Scene + Motion Intent + approved source/reference frames. It does not reverse-engineer creative intent from a photography prompt.

### Automation
- derive video prompt/settings
- select approved reference image(s)
- generate clip
- validate duration/aspect/resolution
- assemble simple documentary sequences
- apply approved Shirtfaced social motion assets when required
- produce clean master and platform derivatives

### Editorial rules
- real actions
- straight cuts
- held shots
- ambient sound where appropriate
- no fake trend language forced onto the footage

### GATE 4 — MOTION APPROVAL
Required for generated motion before public use.

Human judges whether movement, people, product and camera behaviour feel real.

---

## 10. Stage 6 — site/drop assembly

A Campaign/Drop Specification joins product, creative and commercial timing.

```text
campaign_id
type: evergreen | drop | launch | promotion | clearance | event
objective
products[]
worlds/scenes[]
start_at
end_at?
launch_at
inventory_constraints
margin_floor
channel_policy
cadence_policy_id
promotion_policy_id
status
```

### Automation
- build product gallery from approved assets
- prepare collection/drop page
- select approved hero/detail/lifestyle assets
- populate metadata
- stage product availability
- validate links/variants/pricing
- prepare release job

### GATE 5 — COMMERCIAL RELEASE
Human approves:
- product truth
- price
- inventory/availability
- site presentation
- launch time
- campaign state

Nothing goes live because a creative asset was approved.

---

## 11. Stage 7 — Social Studio

Current Social Studio is the beginning of this stage.

### Current manual-source flow
```text
approved/uploaded photo
→ choose Auto/Light/Dark/Adaptive
→ choose Clean/Fingerprint/Identity
→ choose platform outputs
→ GO
→ generated files
```

### Target flow
When an approved source asset arrives from Photography/Video:

1. system reads its Scene, Product and Campaign context
2. determines eligible channels
3. chooses LIGHT/DARK/ADAPTIVE from media
4. chooses recipe and branding strength from campaign/post role
5. composes crops/overlays
6. generates caption candidates, alt text, metadata and cover
7. validates safe zones and output dimensions
8. creates a `SocialPostDraft`
9. presents the finished post package for approval

Manual override remains available for every choice.

### GATE 6 — SOCIAL APPROVAL
Approve the **post package**, not just the source image.

Approval freezes:
- media/version
- crop
- overlay
- cover
- caption
- destination channels
- campaign association

Approved does **not** mean publish immediately. It means eligible for the queue.

---

## 12. Stage 8 — publishing queue

This is the next Social Studio subsystem.

An approved post becomes one or more channel-specific `PublicationJob`s.

### PublicationJob
```text
publication_job_id
social_post_id
campaign_id?
channel: instagram_feed | instagram_reel | instagram_story | tiktok | future
account_id
asset_version_id
caption_version_id
scheduled_at
scheduled_timezone
priority
cadence_policy_id
promotion_policy_id?
state: queued | scheduled | held | publishing | published | failed | cancelled
external_post_id?
published_at?
failure_reason?
retry_count
created_by
approved_by
```

### Queue UI
Social Studio gains three views:

**APPROVAL** — finished drafts waiting for human approval.  
**QUEUE** — calendar/timeline of approved scheduled posts.  
**LIVE** — published posts with performance/status.

### Approval action
After approving a post:

```text
APPROVE
  ↓
recommended date/time shown
  ↓
accept recommendation OR override
  ↓
QUEUE
```

A separate **Publish now** action may exist but must be explicit.

---

## 13. Cadence engine

Do not hard-code "post every Tuesday at 7pm" into Social Studio.

Cadence belongs to a policy engine so the future Marketing Engine can change recommendations without changing the renderer.

### CadencePolicy inputs
- campaign/drop phase
- launch date
- channel
- content role
- recent posting history
- inventory state
- promotion state
- sales velocity
- content availability
- audience/performance history when available
- minimum/maximum spacing rules

### Drop-cycle states
Suggested state machine:

```text
FOUNDATION
→ TEASE
→ REVEAL
→ LAUNCH
→ PROOF
→ SUSTAIN
→ LAST_CALL (only when factually justified)
→ EVERGREEN / CLOSED
```

Each phase supplies a cadence envelope, not a compulsory schedule.

Example conceptually:
- FOUNDATION favours documentary world-building.
- TEASE introduces product evidence without flooding the feed.
- REVEAL increases product clarity.
- LAUNCH allows denser commercial communication around the actual release.
- PROOF mixes wearers/product/detail with documentary content.
- SUSTAIN reduces frequency unless performance or inventory gives a reason to continue.

The exact numbers remain configurable data and should later be learned/tuned from performance.

### Scheduler rules
- honour human-locked dates/times
- never move a manually locked job
- enforce channel minimum spacing
- avoid accidental duplicate media/copy
- coordinate site go-live before posts that claim a product is live
- hold sale-linked posts if product/checkout/site health fails
- recalculate unlocked future slots when campaign state changes
- log every automated schedule change

---

## 14. Promotion engine hook

Promotion is not the same thing as posting.

A `PromotionPlan` references an already approved/published creative and defines:

```text
promotion_plan_id
campaign_id
source_publication_id
objective
channel
budget_policy
start/end
audience_policy
creative_variant_ids[]
margin_floor
inventory_floor
stop_conditions
approval_state
```

Future Marketing Engine can recommend promotion based on organic response, inventory, margin and sales performance.

**Paid spend requires a commercial approval policy.** The system must not silently increase spend because a post got likes.

---

## 15. Marketing Engine — future contract

Marketing Engine is deliberately a separate decision layer. Social Studio renders and queues; Marketing Engine recommends what should happen next.

### Inputs
- publication history
- impressions/reach/views
- watch time/completion where available
- saves/shares/comments
- profile/site clicks
- sessions
- product views
- add-to-cart
- checkout starts
- orders
- revenue
- units
- gross margin
- inventory by SKU
- refunds/cancellations when relevant
- promotion spend and attributed results
- campaign/drop phase
- available approved creative inventory

### Outputs
The engine emits **recommendations/events**, never direct creative approval:

```text
CadenceRecommendation
ContentNeed
PromotionRecommendation
InventoryWarning
CreativeFatigueSignal
DropPhaseRecommendation
SiteMerchandisingRecommendation
ExperimentRecommendation
```

Examples:
- "Need another non-commercial World 01 Reel before next product post."
- "Product proof is converting; surface approved alternate wearer image."
- "Inventory below threshold; suppress promotion candidates for size-constrained SKU."
- "Launch burst complete; return to sustain cadence."
- "No suitable approved creative remains; create a ContentNeed for World Builder."

That last event closes the loop back to ideation/World Builder without automatically publishing generated rubbish.

---

## 16. Sales and attribution layer

The pipeline is incomplete without a shared event model from content to revenue.

Every live URL/post/campaign should carry stable IDs through analytics where platform capability permits.

### Minimum event chain
```text
publication_job_id
→ external_post_id
→ campaign_id
→ landing/session
→ product_id / sku
→ add_to_cart
→ checkout
→ order
→ revenue / margin
```

Attribution will never be perfect. Store both direct attribution and broader campaign/time-window evidence rather than pretending a single model is truth.

### Performance snapshots
Use append-only snapshots/time series so the Marketing Engine can compare:
- first hours
- first day
- 3/7/14/30 day performance
- organic vs promoted
- content role
- world/scene
- product
- campaign phase

---

## 17. Approval gates — the 10% humans must own

The goal is not "human clicks approve on everything." That would automate nothing.

Humans intervene where judgment changes brand or commercial risk.

| Gate | Human owns | Machine owns |
|---|---|---|
| Design | taste, originality, brand fit | generation, validation, variants |
| Product | print/garment truth | placement calculation, SKU preparation |
| Photo | whether it belongs in the world | prompt, generation, technical QA |
| Video | realism and editorial feel | prompt, generation, derivative assembly |
| Commercial release | price/inventory/site/drop truth | page assembly and checks |
| Social | final post package | crops, overlays, metadata, recommendations |
| Paid promotion | spend/risk policy where required | recommendations, pacing within approved bounds |

Routine derivative generation, naming, resizing, scheduling, retries, metadata, reporting and analytics ingestion require no human click when rules pass.

---

## 18. Global state machine

Every major asset should follow explicit states rather than loose booleans.

```text
DRAFT
→ GENERATED
→ REVIEW_REQUIRED
→ APPROVED
→ DERIVATIVE_READY
→ QUEUED
→ SCHEDULED
→ LIVE
→ MEASURED
→ ARCHIVED
```

Possible side states:

```text
REJECTED
HELD
FAILED
SUPERSEDED
CANCELLED
```

Approval is version-specific. Changing approved media/copy/product truth after approval invalidates downstream approval where material.

---

## 19. Event bus / orchestration hooks

Do not make each Studio bench call the next screen directly.

Use domain events/jobs so future modules can subscribe without rewriting the pipeline.

### Core events
```text
idea.created
design.generated
design.approved
product.configured
product.approved
scene.ready
photo.generated
photo.approved
video.generated
video.approved
site.release_ready
site.release_approved
site.published
social.draft_ready
social.approved
publication.queued
publication.scheduled
publication.published
publication.failed
performance.updated
order.created
inventory.changed
campaign.phase_changed
marketing.recommendation_created
content.need_created
```

Each event contains stable IDs, version IDs, timestamp, actor (`human`, `system`, `agent`), correlation/run ID and provenance.

Implementation can begin with a database outbox/job table. It does not require infrastructure theatre on day one. The contract is the important part.

---

## 20. Automation run ledger

Every automated action should be inspectable.

```text
run_id
pipeline_stage
input_ids[]
output_ids[]
model/tool/version
policy_version
started_at
finished_at
status
cost
error
retry_of?
triggered_by
```

This provides:
- auditability
- cost tracking
- reproducibility
- failure recovery
- model/provider swaps
- debugging without guessing what the robot did at 2am

---

## 21. Asset lineage and versioning

Never overwrite an approved master in place.

Every asset derivative records:
- source asset ID
- source version
- renderer version
- template/overlay version
- crop/transform
- generated filename
- checksum
- approval status

A post scheduled for Tuesday must still point to the exact approved bytes on Tuesday even if V4 social templates are generated on Monday night.

---

## 22. Failure and safety behaviour

Automation fails closed at public/commercial boundaries.

### Examples
- image generation fails → retry policy, then review queue
- overlay asset missing → do not silently export unbranded when branding was required
- site product unavailable → hold "LIVE NOW" publication
- publishing API fails → retry with idempotency; never create duplicates
- analytics unavailable → publishing continues; measurement marks delayed
- Marketing Engine unavailable → locked queue continues; no speculative rescheduling
- inventory feed stale → suppress inventory-dependent promotion recommendations
- approved source superseded → future derivatives marked stale and require regeneration/reapproval as appropriate

---

## 23. Scheduling UX

### Social Studio — approved state
After GO and review:

```text
[ APPROVE ]

Channels      Instagram Feed · TikTok
Campaign      Drop 01
Role          Documentary / Tease / Reveal / Launch / Proof / Sustain
Recommended  Fri 14 Aug · 7:42 pm AEST
Cadence       31h after previous feed post
Reason        TEASE phase · documentary gap satisfied · launch in 42h

[ Queue recommended ]   [ Change date/time ]   [ Hold ]
```

### Queue
Calendar + chronological list. Each job shows:
- thumbnail/cover
- channel
- campaign/drop
- role
- date/time/timezone
- locked/recommended
- dependency health
- approval state
- publish state

Drag/reschedule is a human lock. The cadence engine works around locked posts.

### Campaign view
Shows the whole commercial arc across:
- site release
- email/future channels
- Instagram
- TikTok
- paid promotion
- inventory
- sales

This is where the future Marketing Engine recommendations appear.

---

## 24. Site/social dependency graph

Publishing must understand claims.

Examples:

`DROP LIVE` depends on:
- Product approved
- Site release approved
- Product URL healthy
- launch time reached
- product available

`LAST CALL` depends on a factual campaign/inventory condition.

`PRODUCT PROOF` depends on approved Product Specification and approved visual proof.

Pure documentary content has fewer dependencies and can remain available when commerce is held.

---

## 25. Content inventory as a first-class resource

Marketing Engine cannot schedule intelligently if it does not know what approved material exists.

Maintain queryable inventory by:
- world
- scene
- event
- people/role
- product
- content role
- photo/video
- light/dark/adaptive
- platform eligibility
- used/unused
- last used
- campaign
- quality/approval

The engine selects from **approved inventory first**. Generation is triggered only when a genuine content gap exists.

---

## 26. Experiments without wrecking canon

Marketing experiments operate on production variables, not the universe itself.

Safe examples:
- post time
- cover frame
- caption length/mode
- crop
- product/detail ordering in carousel
- promotion audience/budget within policy

Unsafe automatic experiments:
- changing brand voice
- changing world canon
- changing product artwork
- making people perform trend behaviour
- inventing urgency or stock claims

---

## 27. Data model additions required

Minimum new persistent entities:

```text
IdeaBrief
DesignSpec
DesignVersion
ProductSpec
ProductVariant
PlacementSpec
Campaign
CampaignPhase
SocialPost
SocialPostVersion
SocialDerivative
PublicationJob
CadencePolicy
PromotionPlan
PerformanceSnapshot
MarketingRecommendation
ContentNeed
ApprovalDecision
AutomationRun
DomainEvent / OutboxEvent
```

Existing World/Scene/Shot/asset records should be referenced, not duplicated.

---

## 28. API boundaries

Design stable service contracts before provider integrations.

```text
POST /designs/{id}/generate
POST /designs/{id}/approve
POST /products/{id}/proof
POST /products/{id}/approve
POST /scenes/{id}/render/photo
POST /assets/{id}/approve
POST /scenes/{id}/render/video
POST /campaigns/{id}/stage-site
POST /campaigns/{id}/approve-release
POST /social/drafts
POST /social/{id}/approve
POST /social/{id}/queue
PATCH /publication-jobs/{id}/schedule
POST /publication-jobs/{id}/hold
POST /publication-jobs/{id}/publish-now
GET  /publishing/queue
GET  /campaigns/{id}/performance
GET  /marketing/recommendations
POST /marketing/recommendations/{id}/accept
POST /marketing/recommendations/{id}/dismiss
```

Provider-specific Meta/TikTok/store APIs live behind adapters.

---

## 29. Provider adapter rule

Never make domain state depend on one platform's payload shape.

Adapters:
```text
ImageGenerationAdapter
VideoGenerationAdapter
StorageAdapter
StorefrontAdapter
InstagramPublisher
TikTokPublisher
AnalyticsAdapter
CommerceAdapter
PaidMediaAdapter
```

Domain code asks to `publish(job)` or `read_orders(window)`; adapters translate to whatever API exists at the time.

---

## 30. What is built now vs next

### Exists now / established
- World/canon/continuity production architecture
- Scene-as-source renderer principle
- photo library/review workflow
- generated social brand asset system V1–V3
- social publishing recipes and launch system
- Social Studio source selection
- Auto/Light/Dark/Adaptive analysis
- Clean/Fingerprint/Identity selection
- deterministic image crop/overlay/export for current still outputs
- explicit human creative approval philosophy

### Immediate next build
1. **Social approval persistence** — current browser exports become stored `SocialPostVersion` + derivatives.
2. **Publishing Queue UI** — Approval / Queue / Live.
3. **PublicationJob + CadencePolicy schema.**
4. **Manual scheduling first** — date/time/timezone + locks + holds.
5. **Dependency checks** — campaign/site/product state.
6. **Publisher adapter interfaces** with fake/local adapters before real credentials.
7. **Campaign/Drop object** tying site, product and social together.
8. **Performance ingestion contract.**
9. **Marketing Engine event/recommendation contract.**
10. Only then connect real social publishing APIs and automate recommendations.

This sequence keeps today's Social Studio useful while avoiding a throwaway scheduler.

---

## 31. Gaps identified

The existing system had strong creative production concepts but these missing joins prevented a true end-to-end engine:

### Gap A — approval was not a durable cross-stage object
Fix: version-specific `ApprovalDecision` with actor, time, stage and target version.

### Gap B — no persistent SocialPost package
Browser exports alone cannot be queued reliably.
Fix: store the approved media/crop/overlay/caption package and exact bytes/version.

### Gap C — no scheduling domain
Fix: `PublicationJob`, explicit timezone, lock/hold/retry/idempotency states.

### Gap D — cadence had no owner
Fix: `CadencePolicy` belongs to campaign orchestration, not templates or publisher adapters.

### Gap E — site release and social claims were independent
Fix: dependency graph prevents "live" posts before commerce is actually live.

### Gap F — no commercial campaign state machine
Fix: FOUNDATION → TEASE → REVEAL → LAUNCH → PROOF → SUSTAIN → LAST_CALL/EVERGREEN/CLOSED.

### Gap G — analytics did not close the loop
Fix: shared campaign/publication/product IDs + performance snapshots + order/inventory events.

### Gap H — Marketing Engine boundary was undefined
Fix: it emits recommendations and content needs; it does not silently approve creative.

### Gap I — generation could become the default response to every content need
Fix: query approved content inventory first, generate only to fill a real gap.

### Gap J — no automation provenance
Fix: `AutomationRun` + domain event/outbox ledger.

### Gap K — downstream assets could drift when an upstream approved version changes
Fix: immutable versions + stale derivative invalidation.

### Gap L — paid promotion could accidentally be treated as ordinary scheduling
Fix: separate PromotionPlan, budget policy, margin/inventory constraints and approval rules.

---

## 32. 90% automation definition

90% automated means the system should perform without human labour:
- prompt assembly
- routine generation attempts
- technical validation
- derivative generation
- crop/resize/overlay
- filenames/metadata/alt-text drafts
- asset storage/cataloguing
- queue recommendations
- cadence calculations
- dependency checks
- scheduled publishing
- retries
- analytics ingestion
- performance summaries
- content-gap detection
- next-action recommendations

The human should spend time on:
- selecting ideas worth making
- approving design
- approving product truth
- approving the source photograph/video
- approving commercial release
- approving the finished social package
- approving exceptional/high-risk promotion decisions

The machine does the plumbing. The human remains the editor and publisher of record.

---

## 33. Target operating loop

At maturity, a normal cycle looks like this:

```text
Marketing Engine / human identifies opportunity
→ IdeaBrief created
→ design candidates generated
→ HUMAN approves design
→ product/placement generated
→ HUMAN approves product truth
→ World Builder selects/creates suitable Scene
→ photo + video production runs
→ HUMAN approves source media
→ site/drop package assembled
→ HUMAN approves commercial release
→ social packages generated automatically
→ HUMAN approves posts
→ cadence engine assigns recommended slots
→ approved jobs publish automatically at locked/recommended times
→ analytics + commerce events return
→ Marketing Engine evaluates campaign state
→ use existing approved content, reschedule unlocked queue, recommend promotion,
  or create a ContentNeed
→ ContentNeed feeds World Builder/design engine
→ repeat
```

That is the SHIRTFACED production and publishing engine.

Not a social scheduler bolted onto an image generator. A closed-loop brand operating system.
