# SHIRTFACED — The Shirtfaced Shout

Status: Product/activation concept — build-ready infrastructure, activation timing not yet approved  
Date: 13 August 2026  
Scope: Low-friction recurring ownership ritual linked to numbered garments

## Governance

Only project-owner approvals become rules. Recommendations in this document are options unless explicitly approved.

The infrastructure needed to support this mechanic is part of the pre-customer build where it overlaps with the approved numbered-garment ownership system.

---

# 1. Concept

Every SHIRTFACED garment has its permanent SF garment number. A SHOUT can target one number, a range, suffix, production run, campaign cohort or another defined group.

Examples:

`SF 00481`

`SF 01400–01499`

The selected owner receives a defined reward or consequence.

Possible rewards include product, credit, free shipping, access or another approved benefit.

---

# 2. Why it exists

The mechanic can:

- make ownership persist beyond checkout
- make garment numbers meaningful after purchase
- give customers a recurring reason to check the brand
- create early-number provenance without fake exclusivity
- work nationally
- require effectively zero effort from the customer

Promotion law, terms, accounting and fulfilment must be handled correctly before any prize-style activation goes live.

---

# 3. Customer experience

The garment already carries its SF number through the ownership system.

A SHOUT publication could be:

`THIS WEEK'S SHOUT: SF 00481`

or:

`CHECK YOUR TAG. SF 01400–01499. YOU'RE ON THE SHOUT.`

The customer's claimed account can verify ownership automatically.

---

# 4. System requirements

Build support for:

- unique garment number generation
- garment-to-owner mapping
- campaign/run/range querying
- eligibility rules configurable by admin
- selection/audit history
- reward assignment
- claim or automatic fulfilment state
- refund/return/cancellation interaction
- customer notification
- privacy treatment
- admin audit log
- terms/promotion metadata where required

The mapping must be internal, auditable and tied to the same garment identity used by YOUR SHIT.

---

# 5. Data model extension

Possible fields/entities:

- `shout_event_id`
- `selection_type`
- `selection_criteria`
- `garment_id`
- `owner_account_id`
- `selected_at`
- `notified_at`
- `claimed_at`
- `reward_id`
- `fulfilment_status`
- `eligibility_snapshot`
- `audit_metadata`

Do not duplicate the master garment number in a separate numbering system unless explicitly approved.

---

# 6. Activation variants

Possible variants:

- single garment number
- number range
- suffix event
- first-customer anniversary call-back
- production-run event
- campaign-specific event
- Gary's Shout
- historic low-number recognition

These are options, not locked cadence or reward rules.

---

# 7. Pre-customer validation

Validate the system before customer one:

- deterministic selection
- no duplicate/ambiguous garment IDs
- correct current-owner resolution
- transfer handling
- return/refund handling
- notification flow
- reward fulfilment
- audit replay
- admin override/support path
- legal terms attachment where needed

Validation is a readiness requirement, not a reason to defer building the capability.

---

# 8. Measurement once used

Track where relevant:

- notification delivery
- reward claim/fulfilment
- repeat site visits
- direct traffic around SHOUT publication
- customer posts showing numbers
- support burden
- cost per reward
- repeat purchase behaviour among selected cohorts

No cadence, reward value or activation date is approved by this document alone.